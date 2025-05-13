import logging
import asyncio
import mysql.connector
from aiogram import types
from aiogram.filters import Command
from aiogram import Dispatcher
from aiogram.types import CallbackQuery
from handlers.profile import handle_profile
from datetime import datetime, timedelta
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config.config import API_TOKEN, MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
from utils.database import execute_db_query
from config.level import add_experience, notify_level_up
from utils.income_utils import calculate_income_with_bonus
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


logger = logging.getLogger(__name__)

# Глобальная переменная для хранения клавиатуры
prev_keyboard = None

def is_training_completed(user_id: int, training_id: int) -> bool:
    """Проверяет, завершено ли обучение."""
    connection = mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )
    cursor = connection.cursor()
    cursor.execute(
        "SELECT completion_time FROM user_educations WHERE user_id = %s AND education_id = %s",
        (user_id, training_id)
    )
    result = cursor.fetchone()
    connection.close()

    if not result:
        return False  # Обучение не начато
    completion_time = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S.%f")
    return completion_time <= datetime.now()

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

async def handle_education_list(message: types.Message, user_id=None):
    try:
        user_id = user_id or message.from_user.id

        def sync_get_trainings():
            connection = mysql.connector.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE
            )
            cursor = connection.cursor()

            # Получаем максимальный уровень пройденного обучения
            cursor.execute("SELECT max_training_level FROM users WHERE user_id = %s", (user_id,))
            max_training_level = cursor.fetchone()
            if not max_training_level:
                return None  # Пользователь не найден

            max_training_level = max_training_level[0]

            # Получаем следующее обучение (уровень max_training_level + 1)
            cursor.execute(
                "SELECT id, name, cost, duration_minutes FROM education WHERE required_level = %s",
                (max_training_level + 1,)
            )
            next_training = cursor.fetchone()
            connection.close()
            return next_training

        next_training = await asyncio.to_thread(sync_get_trainings)

        if next_training:
            training_id, name, cost, duration_minutes = next_training
            text = (
                "📚 Следующее доступное обучение:\n\n"
                f"{training_id}. {name}\n\n"  # ID перед названием
                f"💵 Стоимость: {cost}💵\n\n"
                f"⏳ Продолжительность: {duration_minutes} мин."
            )

            # Создаем клавиатуру с кнопками
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📚 Пройти обучение")],
                    [KeyboardButton(text="👤 Профиль")],
                    [KeyboardButton(text="🛠️ Доступные работы")],
                    [KeyboardButton(text="‼ Помощь")]
                ],
                resize_keyboard=True  # Кнопки будут автоматически подстраиваться под размер экрана
            )

            await message.answer(text, reply_markup=keyboard)
        else:
            text = "⚠️ Нет доступных обучений для вашего уровня."
            await message.answer(text)

    except Exception as e:
        logger.error(f"Ошибка при получении списка обучений: {e}")
        await message.answer("⚠️ Произошла ошибка при получении списка обучений.")

async def handle_start_education_input(message: types.Message):
    try:
        training_id = int(message.text)  # Получаем ID обучения из сообщения
        await handle_start_education(message, training_id)  # Передаем message и training_id
    except Exception as e:
        logger.error(f"Ошибка при начале обучения: {e}")
        await message.answer("⚠️ Произошла ошибка при начале обучения.")


