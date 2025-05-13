from config.girls import GIRLS
from config.clothes import CLOTHES
import mysql.connector
import logging
from config.config import API_TOKEN, MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
from datetime import datetime
from utils.database import execute_db_query
from aiogram import Bot
from config.config import API_TOKEN
from utils.girls_utils import calculate_girl_bonus


logger = logging.getLogger(__name__)

# Базовые значения
INITIAL_LEVEL = 1  # Начальный уровень
INITIAL_EXPERIENCE = 0  # Начальный опыт
BASE_EXPERIENCE_REQUIRED = 150  # Опыт для перехода с 1 на 2 уровень
EXPERIENCE_MULTIPLIER = 1.1  # Множитель опыта для каждого следующего уровня


# Словарь с разблокируемыми возможностями
LEVEL_UNLOCKS = {
    3: "🏢 Бизнесы: Теперь вы можете покупать и управлять бизнесами!",
    5: "🚗 Новые автомобили: Доступны более мощные и престижные автомобили.",
    10: "🛥 Яхты: Теперь вы можете приобрести свою первую яхту!",
    15: "🏝 Острова: Откройте для себя частные острова и станьте их владельцем.",
    20: "✈️ Самолеты: Теперь вы можете купить частный самолет.",
    # Добавьте другие уровни и разблокировки по необходимости
}
    # Словарь для выдачи девушек на определенных уровнях
LEVEL_TO_GIRL = {
    5: 1,   # На 5 уровне выдается девушка с ID 1
    10: 2,  # На 10 уровне выдается девушка с ID 2
    15: 3,  # На 15 уровне выдается девушка с ID 3
    20: 4,  # На 20 уровне выдается девушка с ID 4
    25: 5,  # На 25 уровне выдается девушка с ID 5
    30: 6,  # На 30 уровне выдается девушка с ID 6
    # Добавьте другие уровни и ID девушек по необходимости
}

def get_required_experience(level: int) -> int:
    """
    Возвращает количество опыта, необходимое для перехода на следующий уровень.
    :param level: Текущий уровень пользователя.
    :return: Количество опыта для перехода на следующий уровень.
    """
    if level < INITIAL_LEVEL:
        raise ValueError("Уровень не может быть меньше начального.")

    # Рассчитываем опыт для уровня
    if level == INITIAL_LEVEL:
        return BASE_EXPERIENCE_REQUIRED
    else:
        return int(BASE_EXPERIENCE_REQUIRED * (EXPERIENCE_MULTIPLIER ** (level - 1)))

def get_user_level_and_experience(user_id: int) -> tuple[int, int]:
    """
    Получает текущий уровень и опыт пользователя из базы данных.
    :param user_id: ID пользователя.
    :return: Текущий уровень и опыт.
    """
    connection = mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )
    cursor = connection.cursor()

    cursor.execute('SELECT level, experience FROM users WHERE user_id = %s', (user_id,))
    result = cursor.fetchone()
    connection.close()

    if not result:
        raise ValueError("Пользователь не найден.")

    level, experience = result
    return level, experience

