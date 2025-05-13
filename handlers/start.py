import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
from config.config import API_TOKEN
from utils.helpers import generate_referral_code
from utils.database import execute_db_query  # Импорт функции для работы с БД
from handlers.profile import handle_profile
from handlers.referral import handle_myref
from handlers.earnings import handle_education_list
from handlers.help import handle_help
from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from config.level import add_experience  # Импорт функции для начисления опыта

# Настройка логирования
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Создаем экземпляр бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()


class StoryStates(StatesGroup):
    STEP_1 = State()
    STEP_2 = State()
    STEP_3 = State()
    STEP_4 = State()
    STEP_5 = State()
    STEP_6 = State()
    STEP_7 = State()
    STEP_FINAL = State()
    # Добавь столько шагов, сколько нужно

STORY_MESSAGES = [
    "🚀 Добро пожаловать!\n🔥 <b>Твоя история начинается здесь…</b>\n\n<b>🎩 Ты, {username} — сын миллиардера.</b>\nТвоя жизнь — это роскошные вечеринки 🎉, дорогие машины 🚗 и путешествия на частных самолётах ✈️. \nКаждый день — это праздник, где весь мир крутится вокруг тебя. \n\n"
    "Но на твой 25-й день рождения всё меняется.\n\n<b><i>❝Сын, я дал тебе всё — но теперь забираю. Если хочешь вернуть — добудь это сам. Только пройдя путь с нуля, ты поймёшь настоящую ценность успеха.❞</i></b>\n\n"
    "Проснувшись на следующее утро, ты обнаруживаешь себя в старой квартире на окраине города с <b>1000$</b> 💵 в кармане.\n\nБольше нет богатства, только шанс доказать свою истинную ценность...",

    "💼 <b>Первый шаг к новой жизни</b>\n\n💡 <b>Твоя первая работа — уборщик в кафе.</b>\n\nКаждый день — это борьба: \n\n✅ Грязные полы 🧼 и изнурительные смены ⏳.\n\n✅ Грубые клиенты 😠 и равнодушный начальник 😐.\n\nНо среди шума посуды и постоянной беготни ты начинаешь замечать главное — у каждого есть возможность подняться выше.\n\n"
    "🔹 Первая честно заработанная зарплата.\n🔹 Мысли о будущем и планы на успех.\n🔹 Понимание: здесь не место для тебя.\n\n<b>Ты решаешь действовать!</b>",


    "🚀 <b>Начало пути: работа, риски, первые деньги</b>\n\n🚗 <b>Собрав немного денег, ты получаешь новые возможности:</b>\n\n"
    "Переходишь работать <b>официантом</b> 🍽️ и <b>поваром</b> 👨‍🍳.\n\nПриобретаешь <b>первую машину</b> 🚗 — твой символ свободы.\n\nУчаствуешь в уличных гонках 🏁, рискуя всем ради крупного выигрыша 💰.\n\n"
    "Впереди — первые бизнес-идеи 💡 и рискованные сделки, но хватит ли смелости воплотить их в жизнь?",

    "🏢 <b>Собственный бизнес и первые инвестиции</b>\n\n"
    "🏪 <b>Ты открываешь свой первый бизнес — маленькое кафе или пекарню.</b>\nТеперь ты отвечаешь за всё:\n\n"
    "Борьба с конкурентами ⚔️.\n\nРасширение бизнеса 📈.\n\nПервые инвестиции в <b>майнинг-ферму</b> ⛏️ для пассивного дохода 💹.\n\n"
    "Однако успех привлекает внимание не только честных людей. Тебе предлагают быстрые деньги через сомнительные сделки. \n<b>Рискнёшь или пойдёшь честным путём?</b>",

    "⚔ <b>Кланы, битвы за влияние и новые горизонты</b>\n\n"
    "Ты становишься <b>заметной фигурой</b> в городе. Теперь игра идёт не только за деньги, но и за власть.\n\n"
    "🔥 <b>Тебе предлагают вступить в клан или создать свой:</b>\n\n"
    "🛡 <b>Защита и союзники или</b> ⚔ <b>борьба за территорию?</b>\n\n"
    "👊 <b>Противостояние группировкам или</b> 💼 <b>договорённости с ними?</b>\n\n"
    "🚀 <b>Расширение бизнеса</b> в другие города и даже страны.\n\nС каждым шагом твоя власть растёт, а с ней – <b>новые враги</b>.",

    "🌍 <b>От бизнеса к мировой экономике</b>\n\n"
    "Ты прошёл путь от уборщика до <b>влиятельного магната</b>. Теперь твоя цель — <b>мировая империя</b>!\n\n"
    "🏝 <b>Покупка островов</b> и строительство элитных курортов.\n\n"
    "🚀 <b>Инвестиции в технологии</b> и промышленный майнинг.\n\n"
    "🐉 <b>Легендарные питомцы</b>, способные менять ход битв.\n\n"
    "Но враги тоже не дремлют. Кто-то из прошлого готов сделать всё, чтобы <b>уничтожить</b> твою империю…",

    "🔥 <b>Что ждёт тебя в этой игре?</b>\n"
    "🌟 <b>Теперь перед тобой — весь мир:</b>\n\n"
    "<b>Уровни и опыт:</b> 📊 Чем больше ты работаешь, учишься и развиваешь бизнес, тем выше твой уровень. Новые уровни открывают доступ к более престижным работам, бизнесам и городам.\n\n"
    "<b>Активы:</b> 🏠 Покупай автомобили 🚗, дома 🏡, яхты 🛥️ и даже острова 🏝️. Каждый актив — это не только статус, но и новые возможности.\n\n"
    "<b>Кланы и войны:</b> ⚔️ Объединяйся с другими игроками или создавай собственный клан, чтобы бороться за контроль над территориями и ресурсами.\n\n"
    "<b>Питомцы:</b> 🐶 Пёс для охраны, 🐱 кот, приносящий удачу, или 🦅 экзотические питомцы с уникальными навыками — они станут твоими верными спутниками.\n\n"
    "<b>Майнинг и инвестиции:</b> ⛏️ Строй майнинг-фермы, вкладывай деньги в банк 🏦 или международные проекты 🌍, чтобы получать пассивный доход.\n\n"
    "💬 <b>Ты готов доказать, что способен заново построить империю? Начни путь прямо сейчас!</b> ✅",

    # Добавь столько сообщений, сколько нужно
]