async def handle_start_education(message: types.Message, training_id: int):
    try:
        user_id = message.from_user.id

        # Проверяем, существует ли пользователь
        user_data = await execute_db_query(
            "SELECT id FROM users WHERE user_id = %s",
            (user_id,)
        )
        if not user_data:
            await message.answer("⚠️ Пользователь не найден. Зарегистрируйтесь через /start.")
            await handle_education_list(message)
            return

        user_db_id = user_data[0][0]  # id пользователя в таблице users

        # Получаем информацию об обучении
        training = await execute_db_query(
            "SELECT cost, duration_minutes, required_level FROM education WHERE id = %s",
            (training_id,)
        )
        if not training:
            await message.answer("⚠️ Обучение не найдено.")
            await handle_education_list(message)
            return

        cost, duration_minutes, required_level = training[0]

        # Проверяем уровень пользователя
        user_level = await execute_db_query(
            "SELECT level FROM users WHERE user_id = %s",
            (user_id,)
        )
        if not user_level:
            await message.answer("⚠️ Пользователь не найден.")
            await handle_education_list(message)
            return

        user_level = user_level[0][0]
        if user_level < required_level:
            await message.answer(f"⚠️ Для этого обучения требуется уровень {required_level}. Ваш уровень: {user_level}.")
            await handle_education_list(message)
            return

        # Проверяем максимальный уровень пройденного обучения
        max_training_level = await execute_db_query(
            "SELECT max_training_level FROM users WHERE user_id = %s",
            (user_id,)
        )
        if not max_training_level:
            await message.answer("⚠️ Пользователь не найден.")
            await handle_education_list(message)
            return

        max_training_level = max_training_level[0][0]

        # Проверяем, что уровень нового обучения равен max_training_level + 1
        if required_level != max_training_level + 1:
            await message.answer(f"⚠️ Вы можете начать только обучение уровня {max_training_level + 1}.")
            await handle_education_list(message)
            return

        # Проверяем, есть ли активное обучение
        active_training = await execute_db_query(
            "SELECT completion_time FROM user_educations WHERE user_id = %s AND completion_time > %s",
            (user_db_id, datetime.now())
        )

        if active_training:
            try:
                completion_time = active_training[0][0]  # completion_time уже является datetime
                remaining_time = completion_time - datetime.now()
                remaining_minutes = int(remaining_time.total_seconds() // 60)
                await message.answer(f"⚠️ У вас уже есть активное обучение. Дождитесь его завершения. Осталось {remaining_minutes} мин.")
                await handle_education_list(message)
                return
            except Exception as e:
                logger.error(f"Ошибка при обработке времени завершения обучения: {e}")
                await message.answer("⚠️ Произошла ошибка при проверке активного обучения.")
                return

        # Проверяем баланс пользователя
        user_balance = await execute_db_query(
            "SELECT balance FROM users WHERE user_id = %s",
            (user_id,)
        )
        if not user_balance:
            await message.answer("⚠️ Пользователь не найден.")
            await handle_education_list(message)
            return

        user_balance = user_balance[0][0]
        if user_balance < cost:
            await message.answer("⚠️ Недостаточно средств для начала обучения.")
            await handle_education_list(message)
            return

        # Начинаем новое обучение
        completion_time = datetime.now() + timedelta(minutes=duration_minutes)

        # Проверяем, есть ли уже запись для этого пользователя и обучения
        existing_training = await execute_db_query(
            "SELECT * FROM user_educations WHERE user_id = %s AND education_id = %s",
            (user_db_id, training_id)
        )

        if existing_training:
            # Обновляем существующую запись
            await execute_db_query(
                '''
                UPDATE user_educations 
                SET completion_time = %s 
                WHERE user_id = %s AND education_id = %s
                ''',
                (completion_time, user_db_id, training_id)
            )
        else:
            # Вставляем новую запись
            await execute_db_query(
                '''
                INSERT INTO user_educations 
                (user_id, education_id, completion_time) 
                VALUES (%s, %s, %s)
                ''',
                (user_db_id, training_id, completion_time)
            )

        # Обновляем максимальный уровень пройденного обучения
        await execute_db_query(
            "UPDATE users SET max_training_level = %s WHERE user_id = %s",
            (required_level, user_id)
        )

        # Списание средств за обучение
        await execute_db_query(
            "UPDATE users SET balance = balance - %s WHERE user_id = %s",
            (cost, user_id)
        )

        await message.answer(f"🎓 Вы начали обучение уровня {required_level}! Оно завершится через {duration_minutes} минут.")
        await handle_education_list(message)

    except Exception as e:
        logger.error(f"Ошибка при начале обучения: {e}")
        await message.answer("⚠️ Произошла ошибка при начале обучения.")
        await handle_education_list(message)

def format_time(hours: float) -> str:
    """Форматирует время в часы, минуты и секунды."""
    total_seconds = int(hours * 3600)
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h} час{'а' if 1 < h % 10 < 5 and not 11 <= h % 100 <= 14 else '' if h == 1 else 'ов'}, {m} минут, {s} секунд"


