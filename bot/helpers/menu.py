from aiogram import Bot
from aiogram import types
from bot.helpers import BotCommands


async def change_main_menu(bot: Bot) -> None:
    bot_commands = [
        types.BotCommand(command=BotCommands.LogFood.value, description="Записать питание 🍽"),
        types.BotCommand(command=BotCommands.LogWater.value, description="Записать воду 💧"),
        types.BotCommand(command=BotCommands.CheckProgress.value,
                         description="Проверить прогресс 📈"),
        types.BotCommand(command=BotCommands.LogWorkout.value,
                         description="Записать тренировки 🏃‍♂️"),
        types.BotCommand(command=BotCommands.GetGraph.value,
                         description="Посмотреть графики 📊",),
        types.BotCommand(command=BotCommands.StartCommand.value,
                         description="Начать работу с ботом 🚀"),
        types.BotCommand(command=BotCommands.SetProfileCommand.value,
                         description="Установить профиль 👤"),
        types.BotCommand(command=BotCommands.HelpCommand.value,
                         description="Узнать о боте ❓"),
    ]
    await bot.delete_my_commands()
    await bot.set_my_commands(bot_commands)