async def add_experience(user_id: int, amount: int) -> tuple[int, int, bool]:
    connection = mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )
    cursor = connection.cursor()

    # Получаем текущий уровень, опыт, ID девушки и ID одежды пользователя
    cursor.execute('SELECT level, experience, girlfriend, clothes FROM users WHERE user_id = %s', (user_id,))
    level, experience, girlfriend_id, clothes_id = cursor.fetchone()

    # Рассчитываем бонусы от девушки
    girl_bonus = calculate_girl_bonus(girlfriend_id)
    experience_bonus = girl_bonus["experience"]

    # Рассчитываем бонус от одежды
    clothes_bonus = 0.0
    if clothes_id in CLOTHES:
        clothes_bonus = CLOTHES[clothes_id]["bonus"].get("experience", 0.0)  # Получаем бонус опыта от одежды

    # Увеличиваем опыт с учетом бонусов от девушки и одежды
    total_experience = experience + amount * (1 + experience_bonus + clothes_bonus)

    required_experience = get_required_experience(level)

    # Проверяем, нужно ли повысить уровень
    new_level = level
    level_increased = False
    while total_experience >= required_experience:
        total_experience -= required_experience
        new_level += 1
        required_experience = get_required_experience(new_level)
        level_increased = True

        # Проверяем, достиг ли игрок уровня, на котором нужно выдать девушку
        if new_level in LEVEL_TO_GIRL:
            girl_id = LEVEL_TO_GIRL[new_level]
            cursor.execute('UPDATE users SET girlfriend = %s WHERE user_id = %s', (girl_id, user_id))
            logger.info(f"Пользователь {user_id} получил девушку {girl_id} на уровне {new_level}.")

    # Обновляем уровень и опыт в базе данных
    cursor.execute('UPDATE users SET level = %s, experience = %s WHERE user_id = %s', (new_level, total_experience, user_id))
    connection.commit()

    # Если уровень повысился, обновляем ранг
    if level_increased:
        await update_rank_based_on_level(user_id, new_level)

    cursor.close()
    connection.close()

    return new_level, total_experience, level_increased

async def notify_level_up(user_id: int, new_level: int):
    """
    Отправляет уведомление о повышении уровня и выдаче девушки.
    :param user_id: ID пользователя.
    :param new_level: Новый уровень пользователя.
    """
    bot = Bot(token=API_TOKEN)  # Создаем экземпляр бота

    try:
        # Формируем текст уведомления
        message_text = f"🎉 Поздравляем! Вы достигли уровня {new_level}!\n"

        # Проверяем, есть ли разблокируемые возможности для этого уровня
        if new_level in LEVEL_UNLOCKS:
            message_text += f"\n{LEVEL_UNLOCKS[new_level]}"

        # Проверяем, получил ли игрок новую девушку
        if new_level in LEVEL_TO_GIRL:
            girl_id = LEVEL_TO_GIRL[new_level]
            girl_name = GIRLS[girl_id]["name"]
            message_text += f"\n\n💖 Вам назначена новая девушка: {girl_name}!"

        # Отправляем сообщение
        await bot.send_message(
            chat_id=user_id,
            text=message_text
        )
    finally:
        # Закрываем сессию бота
        await bot.session.close()

def calculate_level_progress(user_id: int) -> tuple[int, int, float]:
    """
    Рассчитывает прогресс до следующего уровня.
    :param user_id: ID пользователя.
    :return: Текущий уровень, требуемый опыт, процент прогресса.
    """
    level, experience = get_user_level_and_experience(user_id)
    required_experience = get_required_experience(level)
    progress_percent = (experience / required_experience) * 100
    return level, required_experience, progress_percent

async def update_rank_based_on_level(user_id: int, new_level: int):
    # Определяем соответствие уровня и ранга
    level_to_rank = {
        10: 2,  # На 10 уровне ранг повышается до 2
        15: 3,  # На 15 уровне ранг повышается до 3
        20: 4,  # На 20 уровне ранг повышается до 4
        30: 5,  # На 30 уровне ранг повышается до 5
        40: 6,  # На 40 уровне ранг повышается до 6
        # Добавьте другие уровни и ранги по необходимости
    }

    # Получаем текущий ранг пользователя
    connection = mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )
    cursor = connection.cursor()
    cursor.execute('SELECT rank FROM users WHERE user_id = %s', (user_id,))
    current_rank = cursor.fetchone()[0]

    # Определяем новый ранг на основе уровня
    new_rank = current_rank
    for level, rank in level_to_rank.items():
        if new_level >= level and rank > current_rank:
            new_rank = rank

    # Ограничиваем ранг до 20 (ранги с 21 по 30 — донатные или административные)
    if new_rank > 20:
        new_rank = 20

    # Если новый ранг отличается от текущего, обновляем его в базе данных
    if new_rank != current_rank:
        cursor.execute('UPDATE users SET rank = %s WHERE user_id = %s', (new_rank, user_id))
        connection.commit()
        logger.info(f"Ранг пользователя {user_id} обновлен до {new_rank} (уровень {new_level}).")

    cursor.close()
    connection.close()