async def handle_my_businesses(message: types.Message):
    """Показывает информацию о бизнесе пользователя с точным отображением времени до сбора."""
    try:
        user_id = message.from_user.id

        def sync_get_businesses():
            connection = mysql.connector.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE
            )
            cursor = connection.cursor()

            # Получаем id пользователя из таблицы users
            cursor.execute("SELECT id FROM users WHERE user_id = %s", (user_id,))
            user_db_id_result = cursor.fetchone()
            if not user_db_id_result:
                connection.close()
                return None  # Пользователь не найден

            user_db_id = user_db_id_result[0]  # Получаем id пользователя из таблицы users

            # Получаем текущий бизнес пользователя
            cursor.execute('''
                SELECT b.name, ub.level, b.base_income, ub.last_collected_income, 
                       b.base_cost, b.upgrade_cost_multiplier, b.max_accumulation_time
                FROM user_businesses ub
                JOIN businesses b ON ub.business_id = b.id
                WHERE ub.user_id = %s
            ''', (user_db_id,))
            businesses = cursor.fetchall()
            connection.close()
            return businesses

        businesses = await asyncio.to_thread(sync_get_businesses)

        if not businesses:
            await message.answer("⚠️ У вас пока нет бизнесов.")
            return

        name, level, base_income, last_collected_income, base_cost, upgrade_cost_multiplier, max_accumulation_time = businesses[0]
        income_per_hour = base_income * level  # Доход в час с учетом уровня

        # Рассчитываем накопленную прибыль с учетом ограничения на максимальное время накопления
        if last_collected_income:
            time_since_last_collection = datetime.now() - last_collected_income
            hours_since_last_collection = time_since_last_collection.total_seconds() / 3600

            # Ограничиваем время накопления до max_accumulation_time
            hours_since_last_collection = min(hours_since_last_collection, max_accumulation_time)
            accumulated_income = int(income_per_hour * hours_since_last_collection)
        else:
            accumulated_income = 0
            hours_since_last_collection = 0

        # Рассчитываем время до следующего сбора
        if last_collected_income:
            time_until_max_accumulation = max_accumulation_time - hours_since_last_collection
            if time_until_max_accumulation > 0:
                time_until_max_accumulation_str = format_time(time_until_max_accumulation)
            else:
                time_until_max_accumulation_str = "✅ Можно собирать"
        else:
            time_until_max_accumulation_str = "✅ Можно собирать"

        # Рассчитываем стоимость продажи бизнеса
        total_cost = base_cost
        for lvl in range(1, level):
            total_cost += int(base_cost * (upgrade_cost_multiplier ** (lvl - 1)))
        sell_price = int(total_cost * 0.6)  # 60% от общей стоимости

        # Проверяем, можно ли улучшить бизнес
        can_upgrade = level < 7  # Максимальный уровень бизнеса — 7
        upgrade_info = "✅ Можно улучшить" if can_upgrade else "❌ Максимальный уровень"

        text = (
            "🏢 <b>Ваш бизнес:</b>\n\n"
            f"📋 <b>Название:</b> {name}\n"
            f"💵 <b>Доход в час:</b> {income_per_hour}💵\n"
            f"💰 <b>Накоплено в кассе:</b> {accumulated_income}💵\n"
            f"⏳ <b>Время до переполнения кассы:</b> {time_until_max_accumulation_str}\n"
            f"💸 <b>Стоимость продажи:</b> {sell_price}💵\n"
            f"⬆️ <b>Улучшение:</b> {upgrade_info}"
        )

        # Создаем клавиатуру с кнопками
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="💰 Собрать прибыль")],
                [KeyboardButton(text="⬆️ Улучшить бизнес")],
                [KeyboardButton(text="💸 Продать бизнес")],
                [KeyboardButton(text="👤 Профиль")],
                [KeyboardButton(text="‼ Помощь")]
            ],
            resize_keyboard=True  # Кнопки будут автоматически подстраиваться под размер экрана
        )

        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Ошибка при получении списка бизнесов: {e}")
        await message.answer("⚠️ Произошла ошибка при получении списка бизнесов.")