# Асинхронная функция для регистрации пользователя
async def register_user(user_id, username, referral_code, referrer_id, registration_date):
    try:
        query = 'SELECT user_id FROM users WHERE user_id = %s'
        existing_user = await execute_db_query(query, (user_id,))
        
        if existing_user:
            logger.info(f"Пользователь {user_id} уже зарегистрирован.")
            return "Вы уже зарегистрированы."

        # Вставка нового пользователя
        if referrer_id:
            query = '''INSERT INTO users 
                       (user_id, username, referral_code, referrer_id, rank, last_daily, daily_streak, registration_date)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'''
            await execute_db_query(query, (user_id, username, referral_code, referrer_id, 1, None, 0, registration_date))
            
            # Увеличиваем счетчик рефералов у пользователя, который пригласил
            update_referrer_query = 'UPDATE users SET reffer = reffer + 1 WHERE user_id = %s'
            await execute_db_query(update_referrer_query, (referrer_id,))

            # Получаем текущее количество рефералов у пригласившего
            get_reffer_count_query = 'SELECT reffer FROM users WHERE user_id = %s'
            reffer_count_result = await execute_db_query(get_reffer_count_query, (referrer_id,))
            reffer_count = reffer_count_result[0][0] if reffer_count_result else 0

            # Начисляем бонусы за реферала
            base_bonus_money = 100  # Базовый бонус в деньгах
            base_bonus_experience = 50  # Базовый бонус в опыте
            multiplier = 1.5  # Множитель для каждого 3-го реферала

            # Рассчитываем множитель
            bonus_multiplier = multiplier ** (reffer_count // 3)

            # Начисляем деньги
            bonus_money = int(base_bonus_money * bonus_multiplier)
            update_balance_query = 'UPDATE users SET balance = balance + %s WHERE user_id = %s'
            await execute_db_query(update_balance_query, (bonus_money, referrer_id))

            # Начисляем опыт
            bonus_experience = int(base_bonus_experience * bonus_multiplier)
            await add_experience(referrer_id, bonus_experience)

            logger.info(f"Пользователь {user_id} зарегистрирован. Начислено {bonus_money} денег и {bonus_experience} опыта пользователю {referrer_id}.")
        else:
            query = '''INSERT INTO users 
                       (user_id, username, referral_code, rank, last_daily, daily_streak, registration_date)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)'''
            await execute_db_query(query, (user_id, username, referral_code, 1, None, 0, registration_date))

        logger.info(f"Пользователь {user_id} зарегистрирован успешно.")
        return None

    except Exception as e:
        logger.error(f"Ошибка при регистрации пользователя {user_id}: {str(e)}")
        return "⚠️ Произошла ошибка регистрации."
# Обработчик команды /start
@dp.message(Command("start"))
async def handle_start(message: types.Message, state: FSMContext):
    try:
        parts = message.text.split()
        args = " ".join(parts[1:]) if len(parts) > 1 else ""

        user_id = message.from_user.id
        username = message.from_user.username or ""
        registration_date = datetime.now().strftime("%Y-%m-%d")

        # Проверяем, зарегистрирован ли пользователь
        query = 'SELECT user_id FROM users WHERE user_id = %s'
        existing_user = await execute_db_query(query, (user_id,))

        if existing_user:
            # Сообщение для уже зарегистрированных пользователей
            welcome_text = (
                f"🎉 <b>С возвращением, {username}!</b>\n\n"
                "🔄 Готов продолжить свой путь к богатству и успеху? 💪\n"
                "🏆 Мир ждёт твоих достижений — покажи всем, кто здесь будущий миллиардер! 🚀"
            )
            await message.answer(welcome_text, reply_markup=get_main_menu_keyboard())
        else:
            # Регистрация нового пользователя
            referral_code = generate_referral_code()

            # Обработка реферального кода
            referrer_id = None
            if args:
                query = 'SELECT user_id FROM users WHERE referral_code = %s'
                result = await execute_db_query(query, (args,))
                if result:
                    referrer_id = result[0][0]  # Берем первый результат (user_id)
                else:
                    logger.info(f"Реферальный код {args} не найден в базе данных.")

            # Регистрируем пользователя
            await register_user(user_id, username, referral_code, referrer_id, registration_date)

            # Начинаем пошаговое отображение истории
            await state.set_state(StoryStates.STEP_1)
            await send_story_step(message, state, username)

    except Exception as e:
        logger.error(f"Ошибка при обработке команды /start: {str(e)}")
        await message.answer("⚠️ Произошла ошибка при запуске.")


async def send_story_step(message: types.Message, state: FSMContext, username: str):
    try:
        current_state = await state.get_state()

        # Определяем текущий шаг
        if current_state == StoryStates.STEP_1:
            step = 0
        elif current_state == StoryStates.STEP_2:
            step = 1
        elif current_state == StoryStates.STEP_3:
            step = 2
        elif current_state == StoryStates.STEP_4:
            step = 3
        elif current_state == StoryStates.STEP_5:
            step = 4
        elif current_state == StoryStates.STEP_6:
            step = 5
        elif current_state == StoryStates.STEP_7:
            step = 6
        elif current_state == StoryStates.STEP_FINAL:
            # Если это финальный шаг, показываем сообщение "Теперь ты готов начать игру!"
            await state.clear()
            await show_main_menu(message)
            return
        else:
            # Если состояние неизвестно, завершаем историю
            await state.clear()
            await show_main_menu(message)
            return

        # Отправляем сообщение с текущим шагом истории
        await message.answer(STORY_MESSAGES[step].format(username=username), reply_markup=get_next_button())

        # Переходим к следующему шагу
        if step + 1 < len(STORY_MESSAGES):
            next_state = getattr(StoryStates, f"STEP_{step + 2}")
        else:
            # Если история закончилась, переходим к финальному шагу
            next_state = StoryStates.STEP_FINAL

        await state.set_state(next_state)
    except Exception as e:
        logger.error(f"Ошибка в send_story_step: {e}")

# Функция для создания кнопки "Далее"
def get_next_button():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Далее", callback_data="next_story_step"))
    return builder.as_markup()

# Функция для создания основного меню
def get_main_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="📚 Обучения", callback_data="start_education_list"),
        InlineKeyboardButton(text="👤 Профиль", callback_data="start_профиль"),
        InlineKeyboardButton(text="🔗 Реферальная ссылка", callback_data="start_мойреф"),
        InlineKeyboardButton(text="‼ Помощь", callback_data="start_help")
    )
    builder.adjust(2)
    return builder.as_markup()

