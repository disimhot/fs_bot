from aiogram import Router, Bot
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram import F
import matplotlib.pyplot as plt
from config import logger

from bot.helpers import BotCommands
from bot.states import ProfileSave, WaterLog, FoodLog, WorkoutLog
from bot.storage import add_profile_params, get_profile_params_by_id, update_profile_params
from bot.helpers import Person, Food
from bot.helpers.menu import change_main_menu
from bot.keyboards.trainings import get_training_kb

from bot.helpers.training import *

router: Router = Router()
food_searcher = Food()
WORKOUTS = [RUNNING, CYCLING, STRENGTH, SWIMMING, CARDIO, WALKING]


@router.callback_query(ProfileSave.confirmation)
async def process_confirmation(callback_query: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    status = callback_query.data
    if status == "confirm":
        await change_main_menu(bot)
        await callback_query.answer("Подожите, бот рассчитывает норму калорий...")
        await state.update_data(status=status)

        data = await state.get_data()
        try:
            person = Person(**data)
            calorie_goal = person.count_daily_calorie_rate()
            water_goal = await person.count_daily_water_rate()
            data['logged_calories'] = [calorie_goal]
            data['logged_water'] = [water_goal]
            data['water_goal'] = water_goal
            data['calorie_goal'] = calorie_goal
            data['burned_calories'] = 0
            data['drunken_water'] = 0
            add_profile_params(callback_query.from_user.id, data)
            await callback_query.message.reply(
                f"Ваша норма калорий 🍧 : {calorie_goal} ккал\nВаша норма воды 🚰: {water_goal} мл")
            await state.clear()
        except Exception as e:
            logger.error(f"Error while processing confirmation: {str(e)}")
            await callback_query.message.reply("Произошла ошибка при поиске города. Попробуйте снова /set_profile")
            await state.clear()
    elif status == "cancel":
        await state.clear()
        await callback_query.message.reply("Подтверждение отменено.\n Для введения новых данных используйте /set_profile")


@router.message(Command(BotCommands.LogWater.value))
async def log_water(message: Message, state: FSMContext) -> None:
    await message.reply("Введите количество выпитой воды: ")
    await state.set_state(WaterLog.amount)


@router.message(WaterLog.amount)
async def process_water_amount(message: Message, state: FSMContext) -> None:
    water_amount = int(message.text)
    await state.update_data(water_amount=water_amount)
    await message.answer("Подожите, бот рассчитывает оставшуюся норму воды...")
    person_data = get_profile_params_by_id(message.from_user.id)
    water_goal = person_data.get('water_goal')
    logged_water = person_data.get('logged_water')
    drunken_water = person_data.get('drunken_water')
    water_goal -= water_amount
    drunken_water += water_amount
    logged_water.append(water_goal)
    data = {
        'water_goal': water_goal,
        'logged_water': logged_water,
        'drunken_water': drunken_water,
    }

    update_profile_params(message.from_user.id, data)

    await state.clear()
    await message.answer(
        f"Выпито: {water_amount} мл\nОсталось выпить воды: "
        f"{water_goal if water_goal >= 0 else 0} мл")


@router.message(Command(BotCommands.LogFood.value))
async def log_food(message: Message, state: FSMContext) -> None:
    await message.reply("Введите название продукта: ")
    await state.set_state(FoodLog.food)


@router.message(FoodLog.food)
async def process_food_name(message: Message, state: FSMContext) -> None:
    food_name = message.text
    await state.update_data(food_name=food_name)
    await message.reply("Введите количество в граммах: ")
    await state.set_state(FoodLog.amount)


@router.message(FoodLog.amount)
async def process_food_amount(message: Message, state: FSMContext) -> None:
    try:
        food_amount = int(message.text)
        await state.update_data(amount=food_amount)
        state_data = await state.get_data()
        await message.answer("Подожите, бот рассчитывает калории...")
        person_data = get_profile_params_by_id(message.from_user.id)
        calorie_goal = person_data.get('calorie_goal')
        logged_calories = person_data.get('logged_calories')
        nutritional_info = await food_searcher.fetch_fatsecret_data(**state_data)
        calories, fat, carbs, protein = nutritional_info.values()
        logged_cal = calories * food_amount // 100
        new_calorie_goal = calorie_goal - logged_cal
        logged_calories.append(new_calorie_goal)
        data = {
            'calorie_goal': new_calorie_goal,
            'logged_calories': logged_calories
        }
        update_profile_params(message.from_user.id, data)

        await state.clear()
        await message.answer(
            f"✅"
            f"Потреблено: {logged_cal} ккал\nОсталось потребить: "
            f"{new_calorie_goal if new_calorie_goal >= 0 else 0} ккал\n"
            f"В продукте содержится белков {protein}, жиров {fat}, углеводов {carbs}.")
    except Exception as e:
        logger.error(e)
        await message.answer(f"Продукт не найден. Попробуйте найти другой /log_food")


@router.message(Command(BotCommands.LogWorkout.value))
async def log_workout(message: Message, state: FSMContext) -> None:
    await state.set_state(WorkoutLog.workout)
    await message.answer(
        "Пожалуйста, выберите тренировку ниже 🏃‍♂️:",
        reply_markup=get_training_kb()
    )


@router.message(F.text.in_(WORKOUTS))
async def process_training(message: Message, state: FSMContext) -> None:
    workout = message.text
    await state.update_data(workout=workout)
    await message.reply("Cколько минут проходила тренировка?")
    await state.set_state(WorkoutLog.minutes)


@router.message(WorkoutLog.minutes)
async def process_workout_duration(message: Message, state: FSMContext) -> None:
    telegram_id = message.from_user.id
    minutes = int(message.text)
    await state.update_data(minutes=minutes)
    state_data = await state.get_data()
    workout = state_data.get('workout')
    new_burned_cal, new_burned_water = count_training_waste(workout, minutes)
    personal_data = get_profile_params_by_id(telegram_id)

    logged_calories = personal_data.get('logged_calories')
    calorie_goal = personal_data.get('calorie_goal')
    water_goal = personal_data.get('water_goal')
    logged_water = personal_data.get('logged_water')
    burned_calories = personal_data.get('burned_calories')

    new_calorie_goal = calorie_goal + burned_calories
    new_water_goal = water_goal + new_burned_water
    burned_calories += new_burned_cal
    logged_calories.append(new_calorie_goal)
    logged_water.append(new_water_goal)

    data = {
        'calorie_goal': new_calorie_goal,
        'water_goal': new_water_goal,
        'logged_calories': logged_calories,
        'logged_water': logged_water,
        'burned_calories': burned_calories,
    }
    update_profile_params(telegram_id, data)
    await state.clear()
    await message.answer(
        f"🏃 {workout} {minutes} минут — {burned_calories} ккал.\nДополнительно: выпейте "
        f"{new_burned_water} мл воды.")


@router.message(Command(BotCommands.CheckProgress.value))
async def log_training(message: Message) -> None:
    telegram_id = message.from_user.id
    personal_data = get_profile_params_by_id(telegram_id)

    logged_calories = personal_data.get('logged_calories')
    calorie_goal = personal_data.get('calorie_goal')
    rest_calorie_goal = logged_calories[0] - calorie_goal
    water_goal = personal_data.get('water_goal')
    drunken_water = personal_data.get('drunken_water')

    rest_water = water_goal - drunken_water
    burned_calories = personal_data.get('burned_calories')

    await message.answer(
        f"📊 Прогресс:\nВода:\n- Выпито: {drunken_water} мл из {water_goal} мл.\n- Осталось: "
        f"{rest_water} "
        f"мл.\nКалории:\n- "
        f"Потреблено: {rest_calorie_goal} ккал из {logged_calories[0]} ккал.\n- Сожжено: "
        f"{burned_calories} ккал.\n- Осталось: {calorie_goal} ккал"
    )


@router.message(Command(BotCommands.GetGraph.value))
async def get_graph(message: Message) -> None:
    telegram_id = message.from_user.id
    personal_data = get_profile_params_by_id(telegram_id)

    logged_calories = personal_data.get('logged_calories')
    logged_water = personal_data.get('logged_water')

    plt.figure(figsize=(8, 5))
    plt.plot(range(1, len(logged_water) + 1), logged_water, marker="o", linestyle="-", color="blue",
             label="Вода в мл")
    plt.ylabel("Вода в мл")
    plt.title("Потребление воды")
    plt.xticks([])
    plt.legend()
    plt.savefig("water.png")
    plt.close()
    water_file = InputMediaPhoto(type='photo', media=FSInputFile("water.png"))

    plt.figure(figsize=(8, 5))
    plt.plot(range(1, len(logged_calories) + 1), logged_calories, marker="o", linestyle="-",
             color="orange", label="Calories")
    plt.ylabel("Калории")
    plt.title("Потребление калорий")
    plt.xticks([])
    plt.legend()
    plt.savefig("calories.png")
    plt.close()
    calories_file = InputMediaPhoto(type='photo', media=FSInputFile("calories.png"))

    await message.answer_media_group(media=[water_file, calories_file])
