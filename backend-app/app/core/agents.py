import os
import json
import uuid
import logging
from typing import List, Dict, Any, Optional
import asyncio


# Import cấu hình
from .config import ChatAgentConfig as config

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# This file now imports from the modular components to maintain backward compatibility

# Import from new modular files
from .chat_agent import ChatAgent
from .default_agent import (
    get_default_agent,
    generate_chat_response,
    generate_chat_title,
    create_custom_agent,
    generate_response_with_custom_agent
)
from .document_agent import (
    embed_and_store_document,
    chat_with_document
)
from .sql_agent import generate_response_from_sql
from .utils import format_chat_history

# Re-export all necessary components to maintain the same API
__all__ = [
    'ChatAgent',
    'get_default_agent',
    'generate_chat_response',
    'generate_chat_title',
    'create_custom_agent',
    'generate_response_with_custom_agent',
    'embed_and_store_document',
    'chat_with_document',
    'generate_response_from_sql',
    'format_chat_history'
]