# Функция для отображения основного меню
async def show_main_menu(message: types.Message):
    await message.answer("<b>Отлично!</b>\n<b>Спасибо, что прочитал(а) вступление</b>\n\nТеперь ты готов(а) начать игру! \n<b>Выбери действие:</b>", reply_markup=get_main_menu_keyboard())



@dp.callback_query(lambda c: True)
async def handle_callback_query(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        # Подтверждаем нажатие кнопки
        await callback_query.answer()

        # Логируем нажатие
        callback_data = callback_query.data
        username = callback_query.from_user.username or "неизвестно"
        logger.info(f"Пользователь {username} (ID: {callback_query.from_user.id}) нажал на кнопку: {callback_data}")

        # Проверяем, что message существует
        if not callback_query.message:
            logger.error("callback_query.message отсутствует!")
            return

        # Обработка кнопки "Далее"
        if callback_data == "next_story_step":
            username = callback_query.from_user.username or ""
            await send_story_step(callback_query.message, state, username)
            return

        # Обработка других callback-запросов
        callback_handlers = {
            "start_education_list": handle_education_list,
            "start_профиль": handle_profile,
            "start_мойреф": handle_myref,
            "start_help": handle_help
        }

        if callback_data in callback_handlers:
            # ✅ Обрабатываем функцию handle_help отдельно, так как она ожидает один аргумент
            if callback_data == "start_help":
                await handle_help(callback_query.message)
            else:
                await callback_handlers[callback_data](callback_query.message, callback_query.from_user.id)
        else:
            logger.warning(f"Неизвестный callback_data: {callback_data}")

    except Exception as e:
        logger.error(f"Ошибка в обработчике callback_query: {e}")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
