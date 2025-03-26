import os
from dotenv import load_dotenv

# Tải biến môi trường từ file .env
load_dotenv()


# Cấu hình cho ChatAgent
class ChatAgentConfig:
    # API key và thư mục lưu trữ
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")

    # Cấu hình mô hình mặc định
    DEFAULT_MODEL_NAME = "gemini-1.5-flash"
    DEFAULT_TEMPERATURE = 0.7

    # Cấu hình embedding
    EMBEDDING_MODEL = "models/embedding-001"

    # Cấu hình text splitter
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200

    # Cấu hình retriever
    RETRIEVER_SEARCH_TYPE = "similarity"
    RETRIEVER_K = 5

    # Giới hạn độ dài tiêu đề
    MAX_TITLE_LENGTH = 50
    DEFAULT_CHAT_TITLE = "Cuộc trò chuyện mới"

    UPLOAD_DIR = "public/uploads"

    # Prompt mặc định cho hệ thống
    DEFAULT_SYSTEM_PROMPT = """Bạn là một trợ lý thân thiện! Khi trả lời câu hỏi của người dùng:

1. **Trả lời đầy đủ và rõ ràng**, không bỏ sót thông tin quan trọng.

2. **Sắp xếp câu trả lời theo dàn ý**, sử dụng tiêu đề lớn, đầu mục và đánh số khi cần.

3. **Dùng Markdown để định dạng thông tin**, bao gồm:

- **Tiêu đề lớn** (`#`) để nhóm nội dung chính.

- **Tiêu đề nhỏ hơn** (`##`, `###`) để chi tiết hóa.

- **Danh sách có thứ tự:

```markdown
1. Mục 1
2. Mục 2
```

- **Danh sách không thứ tự** sử dụng dấu `-` hoặc `+`:

```markdown
* Mục chính
- Mục con
+ Mục cháu
```

- **Bôi đậm từ khóa quan trọng** để giúp người dùng dễ nắm bắt thông tin.

- **Gạch ngang** (`---`) để phân chia các phần khác nhau.

- **Nếu dữ liệu dạng bảng thì sử dụng các kí tự (`|`, `-`, `:`) để tạo bảng:**

```markdown
| Cột 1 | Cột 2 | Cột 3 |
|-------|-------|-------|
| Dữ liệu 1 | Dữ liệu 2 | Dữ liệu 3 |
| Nội dung | Căn giữa | Căn phải |
```

- **Trích dẫn (Blockquote)** sử dụng (`>`) để làm nổi bật các câu quan trọng hoặc trích dẫn:

```markdown
> Đây là trích dẫn hoặc thông tin quan trọng cần nhấn mạnh
```

- **Liệt kê dạng checkbox** sử dụng (`- [ ]`) để tạo danh sách checklist hoặc các bước thực hiện:

```markdown
- [ ] Công việc chưa hoàn thành
- [x] Công việc đã hoàn thành
```

- **Thêm hình ảnh** sử dụng cú pháp (`![alt text](link_image)`) để hiển thị hình ảnh trực quan.

- **Chèn liên kết** sử dụng cú pháp (`[text](link)`) để chèn liên kết đến trang web hoặc tài liệu khác.

- **Kết hợp biểu tượng cảm xúc** (`:tên_emoji:`) (trên GitHub, Discord, Slack,...) để thể hiện tâm trạng hoặc cảm xúc của câu trả lời.

4. **Cung cấp ví dụ hoặc giải thích khi cần thiết** để giúp người dùng hiểu rõ hơn.

5. **Luôn giữ phong cách trả lời đầy đủ, trọng tâm nhưng đầy đủ ý**.

6. **Kiểm tra lại câu trả lời trước khi gửi** để đảm bảo không có lỗi chính tả hoặc sai sót khác.

7. **Tránh sử dụng ngôn ngữ chuyên môn hoặc khó hiểu**. Sử dụng ngôn ngữ đơn giản, dễ hiểu.

8. **Khi kết thúc cuộc trò chuyện, hỏi người dùng có cần hỗ trợ gì khác không**.

9. **Nếu không chắc chắn về câu trả lời, hãy yêu cầu người dùng cung cấp thêm thông tin**.

10. **Nếu không thể giúp được, hãy thông báo cho người dùng biết**.

Nếu một câu hỏi không rõ ràng hoặc không thực sự mạch lạc, hãy giải thích tại sao thay vì trả lời điều gì đó không chính xác. Nếu bạn không biết câu trả lời cho một câu hỏi, xin đừng chia sẻ thông tin sai lệch."""

    # Prompt cho việc tạo tiêu đề
    TITLE_GENERATION_PROMPT = """Bạn là một trợ lý AI chuyên tạo tiêu đề ngắn gọn và súc tích. 
    Nhiệm vụ của bạn là tạo một tiêu đề ngắn (tối đa 50 ký tự) cho cuộc trò chuyện dựa trên tin nhắn đầu tiên của người dùng.
    Tiêu đề nên phản ánh chủ đề chính hoặc mục đích của cuộc trò chuyện.
    Chỉ trả về tiêu đề, không thêm bất kỳ giải thích hoặc định dạng nào khác.

    Tin nhắn của người dùng: {message}

    Tiêu đề:"""

    # Prompt cho việc trả lời dựa trên tài liệu
    DOCUMENT_QA_PROMPT = """Bạn là một trợ lý AI chuyên trả lời câu hỏi dựa trên tài liệu được cung cấp.
    Hãy sử dụng thông tin từ các đoạn văn bản sau đây để trả lời câu hỏi của người dùng.
    Nếu câu trả lời không có trong tài liệu, hãy nói rằng bạn không tìm thấy thông tin liên quan và đề xuất người dùng đặt câu hỏi khác.
    Không tạo ra thông tin không có trong tài liệu.

    Đoạn văn bản tham khảo:
    {context}

    Câu hỏi: {question}

    Trả lời:"""

    # Prompt cho việc trả lời dựa trên tài liệu với lịch sử trò chuyện
    DOCUMENT_QA_WITH_HISTORY_PROMPT = """Bạn là một trợ lý AI chuyên trả lời câu hỏi dựa trên tài liệu được cung cấp.
    Hãy sử dụng thông tin từ các đoạn văn bản sau đây để trả lời câu hỏi của người dùng.
    Nếu câu trả lời không có trong tài liệu, hãy nói rằng bạn không tìm thấy thông tin liên quan và đề xuất người dùng đặt câu hỏi khác.
    Không tạo ra thông tin không có trong tài liệu.
    
    Lịch sử trò chuyện:
    {chat_history}
    
    Đoạn văn bản tham khảo:
    {context}
    
    Câu hỏi hiện tại: {question}
    
    Trả lời:"""


    API_CHAT_PROMPT_TEMPLATE = """Dựa trên dữ liệu từ API sau đây:
    {context}
    
    {chat_history_text}
    
    Câu hỏi hiện tại: {question}
    
    Yêu cầu:
    1. Trả lời ngắn gọn và chính xác
    2. Chỉ sử dụng thông tin từ dữ liệu được cung cấp
    3. Nếu không có thông tin phù hợp, hãy nói rõ điều đó
    4. Đảm bảo phản hồi nhất quán với các câu trả lời trước đó
    
    Trả lời:"""

    # Thông báo lỗi
    ERROR_MESSAGES = {
        "document_not_found": "Không tìm thấy tài liệu với ID {source_file_id}. Vui lòng tải lên tài liệu trước khi trò chuyện.",
        "no_relevant_info": "Tôi không tìm thấy thông tin liên quan đến câu hỏi của bạn trong tài liệu. Vui lòng thử đặt câu hỏi khác.",
        "processing_error": "Tôi gặp lỗi khi xử lý yêu cầu của bạn. Vui lòng thử lại sau. Lỗi: {error}",
        "api_key_missing": "Google API key is required. Set it in the .env file or pass it to the constructor.",
    }

    dataApiFetching = [
        {
            "id": "cm8o9a3b10000t37ajy36j07t",
            "name": "Nhân sự",
            "value": "human",
            "icon": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIGNsYXNzPSJsdWNpZGUgbHVjaWRlLXVzZXJzIj48cGF0aCBkPSJNMTYgMjF2LTJhNCA0IDAgMCAwLTQtNEg2YTQgNCAwIDAgMC00IDR2MiIvPjxjaXJjbGUgY3g9IjkiIGN5PSI3IiByPSI0Ii8+PHBhdGggZD0iTTIyIDIxdi0yYTQgNCAwIDAgMC0zLTMuODciLz48cGF0aCBkPSJNMTYgMy4xM2E0IDQgMCAwIDEgMCA3Ljc1Ii8+PC9zdmc+",
            "description": "Thông tin về nhân sự",
            "sql_connect": "mysql+pymysql://asgldb:asgl2019@192.168.1.100:3306/shipping_test",
        },
        # {
        #     "id": 2,
        #     "name": "Tuyển dụng",
        #     "icon": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIGNsYXNzPSJsdWNpZGUgbHVjaWRlLWJyaWVmY2FzZSI+PHBhdGggZD0iTTE2IDIwVjRhMiAyIDAgMCAwLTItMmgtNGEyIDIgMCAwIDAtMiAydjE2Ii8+PHJlY3Qgd2lkdGg9IjIwIiBoZWlnaHQ9IjE0IiB4PSIyIiB5PSI2IiByeD0iMiIvPjwvc3ZnPg==",
        #     "description": "Thông tin về tuyển dụng",
        #     "url": "/api/chat/tuyendung",
        # },
        # {
        #     "id": 3,
        #     "name": "Thảo luận",
        #     "icon": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIGNsYXNzPSJsdWNpZGUgbHVjaWRlLW1lc3NhZ2Utc3F1YXJlLWRvdCI+PHBhdGggZD0iTTExLjcgM0g1YTIgMiAwIDAgMC0yIDJ2MTZsNC00aDEyYTIgMiAwIDAgMCAyLTJ2LTIuNyIvPjxjaXJjbGUgY3g9IjE4IiBjeT0iNiIgcj0iMyIvPjwvc3ZnPg==",
        #     "description": "Thông tin về thảo luận",
        #     "url": "/api/chat/thaoluan",
        # },
        # {
        #     "id": 4,
        #     "name": "Tài liệu",
        #     "icon": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIGNsYXNzPSJsdWNpZGUgbHVjaWRlLWZpbGUtdGV4dCI+PHBhdGggZD0iTTE1IDJINmEyIDIgMCAwIDAtMiAydjE2YTIgMiAwIDAgMCAyIDJoMTJhMiAyIDAgMCAwIDItMlY3WiIvPjxwYXRoIGQ9Ik0xNCAydjRhMiAyIDAgMCAwIDIgMmg0Ii8+PHBhdGggZD0iTTEwIDlIOCIvPjxwYXRoIGQ9Ik0xNiAxM0g4Ii8+PHBhdGggZD0iTTE2IDE3SDgiLz48L3N2Zz4=",
        #     "description": "Tài liệu liên quan đến công việc",
        #     "url": "/api/chat/taidulieu",
        # },
        # {
        #     "id": 5,
        #     "name": "Thực đơn",
        #     "icon": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIGNsYXNzPSJsdWNpZGUgbHVjaWRlLXV0ZW5zaWxzIj48cGF0aCBkPSJNMyAydjdjMCAxLjEuOSAyIDIgMmg0YTIgMiAwIDAgMCAyLTJWMiIvPjxwYXRoIGQ9Ik03IDJ2MjAiLz48cGF0aCBkPSJNMjEgMTVWMmE1IDUgMCAwIDAtNSA1djZjMCAxLjEuOSAyIDIgMmgzWm0wIDB2NyIvPjwvc3ZnPg==",
        #     "description": "Thông tin về thực đơn hàng ngày của công ty",
        #     "url": "/api/chat/thucdon",
        # },
        # {
        #     "id": 6,
        #     "name": "Đào tạo",
        #     "icon": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIGNsYXNzPSJsdWNpZGUgbHVjaWRlLWdyYWR1YXRpb24tY2FwIj48cGF0aCBkPSJNMjEuNDIgMTAuOTIyYTEgMSAwIDAgMC0uMDE5LTEuODM4TDEyLjgzIDUuMThhMiAyIDAgMCAwLTEuNjYgMEwyLjYgOS4wOGExIDEgMCAwIDAgMCAxLjgzMmw4LjU3IDMuOTA4YTIgMiAwIDAgMCAxLjY2IDB6Ii8+PHBhdGggZD0iTTIyIDEwdjYiLz48cGF0aCBkPSJNNiAxMi41VjE2YTYgMyAwIDAgMCAxMiAwdi0zLjUiLz48L3N2Zz4=",
        #     "description": "Thông tin về đào tạo",
        #     "url": "/api/chat/daotao",
        # },
        # {
        #     "id": 7,
        #     "name": "Test API dummy Json",
        #     "icon": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIGNsYXNzPSJsdWNpZGUgbHVjaWRlLXBhcnR5LXBvcHBlciI+PHBhdGggZD0iTTUuOCAxMS4zIDIgMjJsMTAuNy0zLjc5Ii8+PHBhdGggZD0iTTQgM2guMDEiLz48cGF0aCBkPSJNMjIgOGguMDEiLz48cGF0aCBkPSJNMTUgMmguMDEiLz48cGF0aCBkPSJNMjIgMjBoLjAxIi8+PHBhdGggZD0ibTIyIDItMi4yNC43NWEyLjkgMi45IDAgMCAwLTEuOTYgMy4xMmMuMS44Ni0uNTcgMS42My0xLjQ1IDEuNjNoLS4zOGMtLjg2IDAtMS42LjYtMS43NiAxLjQ0TDE0IDEwIi8+PHBhdGggZD0ibTIyIDEzLS44Mi0uMzNjLS44Ni0uMzQtMS44Mi4yLTEuOTggMS4xMWMtLjExLjctLjcyIDEuMjItMS40MyAxLjIySDE3Ii8+PHBhdGggZD0ibTExIDIgLjMzLjgyYy4zNC44Ni0uMiAxLjgyLTEuMTEgMS45OEM5LjUyIDQuOSA5IDUuNTIgOSA2LjIzVjciLz48cGF0aCBkPSJNMTEgMTNjMS45MyAxLjkzIDIuODMgNC4xNyAyIDUtLjgzLjgzLTMuMDctLjA3LTUtMi0xLjkzLTEuOTMtMi44My00LjE3LTItNSAuODMtLjgzIDMuMDcuMDcgNSAyWiIvPjwvc3ZnPg==",
        #     "description": "Truy cập api /product để hỏi về thông tin sản phẩm",
        #     "url": "https://dummyjson.com/products",
        # },
    ]
