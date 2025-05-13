from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from utils.database import execute_db_query
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config.clothes import CLOTHES
import logging

logger = logging.getLogger("handlers.clothes")
router = Router()

@router.message(Command("clothes"))
async def handle_clothes(message: Message):
    try:
        user_id = message.from_user.id
        query = "SELECT level, yacht, island FROM users WHERE user_id = %s"
        result = await execute_db_query(query, (user_id,))
        
        if not result:
            await message.answer("Ошибка: пользователь не найден в базе данных.")
            return
        
        user_level, user_yacht, user_island = result[0]
        
        # Если значения NULL, заменяем их на 0
        user_yacht = user_yacht if user_yacht is not None else 0
        user_island = user_island if user_island is not None else 0
        
        # Собираем все доступные одежды (is_premium=False)
        all_available_clothes = [
            (clothes_id, clothes)
            for clothes_id, clothes in CLOTHES.items()
            if clothes['is_premium'] is False and
               user_level >= clothes['level_required'] and
               user_yacht >= clothes['yacht_level_required'] and
               user_island >= clothes['island_level_required']
        ]
        
        # Берем только последние 4 доступные одежды
        available_clothes = all_available_clothes[-4:] if all_available_clothes else []
        
        # Формируем список для вывода
        clothes_list = []
        for clothes_id, clothes in available_clothes:
            # Формируем строку с бонусами
            bonuses = []
            if "experience" in clothes["bonus"]:
                bonuses.append(f"Опыт +{int(clothes['bonus']['experience'] * 100)}%")
            if "income" in clothes["bonus"]:
                bonuses.append(f"Доход +{int(clothes['bonus']['income'] * 100)}%")
            
            # Если есть бонусы, добавляем их к описанию
            bonus_text = f" ({', '.join(bonuses)})" if bonuses else ""
            
            # Формируем строку с одеждой
            clothes_str = f"{clothes_id}. <b>{clothes['name']}</b> - {clothes['price']} 💰{bonus_text}\n\n"
            clothes_list.append(clothes_str)
        
        if clothes_list:
            clothes_list_text = "\n".join(clothes_list)
            await message.answer(f"Доступная одежда:\n\n{clothes_list_text}")
        else:
            await message.answer("Нет доступной одежды для вашего уровня, яхты или острова.")
        
        # Поиск первой недоступной одежды (is_premium=False)
        next_clothes = None
        for clothes_id, clothes in CLOTHES.items():
            if clothes['is_premium'] is False and (
                user_level < clothes['level_required'] or
                user_yacht < clothes['yacht_level_required'] or
                user_island < clothes['island_level_required']
            ):
                next_clothes = clothes
                break
        
        # Добавляем сообщение о следующей одежде
        if next_clothes:
            # Формируем строку с бонусами для следующей одежды
            bonuses = []
            if "experience" in next_clothes["bonus"]:
                bonuses.append(f"Опыт +{int(next_clothes['bonus']['experience'] * 100)}%")
            if "income" in next_clothes["bonus"]:
                bonuses.append(f"Доход +{int(next_clothes['bonus']['income'] * 100)}%")
            
            bonus_text = f" ({', '.join(bonuses)})" if bonuses else ""
            
            next_clothes_message = (
                f"\n\n👕 <b>Следующая одежда:</b> {next_clothes['name']}{bonus_text}\n"
                f"🔓 <b>Требуется:</b>\n"
                f"📊 Уровень: {next_clothes['level_required']} (Ваш: {user_level})\n"
                f"🛥 Яхта: {next_clothes['yacht_level_required']} (Ваш: {user_yacht})\n"
                f"🏝 Остров: {next_clothes['island_level_required']} (Ваш: {user_island})\n"
                f"💵 <b>Цена:</b> {next_clothes['price']} 💰\n\n"
                f"Повышайте уровень, яхту или остров, чтобы открыть новую одежду! 👗✨"
            )
            await message.answer(next_clothes_message, parse_mode="HTML")

            keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="👕 Купить одежду")],
                [KeyboardButton(text="👕 Продать одежду")],
                [KeyboardButton(text="🏠 Имущество")],
                [KeyboardButton(text="👤 Профиль")]
            ],
            resize_keyboard=True  # Кнопки автоматически подстраиваются под размер экрана
            )

        # Отправляем сообщение с клавиатурой
        await message.answer("Выберите действие:", reply_markup=keyboard)

    except Exception as e:
        await message.answer("Ошибка при получении списка одежды.")
        logger.error(f"Ошибка при обработке запроса на доступную одежду: {e}")


