import os
import requests
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

# Tải biến môi trường từ file .env
load_dotenv()

# Đặt API key Google từ biến môi trường
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

class ASGLAPIClient:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.base_url = "https://id.asgl.net.vn/api"
        self.token = None
        self.user_info = None

    def login(self):
        """Đăng nhập và lấy token"""
        login_url = f"{self.base_url}/auth/login"
        
        # Dữ liệu đăng nhập
        payload = {
            'login': self.username,
            'password': self.password
        }
        
        try:
            # Gửi request đăng nhập
            response = requests.post(login_url, data=payload)
            response.raise_for_status()  # Kiểm tra lỗi
            
            # Phân tích kết quả
            result = response.json()
            
            if result.get('success'):
                self.token = result['data']['token']
                self.user_info = result['data']['user']
                return True
            else:
                print("Đăng nhập thất bại:", result.get('message', 'Lỗi không xác định'))
                return False
        
        except requests.RequestException as e:
            print(f"Lỗi kết nối: {e}")
            return False

    def fetch_employees(self):
        """Lấy danh sách nhân viên"""
        if not self.token:
            print("Chưa đăng nhập")
            return []
        
        # URL API nhân viên - thêm limit lớn hơn để lấy nhiều nhân viên hơn
        employees_url = "https://human-be.asgl.net.vn/api/employees?limit=100"
        
        # Headers với Bearer Token
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Gửi request lấy danh sách nhân viên
            response = requests.get(employees_url, headers=headers)
            response.raise_for_status()
            
            # Lấy dữ liệu JSON từ response
            response_data = response.json()
            
            # Kiểm tra và gỡ lỗi cấu trúc dữ liệu
            print("Cấu trúc dữ liệu API trả về:", type(response_data))
            print("Các khóa trong dữ liệu:", response_data.keys() if isinstance(response_data, dict) else "Không phải dict")
            
            # Xác định danh sách nhân viên từ cấu trúc dữ liệu mới
            employees_list = []
            
            # Kiểm tra cấu trúc dữ liệu theo format đã biết
            if (isinstance(response_data, dict) and 
                response_data.get('success') and 
                'data' in response_data and 
                isinstance(response_data['data'], dict) and 
                'employees' in response_data['data'] and 
                isinstance(response_data['data']['employees'], list)):
                
                # Lấy danh sách nhân viên từ đúng vị trí
                employees_list = response_data['data']['employees']
                print(f"Lấy danh sách nhân viên từ response_data['data']['employees'] (list)")
            else:
                print("Cấu trúc dữ liệu không như mong đợi:", response_data)
            
            print(f"Số lượng nhân viên nhận được: {len(employees_list)}")
            
            # Hiển thị số lượng nhân viên có name/full_name
            named_employees = [e for e in employees_list if e.get('full_name') or e.get('name')]
            print(f"Số lượng nhân viên có tên: {len(named_employees)}")
            if named_employees:
                print("Tên một số nhân viên:")
                for i, emp in enumerate(named_employees[:5]):  # Hiển thị 5 nhân viên đầu tiên
                    print(f"  {i+1}. {emp.get('full_name') or emp.get('name', 'N/A')}")
            
            # Chuyển đổi dữ liệu nhân viên thành Langchain documents
            documents = []
            
            for employee in employees_list:
                # Kiểm tra nếu employee là dictionary
                if not isinstance(employee, dict):
                    print(f"Dữ liệu nhân viên không hợp lệ (không phải dict): {type(employee)}")
                    continue
                
                # Lấy tên nhân viên
                employee_name = employee.get('full_name') or employee.get('name', 'Không có tên')
                print(f"Xử lý nhân viên: {employee_name}")
                
                # Tạo nội dung văn bản từ thông tin nhân viên
                content = f"""
                Thông tin nhân viên:
                - Tên: {employee_name}
                - Mã nhân viên: {employee.get('employee_code', 'N/A')}
                - Email: {employee.get('email', 'N/A')}
                - Số điện thoại: {employee.get('phone', 'N/A')}
                - Phòng ban: {employee.get('department', {}).get('name', 'N/A') if isinstance(employee.get('department'), dict) else 'N/A'}
                - Chức vụ: {employee.get('position', {}).get('name', 'N/A') if isinstance(employee.get('position'), dict) else 'N/A'}
                - Địa chỉ: {employee.get('address', 'N/A')}
                - Ngày sinh: {employee.get('birthday', 'N/A')}
                """
                
                doc = Document(
                    page_content=content.strip(),
                    metadata={
                        'source': 'employees_api',
                        'id': employee.get('id', ''),
                        'employee_code': employee.get('employee_code', ''),
                        'full_name': employee_name
                    }
                )
                documents.append(doc)
            
            print(f"Tổng số tài liệu tạo được: {len(documents)}")
            return documents
        
        except requests.RequestException as e:
            print(f"Lỗi lấy dữ liệu nhân viên: {e}")
            return []
        except Exception as e:
            print(f"Lỗi xử lý dữ liệu nhân viên: {e}")
            import traceback
            traceback.print_exc()
            return []

