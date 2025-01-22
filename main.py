import asyncio
from aiogram import Bot, Dispatcher
from aiogram import types
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from config import API_TOKEN
from bot.handlers import get_routers
from bot.helpers import BotCommands
from bot.middlewares import LoggingMiddleware

class BotApp:
    def __init__(self, token: str):
        self.token = token
        self.bot = Bot(token=token, default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        ))
        self.dp = Dispatcher(storage=MemoryStorage())
        self.dp.include_routers(*get_routers())
        self.dp.update.outer_middleware(LoggingMiddleware())
    async def setup_bot_commands(self):
        bot_commands = [
            types.BotCommand(command=BotCommands.StartCommand.value,
                             description="Начать работу с ботом 🚀"),
            types.BotCommand(command=BotCommands.SetProfileCommand.value,
                             description="Установить профиль 👤"),
            types.BotCommand(command=BotCommands.HelpCommand.value,
                             description="Узнать о боте ❓")
        ]
        await self.bot.set_my_commands(bot_commands)

    async def start_polling(self):
        await self.dp.start_polling(self.bot,
                                    allowed_updates=self.dp.resolve_used_update_types())

    async def run(self):
        await self.setup_bot_commands()
        await self.start_polling()


# Main entry point
if __name__ == '__main__':
    app = BotApp(API_TOKEN)
    asyncio.run(app.run())
