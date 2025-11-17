"""
ReAct Agent for Conversational Assistant
Uses tools and memory to help users adjust CVs and skills
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import Tool
from typing import Dict, Any, List, Optional
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


def create_assistant_tools(api_key: str) -> List[Tool]:
    """Create tools for the assistant agent, bound with API key."""
    
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
    
    tools = [
        Tool(
            name="update_cv_section",
            func=lambda cv_text, section, content: json.dumps(
                update_cv_section_tool.invoke({
                    "cv_text": cv_text,
                    "section_name": section,
                    "new_content": content
                })
            ),
            description="Update a specific section in the CV. Input: cv_text (string, the full CV text), section_name (string like 'Experience', 'Skills', 'Certifications', 'Education'), new_content (string with the COMPLETE new section content - this REPLACES the entire section content, so include all items you want to keep). To remove a specific item: first use search_cv to find the current section content, then provide new_content with that item removed. Returns updated CV text."
        ),
        Tool(
            name="search_cv",
            func=lambda cv_text, search_term: json.dumps(
                search_cv_content_tool.invoke({
                    "cv_text": cv_text,
                    "search_term": search_term
                })
            ),
            description="Search for specific content in the CV. Input: cv_text (string), search_term (string to search for). Returns matching lines and locations."
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
    
    return tools


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
    rag_system: Optional[Any] = None  # NEW: RAG system parameter
) -> Dict[str, Any]:
    """
    Process assistant request using a ReAct agent with tools and memory.
    Uses LangChain's AgentExecutor for true ReAct agent behavior.
    """
    try:
        llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=api_key
        )
        
        if memory is None:
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
        
        # Create tools for the agent
        tools = create_assistant_tools(api_key)
        
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
                # Use LangChain's ReAct agent
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
                    max_iterations=5
                )
            except Exception as hub_error:
                # If hub.pull fails, fall through to manual implementation
                use_agent_executor = False
                agent_executor = None
                print(f"Hub not available, using fallback: {hub_error}")
        
        if use_agent_executor and agent_executor:
            try:
                # Prepare input with context
                input_text = f"""You are a helpful assistant that helps users refine their optimized CV and correct skills detection.

{rag_context}
Context:
- Current Optimized CV: {optimized_cv[:1000]}...
- Original CV: {original_cv[:500]}...
- Job Description: {job_description[:500]}...
- CV Skills: {', '.join(cv_skills[:20]) if cv_skills else 'None'}
- Job Skills: {', '.join(job_skills[:20]) if job_skills else 'None'}

User Request: {user_request}

CRITICAL RULES:
- Answer in {target_language}
- Use the available tools to make changes
- When using update_cv_section, pass the full optimized_cv as cv_text parameter
- IMPORTANT: To remove a specific item from a section:
  1. First use search_cv to find the current section content
  2. Read the section content carefully
  3. Create new_content with the item removed but all other items kept
  4. Use update_cv_section with the complete new section content
- After using tools, explain what you changed in {target_language}
- Keep the CV format and structure intact

Available tools:
- update_cv_section(cv_text, section_name, new_content): REPLACES the entire section content. You must provide ALL items you want to keep in new_content.
- search_cv(cv_text, search_term): Search for specific content in the CV to find current section content
- extract_cv_skills(text): Extract skills from CV text
- extract_job_skills(text): Extract skills from job description
- compare_skills(cv_skills_json, job_skills_json): Compare CV skills with job skills

