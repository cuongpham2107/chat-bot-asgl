# FastAPI Backend with Prisma

A backend application built with FastAPI, Prisma Client Python, SQLite, Uvicorn, and Pydantic.

## Setup

### Prerequisites
- Python 3.8+
- pip

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd backend-app
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Generate Prisma Client Python:
```bash
prisma migrate dev --name init
prisma generate
```

5. Apply database migrations:
```bash
prisma db push
```

6. Run seed
```bash
./seed.sh
```


## Running the Application

Start the application with Uvicorn:
```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000.

## API Documentation

Swagger UI documentation is available at http://localhost:8000/docs
ReDoc documentation is available at http://localhost:8000/redoc

## API Endpoints

### Users
- `GET /api/users` - Get all users
- `POST /api/users` - Create a new user
  - Parameters:
    - `email` (string) - User's email address
    - `name` (string) - User's name
    - `password` (string) - User's password
- `GET /api/users/{user_id}` - Get a specific user
- `PUT /api/users/{user_id}` - Update a user
- `DELETE /api/users/{user_id}` - Delete a user
- `GET /api/users/me` - Get current user information

### Authentication
- `POST /api/auth/login` - Login user
  - Parameters:
    - `username` (string) - User's username
    - `password` (string) - User's password
  - Reponse:
    {
      "access_token": "string",
      "token_type": "string"
    }
- `POST /api/auth/register` - Register new user
  - Parameters:
    - `username` (string) - User's username
    - `password` (string) - User's password
    - `name` (string, optional) - User's name

### Chats
- `POST /api/chats/new-conversation` - Create a new conversation with first message and AI response
  - Parameters:
    - `message` (string) - Content of the user's first message
  - Returns:
    - Complete conversation object with messages and auto-generated title
- `POST /api/chats` - Create a new chat
  - Parameters:
    - `title` (string, optional) - Chat title
    - `visibility` (string) - Chat visibility (private/public)
- `GET /api/chats` - Get all chats for current user
- `GET /api/chats/{chat_id}` - Get a specific chat with messages
- `PUT /api/chats/{chat_id}` - Update a chat
  - Parameters:
    - `title` (string) - New chat title
    - `visibility` (string, optional) - Chat visibility (private/public)
- `DELETE /api/chats/{chat_id}` - Delete a chat

### Messages
- `POST /api/messages` - Create a new message
  - Parameters:
    - `content` (string) - Message content
    - `chat_id` (integer) - ID of the chat the message belongs to
    - `role` (string) - Role of the message sender (user/assistant)
- `GET /api/messages` - Get all messages
- `GET /api/messages/{message_id}` - Get a specific message
- `PUT /api/messages/{message_id}` - Update a message
  - Parameters:
    - `content` (string) - Updated message content
- `DELETE /api/messages/{message_id}` - Delete a message




python -m app.scripts.seed_api_data


