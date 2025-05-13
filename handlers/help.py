import asyncio
import logging
from aiogram import types  # Добавь этот импорт
from aiogram.types import Message
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from handlers.profile import handle_profile
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from utils.database import execute_db_query


# Настройка логирования
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = Router()

async def handle_help(message: types.Message):
    help_text = (
        "🌟 <b>Добро пожаловать в игру!</b> 🌟\n\n"
        "Этот бот поможет тебе пройти путь от простого уборщика до легендарного миллиардера! 🚀\n\n"
        
        "📚 <b>Что ты можешь делать в игре:</b>\n\n"
        "1. <b>Проходить обучение</b> 🎓 — развивай свои навыки, чтобы открывать новые возможности для карьерного роста.\n"
        "2. <b>Покупать и улучшать бизнесы</b> 🏢 — создавай свою империю, улучшай бизнесы и зарабатывай деньги! 💰\n"
        "3. <b>Работать</b> 👷 — устраивайся на работу, чтобы зарабатывать и повышать свой уровень.\n"
        "4. <b>Инвестировать</b> 📈 — вкладывай деньги в банк или майнинг-фермы для пассивного дохода.\n"
        "5. <b>Покупать активы</b> 🚗🏠🛥️ — приобретай автомобили, дома, яхты и даже острова, чтобы улучшить свой статус.\n"
        "6. <b>Приглашать друзей</b> 👥 — используй реферальную ссылку, чтобы получать бонусы за приглашённых друзей.\n\n"
        
        "🔥 <b>Основные команды:</b>\n\n"
        "/start — начать игру или вернуться в главное меню 🎮\n"
        "/help — получить помощь и информацию о боте 📖\n"
        "/профиль — посмотреть свой профиль 👤\n"
        "/rank — узнать свой ранг 🏅\n"
        "/daily — получить ежедневный бонус 🎁\n"
        "/мойреф — получить реферальную ссылку 🔗\n\n"
        
        
        "🏢 <b>Бизнесы:</b>\n\n"
        "/mybiz — посмотреть свои бизнесы 🏢\n"
        "/biz — посмотреть доступные бизнесы 📊\n"
        "/buybiz — купить бизнес 💼\n"
        "/upbiz — улучшить бизнес ⬆️\n"
        "/sellbiz — продать бизнес 💸\n"
        "/collectbiz — собрать прибыль с бизнеса 💵\n\n"
        
        "👷 <b>Работа:</b>\n\n"
        "/avjobs — посмотреть доступные работы 📋\n"
        "/getjob — устроиться на работу 👔\n"
        "/myjob — посмотреть текущую работу 👷\n"
        "/collectjob — собрать доход с работы 💰\n"
        "/quitjob — уволиться с работы 🚪\n\n"
        
        "🏦 <b>Банк и инвестиции:</b>\n\n"
        "/bankdep — положить деньги в банк 💳\n"
        "/bankwith — снять деньги с банка 💵\n"
        "/invest1, /invest2, /invest3, /invest4, /invest5 — инвестировать в проекты 📈\n"
        "/claiminvest — забрать доход с инвестиций 💹\n\n"
        
        "🚗 <b>Автомобили:</b>\n\n"
        "/cars — посмотреть доступные автомобили 🚗\n"
        "/buycar — купить автомобиль 🛒\n"
        "/sellcar — продать автомобиль 💸\n\n"
        
        "🏠 <b>Недвижимость:</b>\n\n"
        "/houses — посмотреть доступное жилье 🏠\n"
        "/buyhouse — купить жилье 🛒\n"
        "/sellhouse — продать жилье 💸\n\n"
        
        "🛥️ <b>Яхты:</b>\n\n"
        "/yachts — посмотреть доступные яхты 🛥️\n"
        "/buyyachts — купить яхту 🛒\n"
        "/sellyachts — продать яхту 💸\n\n"

        "<b>Обратная связь:</b>\n"
        "/feedback 'сообщение'\n\n"
        "Мы оперативно ответим на ваш запрос.\n\n"

        
        "💡 <b>Совет:</b> Не забывай про ежедневные бонусы (/daily) и реферальную систему (/мойреф), чтобы быстрее расти! 💸\n\n"
        
        "🚀 <b>Вперёд к успеху! Удачи в игре!</b> 🚀"
    )
    
    # Создаем инлайн кнопку "Профиль"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")]
    ])

    # Отправляем сообщение с кнопкой
    await message.answer(help_text, parse_mode="HTML", reply_markup=keyboard)

async def handle_profile_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await handle_profile(callback_query.message, callback_query.from_user.id)


async def handle_feedback(message: types.Message):
    try:
        # Получаем текст сообщения пользователя
        user_message = message.text.replace("/feedback", "").strip()

        if not user_message:
            await message.answer("❌ Пожалуйста, напишите ваш вопрос после команды /feedback.")
            return

        user_id = message.from_user.id

        # Сохраняем тикет в базу данных
        await execute_db_query(
            "INSERT INTO tickets (user_id, message) VALUES (%s, %s)",
            (user_id, user_message)
        )

        await message.answer("✅ Ваш вопрос отправлен администраторам. Ожидайте ответа.")
        
    except Exception as e:
        logger.error(f"Ошибка при создании тикета: {e}")
        await message.answer("⚠️ Произошла ошибка при отправке вопроса. Попробуйте позже.")