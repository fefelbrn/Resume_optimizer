"""
Langfuse configuration for LLM observability and Debug mode
"""
import os
from typing import Optional, Dict, Any

try:
    from langfuse.langchain import CallbackHandler
    from langfuse import Langfuse
    try:
        from langfuse.langgraph import LangGraphTracer
        LANGRAPH_TRACER_AVAILABLE = True
    except ImportError:
        # Fallback for older versions
        LangGraphTracer = None
        LANGRAPH_TRACER_AVAILABLE = False
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    CallbackHandler = None
    Langfuse = None
    LangGraphTracer = None
    LANGRAPH_TRACER_AVAILABLE = False

_langfuse_enabled = None
_langfuse_client = None

def init_langfuse_client() -> Optional[Any]:
    """Initializes the global Langfuse client (required for Langfuse 3 and above)"""
    global _langfuse_client, _langfuse_enabled
    
    if not LANGFUSE_AVAILABLE:
        return None
    
    if _langfuse_client is not None:
        return _langfuse_client
    
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    if not public_key or not secret_key:
        _langfuse_enabled = False
        return None
    
    try:
        _langfuse_client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host
        )
        _langfuse_enabled = True
        print("Langfuse client initialized")
        return _langfuse_client
    except Exception as e:
        print(f"Langfuse Initionlisation Error: {e}")
        _langfuse_enabled = False
        return None

def is_langfuse_enabled() -> bool:
    """Check if Langfuse is configured and available"""
    global _langfuse_enabled
    if _langfuse_enabled is not None:
        return _langfuse_enabled
    
    init_langfuse_client()
    return _langfuse_enabled or False


def create_langfuse_callback(
    trace_name: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[Any]:
    """
     Creates a Langfuse callback to trace a workflow.
    
    In Langfuse 3 or more, CallbackHandler uses environment variables
    for secret_key and host. Only public_key is passed directly.
    
    Args:
        trace_name: Trace name (e.g., "cv_optimization," "conversational_assistant")
        user_id: User ID (optional)
        session_id: Session ID (optional)
        metadata: Additional metadata (optional)
    
    Returns:
        CallbackHandler if Langfuse is configured, None otherwise
    """
    if not LANGFUSE_AVAILABLE:
        return None
    
    if not is_langfuse_enabled():
        return None
    
    try:
        if not _langfuse_client:
            init_langfuse_client()
        
        if not _langfuse_client:
            return None
        
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        
        # Create handler with trace name and session for unified tracing
        try:
            handler = CallbackHandler(
                public_key=public_key,
                trace_name=trace_name,
                session_id=session_id,
                user_id=user_id,
                metadata=metadata or {}
            )
        except TypeError:
            # Fallback for versions that don't support these parameters directly
            handler = CallbackHandler(public_key=public_key)
            handler._trace_name = trace_name
            handler._session_id = session_id
            handler._user_id = user_id
            handler._metadata = metadata or {}
        
        return handler
    except Exception as e:
        print(f"Fallback Error: Callbakc error creating Langfuse: {e}")
        return None


def create_langgraph_tracer(
    trace_name: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    trace_input: Optional[Any] = None
) -> Optional[Any]:
    """
    Creates a unified callback for LangGraph workflows to trace as a single trace.
    
    This creates a trace manually with input, then creates a CallbackHandler that will
    attach all nodes as spans under this trace.
    
    Args:
        trace_name: Trace name (e.g., "cv_optimization", "conversational_assistant")
        user_id: User ID (optional)
        session_id: Session ID (optional)
        metadata: Additional metadata (optional)
        trace_input: Input data for the trace (optional)
    
    Returns:
        Tuple of (CallbackHandler, trace) if Langfuse is available, (None, None) otherwise
        The trace object can be used to update output later
    """
    if not LANGFUSE_AVAILABLE or not is_langfuse_enabled():
        return None, None
    
    try:
        if not _langfuse_client:
            init_langfuse_client()
        
        if not _langfuse_client:
            return None, None
        
        # Create trace manually with input
        trace = _langfuse_client.trace(
            name=trace_name,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {},
            input=trace_input
        )
        
        # Create callback handler
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        try:
            handler = CallbackHandler(
                public_key=public_key,
                trace_id=trace.id,
                session_id=session_id,
                user_id=user_id
            )
        except (TypeError, AttributeError):
            # Fallback: create handler normally, we'll link via config
            handler = CallbackHandler(
                public_key=public_key,
                session_id=session_id,
                user_id=user_id
            )
        
        handler._langfuse_trace = trace
        handler._trace_id = trace.id
        
        return handler, trace
    except Exception as e:
        print(f"Error creating LangGraph tracer with trace: {e}")
        return create_langfuse_callback(trace_name, user_id, session_id, metadata), None