Analyze the user's request and use the appropriate tools to make the changes."""
            
                # Run the agent
                # AgentExecutor handles memory automatically via the memory parameter
                result = agent_executor.invoke({
                    "input": input_text
                })
                
                explanation = result.get("output", "")
                
                # Try to extract updated CV from tool results
                updated_cv = optimized_cv
                tool_error = None
                if "intermediate_steps" in result:
                    for step in result["intermediate_steps"]:
                        if len(step) > 1:
                            tool_result = step[1]
                            # Handle both dict and string results
                            if isinstance(tool_result, str):
                                try:
                                    tool_result = json.loads(tool_result)
                                except:
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
                                                    updated_cv = parsed["updated_cv"]
                                                else:
                                                    updated_cv = cv_data
                                            except:
                                                updated_cv = cv_data
                                        else:
                                            updated_cv = cv_data
                                    except Exception as e:
                                        print(f"Error extracting updated_cv: {e}")
                
                # If tool returned an error, include it in the explanation
                if tool_error:
                    explanation = f"{explanation}\n\n⚠️ Tool error: {tool_error}"
                
                # Add to memory
                if hasattr(memory, 'chat_memory'):
                    memory.chat_memory.add_user_message(user_request)
                    memory.chat_memory.add_ai_message(explanation)
                
                return {
                    "action": "update_cv",
                    "updated_cv": updated_cv,
                    "explanation": explanation,
                    "sources": sources,  # NEW: Return RAG sources
                    "agent_logs": [explanation]
                }
            except Exception as agent_error:
                # Fallback to simpler implementation if AgentExecutor fails
                print(f"AgentExecutor execution failed, using fallback: {agent_error}")
                use_agent_executor = False
        
        # Fallback to simpler implementation if AgentExecutor not available
        if not use_agent_executor:
            
            # Use simple LLM with tools in prompt (original implementation)
            system_message = f"""You are a helpful assistant that helps users refine their optimized CV and correct skills detection.

Your task is to:
1. Understand the user's request (they may want to add skills, correct skill names, modify CV content, etc.)
2. Use the available tools to make the appropriate changes
3. Provide a clear explanation of what you changed

CRITICAL RULES:
- Answer in {target_language}
- Use tools to perform actions (update_cv_section, search_cv, extract_skills, compare_skills)
- IMPORTANT: To remove a specific item from a section:
  1. First use search_cv to find the current section content
  2. Read the section content carefully
  3. Create new_content with the item removed but all other items kept
  4. Use update_cv_section with the complete new section content
- After using tools, explain what you did in {target_language}
- Keep the CV format and structure intact
- Only make the specific changes requested

Available tools:
- update_cv_section: REPLACES the entire section content. You must provide ALL items you want to keep.
- search_cv: Search for specific content in the CV to find current section content
- extract_cv_skills: Extract skills from CV text
- extract_job_skills: Extract skills from job description
- compare_skills: Compare CV skills with job skills

When the user requests changes:
1. First, understand what they want (CV modification, skill update, or both)
2. Use search_cv if you need to find specific content or read current section content
3. Use update_cv_section to modify CV sections - remember to include ALL items you want to keep
4. Use extract_skills and compare_skills if working with skills
5. Explain your actions clearly in {target_language}

IMPORTANT: The optimized_cv variable contains the current CV text. Use it when calling tools."""
            
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
            
            response = chain.invoke({
                "rag_context": rag_context,
                "optimized_cv": optimized_cv,
                "user_request": user_request,
                "chat_history": chat_history
            })
            
            explanation = response.content
            
            # Try to extract updated CV from response
            updated_cv = optimized_cv
            if len(explanation) > 500 and ("EXPERIENCE" in explanation.upper() or "SKILLS" in explanation.upper()):
                lines = explanation.split('\n')
                cv_start = None
                for i, line in enumerate(lines):
                    if any(keyword in line.upper() for keyword in ["NAME", "EXPERIENCE", "EDUCATION", "SKILLS", "SUMMARY"]):
                        cv_start = i
                        break
                if cv_start:
                    updated_cv = '\n'.join(lines[cv_start:])
            
            # Add to memory
            if hasattr(memory, 'chat_memory'):
                memory.chat_memory.add_user_message(user_request)
                memory.chat_memory.add_ai_message(explanation)
            
            return {
                "action": "update_cv",
                "updated_cv": updated_cv,
                "explanation": explanation,
                "sources": sources,  # NEW: Return RAG sources
                "agent_logs": [explanation]
            }
        
    except Exception as e:
        return {
            "error": str(e),
            "action": None,
            "updated_cv": optimized_cv,
            "explanation": None
        }