async def handle_collect_income(message: types.Message):
    """Собирает доход с бизнесов пользователя, учитывая бонус города и лимит накопления дохода."""
    try:
        user_id = message.from_user.id
        logger.info(f"Пользователь {user_id} пытается собрать доход.")

        def sync_collect_income():
            # Подключаемся к базе данных
            connection = mysql.connector.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE
            )
            cursor = connection.cursor()

            # Получаем id пользователя из таблицы users
            cursor.execute("SELECT id FROM users WHERE user_id = %s", (user_id,))
            user_db_id_result = cursor.fetchone()
            if not user_db_id_result:
                connection.close()
                return 0, 0  # Пользователь не найден

            user_db_id = user_db_id_result[0]  # Получаем id пользователя из таблицы users

            # Получаем данные бизнесов, включая max_accumulation_time
            cursor.execute(''' 
                SELECT ub.business_id, b.base_income, ub.level, ub.last_collected_income, b.max_accumulation_time 
                FROM user_businesses ub 
                JOIN businesses b ON ub.business_id = b.id 
                WHERE ub.user_id = %s 
            ''', (user_db_id,))
            businesses = cursor.fetchall()

            if not businesses:
                connection.close()
                return 0, 0  # Возвращаем два значения: total_income и total_experience

            total_income = 0
            total_experience = 0.03  # Базовый опыт за сбор дохода

            for business_id, base_income, level, last_collected, max_accumulation_time in businesses:
                income = base_income * level

                # Проверяем время последнего сбора дохода
                if not last_collected:
                    cursor.execute(
                        "SELECT purchase_time FROM user_businesses WHERE user_id = %s AND business_id = %s",
                        (user_db_id, business_id)
                    )
                    purchase_time_result = cursor.fetchone()
                    if not purchase_time_result:
                        continue  # Пропускаем, если purchase_time отсутствует

                    purchase_time = purchase_time_result[0]
                    if isinstance(purchase_time, str):
                        reference_time = datetime.strptime(purchase_time, "%Y-%m-%d %H:%M:%S.%f")
                    else:
                        reference_time = purchase_time  # Уже datetime
                else:
                    if isinstance(last_collected, str):
                        reference_time = datetime.strptime(last_collected, "%Y-%m-%d %H:%M:%S.%f")
                    else:
                        reference_time = last_collected  # Уже datetime

                # Рассчитываем время накопления
                time_since_last_collection = datetime.now() - reference_time
                hours_since_last_collection = time_since_last_collection.total_seconds() / 3600

                # ⏳ Ограничиваем накопление дохода по max_accumulation_time
                hours_to_collect = min(hours_since_last_collection, max_accumulation_time)
                income *= hours_to_collect

                # Опыт пропорционален накопленному доходу
                experience_gained = int(5 * hours_to_collect * level)
                total_experience += experience_gained
                total_income += income

                # Обновляем время последнего сбора
                cursor.execute(
                    "UPDATE user_businesses SET last_collected_income = %s WHERE user_id = %s AND business_id = %s",
                    (datetime.now(), user_db_id, business_id)
                )

            connection.commit()
            connection.close()
            return total_income, total_experience  # Возвращаем два значения

        # Выполняем сбор дохода синхронно
        total_income, total_experience = await asyncio.to_thread(sync_collect_income)

        # Если доход равен 0, значит, у пользователя нет бизнесов
        if total_income == 0:
            await message.answer("⚠️ У вас пока нет бизнесов.")
            return

        # Применяем бонус города
        bonus_percent = calculate_income_with_bonus(user_id, total_income)
        total_income_with_bonus = total_income + (total_income * bonus_percent / 100)

        # Начисляем доход пользователю
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE users SET balance = balance + %s WHERE user_id = %s",
            (total_income_with_bonus, user_id)
        )
        connection.commit()
        connection.close()

        # Добавляем опыт пользователю
        new_level, remaining_experience, level_increased = await add_experience(user_id, total_experience)

        # Вывод сообщения пользователю
        result_message = f"💰 Вы собрали доход: {int(total_income_with_bonus)}💵 (с учетом бонуса).\n"
        result_message += f"✨ Вы получили {total_experience} опыта.\n"
        if level_increased:
            result_message += f"🎉 Поздравляем! Вы повысили уровень до {new_level}!"

        await message.answer(result_message)

    except Exception as e:
        logger.error(f"Ошибка при сборе дохода с бизнесов: {e}")
        await message.answer("⚠️ Произошла ошибка при сборе дохода.")


