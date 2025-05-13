from aiogram import types, Router
import logging
from config.config import EXPERIENCE_PER_1000_SOLIX
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from config.mining import MINING_FARMS  # Импортируем данные о майнинг-фермах
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from utils.database import execute_db_query
from utils.income_utils import calculate_income_with_bonus
from config.level import add_experience
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Создаем роутер для обработчиков майнинг-ферм
router = Router()

@router.message(Command("mining_farms"))
async def handle_view_mining_farms(message: types.Message, state: FSMContext):
    """
    Обработчик для просмотра доступных майнинг-ферм.
    Показывает фермы, которые соответствуют требованиям по уровню, городу, дому и самолету.
    В конце показывает одну недоступную ферму с требованиями.
    Премиальные фермы не выводятся.
    """
    try:
        user_id = message.from_user.id

        # Получаем уровень, город, дом и самолет пользователя из базы данных
        user_data_query = """
            SELECT level, city, house, airplane
            FROM users
            WHERE user_id = %s
        """
        user_data_result = await execute_db_query(user_data_query, (user_id,))
        
        if not user_data_result:
            await message.answer("❌ Ваш профиль не найден в базе данных.")
            return

        user_level, user_city, user_house, user_airplane = user_data_result[0]

        # Находим доступные фермы
        available_farms = []
        unavailable_farms = []
        for farm_id, farm in sorted(MINING_FARMS.items()):
            # Пропускаем премиальные фермы
            if farm.get("is_premium", False):
                continue

            # Проверяем, соответствует ли ферма требованиям
            if (
                farm["level_required"] <= user_level and
                farm["city_required"] <= user_city and
                farm["house_required"] <= user_house and
                farm["airplane_required"] <= user_airplane
            ):
                available_farms.append((farm_id, farm))
            else:
                # Сохраняем недоступные фермы
                unavailable_farms.append((farm_id, farm))

        # Берем последние три доступные фермы
        if len(available_farms) > 3:
            available_farms = available_farms[-3:]

        # Формируем сообщение с доступными фермами
        response = "📋 Доступные майнинг-фермы:\n\n"
        for farm_id, farm in available_farms:
            response += (
                f"🆔 ID: {farm_id}\n"
                f"🏷 Название: {farm['name']}\n"
                f"💵 Стоимость: {farm['base_cost']} 💰\n"
                f"📈 Доход: {farm['base_income']} 💰/час\n"
                f"⏳ Время работы: {farm['max_working_hours']} часов\n"
                f"───────────────\n"
            )

        # Если доступных ферм нет
        if not available_farms:
            response = "❌ У вас нет доступных майнинг-ферм.\n\n"

        # Добавляем одну недоступную ферму
        if unavailable_farms:
            # Берем первую недоступную ферму
            farm_id, farm = unavailable_farms[0]
            response += (
                "🔒 Недоступная ферма:\n"
                f"🆔 ID: {farm_id}\n"
                f"🏷 Название: {farm['name']}\n"
                f"💵 Стоимость: {farm['base_cost']} 💰\n"
                f"📈 Доход: {farm['base_income']} 💰/час\n"
                f"⏳ Время работы: {farm['max_working_hours']} часов\n"
                f"📊 Требуется уровень: {farm['level_required']} (ваш: {user_level})\n"
                f"🏙 Требуется город: {farm['city_required']} (ваш: {user_city})\n"
                f"🏠 Требуется дом: {farm['house_required']} (ваш: {user_house})\n"
                f"✈️ Требуется самолет: {farm['airplane_required']} (ваш: {user_airplane})\n"
                f"───────────────\n"
            )

        # Создаем клавиатуру с кнопками
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🛒 Купить ферму")],
                [KeyboardButton(text="💰 Продать ферму")],
                [KeyboardButton(text="👤 Профиль")],
            ],
            resize_keyboard=True  # Кнопки будут автоматически подстраиваться под размер экрана
        )

        # Отправляем сообщение с клавиатурой
        await message.answer(response, reply_markup=keyboard)

    except Exception as e:
        # Логируем ошибку и уведомляем пользователя
        logger.error(f"❌ Ошибка при просмотре майнинг-ферм: {e}")
        await message.answer("⚠️ Произошла ошибка при загрузке списка майнинг-ферм.")


