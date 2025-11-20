"""
ReAct Agent for Conversational Assistant
Uses tools and memory to help users adjust CVs and skills
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import Tool
from typing import Dict, Any, List, Optional, Callable
import json

# Try to import AgentExecutor - different versions have different locations
try:
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain import hub
    HAS_AGENT_EXECUTOR = True
except ImportError:
    try:
        from langchain.agents.agent import AgentExecutor
        from langchain.agents.react.base import ReActDocstoreAgent
        HAS_AGENT_EXECUTOR = False
    except ImportError:
        HAS_AGENT_EXECUTOR = False
try:
    from langchain.memory import ConversationBufferMemory
except ImportError:
    try:
        from langchain_core.memory import ConversationBufferMemory
    except ImportError:
        # Try to import message types for proper fallback
        try:
            from langchain_core.messages import HumanMessage, AIMessage
        except ImportError:
            # If message types not available, create simple compatible classes
            class HumanMessage:
                def __init__(self, content):
                    self.content = content
                    self.type = "human"
            
            class AIMessage:
                def __init__(self, content):
                    self.content = content
                    self.type = "ai"
        
        # Simple fallback with proper message types
        class SimpleChatMemory:
            def __init__(self):
                self.messages = []
            
            def add_user_message(self, msg):
                self.messages.append(HumanMessage(msg))
            
            def add_ai_message(self, msg):
                self.messages.append(AIMessage(msg))
        
        class ConversationBufferMemory:
            def __init__(self, memory_key="chat_history", return_messages=True):
                self.memory_key = memory_key
                self.return_messages = return_messages
                self.chat_memory = SimpleChatMemory()

from utils.tools import (
    update_cv_section_tool,
    search_cv_content_tool,
    extract_skills_tool,
    compare_skills_tool
)
from utils.langfuse_config import create_langfuse_callback


def create_assistant_tools(api_key: str, optimized_cv: str) -> tuple[List[Tool], Callable[[], str]]:
    """Create tools for the assistant agent, bound with API key and current CV.
    
    Returns:
        Tuple of (tools_list, get_current_cv_function)
    """
    
    def extract_cv_skills_wrapper(text: str) -> str:
        result = extract_skills_tool.invoke({"text": text, "text_type": "cv", "api_key": api_key})
        skills = result.get("skills", [])
        return json.dumps({"skills": skills, "count": len(skills)})
    
    def extract_job_skills_wrapper(text: str) -> str:
        result = extract_skills_tool.invoke({"text": text, "text_type": "job", "api_key": api_key})
        skills = result.get("skills", [])
        return json.dumps({"skills": skills, "count": len(skills)})
    
    def compare_skills_wrapper(cv_skills_json: str, job_skills_json: str) -> str:
        cv_data = json.loads(cv_skills_json)
        job_data = json.loads(job_skills_json)
        result = compare_skills_tool.invoke({
            "cv_skills": cv_data.get("skills", []),
            "job_skills": job_data.get("skills", []),
            "api_key": api_key
        })
        return json.dumps(result)
    
    # Store current CV in closure for tools that need it
    current_cv = [optimized_cv]  # Use list to allow modification in nested functions
    
    def update_cv_section_wrapper(section: str, content: str) -> str:
        """Update CV section using the current CV."""
        result = update_cv_section_tool.invoke({
            "cv_text": current_cv[0],
            "section_name": section,
            "new_content": content
        })
        # Update current_cv if successful
        if result.get("status") == "success" and "updated_cv" in result:
            current_cv[0] = result["updated_cv"]
        return json.dumps(result)
    
    def search_cv_wrapper(search_term: str) -> str:
        """Search in the current CV."""
        result = search_cv_content_tool.invoke({
            "cv_text": current_cv[0],
            "search_term": search_term
        })
        return json.dumps(result)
    
    # Function to get current CV (for updating after tool calls)
    def get_current_cv() -> str:
        return current_cv[0]
    
    tools = [
        Tool(
            name="update_cv_section",
            func=update_cv_section_wrapper,
            description="Update a specific section in the CV. Input: section_name (string like 'Experience', 'Skills', 'Certifications', 'Education', 'Summary'), new_content (string with the COMPLETE new section content - this REPLACES the entire section content, so include all items you want to keep). IMPORTANT: To remove text, first use search_cv to find the current section content, then provide new_content with that text removed but ALL other content preserved. Returns JSON with 'updated_cv' (the complete updated CV text) and 'status'. The CV is automatically updated for subsequent operations."
        ),
        Tool(
            name="search_cv",
            func=search_cv_wrapper,
            description="Search for specific content in the current CV. Input: search_term (string to search for). Returns matching lines and locations. The search is performed on the current CV automatically."
        ),
        Tool(
            name="extract_cv_skills",
            func=extract_cv_skills_wrapper,
            description="Extract skills from CV text. Input: text (string, the CV text). Returns JSON with skills list and count."
        ),
        Tool(
            name="extract_job_skills",
            func=extract_job_skills_wrapper,
            description="Extract skills from job description text. Input: text (string, the job description). Returns JSON with skills list and count."
        ),
        Tool(
            name="compare_skills",
            func=lambda cv_json, job_json: compare_skills_wrapper(cv_json, job_json),
            description="Compare CV skills with job skills. Input: cv_skills_json (JSON string with skills), job_skills_json (JSON string with skills). Returns comparison results."
        )
    ]
    
    return tools, get_current_cv


def process_assistant_request_with_agent(
    user_request: str,
    original_cv: str,
    optimized_cv: str,
    job_description: str,
    cv_skills: List[str],
    job_skills: List[str],
    matched_skills: Dict[str, Any],
    api_key: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    language: str = "fr",
    memory: Optional[ConversationBufferMemory] = None,
    rag_system: Optional[Any] = None,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process assistant request using a ReAct agent with tools and memory.
    Uses LangChain's AgentExecutor for true ReAct agent behavior.
    """
    try:
        langfuse_callback = create_langfuse_callback(
            trace_name="assistant_conversation",
            session_id=session_id or "default",
            metadata={
                "model": model,
                "temperature": temperature,
                "language": language,
                "has_rag": rag_system is not None,
                "request_type": "cv_modification"
            }
        )
        
        callbacks = [langfuse_callback] if langfuse_callback else None
        
        llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=api_key,
            callbacks=callbacks
        )
        
        if memory is None:
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
        
        # Create tools for the agent (bound with current CV)
        tools, get_current_cv = create_assistant_tools(api_key, optimized_cv)
        
        # RAG retrieval if available
        rag_context = ""
        sources = []
        if rag_system:
            try:
                # Retrieve relevant chunks using user request as query
                rag_result = rag_system.get_context_with_sources(
                    query=user_request,
                    k_cv=3,
                    k_jd=2
                )
                
                cv_context = rag_result.get("cv_context", "")
                jd_context = rag_result.get("jd_context", "")
                cv_sources = rag_result.get("cv_sources", [])
                jd_sources = rag_result.get("jd_sources", [])
                
                if cv_context or jd_context:
                    rag_context = f"""
Relevant context from semantic search:
CV chunks: {cv_context}
Job description chunks: {jd_context}

Use this context to better understand the user's request and provide accurate responses.
"""
                    sources = cv_sources + jd_sources
            except Exception as e:
                print(f"RAG retrieval failed: {str(e)}")
                rag_context = ""
        
        # Add context variables that tools can access
        context_vars = {
            "optimized_cv": optimized_cv,
            "original_cv": original_cv,
            "job_description": job_description,
            "cv_skills": cv_skills,
            "job_skills": job_skills
        }
        
        # Create a custom prompt that includes context
        language_names = {
            "fr": "French (Français)",
            "en": "English",
            "es": "Spanish (Español)"
        }
        target_language = language_names.get(language, "French (Français)")
        
        # Try to use AgentExecutor if available, fallback to manual if not
        use_agent_executor = HAS_AGENT_EXECUTOR
        agent_executor = None
        
        if use_agent_executor:
            try:
                # Try to use custom prompt first, fallback to hub
                try:
                    from langchain_core.prompts import PromptTemplate
                    # Custom strict ReAct prompt that forces tool usage
                    custom_prompt = PromptTemplate.from_template("""You are a helpful assistant that MUST use tools to perform actions.

You have access to the following tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do, but KEEP IT SHORT
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

CRITICAL: When the user asks to remove/delete text:
1. IMMEDIATELY use search_cv to find it (do not describe, just do it)
2. IMMEDIATELY use update_cv_section to remove it (do not describe, just do it)
3. Then explain what you did

DO NOT describe what you will do - DO IT. Start with Action: immediately.

Begin!

Question: {input}
Thought: {agent_scratchpad}""")
                    prompt_template = custom_prompt
                except:
                    # Fallback to hub prompt
                    prompt_template = hub.pull("hwchase17/react")
                
                # Create agent with ReAct prompt
                agent = create_react_agent(llm, tools, prompt_template)
                
                # Create agent executor with memory
                agent_executor = AgentExecutor(
                    agent=agent,
                    tools=tools,
                    memory=memory,
                    verbose=True,
                    handle_parsing_errors=True,
                    max_iterations=10,  # Increased to allow more tool calls
                    return_intermediate_steps=True  # Important: return tool calls
                )
            except Exception as hub_error:
                # If hub.pull fails, fall through to manual implementation
                use_agent_executor = False
                agent_executor = None
                print(f"Hub not available, using fallback: {hub_error}")
        
        if use_agent_executor and agent_executor:
            try:
                # Prepare input with context - STRICT: Must use tools, not describe
                input_text = f"""You are a helpful assistant that helps users refine their optimized CV and correct skills detection.

{rag_context}

User Request: {user_request}

CRITICAL INSTRUCTIONS - READ CAREFULLY:
- You MUST use the available tools to perform actions. DO NOT describe what you will do - DO IT NOW.
- DO NOT say "I will search" or "I will update" - ACTUALLY CALL THE TOOLS.
- The tools automatically use the current CV - you do NOT need to pass cv_text parameter.
- When the user asks to remove/delete text, you MUST:
  1. IMMEDIATELY call search_cv(search_term="<exact text to find>") - do not describe, just call it
  2. From the search results, identify which section contains the text
  3. IMMEDIATELY call update_cv_section(section_name="<section>", new_content="<complete section without the text>")
  4. The tool will return the updated CV automatically

FORBIDDEN: Do NOT say:
- "I will search" → CALL search_cv NOW
- "I will update" → CALL update_cv_section NOW  
- "Let me do that" → DO IT NOW
- "I'm going to" → DO IT NOW

REQUIRED: You MUST start your response by calling the appropriate tool(s). For deletions:
- Step 1: Call search_cv(search_term="<text>") immediately
- Step 2: Call update_cv_section(section_name="<section>", new_content="<section without text>") immediately
- Step 3: Then explain what you did

Available tools:
- search_cv(search_term): Search in CV. Returns matches with line numbers.
- update_cv_section(section_name, new_content): Updates a section. Returns updated CV.

Example for deletion request:
User: "remove '28/07/2003 | Paris'"
You MUST respond with:
Action: search_cv(search_term="28/07/2003 | Paris")
[Wait for result]
Action: update_cv_section(section_name="Header", new_content="<section without that line>")
[Then explain]

DO NOT describe - ACT. Start by calling tools immediately."""
            
                # Run the agent
                # AgentExecutor handles memory automatically via the memory parameter
                # Pass callbacks to AgentExecutor
                config = {}
                if langfuse_callback:
                    config["callbacks"] = [langfuse_callback]
                
                result = agent_executor.invoke(
                    {"input": input_text},
                    config=config if config else {}
                )
                
                explanation = result.get("output", "")
                
                # Try to extract updated CV from tool results (prioritize tool results)
                updated_cv = optimized_cv
                tool_error = None
                last_updated_cv = None
                
                if "intermediate_steps" in result:
                    # Process steps in reverse to get the most recent update
                    for step in reversed(result["intermediate_steps"]):
                        if len(step) > 1:
                            tool_result = step[1]
                            # Handle both dict and string results
                            if isinstance(tool_result, str):
                                try:
                                    tool_result = json.loads(tool_result)
                                except:
                                    # If not JSON, check if it contains updated_cv pattern
                                    if "updated_cv" in tool_result.lower() or len(tool_result) > 100:
                                        # Might be the CV text itself
                                        if len(tool_result) > len(optimized_cv) * 0.5:
                                            last_updated_cv = tool_result
                                    pass
                            
                            if isinstance(tool_result, dict):
                                # Check for error status
                                if tool_result.get("status") == "error":
                                    tool_error = tool_result.get("error", "Unknown tool error")
                                
                                # Try to get updated_cv from tool result
                                if "updated_cv" in tool_result:
                                    try:
                                        cv_data = tool_result["updated_cv"]
                                        # If it's a string, try to parse it
                                        if isinstance(cv_data, str):
                                            try:
                                                parsed = json.loads(cv_data)
                                                if isinstance(parsed, dict) and "updated_cv" in parsed:
                                                    last_updated_cv = parsed["updated_cv"]
                                                else:
                                                    last_updated_cv = cv_data
                                            except:
                                                last_updated_cv = cv_data
                                        else:
                                            last_updated_cv = cv_data
                                    except Exception as e:
                                        print(f"Error extracting updated_cv: {e}")
                
                # Use the most recent updated_cv if found
                if last_updated_cv and len(last_updated_cv) > len(optimized_cv) * 0.3:
                    updated_cv = last_updated_cv
                
                # Get the current CV from the closure (most reliable)
                try:
                    current_cv_from_tools = get_current_cv()
                    if current_cv_from_tools and current_cv_from_tools != optimized_cv:
                        updated_cv = current_cv_from_tools
                        print(f"CV updated via closure: {len(updated_cv)} chars (was {len(optimized_cv)} chars)")
                except Exception as e:
                    print(f"Error getting current CV from tools: {e}")
                
                # Debug: Check if CV actually changed
                if updated_cv == optimized_cv:
                    print(f"WARNING: updated_cv is identical to optimized_cv. Length: {len(updated_cv)}")
                    print(f"Last updated_cv from tools: {last_updated_cv[:100] if last_updated_cv else 'None'}...")
                
                # If no tool result, try to extract from explanation (fallback)
                if updated_cv == optimized_cv and len(explanation) > 500:
                    # Look for CV-like content in explanation
                    lines = explanation.split('\n')
                    cv_start = None
                    cv_end = None
                    for i, line in enumerate(lines):
                        line_upper = line.upper().strip()
                        # Look for CV section headers
                        if any(keyword in line_upper for keyword in ["NAME", "EXPERIENCE", "EDUCATION", "SKILLS", "SUMMARY", "CERTIFICATIONS"]):
                            if cv_start is None:
                                cv_start = i
                            cv_end = i + 1
                        # If we found a start and hit a blank line or new section, we might have the CV
                        elif cv_start is not None and len(line.strip()) == 0:
                            if i - cv_start > 5:  # At least 5 lines of content
                                cv_end = i
                                break
                    
                    if cv_start is not None:
                        if cv_end is None:
                            cv_end = len(lines)
                        extracted_cv = '\n'.join(lines[cv_start:cv_end])
                        if len(extracted_cv) > len(optimized_cv) * 0.3:
                            updated_cv = extracted_cv
                
                # If tool returned an error, include it in the explanation
                if tool_error:
                    explanation = f"{explanation}\n\nTool error: {tool_error}"
                
                # Add to memory
                if hasattr(memory, 'chat_memory'):
                    memory.chat_memory.add_user_message(user_request)
                    memory.chat_memory.add_ai_message(explanation)
                
                # Only return update_cv action if CV actually changed
                action = "update_cv" if updated_cv != optimized_cv else None
                
                return {
                    "action": action,
                    "updated_cv": updated_cv,
                    "explanation": explanation,
                    "sources": sources,
                    "agent_logs": [explanation]
                }
            except Exception as agent_error:
                # Fallback to simpler implementation if AgentExecutor fails
                print(f"AgentExecutor execution failed, using fallback: {agent_error}")
                use_agent_executor = False
        
        # Fallback to simpler implementation if AgentExecutor not available
        if not use_agent_executor:
            
            # Use simple LLM with tools in prompt (fallback implementation)
            system_message = f"""You are a helpful assistant that helps users refine their optimized CV and correct skills detection.

{rag_context}

WARNING: You are in fallback mode. Since AgentExecutor is not available, you cannot actually call tools.
However, you should still provide helpful guidance and explain what changes would be made.

For the user's request, explain what section would need to be modified and what the updated content would look like.

Answer in {target_language}."""
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_message),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", """{rag_context}
Current optimized CV:
{optimized_cv}

