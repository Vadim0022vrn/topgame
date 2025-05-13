import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from utils.database import execute_db_query
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from handlers.profile import handle_assets
from config.assets import YACHTS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = Router()

@router.message(Command("yachts"))
async def handle_yachts(message: Message):
    try:
        user_id = message.from_user.id
        query = "SELECT level FROM users WHERE user_id = %s"
        result = await execute_db_query(query, (user_id,))
        
        if not result:
            await message.answer("Ошибка: пользователь не найден в базе данных.")
            return
        
        user_level = result[0][0]
        available_yachts = [
            f"{yacht_id} - <b>{yacht['name']} - Цена: {yacht['price']}</b> 💰"
            for yacht_id, yacht in YACHTS.items()
            if yacht['level_required'] <= user_level
        ]
        
        if not available_yachts:
            await message.answer("У вас нет доступных яхт для покупки.")
            return
        
        yachts_list = "\n\n".join(available_yachts)
        await message.answer(f"Доступные яхты для покупки:\n\n{yachts_list}")

        # Получаем следующую яхту, которая будет доступна после повышения уровня
        next_yacht = None
        for yacht_id, yacht in YACHTS.items():
            if yacht['level_required'] > user_level:
                next_yacht = yacht
                break

        # Добавляем сообщение о следующей яхте
        if next_yacht:
            next_yacht_message = (
                f"\n\n🚤 <b>Следующая яхта:</b> {next_yacht['name']}\n"
                f"🔓 <b>Доступна с уровня:</b> {next_yacht['level_required']}\n"
                f"💵 <b>Цена:</b> {next_yacht['price']} 💰\n\n"
                f"Повышайте уровень, чтобы открыть новые яхты! 🌊✨"
            )
            await message.answer(next_yacht_message, parse_mode="HTML")

        # Создаем клавиатуру с кнопками
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🚤 Купить яхту")],
                [KeyboardButton(text="🚤 Продать яхту")],
                [KeyboardButton(text="🏠 Имущество")],
                [KeyboardButton(text="👤 Профиль")]
            ],
            resize_keyboard=True  # Кнопки будут автоматически подстраиваться под размер экрана
        )

        # Отправляем сообщение с клавиатурой
        await message.answer("Выберите действие:", reply_markup=keyboard)

        logger.info(f"Пользователь {user_id} запросил список доступных яхт.")
        
    except Exception as e:
        await message.answer("Ошибка при получении списка яхт.")
        logger.error(f"Ошибка при обработке запроса на доступные яхты: {e}")

@router.message(Command("buyyacht"))
async def handle_buyyacht(message: Message, yacht_id: int):
    try:
        user_id = message.from_user.id

        if yacht_id not in YACHTS:
            await message.answer("Яхта с таким номером не найдена.")
            await handle_assets(message)  # Возвращаем в список яхт
            return

        yacht = YACHTS[yacht_id]
        yacht_name = yacht["name"]
        yacht_price = yacht["price"]
        level_required = yacht["level_required"]
        cashback_amount = int(yacht_price * 0.02)
        experience_gain = 150

        # Получаем уровень, баланс, текущую яхту, опыт и кешбэк пользователя
        query = "SELECT level, balance, yacht, experience, cashback FROM users WHERE user_id = %s"
        result = await execute_db_query(query, (user_id,))
        
        if not result:
            await message.answer("Ошибка: пользователь не найден в базе данных.")
            await handle_assets(message)  # Возвращаем в список яхт
            return
        
        user_level, user_balance, user_yacht, user_experience, user_cashback = result[0]
        
        # Проверка, есть ли уже яхта у пользователя
        if user_yacht:
            await message.answer("У вас уже есть яхта. Вы не можете купить новую.")
            await handle_assets(message)  # Возвращаем в список яхт
            return
        
        if user_level < level_required:
            await message.answer(f"Эта яхта доступна с {level_required} уровня.")
            await handle_assets(message)  # Возвращаем в список яхт
            return
        
        if user_balance < yacht_price:
            await message.answer("У вас недостаточно средств для покупки этой яхты.")
            await handle_assets(message)  # Возвращаем в список яхт
            return
        
        # Вычитаем деньги, обновляем яхту, начисляем кешбэк и опыт
        update_query = """
            UPDATE users 
            SET balance = balance - %s, 
                yacht = %s, 
                experience = experience + %s, 
                cashback = cashback + %s 
            WHERE user_id = %s
        """
        await execute_db_query(update_query, (yacht_price, yacht_id, experience_gain, cashback_amount, user_id))
        
        await message.answer(f"Вы успешно купили {yacht_name} за {yacht_price} 💰!\n"
                             f"Вы получили {experience_gain} опыта и {cashback_amount} 💰 кешбэка.")

        # Логирование успешной покупки
        logger.info(f"Пользователь {user_id} купил {yacht_name} за {yacht_price} 💰. "
                    f"Получено {experience_gain} XP и {cashback_amount} 💰 кешбэка.")

    except Exception as e:
        await message.answer("Ошибка при покупке яхты.")
        logger.error(f"Ошибка при обработке покупки яхты: {e}")

    # Всегда возвращаем пользователя в список яхт
    await handle_assets(message)

@router.message(Command("sellyacht"))
async def handle_sellyacht(message: Message):
    try:
        user_id = message.from_user.id
        query = "SELECT yacht, experience FROM users WHERE user_id = %s"
        result = await execute_db_query(query, (user_id,))
        
        if not result:
            await message.answer("Ошибка: пользователь не найден в базе данных.")
            return
        
        user_yacht, user_experience = result[0]
        
        if not user_yacht:
            await message.answer("У вас нет яхты, чтобы продать её.")
            return
        
        yacht = YACHTS.get(user_yacht)
        
        if not yacht:
            await message.answer("Ошибка: яхта не найдена в базе данных.")
            return
        
        yacht_name = yacht["name"]
        yacht_price = yacht["price"]
        sell_price = int(yacht_price * 0.4)
        sell_experience = 75
        
        update_query = """
            UPDATE users 
            SET yacht = NULL, 
                balance = balance + %s, 
                experience = experience + %s 
            WHERE user_id = %s
        """
        await execute_db_query(update_query, (sell_price, sell_experience, user_id))
        
        await message.answer(f"Вы продали {yacht_name} за {sell_price} 💰 и получили {sell_experience} опыта!")
        
        logger.info(f"Пользователь {user_id} продал {yacht_name} за {sell_price} 💰 и получил {sell_experience} XP.")
        await handle_assets(message)
        
    except Exception as e:
        await message.answer("Ошибка при продаже яхты.")
        logger.error(f"Ошибка при обработке продажи яхты: {e}")
