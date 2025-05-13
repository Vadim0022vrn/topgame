from utils.database import execute_db_query
import logging
from aiogram import types
from datetime import datetime
from config.config import RANKS
from config.assets import CARS
from config.city import CITIES
from config.assets import CARS, HOUSES, YACHTS, PLANES, ISLANDS
from config.girls import GIRLS
from config.clothes import CLOTHES
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.level import calculate_level_progress

logger = logging.getLogger(__name__)

RANK_EMOJIS = {
    **{i: "🩵" for i in range(1, 20)},
    20: "🌸",
    **{i: "🟨" for i in range(21, 26)},
    26: "🟩",
    27: "🟥",
    28: "🔵",
    29: "🌸",
    30: "🟥"
}

async def handle_profile(message, user_id=None):
    try:
        user_id = user_id or message.from_user.id
        query = '''
            SELECT id, username, level, rank, experience, balance, bank, solix, aurix, car, registration_date, city, referrer_id, reffer
            FROM users WHERE user_id = %s
        '''
        profile = await execute_db_query(query, (user_id,))

        if profile:
            id_, username, level, rank, experience, balance, bank, solix, aurix, car, registration_date, city_id, referrer_id, reffer = profile[0]
            rank_name = RANKS.get(rank, "Неизвестно")
            rank_emoji = RANK_EMOJIS.get(rank, "⚪")

            # Получаем текущий уровень, требуемый опыт и процент прогресса
            current_level, required_experience, progress_percent = calculate_level_progress(user_id)

            if registration_date:
                try:
                    days_in_game = (datetime.now() - datetime.strptime(registration_date, "%Y-%m-%d")).days
                    registration_display = f"{days_in_game} дней"
                except Exception:
                    registration_display = "Ошибка обработки даты"
            else:
                registration_display = "Дата регистрации не указана"

            # Проверяем, есть ли у пользователя бизнес
            has_business = await has_user_business(user_id)

            # Проверяем, есть ли у пользователя работа
            has_job = await has_user_job(user_id)

            car_name = CARS.get(car, {}).get("name", "Неизвестно") if car is not None else "Неизвестно"
            city_name = CITIES.get(city_id, {}).get("name", "Неизвестно") if city_id is not None else "Неизвестно"

            # Получаем информацию о реферере, если он есть
            referrer_info = ""
            if referrer_id:
                referrer_query = 'SELECT username FROM users WHERE user_id = %s'
                referrer_result = await execute_db_query(referrer_query, (referrer_id,))
                if referrer_result:
                    referrer_username = referrer_result[0][0]
                    referrer_info = f"👥 Пригласил: <b>{referrer_username}</b>\n"

            profile_text = (
                f"\U0001F4DD <b>Ваш профиль {username}:</b>\n"
                f"🆔 ID: <b>{id_}</b>\n"
                f"🎯 Уровень: <b>{level}</b>\n"
                f"🏅 Ранг: {rank_emoji} <b>{rank_name} ({rank})</b>\n"
                f"✨ Опыт: <b>{experience} / {required_experience}</b>\n"
                f"💵 Баланс: <b>{balance}</b>\n"
                f"💵 Банк: <b>{bank}</b>\n"
                f"💎 Solix: <b>{solix}</b> (Криптовалюта)\n"
                f"🔮 Aurix: <b>{aurix}</b> (Донат)\n"
                f"🚗 Автомобиль: <b>{car_name}</b>\n"
                f"🏙 Город: <b>{city_name}</b>\n"
                f"{referrer_info}"
                f"👥 Приглашено: <b>{reffer}</b> Человек.\n"
                f"⏳ Регистрация: <b>{registration_display} назад</b>"
            )

            # Передаем уровень игрока, наличие бизнеса и работы в get_profile_keyboard
            await message.answer(profile_text, parse_mode="HTML", reply_markup=get_profile_keyboard(level, has_business, has_job))
        else:
            await message.answer("⚠️ Профиль не найден. Зарегистрируйтесь через /start.")

    except Exception as e:
        logging.error(f"Ошибка получения профиля: {str(e)}")
        await message.answer(f"⚠️ Ошибка получения профиля: {str(e)}")

async def handle_rank(message):
    try:
        user_id = message.from_user.id

        def sync_get_rank():
            connection = mysql.connector.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE
            )
            cursor = connection.cursor()
            cursor.execute('SELECT rank FROM users WHERE user_id = %s', (user_id,))
            result = cursor.fetchone()
            connection.close()
            return RANKS.get(result[0], 'Неизвестно') if result else 'Неизвестно'

        rank = await asyncio.to_thread(sync_get_rank)
        await message.answer(f"🏅 Ваш ранг: {rank}")

    except Exception as e:
        logging.error(f"Ошибка получения ранга: {str(e)}")
        await message.answer(f"⚠️ Ошибка получения ранга: {str(e)}")

