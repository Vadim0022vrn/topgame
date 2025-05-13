import logging
from aiogram import Router, types
from aiogram.types import Message
from aiogram.filters import Command
from utils.database import execute_db_query
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from handlers.profile import handle_assets
from config.assets import CARS

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = Router()

@router.message(Command("cars"))
async def handle_cars(message: Message):
    try:
        user_id = message.from_user.id
        
        # Получаем уровень пользователя
        query = "SELECT level FROM users WHERE user_id = %s"
        result = await execute_db_query(query, (user_id,))
        
        if not result:
            await message.answer("Ошибка: пользователь не найден в базе данных.")
            return
        
        user_level = result[0][0]
        
        # Формируем список доступных автомобилей (только обычные, не премиум)
        available_cars = [
            f"{car_id} - <b>{car['name']} - Цена: {car['price']}</b> 💰"
            for car_id, car in CARS.items()
            if car['level_required'] <= user_level and not car.get('is_premium', False)  # Исключаем премиум-автомобили
        ]
        
        if not available_cars:
            await message.answer("У вас нет доступных автомобилей для покупки.")
            return

        # Выводим список доступных автомобилей
        cars_list = "\n\n".join(available_cars)
        await message.answer(f"Доступные автомобили для покупки:\n\n{cars_list}")

        # Получаем следующий автомобиль, который будет доступен после повышения уровня
        next_car = None
        for car_id, car in CARS.items():
            if car['level_required'] > user_level and not car.get('is_premium', False):  # Исключаем премиум-автомобили
                next_car = car
                break

        # Добавляем сообщение о следующем автомобиле
        if next_car:
            next_car_message = (
                f"\n\n🚀 <b>Следующее авто:</b> {next_car['name']}\n"
                f"🔓 <b>Доступно с уровня:</b> {next_car['level_required']}\n"
                f"💵 <b>Цена:</b> {next_car['price']} 💰\n\n"
                f"Повышайте уровень, чтобы открыть лучшее авто! 🚗✨"
            )
            await message.answer(next_car_message, parse_mode="HTML")

        # Создаем клавиатуру с кнопками
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🚗 Купить авто")],
                [KeyboardButton(text="🚗 Продать авто")],
                [KeyboardButton(text="🏠 Имущество")],
                [KeyboardButton(text="👤 Профиль")]
            ],
            resize_keyboard=True  # Кнопки будут автоматически подстраиваться под размер экрана
        )

        # Отправляем сообщение с клавиатурой
        await message.answer("Выберите действие:", reply_markup=keyboard)

        # Логирование запроса пользователя
        logger.info(f"Пользователь {user_id} запросил список доступных автомобилей.")
        
    except Exception as e:
        await message.answer("Ошибка при получении списка автомобилей.")
        logger.error(f"Ошибка при обработке запроса на доступные автомобили: {e}")

@router.message(Command("premium_cars"))
async def handle_premium_cars(message: Message):
    try:
        user_id = message.from_user.id
        
        # Получаем уровень пользователя
        query = "SELECT level FROM users WHERE user_id = %s"
        result = await execute_db_query(query, (user_id,))
        
        if not result:
            await message.answer("Ошибка: пользователь не найден в базе данных.")
            return
        
        user_level = result[0][0]
        
        # Формируем список премиум-автомобилей
        premium_cars = [
            f"{car_id} - <b>{car['name']} - Цена: {car['price']} Aurix</b>"
            for car_id, car in CARS.items()
            if car.get('is_premium', False) and car['level_required'] <= user_level  # Только премиум-автомобили
        ]
        
        if not premium_cars:
            await message.answer("У вас нет доступных премиум-автомобилей для покупки.")
            return

        # Выводим список премиум-автомобилей
        cars_list = "\n\n".join(premium_cars)
        await message.answer(f"Доступные премиум-автомобили:\n\n{cars_list}")

        # Создаем клавиатуру с кнопками
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🚗 Купить премиум-авто")],
                [KeyboardButton(text="🏠 Имущество")],
                [KeyboardButton(text="👤 Профиль")]
            ],
            resize_keyboard=True  # Кнопки будут автоматически подстраиваться под размер экрана
        )

        # Отправляем сообщение с клавиатурой
        await message.answer("Выберите действие:", reply_markup=keyboard)

        # Логирование запроса пользователя
        logger.info(f"Пользователь {user_id} запросил список премиум-автомобилей.")
        
    except Exception as e:
        await message.answer("Ошибка при получении списка премиум-автомобилей.")
        logger.error(f"Ошибка при обработке запроса на премиум-автомобили: {e}")
        