async def handle_buy_mining_farm(message: types.Message, farm_id: int):
    """
    Обработчик для покупки майнинг-фермы.
    У игрока может быть только одна ферма. Если ферма уже есть, покупка новой запрещена.
    """
    try:
        user_id = message.from_user.id

        # Получаем данные о ферме
        farm = MINING_FARMS.get(farm_id)
        if not farm:
            await message.answer("❌ Майнинг-ферма с таким ID не найдена.")
            return

        # Получаем данные пользователя
        user_query = """
            SELECT id, level, city, house, airplane, balance, mining FROM users WHERE user_id = %s
        """
        user_result = await execute_db_query(user_query, (user_id,))

        if not user_result:
            await message.answer("❌ Ваш профиль не найден. Зарегистрируйтесь через /start.")
            return

        user_db_id, user_level, user_city, user_house, user_airplane, user_balance, user_mining = user_result[0]

        # Проверяем, есть ли у игрока уже ферма
        if user_mining is not None:
            await message.answer("❌ У вас уже есть майнинг-ферма. Вы не можете купить новую, пока не продадите текущую.")
            return

        # Проверяем требования к уровню, городу, дому и самолету
        if user_level < farm["level_required"]:
            await message.answer(f"❌ Для покупки этой фермы требуется уровень {farm['level_required']}.")
            return
        if user_city < farm["city_required"]:
            await message.answer(f"❌ Для покупки этой фермы требуется город уровня {farm['city_required']}.")
            return
        if user_house < farm["house_required"]:
            await message.answer(f"❌ Для покупки этой фермы требуется дом уровня {farm['house_required']}.")
            return
        if user_airplane < farm["airplane_required"]:
            await message.answer(f"❌ Для покупки этой фермы требуется самолет уровня {farm['airplane_required']}.")
            return

        # Проверяем баланс пользователя
        if user_balance < farm["base_cost"]:
            await message.answer("❌ Недостаточно средств для покупки этой фермы.")
            return

        # Добавляем запись в таблицу user_mining_farms
        insert_mining_farm_query = """
            INSERT INTO user_mining_farms (user_id, mining_id, start_date, last_income_collection)
            VALUES (%s, %s, %s, %s)
        """
        await execute_db_query(insert_mining_farm_query, (user_db_id, farm_id, datetime.now(), datetime.now()))

        # Обновляем поле mining в таблице users
        update_mining_query = """
            UPDATE users SET mining = %s WHERE user_id = %s
        """
        await execute_db_query(update_mining_query, (farm_id, user_id))

        # Вычитаем стоимость фермы из баланса пользователя
        update_balance_query = """
            UPDATE users SET balance = balance - %s WHERE user_id = %s
        """
        await execute_db_query(update_balance_query, (farm["base_cost"], user_id))

        # Добавляем кэшбек (2% от стоимости фермы)
        cashback = int(farm["base_cost"] * 0.02)
        update_cashback_query = """
            UPDATE users SET cashback = cashback + %s WHERE user_id = %s
        """
        await execute_db_query(update_cashback_query, (cashback, user_id))

        # Добавляем опыт игроку (можно изменить количество опыта)
        experience_to_add = farm["base_cost"] // 1000  # Пример: 1 опыт за каждые 1000$ стоимости фермы
        await add_experience(user_id, experience_to_add)

        # Уведомляем пользователя об успешной покупке
        await message.answer(
            f"✅ Вы успешно купили майнинг-ферму: {farm['name']}!\n"
            f"💵 Стоимость: {farm['base_cost']} 💰\n"
            f"💳 Кэшбек: +{cashback} 💰\n"
            f"🎯 Опыт: +{experience_to_add}"
        )

    except Exception as e:
        logger.error(f"Ошибка при покупке майнинг-фермы: {e}")
        await message.answer("⚠️ Произошла ошибка при покупке майнинг-фермы.")