async def has_user_business(user_id: int) -> bool:
    """
    Проверяет, есть ли у пользователя бизнес.
    """
    # Получаем id пользователя из таблицы users
    user_db_id = await execute_db_query(
        "SELECT id FROM users WHERE user_id = %s",
        (user_id,)
    )
    
    if not user_db_id:
        return False  # Пользователь не найден

    user_db_id = user_db_id[0][0]  # Получаем id пользователя из таблицы users

    # Проверяем, есть ли у пользователя бизнес
    result = await execute_db_query(
        "SELECT business_id FROM user_businesses WHERE user_id = %s",
        (user_db_id,)
    )
    return bool(result)  # True, если есть бизнес, иначе False

async def has_user_job(user_id: int) -> bool:
    """
    Проверяет, есть ли у пользователя работа.
    """
    # Получаем id пользователя из таблицы users
    user_db_id = await execute_db_query(
        "SELECT id FROM users WHERE user_id = %s",
        (user_id,)
    )
    
    if not user_db_id:
        return False  # Пользователь не найден

    user_db_id = user_db_id[0][0]  # Получаем id пользователя из таблицы users

    # Проверяем, есть ли у пользователя работа
    result = await execute_db_query(
        "SELECT job_id FROM user_jobs WHERE user_id = %s",
        (user_db_id,)
    )
    return bool(result)  # True, если есть работа, иначе False


def get_profile_keyboard(user_level: int, has_business: bool, has_job: bool) -> ReplyKeyboardMarkup:
    """
    Создает клавиатуру для профиля в зависимости от уровня игрока, наличия бизнеса и работы.
    """
    # Создаем список кнопок
    buttons = [
        [KeyboardButton(text="📖 Список обучений"), KeyboardButton(text="🛠️ Доступные работы" if not has_job else "💼 Работа")]
    ]

    # Кнопка "Мои бизнесы" или "Купить бизнес" появляется только на 3 уровне и выше
    if user_level >= 3:
        if has_business:
            buttons.append([KeyboardButton(text="🏢 Бизнес")])  # Если есть бизнес
        else:
            buttons.append([KeyboardButton(text="🏢 Доступный бизнес")])  # Если бизнеса нет

    # Добавляем остальные кнопки
    buttons.extend([
        [KeyboardButton(text="🏠 Имущество"), KeyboardButton(text="🏦 Банк"), KeyboardButton(text="🏆 ТОПы")],  # Новая кнопка "Имущество"
        [KeyboardButton(text="💰 Забрать бонус"), KeyboardButton(text="📩 Пригласить друзей")],
        [KeyboardButton(text="🔙 Назад"), KeyboardButton(text="‼ Помощь")]
    ])

    # Создаем клавиатуру с кнопками
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,  # Передаем список строк с кнопками
        resize_keyboard=True  # Кнопки будут автоматически подстраиваться под размер экрана
    )

    return keyboard


#-------------------------------------ИМУЩЕСТВО----------------------------------


async def get_user_assets(user_id: int):
    """
    Получает все активы пользователя из базы данных и конфигурационных файлов.
    """
    assets = {}

    # Получаем бизнесы пользователя
    businesses = await execute_db_query(
        "SELECT b.name, ub.level FROM user_businesses ub "
        "JOIN businesses b ON ub.business_id = b.id "
        "WHERE ub.user_id = (SELECT id FROM users WHERE user_id = %s)",
        (user_id,)
    )
    assets["бизнесы"] = businesses if businesses else []

    # Получаем майнинг-ферму пользователя
    mining_farm = await execute_db_query(
        "SELECT mf.name FROM user_mining_farms umf "
        "JOIN mining_farms mf ON umf.mining_id = mf.id "
        "WHERE umf.user_id = (SELECT id FROM users WHERE user_id = %s)",
        (user_id,)
    )
    assets["майнинг-ферма"] = mining_farm[0][0] if mining_farm else "Нет"

    # Получаем данные пользователя из таблицы users
    user_data = await execute_db_query(
        "SELECT house, car, island, yacht, airplane, clothes, animal, girlfriend "
        "FROM users WHERE user_id = %s",
        (user_id,)
    )
    if user_data:
        house_id, car_id, island_id, yacht_id, airplane_id, clothes_id, animal_id, girlfriend_id = user_data[0]

        # Получаем название дома
        assets["дом"] = HOUSES.get(house_id, {}).get("name", "Нет") if house_id else "Нет"

        # Получаем название машины
        assets["машина"] = CARS.get(car_id, {}).get("name", "Нет") if car_id else "Нет"

        # Получаем название острова
        assets["остров"] = ISLANDS.get(island_id, {}).get("name", "Нет") if island_id else "Нет"

        # Получаем название яхты
        assets["яхта"] = YACHTS.get(yacht_id, {}).get("name", "Нет") if yacht_id else "Нет"

        # Получаем название самолета
        assets["самолет"] = PLANES.get(airplane_id, {}).get("name", "Нет") if airplane_id else "Нет"

        # Получаем название одежды
        assets["одежда"] = CLOTHES.get(clothes_id, {}).get("name", "Нет") if clothes_id else "Нет"

        # Животное пока не реализовано в assets.py, поэтому оставляем "Нет"
        assets["животное"] = "Нет" if not animal_id else "Нет"

        # Получаем информацию о девушке
        if girlfriend_id:
            girl = GIRLS.get(girlfriend_id, {})
            assets["девушка"] = girl.get("name", "Нет")
        else:
            assets["девушка"] = "Нет"

    return assets