async def handle_businesses(message: types.Message):
    global prev_keyboard  # Используем глобальную переменную
    try:
        user_id = message.from_user.id

        def sync_get_businesses():
            connection = mysql.connector.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE
            )
            cursor = connection.cursor()

            # Получаем уровень пользователя и максимальный уровень пройденного обучения
            cursor.execute(
                "SELECT level, max_training_level FROM users WHERE user_id = %s",
                (user_id,)
            )
            user_data = cursor.fetchone()
            if not user_data:
                return None  # Пользователь не найден

            user_level, max_training_level = user_data

            # Получаем список доступных бизнесов
            cursor.execute('''
                SELECT id, name, base_cost, level_required, required_education_id
                FROM businesses
                WHERE level_required <= %s AND (required_education_id IS NULL OR required_education_id <= %s)
            ''', (user_level, max_training_level))
            businesses = cursor.fetchall()
            connection.close()
            return businesses

        businesses = await asyncio.to_thread(sync_get_businesses)

        if businesses:
            text = "🏢 Доступные бизнесы:\n" + "\n".join(
                [f"{idx+1}. {name} — 💵 {base_cost} (Требуется уровень: {level_required})\n"
                 for idx, (id_, name, base_cost, level_required, _) in enumerate(businesses)]
            )

            # Создаем клавиатуру
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="🏢 Купить бизнес")],
                    [KeyboardButton(text="👤 Профиль")]
                ],
                resize_keyboard=True
            )

            # Сохраняем клавиатуру в глобальной переменной
            prev_keyboard = keyboard

            await message.answer(text, reply_markup=keyboard)
        else:
            await message.answer("⚠️ Нет доступных бизнесов для вашего уровня.")

    except Exception as e:
        logger.error(f"Ошибка при получении списка бизнесов: {e}")
        await message.answer("⚠️ Произошла ошибка при получении списка бизнесов.")

        # handlers/earnings.py
import logging
import asyncio
from aiogram import types
from config.config import API_TOKEN, MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
from utils.database import execute_db_query

logger = logging.getLogger(__name__)