User Request: {user_request}

Analyze the request. If you need to use tools, describe which tool and how. Then provide the updated CV text if changes are needed, or explain what you found.""")
            ])
            
            chain = prompt | llm
            
            chat_history = memory.chat_memory.messages if hasattr(memory, 'chat_memory') else []
            
            # Pass callbacks to chain invoke
            invoke_config = {}
            if langfuse_callback:
                invoke_config["callbacks"] = [langfuse_callback]
            
            response = chain.invoke(
                {
                    "rag_context": rag_context,
                    "optimized_cv": optimized_cv,
                    "user_request": user_request,
                    "chat_history": chat_history
                },
                config=invoke_config if invoke_config else {}
            )
            
            explanation = response.content
            
            # Get the current CV from the closure (most reliable)
            updated_cv = optimized_cv
            try:
                current_cv_from_tools = get_current_cv()
                if current_cv_from_tools and current_cv_from_tools != optimized_cv:
                    updated_cv = current_cv_from_tools
                    print(f"CV updated via closure (fallback): {len(updated_cv)} chars (was {len(optimized_cv)} chars)")
            except Exception as e:
                print(f"Error getting current CV from tools: {e}")
            
            # Debug: Check if CV actually changed
            if updated_cv == optimized_cv:
                print(f"WARNING (fallback): updated_cv is identical to optimized_cv. Length: {len(updated_cv)}")
            
            # Try to extract updated CV from response (improved extraction) - fallback
            if updated_cv == optimized_cv and len(explanation) > 500:
                lines = explanation.split('\n')
                cv_start = None
                cv_end = None
                
                # Look for CV-like content in explanation
                for i, line in enumerate(lines):
                    line_upper = line.upper().strip()
                    # Look for CV section headers
                    if any(keyword in line_upper for keyword in ["NAME", "EXPERIENCE", "EDUCATION", "SKILLS", "SUMMARY", "CERTIFICATIONS"]):
                        if cv_start is None:
                            cv_start = i
                        cv_end = i + 1
                    # If we found a start and hit a blank line or new section, we might have the CV
                    elif cv_start is not None and len(line.strip()) == 0:
                        if i - cv_start > 5:  # At least 5 lines of content
                            cv_end = i
                            break
                
                if cv_start is not None:
                    if cv_end is None:
                        cv_end = len(lines)
                    extracted_cv = '\n'.join(lines[cv_start:cv_end])
                    # Only use if it's substantial enough (at least 30% of original length)
                    if len(extracted_cv) > len(optimized_cv) * 0.3:
                        updated_cv = extracted_cv
            
            # Add to memory
            if hasattr(memory, 'chat_memory'):
                memory.chat_memory.add_user_message(user_request)
                memory.chat_memory.add_ai_message(explanation)
            
            # Only return update_cv action if CV actually changed
            action = "update_cv" if updated_cv != optimized_cv else None
            
            return {
                "action": action,
                "updated_cv": updated_cv,
                "explanation": explanation,
                "sources": sources,
                "agent_logs": [explanation]
            }
        
    except Exception as e:
        return {
            "error": str(e),
            "action": None,
            "updated_cv": optimized_cv,
            "explanation": None
        }

