"""
Configuration Langfuse pour l'observabilité des LLM
"""
import os
from typing import Optional, Dict, Any

try:
    from langfuse.langchain import CallbackHandler
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    CallbackHandler = None
    Langfuse = None

_langfuse_enabled = None
_langfuse_client = None

def init_langfuse_client() -> Optional[Any]:
    """Initialise le client Langfuse global (requis pour Langfuse 3.x)"""
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
        print("✅ Langfuse client initialisé")
        return _langfuse_client
    except Exception as e:
        print(f"⚠️  Erreur initialisation Langfuse: {e}")
        _langfuse_enabled = False
        return None

def is_langfuse_enabled() -> bool:
    """Vérifie si Langfuse est configuré et disponible"""
    global _langfuse_enabled
    if _langfuse_enabled is not None:
        return _langfuse_enabled
    
    # Initialiser le client pour vérifier la configuration
    init_langfuse_client()
    return _langfuse_enabled or False


def create_langfuse_callback(
    trace_name: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[Any]:
    """
    Crée un callback Langfuse pour tracer un workflow.
    
    Dans Langfuse 3.x, le CallbackHandler utilise les variables d'environnement
    pour secret_key et host. Seul public_key est passé directement.
    
    Args:
        trace_name: Nom de la trace (ex: "cv_optimization", "assistant_conversation")
        user_id: ID utilisateur (optionnel)
        session_id: ID de session (optionnel)
        metadata: Métadonnées supplémentaires (optionnel)
    
    Returns:
        CallbackHandler si Langfuse est configuré, None sinon
    """
    if not LANGFUSE_AVAILABLE:
        return None
    
    if not is_langfuse_enabled():
        return None
    
    try:
        # S'assurer que le client Langfuse est initialisé (requis pour Langfuse 3.x)
        if not _langfuse_client:
            init_langfuse_client()
        
        if not _langfuse_client:
            return None
        
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        
        # Dans Langfuse 3.x, CallbackHandler utilise le client global initialisé
        # et les variables d'environnement. On passe seulement public_key.
        handler = CallbackHandler(
            public_key=public_key
        )
        
        # Note: trace_name, user_id, session_id et metadata sont gérés
        # via le contexte LangChain lors de l'invocation, pas dans CallbackHandler
        return handler
    except Exception as e:
        print(f"⚠️  Erreur création callback Langfuse: {e}")
        return None