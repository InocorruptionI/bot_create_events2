import asyncio
import handlers
import logging

from aiogram import Dispatcher, Bot
from constants import TOKEN


bot = Bot(token=TOKEN)
dp = Dispatcher()


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    dp.include_router(handlers.router)
    logging.basicConfig(level=logging.INFO)

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print('Exit')
