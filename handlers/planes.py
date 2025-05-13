import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from utils.database import execute_db_query
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from handlers.profile import handle_assets
from config.assets import PLANES

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = Router()

@router.message(Command("planes"))
async def handle_planes(message: Message):
    try:
        user_id = message.from_user.id
        
        # Получаем уровень пользователя
        query = "SELECT level FROM users WHERE user_id = %s"
        result = await execute_db_query(query, (user_id,))
        
        if not result:
            await message.answer("Ошибка: пользователь не найден в базе данных.")
            return
        
        user_level = result[0][0]
        
        # Формируем список доступных самолетов
        available_planes = [
            f"{plane_id} - <b>{plane['name']} - Цена: {plane['price']}</b> 💰"
            for plane_id, plane in PLANES.items()
            if plane['level_required'] <= user_level
        ]
        
        if not available_planes:
            await message.answer("У вас нет доступных самолетов для покупки.")
            return

        # Выводим список доступных самолетов
        planes_list = "\n\n".join(available_planes)
        await message.answer(f"Доступные самолеты для покупки:\n\n{planes_list}")

        # Получаем следующий самолет, который будет доступен после повышения уровня
        next_plane = None
        for plane_id, plane in PLANES.items():
            if plane['level_required'] > user_level:
                next_plane = plane
                break

        # Добавляем сообщение о следующем самолете
        if next_plane:
            next_plane_message = (
                f"\n\n✈️ <b>Следующий самолет:</b> {next_plane['name']}\n"
                f"🔓 <b>Доступен с уровня:</b> {next_plane['level_required']}\n"
                f"💵 <b>Цена:</b> {next_plane['price']} 💰\n\n"
                f"Повышайте уровень, чтобы открыть новые самолеты! 🛫✨"
            )
            await message.answer(next_plane_message, parse_mode="HTML")

        # Создаем клавиатуру с кнопками
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✈️ Купить самолет")],
                [KeyboardButton(text="✈️ Продать самолет")],
                [KeyboardButton(text="🏠 Имущество")],
                [KeyboardButton(text="👤 Профиль")]
            ],
            resize_keyboard=True  # Кнопки будут автоматически подстраиваться под размер экрана
        )

        # Отправляем сообщение с клавиатурой
        await message.answer("Выберите действие:", reply_markup=keyboard)

        logger.info(f"Пользователь {user_id} запросил список доступных самолетов.")
        
    except Exception as e:
        await message.answer("Ошибка при получении списка самолетов.")
        logger.error(f"Ошибка при обработке запроса на доступные самолеты: {e}")

@router.message(Command("buyplane"))
async def handle_buyplane(message: Message, plane_id: int):
    try:
        user_id = message.from_user.id

        if plane_id not in PLANES:
            await message.answer("Самолет с таким номером не найден.")
            await handle_assets(message)  # Возвращаем в список самолетов
            return

        plane = PLANES[plane_id]
        plane_name = plane["name"]
        plane_price = plane["price"]
        level_required = plane["level_required"]
        cashback_amount = int(plane_price * 0.02)  # 2% кешбэка
        experience_gain = 100  # Опыт за покупку

        # Получаем уровень, баланс, текущий самолет, опыт и кешбэк пользователя
        query = "SELECT level, balance, airplane, experience, cashback FROM users WHERE user_id = %s"
        result = await execute_db_query(query, (user_id,))
        
        if not result:
            await message.answer("Ошибка: пользователь не найден в базе данных.")
            await handle_assets(message)  # Возвращаем в список самолетов
            return
        
        user_level, user_balance, user_plane, user_experience, user_cashback = result[0]
        
        # Проверка, есть ли уже самолет у пользователя
        if user_plane:
            await message.answer("У вас уже есть самолет. Вы не можете купить новый.")
            await handle_assets(message)  # Возвращаем в список самолетов
            return
        
        if user_level < level_required:
            await message.answer(f"Этот самолет доступен с {level_required} уровня.")
            await handle_assets(message)  # Возвращаем в список самолетов
            return
        
        if user_balance < plane_price:
            await message.answer("У вас недостаточно средств для покупки этого самолета.")
            await handle_assets(message)  # Возвращаем в список самолетов
            return
        
        # Вычитаем деньги, обновляем самолет, начисляем кешбэк и опыт
        update_query = """
            UPDATE users 
            SET balance = balance - %s, 
                airplane = %s, 
                experience = experience + %s, 
                cashback = cashback + %s 
            WHERE user_id = %s
        """
        await execute_db_query(update_query, (plane_price, plane_id, experience_gain, cashback_amount, user_id))
        
        await message.answer(f"Вы успешно купили {plane_name} за {plane_price} 💰!\n"
                             f"Вы получили {experience_gain} опыта и {cashback_amount} 💰 кешбэка.")

        # Логирование успешной покупки
        logger.info(f"Пользователь {user_id} купил {plane_name} за {plane_price} 💰. "
                    f"Получено {experience_gain} XP и {cashback_amount} 💰 кешбэка.")

    except Exception as e:
        await message.answer("Ошибка при покупке самолета.")
        logger.error(f"Ошибка при обработке покупки самолета: {e}")

    # Всегда возвращаем пользователя в список самолетов
    await handle_assets(message)

@router.message(Command("sellplane"))
async def handle_sellplane(message: Message):
    try:
        user_id = message.from_user.id

        # Получаем информацию о текущем самолете пользователя
        query = "SELECT airplane, experience FROM users WHERE user_id = %s"
        result = await execute_db_query(query, (user_id,))

        if not result:
            await message.answer("Ошибка: пользователь не найден в базе данных.")
            return

        user_plane, user_experience = result[0]

        # Проверка, есть ли у пользователя самолет
        if not user_plane:
            await message.answer("У вас нет самолета, чтобы продать его.")
            return

        # Получаем информацию о самолете, который пользователь хочет продать
        plane = PLANES.get(user_plane)

        if not plane:
            await message.answer("Ошибка: самолет не найден в базе данных.")
            return

        plane_name = plane["name"]
        plane_price = plane["price"]
        sell_price = int(plane_price * 0.4)  # 40% от стоимости самолета
        sell_experience = 50  # Количество опыта за продажу

        # Убираем самолет и начисляем деньги и опыт пользователю
        update_query = """
            UPDATE users 
            SET airplane = NULL, 
                balance = balance + %s, 
                experience = experience + %s 
            WHERE user_id = %s
        """
        await execute_db_query(update_query, (sell_price, sell_experience, user_id))

        await message.answer(f"Вы продали {plane_name} за {sell_price} 💰 и получили {sell_experience} опыта!")

        # Логирование успешной продажи
        logger.info(f"Пользователь {user_id} продал {plane_name} за {sell_price} 💰 и получил {sell_experience} XP.")
        await handle_assets(message)

    except Exception as e:
        await message.answer("Ошибка при продаже самолета.")
        logger.error(f"Ошибка при обработке продажи самолета: {e}")