async def handle_buy_business(message: types.Message, business_id: int):
    try:
        user_id = message.from_user.id

        # Проверяем, существует ли пользователь в таблице users
        user_exists = await execute_db_query(
            "SELECT id FROM users WHERE user_id = %s",
            (user_id,)
        )
        if not user_exists:
            await message.answer("⚠️ Пользователь не найден. Зарегистрируйтесь через /start.")
            return

        user_db_id = user_exists[0][0]  # Получаем id пользователя из таблицы users

        # Остальная логика покупки бизнеса
        def sync_buy_business():
            connection = mysql.connector.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE
            )
            cursor = connection.cursor()

            # Проверяем, есть ли у пользователя уже бизнес
            cursor.execute(
                "SELECT business_id FROM user_businesses WHERE user_id = %s",
                (user_db_id,)
            )
            existing_business = cursor.fetchone()

            if existing_business:
                connection.close()
                return "⚠️ У вас уже есть бизнес. Сначала продайте его, чтобы купить новый."

            # Получаем информацию о бизнесе
            cursor.execute(
                "SELECT name, base_cost, level_required, required_education_id FROM businesses WHERE id = %s",
                (business_id,)
            )
            business = cursor.fetchone()

            if not business:
                connection.close()
                return "⚠️ Бизнес не найден."

            name, base_cost, level_required, required_education_id = business

            # Проверяем уровень пользователя
            cursor.execute(
                "SELECT level, max_training_level, balance FROM users WHERE id = %s",
                (user_db_id,)
            )
            user_data = cursor.fetchone()

            if not user_data:
                connection.close()
                return "⚠️ Пользователь не найден."

            user_level, max_training_level, user_balance = user_data

            # Проверяем, что уровень пользователя достаточен
            if user_level < level_required:
                connection.close()
                return f"⚠️ Для покупки этого бизнеса требуется уровень {level_required}. Ваш уровень: {user_level}."

            # Проверяем, что пользователь прошел необходимое обучение
            if required_education_id and max_training_level < required_education_id:
                connection.close()
                return f"⚠️ Для покупки этого бизнеса требуется пройти обучение уровня {required_education_id}."

            # Проверяем баланс пользователя
            if user_balance < base_cost:
                connection.close()
                return "⚠️ Недостаточно средств для покупки бизнеса."

            # Покупаем бизнес
            cursor.execute(
                "INSERT INTO user_businesses (user_id, business_id, level, last_collected_income) VALUES (%s, %s, 1, %s)",
                (user_db_id, business_id, datetime.now())
            )

            # Списание средств
            cursor.execute(
                "UPDATE users SET balance = balance - %s WHERE id = %s",
                (base_cost, user_db_id)
            )

            # Начисляем кэшбек (2% от стоимости бизнеса)
            cashback_amount = int(base_cost * 0.02)  # 2% от стоимости бизнеса
            cursor.execute(
                "UPDATE users SET cashback = cashback + %s WHERE id = %s",
                (cashback_amount, user_db_id)
            )

            connection.commit()
            connection.close()
            return f"🎉 Вы успешно купили бизнес «{name}»!"

        result = await asyncio.to_thread(sync_buy_business)
        await message.answer(result)

    except Exception as e:
        logger.error(f"Ошибка при покупке бизнеса: {e}")
        await message.answer("⚠️ Произошла ошибка при покупке бизнеса.")


async def handle_buy_business_input(message: types.Message):
    global prev_keyboard  # Используем глобальную переменную
    try:
        # Проверяем, соответствует ли ввод формату "b_номер"
        if not message.text.startswith("b_"):
            await message.answer("❌ Неверный формат. Используйте: b_номер (например, b_1)")
            return

        # Извлекаем ID бизнеса
        try:
            business_id_str = message.text.split("_")[1]
            business_id = int(business_id_str)
        except (IndexError, ValueError):
            await message.answer("❌ Неверный формат. Пример: b_1", reply_markup=prev_keyboard)
            return

        # Вызываем функцию покупки бизнеса
        result = await handle_buy_business(message, business_id)

        # Возвращаем прежнюю клавиатуру
        if prev_keyboard:
            await message.answer(result, reply_markup=prev_keyboard)
        else:
            await message.answer(result)  # Если клавиатура не сохранена, отправляем без неё

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.answer("⚠️ Произошла ошибка.", reply_markup=prev_keyboard)


