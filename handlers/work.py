import asyncio
import logging
import html
from utils.database import execute_db_query  # Используем execute_db_query
from aiogram import types, Bot, Dispatcher
from config.config import API_TOKEN
from datetime import datetime, timedelta
from config.city import CITIES
from utils.income_utils import calculate_income_with_bonus
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config.level import add_experience

logger = logging.getLogger(__name__)

async def get_user_level(user_id: int) -> int:
    """Получает уровень пользователя из базы данных."""
    try:
        query = "SELECT level FROM users WHERE user_id = %s"
        result = await execute_db_query(query, (user_id,))
        return result[0][0] if result else 1  # Возвращаем уровень пользователя (по умолчанию 1)
    except Exception as e:
        logger.error(f"Ошибка при получении уровня пользователя: {e}")
        return 1

async def get_user_education(user_id: int) -> int:
    """Получает ID последнего завершенного обучения пользователя."""
    try:
        query = """
            SELECT education_id 
            FROM user_educations 
            WHERE user_id = %s 
            ORDER BY completion_time DESC 
            LIMIT 1
        """
        result = await execute_db_query(query, (user_id,))
        return result[0][0] if result else None  # Возвращаем ID обучения или None
    except Exception as e:
        logger.error(f"Ошибка при получении образования пользователя: {e}")
        return None

async def get_user_db_id(user_id: int) -> int:
    """Получает id пользователя из таблицы users по его Telegram ID."""
    try:
        query = """
            SELECT id 
            FROM users 
            WHERE user_id = %s
        """
        result = await execute_db_query(query, (user_id,))
        return result[0][0] if result else 0
    except Exception as e:
        logger.error(f"Ошибка при получении id пользователя: {e}")
        return 0


async def calculate_accumulated_income(user_id: int, hourly_income: int) -> int:
    """Рассчитывает накопленную прибыль с учетом ограничения на максимальное время накопления."""
    try:
        # Получаем id пользователя из таблицы users
        user_db_id = await get_user_db_id(user_id)
        if not user_db_id:
            return 0

        # Получаем время последнего сбора дохода
        query = """
            SELECT last_income_collection 
            FROM user_jobs 
            WHERE user_id = %s
        """
        result = await execute_db_query(query, (user_db_id,))
        if not result or not result[0][0]:
            return 0

        last_collection_time = result[0][0]
        current_time = datetime.now()

        # Вычисляем разницу в часах
        time_difference = current_time - last_collection_time
        hours_passed = time_difference.total_seconds() / 3600

        # Ограничиваем время накопления 5 часами (как в функции сбора дохода)
        max_accumulation_time = 5  # Максимальное время накопления в часах
        hours_passed = min(hours_passed, max_accumulation_time)

        # Рассчитываем накопленную прибыль
        accumulated_income = int(hours_passed * hourly_income)
        return accumulated_income
    except Exception as e:
        logger.error(f"Ошибка при расчете накопленной прибыли: {e}")
        return 0



async def get_current_job_id(user_id: int) -> int:
    """Получает id текущей работы пользователя."""
    try:
        # Получаем id пользователя из таблицы users
        user_db_id = await get_user_db_id(user_id)
        if not user_db_id:
            return 0

        query = """
            SELECT job_id 
            FROM user_jobs 
            WHERE user_id = %s
        """
        result = await execute_db_query(query, (user_db_id,))
        return result[0][0] if result else 0
    except Exception as e:
        logger.error(f"Ошибка при получении id текущей работы: {e}")
        return 0

async def get_current_job(user_id: int):
    """Получает текущую работу пользователя."""
    try:
        # Получаем id пользователя из таблицы users
        user_db_id = await get_user_db_id(user_id)
        if not user_db_id:
            return None

        # Получаем текущую работу пользователя
        query = """
            SELECT j.id, j.name, j.description, j.income, j.required_level, 
                   j.required_education_id, j.required_car_id, j.required_house_id, j.required_city_id
            FROM user_jobs uj
            JOIN jobs j ON uj.job_id = j.id
            WHERE uj.user_id = %s
        """
        result = await execute_db_query(query, (user_db_id,))
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Ошибка при получении текущей работы: {e}")
        return None


