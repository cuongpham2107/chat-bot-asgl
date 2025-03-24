import os
import json
import uuid
import logging
from typing import List, Dict, Any, Optional
import asyncio

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.document_transformers import EmbeddingsRedundantFilter
from langchain.retrievers.document_compressors import DocumentCompressorPipeline

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
from .api_agent import generate_response_from_api
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
    'generate_response_from_api',
    'format_chat_history'
]
