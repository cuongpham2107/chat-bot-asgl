import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain import hub
from .config import ChatAgentConfig as config

logger = logging.getLogger(__name__)


class SQLAssistant:
    def __init__(
        self, 
        db_uri: str, 
        api_key: Optional[str] = config.GOOGLE_API_KEY,  
        model: str = config.DEFAULT_MODEL_NAME
    ):
        # Khởi tạo như phiên bản trước
        if api_key:
            os.environ['GOOGLE_API_KEY'] = api_key
        
        os.environ['LANGCHAIN_TRACING'] = 'false'
        
        try:
            self.db = SQLDatabase.from_uri(db_uri)
            logger.info(f"Đã kết nối đến cơ sở dữ liệu: {db_uri}")
            
            self.llm = ChatGoogleGenerativeAI(model=model)
            logger.info(f"Đã khởi tạo LLM: {model}")
            
            # Mẫu prompt với DEFAULT_SYSTEM_PROMPT từ config - đã sửa đổi
            self.answer_prompt_template = ChatPromptTemplate.from_messages([
                ("system", f"""{config.DEFAULT_SYSTEM_PROMPT}

                Bạn là một trợ lý chat thân thiện giúp cung cấp thông tin từ kết quả tìm kiếm.
                Hãy trả lời theo cách ngắn gọn, dễ hiểu và thân thiện. 
                Nếu phát hiện insights thú vị từ dữ liệu, hãy chia sẻ.
                Không đề cập đến SQL, truy vấn, hoặc cơ sở dữ liệu trong câu trả lời của bạn."""),
                ("human", """Câu hỏi: {question}
                
                Kết quả tìm kiếm: {result}
                
                Vui lòng cung cấp câu trả lời theo phong cách chat thân mật, 
                giải thích thông tin một cách dễ hiểu.""")
            ])
        
        except Exception as e:
            logger.error(f"Lỗi khởi tạo: {e}")
            raise
    
    def write_query(self, question: str) -> str:
        """
        Tạo truy vấn SQL cho một câu hỏi đã cho.
        """
        try:
            prompt_value = hub.pull("langchain-ai/sql-query-system-prompt").invoke({
                "dialect": self.db.dialect,
                "top_k": 10,
                "table_info": self.db.get_table_info(),
                "input": question,
            })
            
            message_content = prompt_value.messages[0].content
            response = self.llm.invoke(message_content)
            query = response.content.strip()
            
            # Trích xuất SQL từ khối mã nếu có
            if "```sql" in query:
                query = query.split("```sql")[1].split("```")[0].strip()
            
            logger.info(f"Đã tạo truy vấn cho câu hỏi: {question}")
            return query
        
        except Exception as e:
            logger.error(f"Lỗi tạo truy vấn: {e}")
            raise
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Thực thi truy vấn SQL và trả về kết quả.
        """
        try:
            execute_query_tool = QuerySQLDatabaseTool(db=self.db)
            result = execute_query_tool.invoke(query)
            logger.info(f"Đã thực thi truy vấn thành công: {query}")
            return result
        
        except Exception as e:
            logger.error(f"Lỗi thực thi truy vấn: {e}")
            raise
    
    def generate_answer(self, question: str, query: str, result: List[Dict[str, Any]]) -> str:
        """
        Tạo câu trả lời ngôn ngữ tự nhiên từ kết quả truy vấn.
        """
        try:
            prompt_value = self.answer_prompt_template.invoke({
                "question": question,
                "query": query,
                "result": result
            })
            
            response = self.llm.invoke(prompt_value.messages)
            logger.info("Đã tạo câu trả lời ngôn ngữ tự nhiên")
            return response.content
        
        except Exception as e:
            logger.error(f"Lỗi tạo câu trả lời: {e}")
            raise
    
    def process_question(self, question: str) -> Dict[str, Any]:
        """
        Phương thức toàn diện để xử lý câu hỏi ngôn ngữ tự nhiên.
        """
        try:
            # Tạo truy vấn SQL
            query = self.write_query(question)
            
            # Thực thi truy vấn
            result = self.execute_query(query)
            
            # Tạo câu trả lời ngôn ngữ tự nhiên
            answer = self.generate_answer(question, query, result)
            
            return {
                "question": question,
                "query": query,
                "result": result,
                "answer": answer
            }
        
        except Exception as e:
            logger.error(f"Lỗi xử lý câu hỏi: {e}")
            return {
                "question": question,
                "error": str(e)
            }

async def generate_response_from_sql(
    answer: str, 
    value_db_connect: str, 
    chat_history: Optional[List[Dict[str, str]]] = None) -> str:
    try:
        # Find the database connection info from the config
        db_info = next((item for item in config.dataApiFetching if item["value"] == value_db_connect), None)
        
        if not db_info:
            logger.error(f"Database connection not found for value: {value_db_connect}")
            return f"Xin lỗi, không tìm thấy kết nối cơ sở dữ liệu cho '{value_db_connect}'"
        
        # Get the SQL connection string
        db_uri = db_info['sql_connect']
        
        # Create SQLAssistant instance with the provided database URI
        sql_assistant = SQLAssistant(db_uri=db_uri)
        
        # Process the question using SQLAssistant
        result = sql_assistant.process_question(answer)
        
        # If there was an error in processing
        if "error" in result:
            logger.error(f"Error in SQL processing: {result['error']}")
            return f"Xin lỗi, tôi gặp sự cố khi truy vấn cơ sở dữ liệu: {result['error']}"
        
        # Return the natural language answer
        return result["answer"]
        
    except Exception as e:
        logger.error(f"Error generating response from SQL: {str(e)}")
        return config.ERROR_MESSAGES.get("processing_error", "Processing error: {error}").format(error=str(e))

