import asyncio
import logging
import mysql.connector
from datetime import datetime, timedelta
from config.config import API_TOKEN, MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

logger = logging.getLogger(__name__)

async def handle_daily(message):
    """Начисляет пользователю ежедневный бонус с растущими значениями."""
    try:
        user_id = message.from_user.id
        today = datetime.now().date()

        def sync_get_and_update_bonus():
            connection = mysql.connector.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE
            )
            cursor = connection.cursor()

            cursor.execute(
                'SELECT last_daily, daily_streak FROM users WHERE user_id = %s',
                (user_id,))
            result = cursor.fetchone()

            if result:
                last_daily, daily_streak = result
                if last_daily == today:  # Сравниваем с today напрямую
                    connection.close()
                    return None, None, daily_streak  # Бонус уже получен сегодня, возвращаем None для money_bonus и exp_bonus

                # Проверяем, была ли пропущена серия
                if last_daily:
                    if isinstance(last_daily, str):  # Если last_daily - строка
                        last_date = datetime.strptime(last_daily, "%Y-%m-%d").date()
                    else:  # Если last_daily - уже datetime.date
                        last_date = last_daily

                    if (today - last_date).days > 1:
                        daily_streak = 1  # Сброс серии
                    elif (today - last_date).days == 1:
                        daily_streak += 1  # Продолжение серии
                    else:
                        daily_streak = daily_streak  # Бонус уже получен сегодня
                else:
                    daily_streak = 1  # Первый день серии

                # Рассчитываем бонус денег
                money_step = 50  # Шаг увеличения денежного бонуса
                money_bonus = (daily_streak // 10) * 500 + (daily_streak % 10) * (money_step * (daily_streak // 10 + 1))

                # Рассчитываем бонус опыта
                exp_step = 5  # Шаг увеличения бонуса опыта
                exp_bonus = (daily_streak // 10) * 50 + (daily_streak % 10) * (exp_step * (daily_streak // 10 + 1))

                # Обновляем баланс и опыт пользователя
                cursor.execute(
                    'UPDATE users SET balance = balance + %s, experience = experience + %s, last_daily = %s, daily_streak = %s WHERE user_id = %s',
                    (money_bonus, exp_bonus, today, daily_streak, user_id)
                )
                connection.commit()
                connection.close()
                return money_bonus, exp_bonus, daily_streak
            else:
                connection.close()
                return None, None, 0  # Пользователь не найден, возвращаем None для money_bonus и exp_bonus

        money_bonus, exp_bonus, streak = await asyncio.to_thread(sync_get_and_update_bonus)

        if money_bonus is None and exp_bonus is None:
            await message.answer("🎁 Вы уже получили сегодняшний бонус!")
        else:
            await message.answer(
                f"🎉 Вы получили {money_bonus}💵 и {exp_bonus} опыта за сегодняшний вход!\n"
                f"📅 Серия дней: {streak}."
            )

    except Exception as e:
        logger.error(f"Ошибка при получении ежедневного бонуса: {str(e)}")
        await message.answer("⚠️ Произошла ошибка при начислении бонуса.")