async def handle_buycar(message: types.Message, car_id: int):
    try:
        user_id = message.from_user.id

        # Проверяем, существует ли пользователь в таблице users
        user_exists = await execute_db_query(
            "SELECT id FROM users WHERE user_id = %s",
            (user_id,)
        )
        if not user_exists:
            await message.answer("⚠️ Пользователь не найден. Зарегистрируйтесь через /start.")
            await handle_assets(message)  # Возвращаем в список автомобилей
            return

        user_db_id = user_exists[0][0]  # Получаем id пользователя из таблицы users

        # Проверяем, существует ли автомобиль с таким ID
        if car_id not in CARS:
            await message.answer("⚠️ Автомобиль с таким ID не найден.")
            await handle_assets(message)  # Возвращаем в список автомобилей
            return

        car = CARS[car_id]
        car_name = car["name"]
        car_price = car["price"]
        level_required = car["level_required"]
        is_premium = car.get("is_premium", False)  # Проверяем, является ли автомобиль премиумным

        # Проверяем уровень пользователя
        user_level = await execute_db_query(
            "SELECT level FROM users WHERE user_id = %s",
            (user_id,)
        )
        if not user_level:
            await message.answer("⚠️ Пользователь не найден.")
            await handle_assets(message)  # Возвращаем в список автомобилей
            return

        user_level = user_level[0][0]
        if user_level < level_required:
            await message.answer(f"⚠️ Для покупки этого автомобиля требуется уровень {level_required}. Ваш уровень: {user_level}.")
            await handle_assets(message)  # Возвращаем в список автомобилей
            return

        # Проверяем баланс пользователя (в зависимости от типа автомобиля)
        if is_premium:
            # Для премиум-автомобилей списываем Aurix
            user_balance = await execute_db_query(
                "SELECT aurix FROM users WHERE user_id = %s",
                (user_id,)
            )
            currency_name = "Aurix"
        else:
            # Для обычных автомобилей списываем баланс
            user_balance = await execute_db_query(
                "SELECT balance FROM users WHERE user_id = %s",
                (user_id,)
            )
            currency_name = "💵"

        if not user_balance:
            await message.answer("⚠️ Пользователь не найден.")
            await handle_assets(message)  # Возвращаем в список автомобилей
            return

        user_balance = user_balance[0][0]
        if user_balance < car_price:
            await message.answer(f"⚠️ Недостаточно {currency_name} для покупки автомобиля.")
            await handle_assets(message)  # Возвращаем в список автомобилей
            return

        # Проверяем, есть ли у пользователя уже автомобиль
        user_car = await execute_db_query(
            "SELECT car FROM users WHERE user_id = %s",
            (user_id,)
        )
        if user_car and user_car[0][0]:
            await message.answer("⚠️ У вас уже есть автомобиль. Сначала продайте его, чтобы купить новый.")
            await handle_assets(message)  # Возвращаем в список автомобилей
            return

        # Покупаем автомобиль (в зависимости от типа)
        if is_premium:
            # Для премиум-автомобилей списываем Aurix
            await execute_db_query(
                "UPDATE users SET car = %s, aurix = aurix - %s WHERE user_id = %s",
                (car_id, car_price, user_id)
            )
        else:
            # Для обычных автомобилей списываем баланс
            await execute_db_query(
                "UPDATE users SET car = %s, balance = balance - %s WHERE user_id = %s",
                (car_id, car_price, user_id)
            )

        await message.answer(f"🎉 Вы успешно купили автомобиль «{car_name}» за {car_price}{currency_name}!")

    except Exception as e:
        logger.error(f"Ошибка при покупке автомобиля: {e}")
        await message.answer("⚠️ Произошла ошибка при покупке автомобиля.")

    # Всегда возвращаем пользователя в список доступных автомобилей
    await handle_assets(message)

@router.message(Command("sellcar"))
async def handle_sellcar(message: Message):
    try:
        user_id = message.from_user.id

        # Получаем информацию о текущем автомобиле пользователя
        query = "SELECT car, experience FROM users WHERE user_id = %s"
        result = await execute_db_query(query, (user_id,))

        if not result:
            await message.answer("Ошибка: пользователь не найден в базе данных.")
            return

        user_car, user_experience = result[0]

        # Проверка, есть ли у пользователя автомобиль
        if not user_car:
            await message.answer("У вас нет автомобиля, чтобы продать его.")
            return

        # Получаем информацию о машине, которую пользователь хочет продать
        car = CARS.get(user_car)

        if not car:
            await message.answer("Ошибка: автомобиль не найден в базе данных.")
            return

        car_name = car["name"]
        car_price = car["price"]
        sell_price = int(car_price * 0.4)  # 40% от стоимости автомобиля
        sell_experience = 50  # Количество опыта за продажу (можно менять)

        # Убираем автомобиль и начисляем деньги и опыт пользователю
        update_query = """
            UPDATE users 
            SET car = NULL, 
                balance = balance + %s, 
                experience = experience + %s 
            WHERE user_id = %s
        """
        await execute_db_query(update_query, (sell_price, sell_experience, user_id))

        await message.answer(f"Вы продали {car_name} за {sell_price} 💰 и получили {sell_experience} опыта!")

        # Логирование успешной продажи
        logger.info(f"Пользователь {user_id} продал {car_name} за {sell_price} 💰 и получил {sell_experience} XP.")
        await handle_assets(message)

    except Exception as e:
        await message.answer("Ошибка при продаже автомобиля.")
        logger.error(f"Ошибка при обработке продажи автомобиля: {e}")
