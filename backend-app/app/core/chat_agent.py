import os
import json
import uuid
import logging
from typing import List, Dict, Any, Optional

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

class ChatAgent:
    """
    Agent chat sử dụng mô hình Google Generative AI.
    Lớp này quản lý việc tạo phản hồi từ AI dựa trên tin nhắn của người dùng.
    """
    
    def __init__(
        self, 
        model_name: str = config.DEFAULT_MODEL_NAME, 
        temperature: float = config.DEFAULT_TEMPERATURE,
        system_prompt: str = config.DEFAULT_SYSTEM_PROMPT,
        api_key: Optional[str] = None
    ):
        """Khởi tạo agent chat.
        
        Tham số:
            model_name: Tên của mô hình Google Generative AI sử dụng.
            temperature: Điều khiển tính ngẫu nhiên. Giá trị cao hơn (ví dụ: 0.8) làm cho đầu ra ngẫu nhiên hơn, 
                         giá trị thấp hơn (ví dụ: 0.2) làm cho nó có tính quyết định hơn.
            system_prompt: Prompt hệ thống sử dụng cho cuộc trò chuyện.
            api_key: Google API key. Nếu None, sẽ sử dụng GOOGLE_API_KEY từ biến môi trường.
        """
        self.model_name = model_name
        self.temperature = temperature
        self.system_prompt = system_prompt
        self.api_key = api_key or config.GOOGLE_API_KEY
        self.llm = None
        self.chat_chain = None
        self.embeddings = None
        self.document_qa_chain = None
        
        # Khởi tạo lịch sử tin nhắn
        self.message_history = ChatMessageHistory()
    
    def _initialize_llm(self):
        """Khởi tạo mô hình ngôn ngữ và chuỗi hội thoại nếu chưa được khởi tạo."""
        if self.llm is None:
            if not self.api_key:
                raise ValueError(config.ERROR_MESSAGES["api_key_missing"])
            
            try:
                # Khởi tạo mô hình LLM
                self.llm = ChatGoogleGenerativeAI(
                    model=self.model_name,
                    temperature=self.temperature,
                    google_api_key=self.api_key
                )
                
                # Tạo prompt template hiện đại
                prompt = ChatPromptTemplate.from_messages([
                    MessagesPlaceholder(variable_name="history"),
                    ("human", "{input}")
                ])
                
                # Tạo chuỗi xử lý hiện đại
                self.chat_chain = (
                    {"history": lambda x: self._prepare_history_with_system_prompt(x["history"]), 
                     "input": lambda x: x["input"]}
                    | prompt
                    | self.llm
                    | StrOutputParser()
                )
                
                # Khởi tạo embeddings nếu chưa được khởi tạo
                if self.embeddings is None:
                    self.embeddings = GoogleGenerativeAIEmbeddings(
                        model=config.EMBEDDING_MODEL,
                        google_api_key=self.api_key
                    )
                
                # Tạo document QA chain
                document_qa_prompt = ChatPromptTemplate.from_template(config.DOCUMENT_QA_PROMPT)
                self.document_qa_chain = (
                    {"context": lambda x: x["context"], "question": lambda x: x["question"]}
                    | document_qa_prompt
                    | self.llm
                    | StrOutputParser()
                )
                
                logger.info(f"Initialized ChatGoogleGenerativeAI with model {self.model_name}")
            except Exception as e:
                logger.error(f"Error initializing ChatGoogleGenerativeAI: {str(e)}")
                raise
    
    def _prepare_history_with_system_prompt(self, history_messages):
        """
        Chuẩn bị lịch sử tin nhắn với system prompt.
        Nếu lịch sử trống, thêm system prompt vào đầu tiên như một human message.
        """
        if not history_messages:
            # Nếu không có lịch sử, thêm system prompt như một human message
            return [HumanMessage(content=f"Instructions: {self.system_prompt}")]
        return history_messages
    
    async def generate_response(self, message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Tạo phản hồi cho tin nhắn của người dùng.
        
        Tham số:
            message: Tin nhắn của người dùng.
            chat_history: Danh sách tùy chọn các tin nhắn trước đó theo định dạng 
                         [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        
        Trả về:
            Phản hồi của trợ lý AI.
        """
        # Khởi tạo LLM nếu chưa được khởi tạo
        self._initialize_llm()
        
        # Xử lý lịch sử trò chuyện
        history_messages = []
        
        # Nếu lịch sử trò chuyện được cung cấp, chuyển đổi thành định dạng tin nhắn
        if chat_history:
            for msg in chat_history:
                if msg["role"] == "user":
                    history_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    history_messages.append(AIMessage(content=msg["content"]))
                elif msg["role"] == "system":
                    # Bỏ qua system message vì chúng ta sẽ xử lý nó trong _prepare_history_with_system_prompt
                    continue
        
        try:
            # Tạo phản hồi sử dụng chuỗi xử lý hiện đại
            response = await self.chat_chain.ainvoke({
                "history": history_messages,
                "input": message
            })
            return response
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return config.ERROR_MESSAGES["processing_error"].format(error=str(e))
    
    async def generate_title(self, message: str) -> str:
        """Tạo tiêu đề cho cuộc trò chuyện dựa trên tin nhắn đầu tiên của người dùng.
        
        Tham số:
            message: Tin nhắn đầu tiên của người dùng.
            
        Trả về:
            Tiêu đề ngắn gọn cho cuộc trò chuyện.
        """
        # Khởi tạo LLM nếu chưa được khởi tạo
        self._initialize_llm()
        
        try:
            # Tạo prompt template cho việc tạo tiêu đề
            title_prompt = ChatPromptTemplate.from_messages([
                ("human", config.TITLE_GENERATION_PROMPT.format(message=message))
            ])
            
            # Tạo chuỗi xử lý cho việc tạo tiêu đề
            title_chain = title_prompt | self.llm | StrOutputParser()
            
            # Tạo tiêu đề
            title = await title_chain.ainvoke({})
            
            # Làm sạch tiêu đề (loại bỏ dấu ngoặc kép, dấu xuống dòng, v.v.)
            title = title.strip().strip('"').strip()
            
            # Giới hạn độ dài tiêu đề
            if len(title) > config.MAX_TITLE_LENGTH:
                title = title[:config.MAX_TITLE_LENGTH-3] + "..."
                
            return title
        except Exception as e:
            logger.error(f"Error generating title: {str(e)}")
            return config.DEFAULT_CHAT_TITLE
    
    def clear_history(self):
        """Xóa lịch sử tin nhắn."""
        self.message_history.clear()
    
    async def embed_and_store_document(self, text: str, source_file_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Nhúng văn bản và lưu trữ trong ChromaDB.
        
        Tham số:
            text: Nội dung văn bản cần nhúng.
            source_file_id: ID của file nguồn.
            metadata: Metadata bổ sung cho tài liệu.
            
        Trả về:
            ID của collection đã tạo trong ChromaDB.
        """
        # Khởi tạo LLM và embeddings nếu chưa được khởi tạo
        self._initialize_llm()
        
        try:
            # Tạo ID cho collection
            collection_id = f"doc_{source_file_id}_{uuid.uuid4().hex[:8]}"
            
            # Chuẩn bị metadata
            if metadata is None:
                metadata = {}
            
            # Thêm source_file_id vào metadata
            doc_metadata = {
                "source_file_id": source_file_id,
                **metadata
            }
            
            # Chia nhỏ văn bản thành các đoạn
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=config.CHUNK_SIZE,
                chunk_overlap=config.CHUNK_OVERLAP,
                length_function=len,
            )
            
            # Tạo documents từ văn bản
            docs = text_splitter.create_documents(
                [text], 
                metadatas=[doc_metadata]
            )
            
            # Tạo thư mục persist nếu chưa tồn tại
            persist_directory = os.path.join(config.CHROMA_PERSIST_DIRECTORY, collection_id)
            os.makedirs(persist_directory, exist_ok=True)
            
            # Tạo và lưu trữ vector store
            Chroma.from_documents(
                documents=docs,
                embedding=self.embeddings,
                persist_directory=persist_directory,
                collection_name=collection_id
            )
            
            logger.info(f"Successfully embedded and stored document with collection ID: {collection_id}")
            return collection_id
            
        except Exception as e:
            logger.error(f"Error embedding and storing document: {str(e)}")
            raise
    
    async def chat_with_document(self, message: str, source_file_id: str, metadata: Optional[Dict[str, Any]] = None, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Trò chuyện với tài liệu đã được nhúng.
        
        Tham số:
            message: Tin nhắn của người dùng.
            source_file_id: ID của file nguồn.
            metadata: Metadata của file, có thể chứa collection_id.
            chat_history: Danh sách tùy chọn các tin nhắn trước đó.
            
        Trả về:
            Phản hồi của trợ lý AI dựa trên tài liệu.
        """
        # Khởi tạo LLM nếu chưa được khởi tạo
        self._initialize_llm()
        
        try:
            # Lấy collection_id từ metadata nếu có
            collection_id = None
            if metadata:
                # Xử lý metadata có thể là string hoặc dict
                if isinstance(metadata, str):
                    try:
                        metadata_dict = json.loads(metadata)
                        collection_id = metadata_dict.get("collection_id")
                    except json.JSONDecodeError:
                        logger.error(f"Error parsing metadata JSON for file {source_file_id}")
                else:
                    collection_id = metadata.get("collection_id")
            
            # Nếu không có collection_id trong metadata, tìm dựa trên source_file_id
            if not collection_id:
                collection_dirs = [d for d in os.listdir(config.CHROMA_PERSIST_DIRECTORY) 
                                if os.path.isdir(os.path.join(config.CHROMA_PERSIST_DIRECTORY, d)) 
                                and d.startswith(f"doc_{source_file_id}_")]
                
                if not collection_dirs:
                    return config.ERROR_MESSAGES["document_not_found"].format(source_file_id=source_file_id)
                
                # Sử dụng collection đầu tiên tìm thấy
                collection_id = collection_dirs[0]
            
            # Tải vector store
            vectorstore = Chroma(
                persist_directory=os.path.join(config.CHROMA_PERSIST_DIRECTORY, collection_id),
                embedding_function=self.embeddings,
                collection_name=collection_id
            )
            
            # Tạo retriever cơ bản
            basic_retriever = vectorstore.as_retriever(
                search_type=config.RETRIEVER_SEARCH_TYPE,
                search_kwargs={"k": config.RETRIEVER_K}
            )
            
            # Tạo bộ lọc tài liệu dư thừa
            redundant_filter = EmbeddingsRedundantFilter(embeddings=self.embeddings)
            
            # Tạo pipeline nén tài liệu
            pipeline = DocumentCompressorPipeline(transformers=[redundant_filter])
            
            # Tạo retriever nén ngữ cảnh
            retriever = ContextualCompressionRetriever(
                base_compressor=pipeline,
                base_retriever=basic_retriever
            )
            
            # Truy xuất tài liệu liên quan
            docs = await retriever.ainvoke(message)
            
            # Nếu không tìm thấy tài liệu liên quan
            if not docs:
                return config.ERROR_MESSAGES["no_relevant_info"]
            
            # Chuẩn bị ngữ cảnh từ tài liệu
            context = "\n\n".join([doc.page_content for doc in docs])
            
            # Chuẩn bị prompt với lịch sử trò chuyện nếu có
            if chat_history and len(chat_history) > 0:
                # Tạo chuỗi lịch sử trò chuyện
                chat_history_text = ""
                for msg in chat_history:
                    role = "Người dùng" if msg["role"] == "user" else "Trợ lý"
                    chat_history_text += f"{role}: {msg['content']}\n"
                
                # Tạo prompt với lịch sử trò chuyện
                document_qa_prompt_with_history = ChatPromptTemplate.from_template(
                    config.DOCUMENT_QA_WITH_HISTORY_PROMPT
                )
                
                # Tạo phản hồi dựa trên tài liệu và lịch sử trò chuyện
                response = await (
                    document_qa_prompt_with_history 
                    | self.llm 
                    | StrOutputParser()
                ).ainvoke({
                    "chat_history": chat_history_text,
                    "context": context,
                    "question": message
                })
            else:
                # Sử dụng prompt mặc định nếu không có lịch sử trò chuyện
                response = await self.document_qa_chain.ainvoke({
                    "context": context,
                    "question": message
                })
            
            return response
            
        except Exception as e:
            logger.error(f"Error chatting with document: {str(e)}")
            return config.ERROR_MESSAGES["processing_error"].format(error=str(e))
