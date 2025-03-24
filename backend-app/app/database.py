from prisma import Prisma

# Create a single instance of the Prisma client
prisma = Prisma()

async def connect():
    await prisma.connect()

async def disconnect():
    await prisma.disconnect()