@router.message(Command("buyclothes"))
async def handle_buy_clothes(message: Message, clothes_id: int):
    try:
        user_id = message.from_user.id

        # Проверяем, существует ли одежда с таким ID
        if clothes_id not in CLOTHES:
            await message.answer("Одежда с таким номером не найдена.")
            return

        clothes = CLOTHES[clothes_id]
        clothes_name = clothes["name"]
        clothes_price = clothes["price"]
        is_premium = clothes["is_premium"]
        level_required = clothes["level_required"]
        yacht_level_required = clothes["yacht_level_required"]
        island_level_required = clothes["island_level_required"]

        # Получаем данные пользователя
        query = """
            SELECT level, yacht, island, balance, aurix, clothes 
            FROM users 
            WHERE user_id = %s
        """
        result = await execute_db_query(query, (user_id,))
        
        if not result:
            await message.answer("Ошибка: пользователь не найден в базе данных.")
            await handle_clothes(message)
            return
        
        user_level, user_yacht, user_island, user_balance, user_aurix, user_clothes = result[0]

        # Если значения NULL, заменяем их на 0
        user_yacht = user_yacht if user_yacht is not None else 0
        user_island = user_island if user_island is not None else 0

        # Проверяем, есть ли у пользователя уже одежда
        if user_clothes is not None:
            await message.answer("У вас уже есть одежда. Продайте её, чтобы купить новую.")
            await handle_clothes(message)
            return

        # Проверяем уровень, яхту и остров
        if user_level < level_required:
            await message.answer(f"Эта одежда доступна с {level_required} уровня.")
            await handle_clothes(message)
            return
        if user_yacht < yacht_level_required:
            await message.answer(f"Для этой одежды требуется яхта уровня {yacht_level_required}.")
            await handle_clothes(message)
            return
        if user_island < island_level_required:
            await message.answer(f"Для этой одежды требуется остров уровня {island_level_required}.")
            await handle_clothes(message)
            return

        # Проверяем баланс или Aurix в зависимости от типа одежды
        if is_premium:
            if user_aurix < clothes_price:
                await message.answer("У вас недостаточно Aurix для покупки этой одежды.")
                await handle_clothes(message)
                return
        else:
            if user_balance < clothes_price:
                await message.answer("У вас недостаточно средств для покупки этой одежды.")
                await handle_clothes(message)
                return

        # Вычисляем cashback (2% от стоимости одежды)
        cashback = int(clothes_price * 0.02)

        # Опыт за покупку (вы можете изменить это значение)
        experience_reward = 50  # Пример: 50 опыта за покупку

        # Обновляем данные пользователя
        if is_premium:
            update_query = """
                UPDATE users 
                SET clothes = %s, aurix = aurix - %s, cashback = cashback + %s, experience = experience + %s 
                WHERE user_id = %s
            """
        else:
            update_query = """
                UPDATE users 
                SET clothes = %s, balance = balance - %s, cashback = cashback + %s, experience = experience + %s 
                WHERE user_id = %s
            """
        
        await execute_db_query(update_query, (clothes_id, clothes_price, cashback, experience_reward, user_id))

        # Сообщение об успешной покупке
        await message.answer(f"Вы успешно купили {clothes_name} за {clothes_price} {'Aurix' if is_premium else '💰'}!")
        logger.info(f"Пользователь {user_id} купил {clothes_name} за {clothes_price} {'Aurix' if is_premium else '💰'}.")

        # Возвращаем пользователя в раздел доступной одежды
        await handle_clothes(message)

    except Exception as e:
        await message.answer("Ошибка при покупке одежды.")
        logger.error(f"Ошибка при обработке покупки одежды: {e}")

        # Возвращаем пользователя в раздел доступной одежды даже при ошибке
        await handle_clothes(message)

@router.message(Command("sellclothes"))
async def handle_sell_clothes(message: Message):
    try:
        user_id = message.from_user.id

        # Получаем данные пользователя
        query = "SELECT clothes FROM users WHERE user_id = %s"
        result = await execute_db_query(query, (user_id,))
        
        if not result:
            await message.answer("Ошибка: пользователь не найден в базе данных.")
            return
        
        user_clothes = result[0][0]

        # Проверяем, есть ли у пользователя одежда
        if user_clothes is None:
            await message.answer("У вас нет одежды для продажи.")
            return

        # Получаем информацию об одежде
        clothes = CLOTHES.get(user_clothes)
        if not clothes:
            await message.answer("Ошибка: информация об одежде не найдена.")
            return

        clothes_name = clothes["name"]
        clothes_price = clothes["price"]

        # Вычисляем стоимость продажи (30% от стоимости одежды)
        sell_price = int(clothes_price * 0.3)

        # Опыт за продажу (вы можете изменить это значение)
        experience_reward = 20  # Пример: 20 опыта за продажу

        # Обновляем данные пользователя
        update_query = """
            UPDATE users 
            SET clothes = NULL, balance = balance + %s, experience = experience + %s 
            WHERE user_id = %s
        """
        await execute_db_query(update_query, (sell_price, experience_reward, user_id))

        # Сообщение об успешной продаже
        await message.answer(f"Вы продали {clothes_name} за {sell_price} 💰.")
        logger.info(f"Пользователь {user_id} продал {clothes_name} за {sell_price} 💰.")

        # Возвращаем пользователя в раздел доступной одежды
        await handle_clothes(message)

    except Exception as e:
        await message.answer("Ошибка при продаже одежды.")
        logger.error(f"Ошибка при обработке продажи одежды: {e}")

        # Возвращаем пользователя в раздел доступной одежды
        await handle_clothes(message)

