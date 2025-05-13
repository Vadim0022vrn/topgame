from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from utils.database import execute_db_query
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from handlers.profile import handle_assets
from config.assets import HOUSES
import logging

logger = logging.getLogger("handlers.house")
router = Router()

@router.message(Command("houses"))
async def handle_houses(message: Message):
    try:
        user_id = message.from_user.id
        query = "SELECT level FROM users WHERE user_id = %s"
        result = await execute_db_query(query, (user_id,))
        
        if not result:
            await message.answer("Ошибка: пользователь не найден в базе данных.")
            return
        
        user_level = result[0][0]
        available_houses = [
            f"{house_id}. <b>{house['name']} - {house['price']}</b> 💰\n"
            for house_id, house in HOUSES.items() if user_level >= house['level_required']
        ]
        
        if available_houses:
            houses_list = "\n".join(available_houses)
            await message.answer(f"Доступное жилье:\n\n{houses_list}")

            # Получаем следующий дом, который будет доступен после повышения уровня
            next_house = None
            for house_id, house in HOUSES.items():
                if house['level_required'] > user_level:
                    next_house = house
                    break

            # Добавляем сообщение о следующем доме
            if next_house:
                next_house_message = (
                    f"\n\n🏠 <b>Следующий дом:</b> {next_house['name']}\n"
                    f"🔓 <b>Доступен с уровня:</b> {next_house['level_required']}\n"
                    f"💵 <b>Цена:</b> {next_house['price']} 💰\n\n"
                    f"Повышайте уровень, чтобы открыть лучшее жилье! 🏡✨"
                )
                await message.answer(next_house_message, parse_mode="HTML")
        else:
            await message.answer("Нет доступного жилья для вашего уровня.")
        
        # Создаем клавиатуру с кнопками
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🏠 Купить дом")],
                [KeyboardButton(text="🏠 Продать дом")],
                [KeyboardButton(text="🏠 Имущество")],
                [KeyboardButton(text="👤 Профиль")]
            ],
            resize_keyboard=True  # Кнопки будут автоматически подстраиваться под размер экрана
        )

        # Отправляем сообщение с клавиатурой
        await message.answer("Выберите действие:", reply_markup=keyboard)

    except Exception as e:
        await message.answer("Ошибка при получении списка жилья.")
        logger.error(f"Ошибка при обработке запроса на доступное жилье: {e}")

@router.message(Command("buyhouse"))
async def handle_buyhouse(message: Message, house_id: int):
    try:
        user_id = message.from_user.id

        if house_id not in HOUSES:
            await message.answer("Жилье с таким номером не найдено.")
            await handle_assets(message)  # Возвращаем в список домов
            return

        house = HOUSES[house_id]
        house_name, house_price, level_required = house["name"], house["price"], house["level_required"]

        query = "SELECT level, balance, house FROM users WHERE user_id = %s"
        result = await execute_db_query(query, (user_id,))
        
        if not result:
            await message.answer("Ошибка: пользователь не найден в базе данных.")
            await handle_assets(message)  # Возвращаем в список домов
            return
        
        user_level, user_balance, user_house = result[0]
        
        if user_house:
            await message.answer("У вас уже есть жилье. Продайте его, чтобы купить новое.")
            await handle_assets(message)  # Возвращаем в список домов
            return
        
        if user_level < level_required:
            await message.answer(f"Это жилье доступно с {level_required} уровня.")
            await handle_assets(message)  # Возвращаем в список домов
            return
        
        if user_balance < house_price:
            await message.answer("У вас недостаточно средств для покупки этого жилья.")
            await handle_assets(message)  # Возвращаем в список домов
            return
        
        cashback = house_price * 0.02
        exp_reward = 50  # Опыт за покупку
        update_query = "UPDATE users SET balance = balance - %s, house = %s, cashback = cashback + %s, experience = experience + %s WHERE user_id = %s"
        await execute_db_query(update_query, (house_price, house_id, cashback, exp_reward, user_id))
        
        await message.answer(f"Вы успешно купили {house_name} за {house_price} 💰!")
        logger.info(f"Пользователь {user_id} купил {house_name} за {house_price} 💰.")

    except Exception as e:
        await message.answer("Ошибка при покупке жилья.")
        logger.error(f"Ошибка при обработке покупки жилья: {e}")

    # Всегда возвращаем пользователя в список домов
    await handle_assets(message)

@router.message(Command("sellhouse"))
async def handle_sellhouse(message: Message):
    try:
        user_id = message.from_user.id
        query = "SELECT house FROM users WHERE user_id = %s"
        result = await execute_db_query(query, (user_id,))
        
        if not result:
            await message.answer("Ошибка: пользователь не найден в базе данных.")
            return
        
        user_house = result[0][0]
        if not user_house:
            await message.answer("У вас нет жилья для продажи.")
            return
        
        house = HOUSES.get(user_house)
        if not house:
            await message.answer("Ошибка: жилье не найдено в базе данных.")
            return
        
        house_name, house_price = house["name"], house["price"]
        sell_price = house_price * 0.4
        exp_reward = 20  # Опыт за продажу
        update_query = "UPDATE users SET house = NULL, balance = balance + %s, experience = experience + %s WHERE user_id = %s"
        await execute_db_query(update_query, (sell_price, exp_reward, user_id))
        
        await message.answer(f"Вы продали {house_name} за {sell_price} 💰.")
        logger.info(f"Пользователь {user_id} продал {house_name} за {sell_price} 💰.")
        await handle_assets(message)


    except Exception as e:
        await message.answer("Ошибка при продаже жилья.")
        logger.error(f"Ошибка при обработке продажи жилья: {e}")