async def format_assets_message(assets: dict) -> str:
    """
    Форматирует информацию об имуществе в красивое сообщение.
    """
    message = "🏰 <b>Ваше имущество:</b>\n\n"

    # Бизнесы
    if assets["бизнесы"]:
        message += "🏢 <b>Бизнесы:</b>\n"
        for business in assets["бизнесы"]:
            message += f"  - {business[0]} (уровень {business[1]})\n"
        message += "\n"
    else:
        message += "🏢 <b>Бизнесы:</b> Нет\n\n"

    # Майнинг-ферма
    message += f"💰 <b>Майнинг-ферма:</b> {assets['майнинг-ферма']}\n\n"

    # Дом
    message += f"🏠 <b>Дом:</b> {assets['дом']}\n\n"

    # Машина
    message += f"🚗 <b>Машина:</b> {assets['машина']}\n\n"

    # Остров
    message += f"🏝 <b>Остров:</b> {assets['остров']}\n\n"

    # Яхта
    message += f"🛥 <b>Яхта:</b> {assets['яхта']}\n\n"

    # Самолет
    message += f"✈️ <b>Самолет:</b> {assets['самолет']}\n\n"

    # Одежда
    message += f"👕 <b>Одежда:</b> {assets['одежда']}\n\n"

    # Животное
    message += f"🐾 <b>Животное:</b> {assets['животное']}\n\n"

    # Девушка
    message += f"👩 <b>Девушка:</b> {assets['девушка']}\n\n"

    return message


async def handle_assets(message: types.Message):
    """
    Обработчик команды /имущество.
    """
    try:
        user_id = message.from_user.id

        # Получаем данные об имуществе
        assets = await get_user_assets(user_id)

        # Формируем сообщение
        message_text = await format_assets_message(assets)

        # Создаем список кнопок
        buttons = []

        # Кнопки для майнинг-фермы
        if assets["майнинг-ферма"] == "Нет":
            buttons.append(KeyboardButton(text="📋 Доступные фермы"))
        else:
            buttons.append(KeyboardButton(text="💰 Моя ферма"))

        # Кнопки для автомобиля
        if assets["машина"] == "Нет":
            buttons.append(KeyboardButton(text="🚗 Выбрать авто"))
        else:
            buttons.append(KeyboardButton(text="🚗 Продать авто"))

        # Кнопки для дома
        if assets["дом"] == "Нет":
            buttons.append(KeyboardButton(text="🏠 Выбрать дом"))
        else:
            buttons.append(KeyboardButton(text="🏠 Продать дом"))

        # Кнопки для самолета
        if assets["самолет"] == "Нет":
            buttons.append(KeyboardButton(text="✈️ Выбрать самолет"))
        else:
            buttons.append(KeyboardButton(text="✈️ Продать самолет"))

        # Кнопки для яхты
        if assets["яхта"] == "Нет":
            buttons.append(KeyboardButton(text="🛥️ Выбрать яхту"))
        else:
            buttons.append(KeyboardButton(text="🛥️ Продать яхту"))

        # Кнопки для острова
        if assets["остров"] == "Нет":
            buttons.append(KeyboardButton(text="🏝️ Выбрать остров"))
        else:
            buttons.append(KeyboardButton(text="🏝️ Продать остров"))

        # Кнопки для одежды
        if assets["одежда"] == "Нет":
            buttons.append(KeyboardButton(text="👕 Выбрать одежду"))
        else:
            buttons.append(KeyboardButton(text="👕 Продать одежду"))

        # Кнопка "Девушка", если она есть
        if assets["девушка"] != "Нет":
            buttons.append(KeyboardButton(text="👩 Девушка"))

        # Кнопки "Профиль" и "Помощь"
        buttons.append(KeyboardButton(text="👤 Профиль"))
        buttons.append(KeyboardButton(text="‼ Помощь"))

        # Разбиваем кнопки на пары
        paired_buttons = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

        # Создаем клавиатуру с кнопками
        keyboard = ReplyKeyboardMarkup(
            keyboard=paired_buttons,  # Передаем список пар кнопок
            resize_keyboard=True  # Кнопки будут автоматически подстраиваться под размер экрана
        )

        # Отправляем сообщение с клавиатурой
        await message.answer(message_text, parse_mode="HTML", reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Ошибка при получении имущества: {e}")
        await message.answer("⚠️ Произошла ошибка при получении данных об имуществе.")