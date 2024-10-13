import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import router
from config import API_TOKEN
from utils import scheduled_bump

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)

async def main():
    asyncio.create_task(scheduled_bump(bot))
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())