async def get_next_job(user_id: int):
    """Получает следующую работу для пользователя."""
    try:
        assets = await get_user_assets(user_id)
        user_level = assets["user_level"]
        max_training_level = await get_user_max_training_level(user_id)
        current_job_id = await get_current_job_id(user_id)  # ID текущей работы

        # Если пользователь не работает, показываем работу с id = 1
        if current_job_id == 0:
            next_job_id = 1
        else:
            next_job_id = current_job_id + 1  # Следующая работа

        query = """
            SELECT id, name, description, income, required_level, 
                   required_education_id, required_car_id, required_house_id, required_city_id
            FROM jobs
            WHERE id = %s 
              AND required_level <= %s 
              AND (required_education_id IS NULL OR required_education_id <= %s)
              AND (required_car_id IS NULL OR %s >= required_car_id)
              AND (required_house_id IS NULL OR %s >= required_house_id)
              AND (required_city_id IS NULL OR %s >= required_city_id)
        """
        job = await execute_db_query(query, (
            next_job_id,
            user_level,
            max_training_level,
            assets["car_id"],
            assets["house_id"],
            assets["city_id"],
        ))

        return job[0] if job else None
    except Exception as e:
        logger.error(f"Ошибка при получении следующей работы: {e}")
        return None


async def get_user_assets(user_id: int) -> dict:
    """Получает данные о активах пользователя (автомобиль, дом, город) и их уровнях."""
    try:
        query = """
            SELECT car, house, city, level, max_training_level 
            FROM users 
            WHERE user_id = %s
        """
        result = await execute_db_query(query, (user_id,))
        if result:
            car_id, house_id, city_id, user_level, max_training_level = result[0]
            return {
                "car_id": car_id,
                "house_id": house_id,
                "city_id": city_id,
                "user_level": user_level,
                "max_training_level": max_training_level,  # Добавляем уровень обучения
            }
        else:
            return {
                "car_id": None,
                "house_id": None,
                "city_id": None,
                "user_level": 0,
                "max_training_level": 0,  # По умолчанию 0
            }
    except Exception as e:
        logger.error(f"Ошибка при получении активов пользователя: {e}")
        return {
            "car_id": None,
            "house_id": None,
            "city_id": None,
            "user_level": 0,
            "max_training_level": 0,  # По умолчанию 0
        }

async def get_available_jobs(user_id: int):
    """Получает список доступных работ для пользователя, исключая работы с ID меньше или равным текущей."""
    try:
        assets = await get_user_assets(user_id)
        user_level = assets["user_level"]
        max_training_level = await get_user_max_training_level(user_id)
        current_job_id = await get_current_job_id(user_id)  # ID текущей работы

        # Получаем список всех работ, которые соответствуют требованиям и имеют ID больше текущей
        query = """
            SELECT id, name, description, income, required_level, 
                   required_education_id, required_car_id, required_house_id, required_city_id
            FROM jobs
            WHERE required_level <= %s 
              AND (required_education_id IS NULL OR required_education_id <= %s)
              AND (required_car_id IS NULL OR %s >= required_car_id)
              AND (required_house_id IS NULL OR %s >= required_house_id)
              AND (required_city_id IS NULL OR %s >= required_city_id)
              AND id > %s  # Исключаем работы с ID меньше или равным текущей
        """
        available_jobs = await execute_db_query(query, (
            user_level,
            max_training_level,
            assets["car_id"],
            assets["house_id"],
            assets["city_id"],
            current_job_id,  # Исключаем работы с ID <= текущей
        ))

        # Получаем одну недоступную работу (следующую после доступных)
        next_unavailable_job_query = """
            SELECT id, name, description, income, required_level, 
                   required_education_id, required_car_id, required_house_id, required_city_id
            FROM jobs
            WHERE id > %s  # Работа с ID больше текущей
              AND (required_level > %s  # Уровень выше текущего
                   OR (required_education_id IS NOT NULL AND required_education_id > %s)  # Требуется более высокое образование
                   OR (required_car_id IS NOT NULL AND %s < required_car_id)  # Требуется более высокий автомобиль
                   OR (required_house_id IS NOT NULL AND %s < required_house_id)  # Требуется более высокий дом
                   OR (required_city_id IS NOT NULL AND %s < required_city_id))  # Требуется более высокий город
            ORDER BY id ASC
            LIMIT 1
        """
        next_unavailable_job = await execute_db_query(next_unavailable_job_query, (
            current_job_id,
            user_level,
            max_training_level,
            assets["car_id"],
            assets["house_id"],
            assets["city_id"],
        ))

        return {
            "available_jobs": available_jobs,
            "next_unavailable_job": next_unavailable_job[0] if next_unavailable_job else None,
            "user_assets": assets  # Добавляем данные пользователя
        }
    except Exception as e:
        logger.error(f"Ошибка при получении доступных работ: {e}")
        return {"available_jobs": [], "next_unavailable_job": None, "user_assets": None}