# Регистрация обработчика для команды /buy_mining_farm
@router.message(Command("buy_mining_farm"))
async def handle_buy_mining_farm_command(message: types.Message):
    """
    Обработчик для команды /buy_mining_farm.
    Ожидает ввод в формате mining_<ID>.
    """
    try:
        # Извлекаем текст после команды
        command_parts = message.text.split(" ", 1)
        if len(command_parts) < 2:
            await message.answer("❌ Используйте формат: /buy_mining_farm mining_<ID> (например, /buy_mining_farm mining_2)")
            return

        # Получаем часть с ID фермы
        farm_input = command_parts[1].strip()

        # Проверяем, начинается ли ввод с "mining_"
        if not farm_input.startswith("mining_"):
            await message.answer("❌ Неверный формат. Используйте: /buy_mining_farm mining_<ID> (например, /buy_mining_farm mining_2)")
            return

        # Извлекаем ID фермы
        farm_id_str = farm_input.split("_")[1]
        if not farm_id_str.isdigit():
            await message.answer("❌ ID фермы должен быть числом. Используйте формат: /buy_mining_farm mining_<ID> (например, /buy_mining_farm mining_2)")
            return

        farm_id = int(farm_id_str)

        # Вызываем обработчик покупки фермы
        await handle_buy_mining_farm(message, farm_id)

    except Exception as e:
        logger.error(f"Ошибка при обработке команды /buy_mining_farm: {e}")
        await message.answer("⚠️ Произошла ошибка при обработке команды.")


async def handle_sell_mining_farm(message: types.Message):
    """
    Обработчик для продажи майнинг-фермы.
    Игрок получает 40% от стоимости фермы, а также опыт за продажу.
    """
    try:
        user_id = message.from_user.id

        # Получаем данные пользователя и его ферму
        user_query = """
            SELECT id, mining FROM users WHERE user_id = %s
        """
        user_result = await execute_db_query(user_query, (user_id,))

        if not user_result:
            await message.answer("❌ Ваш профиль не найден. Зарегистрируйтесь через /start.")
            return

        user_db_id, user_mining = user_result[0]

        # Проверяем, есть ли у игрока ферма
        if user_mining is None:
            await message.answer("❌ У вас нет майнинг-фермы для продажи.")
            return

        # Получаем данные о ферме
        farm = MINING_FARMS.get(user_mining)
        if not farm:
            await message.answer("❌ Данные о вашей ферме не найдены.")
            return

        # Вычисляем 40% от стоимости фермы
        sell_price = int(farm["base_cost"] * 0.4)

        # Начисляем игроку 40% от стоимости фермы
        update_balance_query = """
            UPDATE users SET balance = balance + %s WHERE user_id = %s
        """
        await execute_db_query(update_balance_query, (sell_price, user_id))

        # Удаляем запись о ферме из таблицы user_mining_farms
        delete_mining_farm_query = """
            DELETE FROM user_mining_farms WHERE user_id = %s AND mining_id = %s
        """
        await execute_db_query(delete_mining_farm_query, (user_db_id, user_mining))

        # Обнуляем поле mining в таблице users
        update_mining_query = """
            UPDATE users SET mining = NULL WHERE user_id = %s
        """
        await execute_db_query(update_mining_query, (user_id,))

        # Начисляем опыт за продажу фермы (можно изменить количество опыта)
        experience_to_add = farm["base_cost"] // 2000  # Пример: 1 опыт за каждые 2000$ стоимости фермы
        await add_experience(user_id, experience_to_add)

        # Уведомляем пользователя об успешной продаже
        await message.answer(
            f"✅ Вы успешно продали майнинг-ферму: {farm['name']}!\n"
            f"💵 Получено: {sell_price} 💰 (40% от стоимости)\n"
            f"🎯 Опыт: +{experience_to_add}"
        )

    except Exception as e:
        logger.error(f"Ошибка при продаже майнинг-фермы: {e}")
        await message.answer("⚠️ Произошла ошибка при продаже майнинг-фермы.")


