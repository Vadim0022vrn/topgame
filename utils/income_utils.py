import mysql.connector
from config.config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
from config.city import CITIES
from config.clothes import CLOTHES
from utils.girls_utils import calculate_girl_bonus
import logging

logger = logging.getLogger(__name__)

def calculate_income_with_bonus(user_id, total_income):
    """Рассчитывает бонус города, девушки и одежды."""
    try:
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = connection.cursor()

        # Получаем город, ID девушки и ID одежды пользователя
        cursor.execute("SELECT city, girlfriend, clothes FROM users WHERE user_id = %s", (user_id,))
        city_id, girlfriend_id, clothes_id = cursor.fetchone()

        # Рассчитываем бонус города
        city_bonus = 0.0
        if city_id in CITIES:
            city_bonus = CITIES[city_id]["bonus"]

        # Рассчитываем бонусы от девушки
        girl_bonus = calculate_girl_bonus(girlfriend_id)
        income_bonus = girl_bonus.get("income", 0.0)  # Получаем бонус дохода, если он есть

        # Рассчитываем бонус от одежды
        clothes_bonus = 0.0
        if clothes_id in CLOTHES:
            clothes_bonus = CLOTHES[clothes_id]["bonus"].get("income", 0.0)  # Получаем бонус дохода от одежды

        # Общий бонус (город + девушка + одежда)
        total_bonus = city_bonus + income_bonus + clothes_bonus

        connection.close()

        # Возвращаем только процент бонуса (например, 0.1 для 10%)
        return total_bonus

    except Exception as e:
        logger.error(f"Ошибка при расчёте бонуса для пользователя {user_id}: {e}")
        return 0.0  # Возвращаем 0 в случае ошибки