async def get_user_max_training_level(user_id: int) -> int:
    try:
        query = """
            SELECT max_training_level 
            FROM users 
            WHERE user_id = %s
        """
        result = await execute_db_query(query, (user_id,))
        return result[0][0] if result else 0
    except Exception as e:
        logger.error(f"Ошибка при получении max_training_level пользователя: {e}")
        return 0

async def show_available_jobs(message: types.Message):
    try:
        user_id = message.from_user.id
        jobs_data = await get_available_jobs(user_id)

        available_jobs = jobs_data["available_jobs"]
        next_unavailable_job = jobs_data["next_unavailable_job"]
        user_assets = jobs_data["user_assets"]  # Данные пользователя

        if not available_jobs and not next_unavailable_job:
            await message.answer("🚫 У вас нет доступных работ. Проверьте уровень, образование и активы.")
            return

        job_texts = []

        # Выводим доступные работы
        if available_jobs:
            job_texts.append("💼 Доступные работы:\n")
            for job in available_jobs:
                (
                    job_id, name, description, income, required_level,
                    required_education_id, required_car_id, required_house_id, required_city_id
                ) = job

                city_name = "Не требуется"
                if required_city_id:
                    city_name = CITIES.get(required_city_id, {}).get("name", "Неизвестный город")

                job_text = (
                    f"💼 {name}\n"
                    f"📝 Описание: {description}\n"
                    f"💰 Заработок: {income}💵\n"
                    f"🎯 Требуемый уровень: {required_level}\n"
                )

                if required_education_id:
                    job_text += f"🎓 Требуется обучение: {required_education_id}\n"
                if required_car_id:
                    job_text += f"🚗 Требуется автомобиль: {required_car_id}\n"
                if required_house_id:
                    job_text += f"🏠 Требуется дом: {required_house_id}\n"
                if required_city_id:
                    job_text += f"🌆 Требуется город: {city_name}\n"

                job_texts.append(job_text)

        # Выводим одну недоступную работу
        if next_unavailable_job:
            (
                job_id, name, description, income, required_level,
                required_education_id, required_car_id, required_house_id, required_city_id
            ) = next_unavailable_job

            city_name = "Не требуется"
            if required_city_id:
                city_name = CITIES.get(required_city_id, {}).get("name", "Неизвестный город")

            job_texts.append("🔒 Следующая недоступная работа:\n")
            job_texts.append(
                f"💼 {name}\n"
                f"📝 Описание: {description}\n"
                f"💰 Заработок: {income}💵"
            )

            # Уровень
            job_texts.append(f"🎯 Требуется уровень: {required_level} (у вас {user_assets['user_level']})")

            # Образование
            if required_education_id:
                job_texts.append(f"🎓 Требуется обучение: {required_education_id} (у вас {user_assets['max_training_level']})")

            # Автомобиль
            if required_car_id:
                job_texts.append(f"🚗 Требуется автомобиль: {required_car_id} (у вас {user_assets['car_id']})")

            # Дом
            if required_house_id:
                job_texts.append(f"🏠 Требуется дом: {required_house_id} (у вас {user_assets['house_id']})")

            # Город
            if required_city_id:
                job_texts.append(f"🌆 Требуется город: {city_name} (у вас {CITIES.get(user_assets['city_id'], {}).get('name', 'Неизвестный город')})\n")

        # Создаем клавиатуру с кнопками "Устроиться на работу", "Профиль", "Помощь"
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="💼 Устроиться на работу")],
                [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="💼 Работа")],
                [KeyboardButton(text="‼ Помощь")]
            ],
            resize_keyboard=True
        )

        await message.answer("\n\n".join(job_texts), reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Ошибка при отображении доступных работ: {e}")
        await message.answer("⚠️ Произошла ошибка при получении списка работ.")


async def handle_get_job(message: types.Message, job_id: int = None):
    """Обработчик для устройства на работу (только на id = 1)."""
    try:
        user_id = message.from_user.id

        # Если job_id не передан, используем работу с id = 1
        if job_id is None:
            job_id = 1

        # Получаем ID пользователя из таблицы users
        user_db_id_query = """
            SELECT id FROM users WHERE user_id = %s
        """
        user_db_id_result = await execute_db_query(user_db_id_query, (user_id,))

        if not user_db_id_result:
            await message.answer("⚠️ Пользователь не найден. Зарегистрируйтесь через /start.")
            return

        user_db_id = user_db_id_result[0][0]  # Получаем id пользователя из таблицы users

        # Проверяем, что пользователь безработный
        current_job_query = """
            SELECT job_id FROM user_jobs WHERE user_id = %s
        """
        current_job = await execute_db_query(current_job_query, (user_db_id,))

        if current_job:
            await message.answer("⚠️ Вы уже работаете. Используйте /promotejob для повышения.")
            return

        # Получаем информацию о работе
        job_query = """
            SELECT name, required_level, required_education_id, required_car_id, required_house_id, required_city_id
            FROM jobs
            WHERE id = %s
        """
        job_data = await execute_db_query(job_query, (job_id,))

        if not job_data:
            await message.answer("⚠️ Работа не найдена.")
            return

        job_name, required_level, required_education_id, required_car_id, required_house_id, required_city_id = job_data[0]

        # Проверяем требования работы
        user_data_query = """
            SELECT level, max_training_level, car, house, city
            FROM users
            WHERE id = %s
        """
        user_data = await execute_db_query(user_data_query, (user_db_id,))

        if not user_data:
            await message.answer("⚠️ Пользователь не найден. Зарегистрируйтесь через /start.")
            return

        user_level, max_training_level, user_car, user_house, user_city = user_data[0]

        if user_level < required_level:
            await message.answer(f"⚠️ Для этой работы требуется уровень {required_level}. Ваш уровень: {user_level}.")
            return

        if required_education_id and max_training_level < required_education_id:
            await message.answer(f"⚠️ Для этой работы требуется обучение уровня {required_education_id}.")
            return

        if required_car_id and user_car < required_car_id:
            await message.answer(f"⚠️ Для этой работы требуется автомобиль с ID {required_car_id}.")
            return

        if required_house_id and user_house < required_house_id:
            await message.answer(f"⚠️ Для этой работы требуется дом с ID {required_house_id}.")
            return

        if required_city_id and user_city < required_city_id:
            await message.answer(f"⚠️ Для этой работы требуется город с ID {required_city_id}.")
            return

        # Устраиваем пользователя на работу
        update_job_query = """
            INSERT INTO user_jobs (user_id, job_id, start_date, last_income_collection)
            VALUES (%s, %s, %s, %s)
        """
        await execute_db_query(update_job_query, (user_db_id, job_id, datetime.now(), datetime.now()))

        await message.answer(f"🎉 Вы успешно устроились на работу «{job_name}»!")

        # После успешного устройства на работу вызываем обработчик с информацией о текущей работе
        await handle_my_job(message)
    
    except Exception as e:
        logger.error(f"Ошибка при устройстве на работу: {e}")
        await message.answer("⚠️ Произошла ошибка при устройстве на работу.")


async def handle_promote_job(message: types.Message):
    """Обработчик для повышения на следующую работу."""
    try:
        user_id = message.from_user.id

        # Получаем ID пользователя из таблицы users
        user_db_id_query = """
            SELECT id FROM users WHERE user_id = %s
        """
        user_db_id_result = await execute_db_query(user_db_id_query, (user_id,))

        if not user_db_id_result:
            await message.answer("⚠️ Пользователь не найден. Зарегистрируйтесь через /start.")
            return

        user_db_id = user_db_id_result[0][0]  # Получаем id пользователя из таблицы users

        # Получаем текущую работу пользователя
        current_job_query = """
            SELECT job_id FROM user_jobs WHERE user_id = %s
        """
        current_job = await execute_db_query(current_job_query, (user_db_id,))

        if not current_job:
            await message.answer("⚠️ Вы не работаете. Используйте /getjob для устройства на работу.")
            return

        current_job_id = current_job[0][0]

        # Получаем следующую доступную работу
        next_job = await get_next_job(user_id)
        if not next_job:
            await message.answer("🚫 У вас нет доступных работ для повышения.")
            return

        next_job_id = next_job[0]  # ID следующей работы

        # Проверяем, что следующая работа действительно следующая по порядку
        if next_job_id != current_job_id + 1:
            await message.answer("⚠️ Вы можете повышаться только на следующую работу.")
            return

        # Получаем информацию о следующей работе
        job_query = """
            SELECT name, required_level, required_education_id, required_car_id, required_house_id, required_city_id
            FROM jobs
            WHERE id = %s
        """
        job_data = await execute_db_query(job_query, (next_job_id,))

        if not job_data:
            await message.answer("⚠️ Работа не найдена.")
            return

        job_name, required_level, required_education_id, required_car_id, required_house_id, required_city_id = job_data[0]

        # Проверяем требования работы
        user_data_query = """
            SELECT level, max_training_level, car, house, city
            FROM users
            WHERE id = %s
        """
        user_data = await execute_db_query(user_data_query, (user_db_id,))

        if not user_data:
            await message.answer("⚠️ Пользователь не найден. Зарегистрируйтесь через /start.")
            return

        user_level, max_training_level, user_car, user_house, user_city = user_data[0]

        if user_level < required_level:
            await message.answer(f"⚠️ Для этой работы требуется уровень {required_level}. Ваш уровень: {user_level}.")
            return

        if required_education_id and max_training_level < required_education_id:
            await message.answer(f"⚠️ Для этой работы требуется обучение уровня {required_education_id}.")
            return

        if required_car_id and user_car < required_car_id:
            await message.answer(f"⚠️ Для этой работы требуется автомобиль с ID {required_car_id}.")
            return

        if required_house_id and user_house < required_house_id:
            await message.answer(f"⚠️ Для этой работы требуется дом с ID {required_house_id}.")
            return

        if required_city_id and user_city < required_city_id:
            await message.answer(f"⚠️ Для этой работы требуется город с ID {required_city_id}.")
            return

        # Обновляем запись о работе пользователя
        update_job_query = """
            UPDATE user_jobs 
            SET job_id = %s, start_date = %s, last_income_collection = %s
            WHERE user_id = %s
        """
        await execute_db_query(update_job_query, (next_job_id, datetime.now(), datetime.now(), user_db_id))

        await message.answer(f"🎉 Вы успешно повысились на работу «{job_name}»!")
    
    except Exception as e:
        logger.error(f"Ошибка при повышении на работу: {e}")
        await message.answer("⚠️ Произошла ошибка при повышении на работу.")


async def handle_collect_jobs(message: types.Message):
    """
    Обработчик для сбора дохода с работы.
    Использование: /collectincome
    """
    try:
        user_id = message.from_user.id

        # Получаем ID пользователя из таблицы users
        user_db_id_query = """
            SELECT id FROM users WHERE user_id = %s
        """
        user_db_id_result = await execute_db_query(user_db_id_query, (user_id,))

        if not user_db_id_result:
            await message.answer("⚠️ Пользователь не найден. Зарегистрируйтесь через /start.")
            return

        user_db_id = user_db_id_result[0][0]  # Получаем id пользователя из таблицы users

        # Получаем текущую работу пользователя
        current_job_query = """
            SELECT job_id, start_date, last_income_collection
            FROM user_jobs
            WHERE user_id = %s
        """
        current_job = await execute_db_query(current_job_query, (user_db_id,))

        if not current_job:
            await message.answer("⚠️ Вы не устроены на работу.")
            return

        job_id, start_date, last_income_collection = current_job[0]

        # Получаем информацию о работе
        job_query = """
            SELECT income FROM jobs WHERE id = %s
        """
        job_data = await execute_db_query(job_query, (job_id,))

        if not job_data:
            await message.answer("⚠️ Работа не найдена.")
            return

        income_per_hour = job_data[0][0]

        # Рассчитываем время с момента последнего сбора дохода
        if last_income_collection:
            time_since_last_collection = datetime.now() - last_income_collection
        else:
            time_since_last_collection = datetime.now() - start_date

        # Ограничиваем время накопления 5 часами
        max_accumulation_time = timedelta(hours=5)
        if time_since_last_collection > max_accumulation_time:
            time_since_last_collection = max_accumulation_time

        # Рассчитываем накопленный доход
        hours_since_last_collection = time_since_last_collection.total_seconds() / 3600
        accumulated_income = int(hours_since_last_collection * income_per_hour)

        # Применяем бонус города
        bonus_percent = calculate_income_with_bonus(user_id, accumulated_income)
        total_income_with_bonus = accumulated_income + (accumulated_income * bonus_percent / 100)

        # Начисляем доход пользователю
        update_balance_query = """
            UPDATE users SET balance = balance + %s WHERE id = %s
        """
        await execute_db_query(update_balance_query, (total_income_with_bonus, user_db_id))

        # Начисляем опыт (1 опыт за каждые 10💵 дохода)
        experience_earned = total_income_with_bonus // 10  # Опыт = доход / 10
        if experience_earned > 0:
            new_level, remaining_experience, level_increased = await add_experience(user_id, experience_earned)

            # Если уровень повышен, отправляем уведомление
            if level_increased:
                await message.answer(f"🎉 Поздравляем! Вы достигли уровня {new_level}!")

        # Обновляем время последнего сбора дохода
        update_last_income_collection_query = """
            UPDATE user_jobs SET last_income_collection = %s WHERE user_id = %s
        """
        await execute_db_query(update_last_income_collection_query, (datetime.now(), user_db_id))

        await message.answer(
            f"💰 Вы собрали доход: {accumulated_income}💵.\n"
            f"🏙 С учетом бонуса города: {total_income_with_bonus}💵.\n"
            f"✨ Вы получили {experience_earned} опыта."
        )
    
    except Exception as e:
        logger.error(f"Ошибка при сборе дохода: {e}")
        await message.answer("⚠️ Произошла ошибка при сборе дохода.")



async def handle_my_job(message: types.Message):
    """Обработчик команды /myjob."""
    try:
        user_id = message.from_user.id
        current_job = await get_current_job(user_id)

        if not current_job:
            await message.answer("🚫 Вы сейчас не работаете.")
            return

        (
            job_id, name, description, income, required_level,
            required_education_id, required_car_id, required_house_id, required_city_id
        ) = current_job

        city_name = "Не требуется"
        if required_city_id:
            city_name = CITIES.get(required_city_id, {}).get("name", "Неизвестный город")

        # Рассчитываем накопленную прибыль с учетом ограничения на максимальное время накопления
        accumulated_income = await calculate_accumulated_income(user_id, income)

        # Ограничиваем время накопления 5 часами (как в функции сбора дохода)
        max_accumulation_time = 5  # Максимальное время накопления в часах
        accumulated_income = min(accumulated_income, income * max_accumulation_time)

        job_text = (
            f"💼 Ваша текущая работа: <b>{name}</b>\n\n"
            f"📝 Описание: {description}\n\n"
            f"💰 Заработок: {income}💵/ч.\n\n"
            f"💵 Накоплено прибыли: {accumulated_income}💵\n"
        )

        # Создаем клавиатуру с кнопками
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="💵 Собрать зарплату")],
                [KeyboardButton(text="⬆️ Повышение"), KeyboardButton(text="🛠️ Доступные работы")],
                [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="‼ Помощь")]
            ],
            resize_keyboard=True
        )

        await message.answer(job_text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Ошибка при отображении текущей работы: {e}")
        await message.answer("⚠️ Произошла ошибка при получении информации о вашей работе.")
