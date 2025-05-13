import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from utils.database import execute_db_query
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from handlers.profile import handle_assets
from config.assets import ISLANDS

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = Router()

@router.message(Command("islands"))
async def handle_islands(message: Message):
    try:
        user_id = message.from_user.id
        
        # Получаем уровень пользователя
        query = "SELECT level FROM users WHERE user_id = %s"
        result = await execute_db_query(query, (user_id,))
        
        if not result:
            await message.answer("Ошибка: пользователь не найден в базе данных.")
            return
        
        user_level = result[0][0]
        
        # Формируем список доступных островов
        available_islands = [
            f"{island_id} - <b>{island['name']} - Цена: {island['price']}</b> 💰"
            for island_id, island in ISLANDS.items()
            if island['level_required'] <= user_level
        ]
        
        if not available_islands:
            await message.answer("У вас нет доступных островов для покупки.")
            return

        # Выводим список доступных островов
        islands_list = "\n\n".join(available_islands)
        await message.answer(f"Доступные острова для покупки:\n\n{islands_list}")

        # Получаем следующий остров, который будет доступен после повышения уровня
        next_island = None
        for island_id, island in ISLANDS.items():
            if island['level_required'] > user_level:
                next_island = island
                break

        # Добавляем сообщение о следующем острове
        if next_island:
            next_island_message = (
                f"\n\n🏝 <b>Следующий остров:</b> {next_island['name']}\n"
                f"🔓 <b>Доступен с уровня:</b> {next_island['level_required']}\n"
                f"💵 <b>Цена:</b> {next_island['price']} 💰\n\n"
                f"Повышайте уровень, чтобы открыть новые острова! 🌴✨"
            )
            await message.answer(next_island_message, parse_mode="HTML")

        # Создаем клавиатуру с кнопками
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🏝 Купить остров")],
                [KeyboardButton(text="🏝 Продать остров")],
                [KeyboardButton(text="🏠 Имущество")],
                [KeyboardButton(text="👤 Профиль")]
            ],
            resize_keyboard=True  # Кнопки будут автоматически подстраиваться под размер экрана
        )

        # Отправляем сообщение с клавиатурой
        await message.answer("Выберите действие:", reply_markup=keyboard)

        logger.info(f"Пользователь {user_id} запросил список доступных островов.")
        
    except Exception as e:
        await message.answer("Ошибка при получении списка островов.")
        logger.error(f"Ошибка при обработке запроса на доступные острова: {e}")

@router.message(Command("buyisland"))
async def handle_buyisland(message: Message, island_id: int):
    try:
        user_id = message.from_user.id

        if island_id not in ISLANDS:
            await message.answer("Остров с таким номером не найден.")
            await handle_assets(message)  # Возвращаем в список островов
            return

        island = ISLANDS[island_id]
        island_name = island["name"]
        island_price = island["price"]
        level_required = island["level_required"]
        cashback_amount = int(island_price * 0.02)  # 2% кешбэка
        experience_gain = 100  # Опыт за покупку

        # Получаем уровень, баланс, текущий остров, опыт и кешбэк пользователя
        query = "SELECT level, balance, island, experience, cashback FROM users WHERE user_id = %s"
        result = await execute_db_query(query, (user_id,))
        
        if not result:
            await message.answer("Ошибка: пользователь не найден в базе данных.")
            await handle_assets(message)  # Возвращаем в список островов
            return
        
        user_level, user_balance, user_island, user_experience, user_cashback = result[0]
        
        # Проверка, есть ли уже остров у пользователя
        if user_island:
            await message.answer("У вас уже есть остров. Вы не можете купить новый.")
            await handle_assets(message)  # Возвращаем в список островов
            return
        
        if user_level < level_required:
            await message.answer(f"Этот остров доступен с {level_required} уровня.")
            await handle_assets(message)  # Возвращаем в список островов
            return
        
        if user_balance < island_price:
            await message.answer("У вас недостаточно средств для покупки этого острова.")
            await handle_assets(message)  # Возвращаем в список островов
            return
        
        # Вычитаем деньги, обновляем остров, начисляем кешбэк и опыт
        update_query = """
            UPDATE users 
            SET balance = balance - %s, 
                island = %s, 
                experience = experience + %s, 
                cashback = cashback + %s 
            WHERE user_id = %s
        """
        await execute_db_query(update_query, (island_price, island_id, experience_gain, cashback_amount, user_id))
        
        await message.answer(f"Вы успешно купили {island_name} за {island_price} 💰!\n"
                             f"Вы получили {experience_gain} опыта и {cashback_amount} 💰 кешбэка.")

        # Логирование успешной покупки
        logger.info(f"Пользователь {user_id} купил {island_name} за {island_price} 💰. "
                    f"Получено {experience_gain} XP и {cashback_amount} 💰 кешбэка.")

    except Exception as e:
        await message.answer("Ошибка при покупке острова.")
        logger.error(f"Ошибка при обработке покупки острова: {e}")

    # Всегда возвращаем пользователя в список островов
    await handle_assets(message)

@router.message(Command("sellisland"))
async def handle_sellisland(message: Message):
    try:
        user_id = message.from_user.id

        # Получаем информацию о текущем острове пользователя
        query = "SELECT island, experience FROM users WHERE user_id = %s"
        result = await execute_db_query(query, (user_id,))

        if not result:
            await message.answer("Ошибка: пользователь не найден в базе данных.")
            return

        user_island, user_experience = result[0]

        # Проверка, есть ли у пользователя остров
        if not user_island:
            await message.answer("У вас нет острова, чтобы продать его.")
            return

        # Получаем информацию об острове, который пользователь хочет продать
        island = ISLANDS.get(user_island)

        if not island:
            await message.answer("Ошибка: остров не найден в базе данных.")
            return

        island_name = island["name"]
        island_price = island["price"]
        sell_price = int(island_price * 0.4)  # 40% от стоимости острова
        sell_experience = 50  # Количество опыта за продажу

        # Убираем остров и начисляем деньги и опыт пользователю
        update_query = """
            UPDATE users 
            SET island = NULL, 
                balance = balance + %s, 
                experience = experience + %s 
            WHERE user_id = %s
        """
        await execute_db_query(update_query, (sell_price, sell_experience, user_id))

        await message.answer(f"Вы продали {island_name} за {sell_price} 💰 и получили {sell_experience} опыта!")

        # Логирование успешной продажи
        logger.info(f"Пользователь {user_id} продал {island_name} за {sell_price} 💰 и получил {sell_experience} XP.")
        await handle_assets(message)

    except Exception as e:
        await message.answer("Ошибка при продаже острова.")
        logger.error(f"Ошибка при обработке продажи острова: {e}")