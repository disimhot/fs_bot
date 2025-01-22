from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from bot.helpers.training import *


def get_training_kb() -> InlineKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text=RUNNING),
            KeyboardButton(text=CYCLING)
        ], [
            KeyboardButton(text=STRENGTH),
            KeyboardButton(text=SWIMMING),
        ],
        [
            KeyboardButton(text=CARDIO),
            KeyboardButton(text=WALKING),
        ]]

    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выберите тренировку"
    )

    return keyboard