# Chia nhỏ văn bản
def split_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    return text_splitter.split_documents(documents)

# Tạo vector store với ChromaDB
def create_vector_store(splits):
    # Sử dụng Google Generative AI Embeddings với model text-embedding-004
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    vectorstore = Chroma.from_documents(
        documents=splits, 
        embedding=embeddings, 
        persist_directory=os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    )
    return vectorstore

# Thiết lập chuỗi truy vấn RAG
def setup_rag_chain(vectorstore):
    # Retriever
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 1}  # Trả về 1 tài liệu phù hợp nhất (để tránh lỗi khi có ít tài liệu)
    )
    
    # Mẫu prompt
    template = """Sử dụng các ngữ cảnh sau để trả lời câu hỏi:
    {context}
    
    Câu hỏi: {question}
    """
    prompt = ChatPromptTemplate.from_template(template)
    
    # Mô hình ngôn ngữ Google - Sử dụng tên mô hình đúng định dạng
    model = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",  # Cập nhật tên mô hình
        temperature=0.7,
        convert_system_message_to_human=True  # Thêm tùy chọn này để đảm bảo tương thích
    )
    
    # Xây dựng chuỗi RAG
    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | model
        | StrOutputParser()
    )
    
    return rag_chain

def main():
    # Thông tin đăng nhập
    username = "asgl-01940"
    password = "66668889"
    
    # Khởi tạo client API
    api_client = ASGLAPIClient(username, password)
    
    # Đăng nhập
    if not api_client.login():
        print("Đăng nhập thất bại")
        return
    
    # In thông tin người dùng
    print("Đăng nhập thành công:")
    print(f"Tên: {api_client.user_info.get('full_name')}")
    print(f"Username: {api_client.user_info.get('username')}")
    
    # Lấy danh sách nhân viên
    documents = api_client.fetch_employees()
    
    # Kiểm tra dữ liệu
    if not documents:
        print("Không có dữ liệu nhân viên")
        return
    
    # Chia nhỏ tài liệu
    splits = split_documents(documents)
    
    # Tạo vector store
    vectorstore = create_vector_store(splits)
    
    # Thiết lập chuỗi RAG
    rag_chain = setup_rag_chain(vectorstore)
    
    # Ví dụ truy vấn
    while True:
        query = input("\nNhập câu hỏi (hoặc 'thoát' để kết thúc): ")
        
        if query.lower() == 'thoát':
            break
        
        try:
            result = rag_chain.invoke(query)
            print("\nKết quả:")
            print(result)
        except Exception as e:
            print(f"\nLỗi khi xử lý câu hỏi: {e}")
            # Thêm mã kiểm tra mô hình có sẵn
            try:
                # Hiển thị các mô hình có sẵn
                import google.generativeai as genai
                genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
                models = genai.list_models()
                print("\nCác mô hình có sẵn:")
                for model in models:
                    print(f"- {model.name}")
                print("\nVui lòng cập nhật mã nguồn với một trong những mô hình ở trên.")
            except Exception as list_error:
                print(f"Không thể liệt kê mô hình: {list_error}")

if __name__ == "__main__":
    main()