from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

@router.message(Command("my_mining_farm"))
async def handle_my_mining_farm(message: types.Message):
    """
    Обработчик для просмотра информации о текущей ферме игрока.
    Показывает подробную информацию о ферме, включая накопленный доход и кнопки для управления.
    """
    try:
        user_id = message.from_user.id

        # Получаем данные пользователя и его ферму
        user_query = """
            SELECT id, mining FROM users WHERE user_id = %s
        """
        user_result = await execute_db_query(user_query, (user_id,))

        if not user_result:
            await message.answer("❌ Ваш профиль не найден. Зарегистрируйтесь через /start.")
            return

        user_db_id, user_mining = user_result[0]

        # Проверяем, есть ли у игрока ферма
        if user_mining is None:
            await message.answer("❌ У вас нет майнинг-фермы.")
            return

        # Получаем данные о ферме
        farm = MINING_FARMS.get(user_mining)
        if not farm:
            await message.answer("❌ Данные о вашей ферме не найдены.")
            return

        # Получаем время последнего сбора дохода
        mining_farm_query = """
            SELECT last_income_collection 
            FROM user_mining_farms 
            WHERE user_id = %s AND mining_id = %s
        """
        mining_farm_result = await execute_db_query(mining_farm_query, (user_db_id, user_mining))

        if not mining_farm_result or not mining_farm_result[0][0]:
            await message.answer("❌ Ошибка при получении данных о ферме.")
            return

        last_income_collection = mining_farm_result[0][0]
        current_time = datetime.now()

        # Рассчитываем время с момента последнего сбора дохода
        time_since_last_collection = current_time - last_income_collection

        # Ограничиваем время накопления максимальным временем работы фермы
        max_working_hours = farm["max_working_hours"]
        max_accumulation_time = timedelta(hours=max_working_hours)
        if time_since_last_collection > max_accumulation_time:
            time_since_last_collection = max_accumulation_time

        # Рассчитываем накопленный доход
        hours_since_last_collection = time_since_last_collection.total_seconds() / 3600
        accumulated_income = int(hours_since_last_collection * farm["base_income"])

        # Вычисляем стоимость продажи (40% от базовой стоимости)
        sell_price = int(farm["base_cost"] * 0.4)

        # Формируем сообщение с информацией о ферме
        response = (
            f"🏭 Ваша майнинг-ферма:\n\n"
            f"🆔 ID: {user_mining}\n"
            f"🏷 Название: {farm['name']}\n"
            f"💵 Стоимость: {farm['base_cost']} 💰\n"
            f"📈 Доход: {farm['base_income']} solix/час\n"
            f"⏳ Время работы: {farm['max_working_hours']} часов\n"
            f"📊 Требуется уровень: {farm['level_required']}\n"
            f"🏙 Требуется город: {farm['city_required']}\n"
            f"🏠 Требуется дом: {farm['house_required']}\n"
            f"✈️ Требуется самолет: {farm['airplane_required']}\n"
            f"───────────────\n"
            f"💰 Накопленный доход: {accumulated_income} solix\n"
            f"💰 Стоимость продажи: {sell_price} 💰 (40% от стоимости)\n"
        )

        # Создаем клавиатуру с кнопками
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="💰 Собрать доход")],
                [KeyboardButton(text="💰 Продать ферму"), KeyboardButton(text="📋 Доступные фермы")],
                [KeyboardButton(text="🏦 Банк"), KeyboardButton(text="👤 Профиль")],
            ],
            resize_keyboard=True  # Кнопки будут автоматически подстраиваться под размер экрана
        )

        # Отправляем сообщение с информацией о ферме и кнопками
        await message.answer(response, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Ошибка при просмотре майнинг-фермы: {e}")
        await message.answer("⚠️ Произошла ошибка при загрузке информации о ферме.")

async def handle_collect_mining_income(message: types.Message):
    """
    Обработчик для сбора дохода с майнинг-фермы.
    Доход добавляется в solix, а не в balance.
    """
    try:
        user_id = message.from_user.id

        # Получаем данные пользователя и его ферму
        user_query = """
            SELECT id, mining FROM users WHERE user_id = %s
        """
        user_result = await execute_db_query(user_query, (user_id,))

        if not user_result:
            await message.answer("❌ Ваш профиль не найден. Зарегистрируйтесь через /start.")
            return

        user_db_id, user_mining = user_result[0]

        # Проверяем, есть ли у игрока ферма
        if user_mining is None:
            await message.answer("❌ У вас нет майнинг-фермы для сбора дохода.")
            return

        # Получаем данные о ферме
        farm = MINING_FARMS.get(user_mining)
        if not farm:
            await message.answer("❌ Данные о вашей ферме не найдены.")
            return

        # Получаем время последнего сбора дохода
        mining_farm_query = """
            SELECT last_income_collection 
            FROM user_mining_farms 
            WHERE user_id = %s AND mining_id = %s
        """
        mining_farm_result = await execute_db_query(mining_farm_query, (user_db_id, user_mining))

        if not mining_farm_result or not mining_farm_result[0][0]:
            await message.answer("❌ Ошибка при получении данных о ферме.")
            return

        last_income_collection = mining_farm_result[0][0]
        current_time = datetime.now()

        # Рассчитываем время с момента последнего сбора дохода
        time_since_last_collection = current_time - last_income_collection

        # Ограничиваем время накопления максимальным временем работы фермы
        max_working_hours = farm["max_working_hours"]
        max_accumulation_time = timedelta(hours=max_working_hours)
        if time_since_last_collection > max_accumulation_time:
            time_since_last_collection = max_accumulation_time

        # Рассчитываем накопленный доход
        hours_since_last_collection = time_since_last_collection.total_seconds() / 3600
        base_income = int(hours_since_last_collection * farm["base_income"])

        # Рассчитываем бонусы (город, девушка, одежда)
        bonus_percent = calculate_income_with_bonus(user_id, base_income)
        total_income_with_bonus = base_income + (base_income * bonus_percent / 100)

        # Начисляем доход в solix
        update_solix_query = """
            UPDATE users SET solix = solix + %s WHERE id = %s
        """
        await execute_db_query(update_solix_query, (total_income_with_bonus, user_db_id))

        # Начисляем опыт (10 опыта за каждые 1000 solix)
        experience_per_1000_solix = 10  # Можно изменить это значение
        experience_earned = int(total_income_with_bonus // 1000) * experience_per_1000_solix

        if experience_earned > 0:
            new_level, remaining_experience, level_increased = await add_experience(user_id, experience_earned)

            # Если уровень повышен, отправляем уведомление
            if level_increased:
                await message.answer(f"🎉 Поздравляем! Вы достигли уровня {new_level}!")

        # Обновляем время последнего сбора дохода
        update_last_income_collection_query = """
            UPDATE user_mining_farms 
            SET last_income_collection = %s 
            WHERE user_id = %s AND mining_id = %s
        """
        await execute_db_query(update_last_income_collection_query, (current_time, user_db_id, user_mining))

        await message.answer(
            f"💰 Вы собрали доход с майнинг-фермы: {total_income_with_bonus} solix.\n"
            f"✨ Вы получили {experience_earned} опыта."
        )

    except Exception as e:
        logger.error(f"Ошибка при сборе дохода с майнинг-фермы: {e}")
        await message.answer("⚠️ Произошла ошибка при сборе дохода с майнинг-фермы.")