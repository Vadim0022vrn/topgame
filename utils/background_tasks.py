# background_tasks.py
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot
from config.config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
from utils.database import execute_db_query
from config.level import get_required_experience, add_experience, notify_level_up
import mysql.connector
import logging

logger = logging.getLogger(__name__)

async def check_completed_trainings(bot: Bot):
    """Фоновая задача для проверки завершения обучений."""
    while True:
        try:
            # Получаем список завершенных обучений с user_id из Telegram
            with mysql.connector.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE
            ) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT u.user_id, ue.education_id 
                        FROM user_educations ue
                        JOIN users u ON ue.user_id = u.id
                        WHERE ue.completion_time <= %s
                        """,
                        (datetime.now(),)
                    )
                    completed_trainings = cursor.fetchall()

            # Отправляем уведомления и начисляем опыт
            for user_id, education_id in completed_trainings:
                try:
                    logger.info(f"Обработка обучения {education_id} для пользователя {user_id}.")

                    # Получаем название обучения и награду за опыт
                    with mysql.connector.connect(
                        host=MYSQL_HOST,
                        port=MYSQL_PORT,
                        user=MYSQL_USER,
                        password=MYSQL_PASSWORD,
                        database=MYSQL_DATABASE
                    ) as connection:
                        with connection.cursor() as cursor:
                            cursor.execute(
                                "SELECT name, experience_reward FROM education WHERE id = %s",
                                (education_id,)
                            )
                            training_name, experience_reward = cursor.fetchone()

                    # Отправляем уведомление
                    try:
                        await bot.send_message(
                            chat_id=user_id,
                            text=f"🎓 Ваше обучение «{training_name}» завершено!\n"
                                 f"✨ Вы получили {experience_reward} опыта!"
                        )

                        # Начисляем опыт пользователю
                        await add_experience(user_id, experience_reward)

                        # Удаляем запись об обучении после отправки уведомления
                        with mysql.connector.connect(
                            host=MYSQL_HOST,
                            port=MYSQL_PORT,
                            user=MYSQL_USER,
                            password=MYSQL_PASSWORD,
                            database=MYSQL_DATABASE
                        ) as connection:
                            with connection.cursor() as cursor:
                                cursor.execute(
                                    "DELETE FROM user_educations WHERE user_id = (SELECT id FROM users WHERE user_id = %s) AND education_id = %s",
                                    (user_id, education_id)
                                )
                                connection.commit()
                                logger.info(f"✅ Запись об обучении {education_id} пользователя {user_id} удалена.")

                    except Exception as e:
                        if "chat not found" in str(e):
                            logger.warning(f"⚠️ Пользователь {user_id} не найден или заблокировал бота.")
                        else:
                            raise e  # Пробрасываем другие ошибки

                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")

            # Пауза между проверками (например, каждые 60 секунд)
            await asyncio.sleep(60)

        except Exception as e:
            logger.error(f"Ошибка в фоновой задаче: {e}")
            await asyncio.sleep(60)  # Пауза перед повторной попыткой


async def check_business_accumulation(bot: Bot):
    """Фоновая задача для проверки накопления доходов от бизнесов."""
    while True:
        try:
            # Получаем список бизнесов, у которых накоплена полная касса
            connection = mysql.connector.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE
            )
            cursor = connection.cursor()
            cursor.execute(''' 
                SELECT u.user_id, b.name, ub.last_collected_income, b.max_accumulation_time
                FROM user_businesses ub
                JOIN businesses b ON ub.business_id = b.id
                JOIN users u ON ub.user_id = u.id
                WHERE ub.last_collected_income IS NOT NULL
            ''')
            businesses = cursor.fetchall()
            cursor.close()
            connection.close()

            # Отправляем уведомления
            for user_id, business_name, last_collected_income, max_accumulation_time in businesses:
                try:
                    # Если last_collected_income уже является объектом datetime, просто используем его
                    last_collected_time = last_collected_income
                    time_since_last_collection = datetime.now() - last_collected_time

                    # Проверяем, истекло ли время накопления
                    if time_since_last_collection.total_seconds() >= max_accumulation_time * 3600:
                        await bot.send_message(
                            chat_id=user_id,  # Теперь user_id — это Telegram ID
                            text=f"⚠️ Ваш бизнес «{business_name}» накопил полную кассу!\n"
                                 f"Соберите доход, чтобы продолжить накопление."
                        )
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")

            # Пауза между проверками (например, каждые 120 секунд)
            await asyncio.sleep(120)

        except Exception as e:
            logger.error(f"Ошибка в фоновой задаче: {e}")
            await asyncio.sleep(60)  # Пауза перед повторной попыткой


async def check_job_accumulation(bot: Bot):
    """Фоновая задача для проверки накопления зарплаты с работы."""
    while True:
        try:
            # Получаем список работ, у которых накоплена полная зарплата
            connection = mysql.connector.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE
            )
            cursor = connection.cursor()
            cursor.execute('''
                SELECT u.user_id, j.name, uj.last_income_collection
                FROM user_jobs uj
                JOIN jobs j ON uj.job_id = j.id
                JOIN users u ON uj.user_id = u.id
                WHERE uj.last_income_collection IS NOT NULL
            ''')
            jobs = cursor.fetchall()
            cursor.close()
            connection.close()

            # Отправляем уведомления
            for user_id, job_name, last_income_collection in jobs:
                try:
                    # Если last_income_collection уже является объектом datetime, просто используем его
                    last_collection_time = last_income_collection
                    time_since_last_collection = datetime.now() - last_collection_time

                    # Максимальное время накопления зарплаты (5 часов)
                    max_accumulation_time = timedelta(hours=5)

                    # Проверяем, истекло ли время накопления
                    if time_since_last_collection >= max_accumulation_time:
                        await bot.send_message(
                            chat_id=user_id,  # Telegram ID пользователя
                            text=f"⚠️ Ваша работа «{job_name}» накопила полную зарплату!\n"
                                 f"Соберите доход, чтобы продолжить накопление."
                        )
                except Exception as e:
                    if "chat not found" in str(e):
                        logger.warning(f"⚠️ Пользователь {user_id} не найден или заблокировал бота.")
                    else:
                        logger.error(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")

            # Пауза между проверками (например, каждые 120 секунд)
            await asyncio.sleep(240)

        except Exception as e:
            logger.error(f"Ошибка в фоновой задаче: {e}")
            await asyncio.sleep(120)  # Пауза перед повторной попыткой


async def check_investments(bot: Bot):
    """Фоновая задача для проверки завершенных инвестиций."""
    while True:
        try:

            # Получаем список завершенных инвестиций
            connection = mysql.connector.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE
            )
            cursor = connection.cursor()
            cursor.execute('''
                SELECT user_id, amount, profit
                FROM investments
                WHERE end_time <= NOW()
            ''')
            investments = cursor.fetchall()
            cursor.close()
            connection.close()

            # Отправляем уведомления
            for user_id, amount, profit in investments:
                try:
                    await bot.send_message(
                        chat_id=user_id,  # Telegram ID пользователя
                        text=f"⚠️ Ваша инвестиция на сумму {amount} 💰 завершена!\n"
                             f"Прибыль: {profit} 💰. Соберите её с помощью команды /claiminvest."
                    )
                    logger.info(f"✅ Уведомление отправлено пользователю {user_id}.")
                except Exception as e:
                    if "chat not found" in str(e):
                        logger.warning(f"⚠️ Пользователь {user_id} не найден или заблокировал бота.")
                    else:
                        logger.error(f"❌ Ошибка при отправке уведомления пользователю {user_id}: {e}")

            # Пауза между проверками (например, каждые 120 секунд)
            await asyncio.sleep(120)

        except Exception as e:
            logger.error(f"❌ Ошибка в фоновой задаче: {e}")
            await asyncio.sleep(60)  # Пауза перед повторной попыткой



async def check_level_up(bot: Bot):
    """Фоновая задача для проверки и повышения уровня пользователей."""
    try:
        while True:
            try:
                # Получаем список пользователей с их уровнем и опытом
                connection = mysql.connector.connect(
                    host=MYSQL_HOST,
                    port=MYSQL_PORT,
                    user=MYSQL_USER,
                    password=MYSQL_PASSWORD,
                    database=MYSQL_DATABASE
                )
                cursor = connection.cursor()
                cursor.execute('''
                    SELECT user_id, level, experience
                    FROM users
                ''')
                users = cursor.fetchall()
                cursor.close()
                connection.close()

                # Проверяем каждого пользователя
                for user_id, level, experience in users:
                    try:
                        # Получаем необходимый опыт для следующего уровня
                        required_experience = get_required_experience(level)

                        # Если текущий опыт больше или равен необходимому
                        if experience >= required_experience:
                            # Повышаем уровень и отправляем уведомление
                            new_level, remaining_experience, level_increased = await add_experience(user_id, 0)
                            if level_increased:
                                await notify_level_up(user_id, new_level)
                    except Exception as e:
                        logger.error(f"❌ Ошибка при проверке уровня пользователя {user_id}: {e}")
            except Exception as e:
                logger.error(f"❌ Ошибка в фоновой задаче: {e}")
                await asyncio.sleep(60)  # Пауза перед повторной попыткой
            await asyncio.sleep(120)  # Пауза между проверками
    except asyncio.CancelledError:
        # Задача была отменена (например, при остановке бота)
        logger.info("Фоновая задача check_level_up завершена.")
    except KeyboardInterrupt:
        # Обработка прерывания (Ctrl+C)
        logger.info("Фоновая задача check_level_up прервана.")