async def handle_upgrade_business(message: types.Message):
    """Улучшает бизнес пользователя."""
    try:
        user_id = message.from_user.id

        def sync_upgrade_business():
            connection = mysql.connector.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE
            )
            cursor = connection.cursor()

            # Получаем id пользователя из таблицы users
            cursor.execute("SELECT id FROM users WHERE user_id = %s", (user_id,))
            user_db_id_result = cursor.fetchone()
            if not user_db_id_result:
                connection.close()
                return "⚠️ Пользователь не найден. Зарегистрируйтесь через /start."

            user_db_id = user_db_id_result[0]  # Получаем id пользователя из таблицы users

            # Получаем текущий бизнес пользователя
            cursor.execute('''
                SELECT ub.business_id, ub.level, b.base_income, b.upgrade_cost_multiplier
                FROM user_businesses ub
                JOIN businesses b ON ub.business_id = b.id
                WHERE ub.user_id = %s
            ''', (user_db_id,))
            business = cursor.fetchone()

            if not business:
                connection.close()
                return "⚠️ У вас пока нет бизнесов."

            business_id, current_level, base_income, upgrade_cost_multiplier = business

            # Проверяем, можно ли улучшить бизнес
            if current_level >= 7:  # Максимальный уровень бизнеса — 7
                connection.close()
                return "❌ Ваш бизнес уже достиг максимального уровня."

            # Рассчитываем стоимость улучшения
            upgrade_cost = int(base_income * (upgrade_cost_multiplier ** (current_level - 1)))

            # Проверяем баланс пользователя
            cursor.execute(
                "SELECT balance FROM users WHERE id = %s",
                (user_db_id,)
            )
            user_balance = cursor.fetchone()[0]

            if user_balance < upgrade_cost:
                connection.close()
                return f"⚠️ Недостаточно средств для улучшения. Требуется: {upgrade_cost}💵."

            # Улучшаем бизнес
            new_level = current_level + 1
            cursor.execute(
                "UPDATE user_businesses SET level = %s WHERE user_id = %s AND business_id = %s",
                (new_level, user_db_id, business_id)
            )

            # Списание средств
            cursor.execute(
                "UPDATE users SET balance = balance - %s WHERE id = %s",
                (upgrade_cost, user_db_id)
            )

            connection.commit()
            connection.close()
            return f"🎉 Вы улучшили бизнес до уровня {new_level}! Новый доход: {base_income * new_level}💵/ч."

        result = await asyncio.to_thread(sync_upgrade_business)
        await message.answer(result)

    except Exception as e:
        logger.error(f"Ошибка при улучшении бизнеса: {e}")
        await message.answer("⚠️ Произошла ошибка при улучшении бизнеса.")

async def handle_sell_business(message: types.Message):
    """Продает бизнес пользователя."""
    try:
        user_id = message.from_user.id
        logger.info(f"Пользователь {user_id} пытается продать бизнес.")

        def sync_sell_business():
            connection = mysql.connector.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE
            )
            cursor = connection.cursor()

            # Получаем id пользователя из таблицы users
            cursor.execute("SELECT id FROM users WHERE user_id = %s", (user_id,))
            user_db_id_result = cursor.fetchone()
            if not user_db_id_result:
                connection.close()
                return "⚠️ Пользователь не найден. Зарегистрируйтесь через /start."

            user_db_id = user_db_id_result[0]  # Получаем id пользователя из таблицы users

            # Получаем текущий бизнес пользователя
            cursor.execute('''
                SELECT ub.business_id, ub.level, b.base_cost, b.upgrade_cost_multiplier
                FROM user_businesses ub
                JOIN businesses b ON ub.business_id = b.id
                WHERE ub.user_id = %s
            ''', (user_db_id,))
            business = cursor.fetchone()

            if not business:
                connection.close()
                return "⚠️ У вас пока нет бизнесов."

            business_id, current_level, base_cost, upgrade_cost_multiplier = business
            logger.info(f"Результат запроса бизнеса: {business}")

            # Рассчитываем общую стоимость бизнеса (покупка + улучшения)
            total_cost = base_cost
            for level in range(1, current_level):
                total_cost += int(base_cost * (upgrade_cost_multiplier ** (level - 1)))

            # Рассчитываем цену продажи (60% от общей стоимости)
            sell_price = int(total_cost * 0.6)

            # Удаляем бизнес пользователя
            cursor.execute(
                "DELETE FROM user_businesses WHERE user_id = %s AND business_id = %s",
                (user_db_id, business_id)
            )

            # Начисляем средства за продажу
            cursor.execute(
                "UPDATE users SET balance = balance + %s WHERE id = %s",
                (sell_price, user_db_id)
            )

            connection.commit()
            connection.close()
            return f"💰 Вы продали бизнес за {sell_price}💵."

        result = await asyncio.to_thread(sync_sell_business)
        await message.answer(result)

    except Exception as e:
        logger.error(f"Ошибка при продаже бизнеса: {e}")
        await message.answer("⚠️ Произошла ошибка при продаже бизнеса.")