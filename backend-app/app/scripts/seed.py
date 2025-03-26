import asyncio
import hashlib
import sys
from app.database import prisma, connect, disconnect

# Helper function to hash passwords (same as in user.py)
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

async def seed_database():
    print("Connecting to database...")
    try:
        await connect()
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        return
    
    try:
        print("Seeding users...")
        
        # Define sample users
        users = [
            {
                "username": "admin",
                "name": "Admin User",
                "password": hash_password("admin123")
            },
            {
                "username": "user1",
                "name": "Regular User 1",
                "password": hash_password("user123")
            },
            {
                "username": "user2",
                "name": "Regular User 2",
                "password": hash_password("user456")
            },
            {
                "username": "support",
                "name": "Support Team",
                "password": hash_password("support789")
            }
        ]
        
        created_users = []
        
        # Add users to database
        for user_data in users:
            try:
                # Check if user already exists
                existing_user = await prisma.user.find_unique(
                    where={"username": user_data["username"]}
                )
                
                if existing_user:
                    print(f"User with username {user_data['username']} already exists, skipping...")
                    created_users.append(existing_user)
                    continue
                
                # Create new user
                user = await prisma.user.create(data=user_data)
                created_users.append(user)
                print(f"Created user: {user.name} ({user.username})")
            except Exception as e:
                print(f"Error creating user {user_data['username']}: {str(e)}")
        
        # Create sample chats and messages
        if created_users:
            print("Seeding chats and messages...")
            
            # Create chats for different users
            for i, user in enumerate(created_users):
                try:
                    # Create multiple chats for each user
                    for j in range(1, 3):
                        chat_title = f"{user.name}'s Chat {j}"
                        visibility = "public" if j % 2 == 0 else "private"
                        
                        chat = await prisma.chat.create(
                            data={
                                "title": chat_title,
                                "visibility": visibility,
                                "userId": user.id,
                                "messages": {
                                    "create": [
                                        {
                                            "role": "user",
                                            "content": f"Hello, this is a test message {j} in {chat_title}"
                                        },
                                        {
                                            "role": "assistant",
                                            "content": f"Hi there! I'm responding to your test message in {chat_title}"
                                        },
                                        {
                                            "role": "user",
                                            "content": "Can you help me with something?"
                                        },
                                        {
                                            "role": "assistant",
                                            "content": "Of course! What do you need help with?"
                                        }
                                    ]
                                }
                            }
                        )
                        print(f"Created chat: {chat.title} with 4 messages for user {user.username}")
                except Exception as e:
                    print(f"Error creating chat for user {user.username}: {str(e)}")
        
        print("Database seeding completed successfully!")
    
    except Exception as e:
        print(f"Error seeding database: {str(e)}")
        # Print full traceback for debugging
        import traceback
        traceback.print_exc()
    
    finally:
        print("Disconnecting from database...")
        try:
            await disconnect()
        except Exception as e:
            print(f"Error disconnecting from database: {str(e)}")

def run_seed():
    """Function to run the seed from command line"""
    asyncio.run(seed_database())
    
if __name__ == "__main__":
    run_seed()
