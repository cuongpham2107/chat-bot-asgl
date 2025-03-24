from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import user, chat, message, auth, file
from . import database
from .middleware import AuthMiddleware
from .core.config import ChatAgentConfig

app = FastAPI(title="Chat API", description="FastAPI Chat Application with Prisma")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware
app.add_middleware(AuthMiddleware)

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(user.router, prefix="/api/users", tags=["users"])
app.include_router(chat.router, prefix="/api/chats", tags=["chats"])
app.include_router(message.router, prefix="/api/messages", tags=["messages"])
app.include_router(file.router, prefix="/api/files", tags=["files"])


@app.get("/")
async def root():
    return {"message": "Welcome to the Chat API"}

@app.get('/api/options')
async def get_options():
    return ChatAgentConfig.dataApiFetching