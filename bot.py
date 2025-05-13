import logging
import asyncio
import mysql.connector
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.types import CallbackQuery, ReplyKeyboardRemove
from aiogram.client.default import DefaultBotProperties
from config.config import API_TOKEN, MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
from middlewares.rate_limiter import RateLimiterMiddleware
from utils.database import init_db, add_trainings_to_db, add_businesses_to_db, add_jobs_to_db, add_mining_farms_to_db
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# 🔧 Настройка логирования в файл log.log
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log.log",
    filemode="a"
)

logger = logging.getLogger(__name__)

# Инициализация
storage = MemoryStorage()
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)

dp.message.middleware(RateLimiterMiddleware())
dp.callback_query.middleware(RateLimiterMiddleware())

# Импорт обработчиков
from utils.database import init_db, add_trainings_to_db, add_businesses_to_db, add_jobs_to_db
from utils.background_tasks import check_completed_trainings, check_business_accumulation, check_job_accumulation, check_investments, check_level_up
from handlers.start import handle_start, handle_callback_query
from handlers.daily import handle_daily
from handlers.profile import handle_rank, handle_profile, handle_assets
from handlers.help import handle_help, handle_profile_callback, handle_feedback
from config.level import add_experience, calculate_level_progress
from handlers.work import show_available_jobs, handle_get_job, handle_collect_jobs, handle_promote_job, handle_my_job, get_next_job
from handlers.admin import (
    handle_setrank,
    handle_setbalance,
    handle_setlevel,
    handle_resetuser,
    handle_userinfo,
    handle_ban,
    handle_unban,
    handle_givebalance,
    handle_stats,
    handle_topusers,
    handle_addcurrency,
    handle_giveall,
    handle_mod,
    handle_banlist,
    handle_broadcast,
    handle_ticket_list,
    handle_reply_ticket,
    handle_close_ticket,
    handle_showlogs
)
from handlers.referral import handle_myref
from handlers.earnings import (
    handle_education_list,
    handle_start_education_input,
    handle_start_education,
    handle_my_businesses,
    handle_collect_income,
    handle_businesses,
    handle_buy_business,
    handle_upgrade_business,
    handle_buy_business_input,
    handle_sell_business
)
from config.assets import CARS, HOUSES, YACHTS, PLANES, ISLANDS
from config.businesses import BUSINESSES
from config.trainings import TRAININGS
from handlers.bank import (
    handle_deposit,
    handle_withdraw,
    handle_investment,
    handle_claim_investments,
    handle_bank,
    handle_collect_cashback,
    handle_investment_choice,
    handle_investment_amount,
    handle_invalid_amount,
    InvestmentState,
    handle_invests
)
from handlers.car import handle_cars, handle_buycar, handle_sellcar, handle_premium_cars
from handlers.house import handle_houses, handle_buyhouse, handle_sellhouse
from handlers.yachts import handle_yachts, handle_buyyacht, handle_sellyacht
from handlers.top import handle_top, handle_toplevel, handle_toprefs, handle_top_command
from handlers.planes import handle_planes, handle_buyplane, handle_sellplane
from handlers.islands import handle_islands, handle_buyisland, handle_sellisland
from handlers.girls import handle_my_girl, handle_break_up, handle_confirm_break_up, BreakUpStates
from handlers.clothes_handler import handle_clothes, handle_buy_clothes, handle_sell_clothes
from handlers.mining_handlers import handle_view_mining_farms, handle_buy_mining_farm_command, handle_buy_mining_farm, handle_sell_mining_farm, handle_my_mining_farm, handle_collect_mining_income


# Регистрация обработчиков с логированием выполнения команд
# 📜 Пользовательские команды
dp.message.register(handle_start, Command("start")) #старт/начать (регистрация)
dp.message.register(handle_daily, Command("daily")) #получить ежедневный бонус (в разработке)
dp.message.register(handle_rank, Command("rank")) #Проверить свой ранг
dp.message.register(handle_profile, Command("профиль")) #профиль
dp.message.register(handle_myref, Command("мойреф")) #Мой реферальный код
dp.message.register(handle_help, Command("help"))                   #помощь
dp.message.register(handle_assets, Command("assets"))   #Имущество
dp.message.register(handle_feedback, Command("feedback"))  #Обратная связь (оставить тикет)

dp.message.register(handle_education_list, Command("education_list"))  #доступные обучения
dp.message.register(handle_start_education, Command("startedu"))       #начать обучение

dp.message.register(handle_my_businesses, Command("mybiz"))    #мои бизнесы
dp.message.register(handle_collect_income, Command("collectbiz"))  #собрать прибыль с бизнеса
dp.message.register(handle_businesses, Command("biz"))      #доступные бизнесы
dp.message.register(handle_buy_business, Command("buybiz"))   #купить бизнес
dp.message.register(handle_upgrade_business, Command("upbiz")) #улучшить бизнес
dp.message.register(handle_sell_business, Command("sellbiz"))   #продать бизнес

dp.message.register(show_available_jobs, Command("avjobs"))          #доступные работы
dp.message.register(handle_get_job, Command("getjob"))             #устроиться на работу
dp.message.register(handle_collect_jobs, Command("collectjob"))  #собрать доход с работы
dp.message.register(handle_my_job, Command("myjob"))            #Моя работа
dp.message.register(handle_promote_job, Command("promotejob"))  #Повысить уровень работы

dp.message.register(handle_deposit, Command("bankdep"))          #положить в банк
dp.message.register(handle_withdraw, Command("bankwith"))          #снять с банка
dp.message.register(handle_investment, Command("invest1", "invest2", "invest3", "invest4", "invest5"))  # инвестиции
dp.message.register(handle_claim_investments, Command("claiminvest"))  # забрать инвестиции
dp.message.register(handle_bank, Command("bank"))                      #Твой профиль банка
dp.message.register(handle_collect_cashback, Command("collcash"))          #Собрать кэшбек
dp.message.register(handle_invests, Command("invests"))                 #Доступные инвестиции

dp.message.register(handle_cars, Command("cars"))  #Список доступных авто
dp.message.register(handle_buycar, Command("buycar"))    #Купить авто
dp.message.register(handle_sellcar, Command("sellcar"))  #Продать авто
dp.message.register(handle_premium_cars, Command("premcar")) #Список донат авто

dp.message.register(handle_houses, Command("houses"))  #Список доступного жилья
dp.message.register(handle_buyhouse, Command("buyhouse"))    #Купить жилье
dp.message.register(handle_sellhouse, Command("sellhouse"))  #Продать жилье

dp.message.register(handle_yachts, Command("yachts"))  #Список доступных яхт
dp.message.register(handle_buyyacht, Command("buyyachts"))    #Купить яхту
dp.message.register(handle_sellyacht, Command("sellyachts"))  #Продать яхту

dp.message.register(handle_top, Command("top"))  #Топ игроков по балансу
dp.message.register(handle_toplevel, Command("toplevel")) #Топ по уровню
dp.message.register(handle_toprefs, Command("toprefs")) #Топ по реффералам
dp.message.register(handle_top_command, Command("tops")) #Информация по топам

dp.message.register(handle_planes, Command("planes")) #Список доступных самолетов
dp.message.register(handle_buyplane, Command("buyplane")) #Купить самолет
dp.message.register(handle_sellplane, Command("sellplane")) #Продать самолет

dp.message.register(handle_islands, Command("islands")) #Список доступных островов
dp.message.register(handle_buyisland, Command("buyisland")) #Купить остров
dp.message.register(handle_sellisland, Command("sellisland")) #Продать остров

dp.message.register(handle_my_girl, Command("mygirl"))  # Просмотр своей девшуки

dp.message.register(handle_clothes, Command("clothes")) #Список доступных одежд
dp.message.register(handle_sell_clothes, Command("sellcloth")) #Купить одежду
dp.message.register(handle_buy_clothes, Command("buycloth"))   #Продать одежду

dp.message.register(handle_view_mining_farms, Command("mining")) # Доступные майнинг-фермы
dp.message.register(handle_buy_mining_farm_command, Command("buyminig")) # Купить ферму
dp.message.register(handle_sell_mining_farm, Command("sellmining"))    # Продать ферму
dp.message.register(handle_my_mining_farm, Command("mymining"))      # Моя ферма
dp.message.register(handle_collect_mining_income, Command("collmining"))  # Собрать доход с фермы


# 🛡 Административные команды
dp.message.register(handle_setrank, Command("setrank"))     # Установить ранг
dp.message.register(handle_setbalance, Command("setbalance"))# Установить баланс
dp.message.register(handle_setlevel, Command("setlevel"))  # Установить уровень
dp.message.register(handle_resetuser, Command("resetuser"))# Обнулить игрока
dp.message.register(handle_userinfo, Command("userinfo"))  # Информация об игроке
dp.message.register(handle_ban, Command("ban"))            # Бан
dp.message.register(handle_unban, Command("unban"))        # Разбан
dp.message.register(handle_givebalance, Command("givebalance"))   # Выдать денег
dp.message.register(handle_giveall, Command("giveall"))    #  Выдать денег всем
dp.message.register(handle_stats, Command("stats"))        # Статистика бота
dp.message.register(handle_topusers, Command("topusers"))   # Топ 10 игроков
dp.message.register(handle_addcurrency, Command("addcurrency")) # Выдать определенную валюту
dp.message.register(handle_mod, Command("mod"))          # Выдать модератора
dp.message.register(handle_banlist, Command("banlist"))    # Банлист
dp.message.register(handle_showlogs, Command("showlogs"))     # Вывести последние логи
dp.message.register(handle_broadcast, Command("broadcast"))    # Сообщение всем игрокам
dp.message.register(handle_ticket_list, Command("ticketlist"))  # Посмотреть тикеты
dp.message.register(handle_reply_ticket, Command("replyticket"))# Ответить на тикет
dp.message.register(handle_close_ticket, Command("closeticket"))# Закрыть тикет (если без ответа)

dp.message.register(handle_investment_choice, lambda message: message.text in ["Инвестиция 1", "Инвестиция 2", "Инвестиция 3", "Инвестиция 4", "Инвестиция 5"])
dp.message.register(handle_investment_amount, InvestmentState.waiting_for_amount, lambda message: message.text.isdigit())
dp.message.register(handle_invalid_amount, InvestmentState.waiting_for_amount)
dp.message.register(handle_start_education_input, lambda message: message.text.isdigit())
dp.message.register(handle_buy_business_input, lambda message: message.text.startswith("b_"))

dp.callback_query.register(handle_profile_callback, lambda c: c.data == "profile")
dp.callback_query.register(handle_callback_query)

@dp.message(lambda message: message.text == "🛒 Купить ферму")
async def handle_buy_mining_farm_prompt(message: types.Message):
    await message.answer(
        "Введите ID фермы в формате <code>mining_номер</code> (например, mining_2):",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()  # Убираем клавиатуру
    )

@dp.message(lambda message: message.text.startswith("mining_"))
async def handle_buy_mining_farm_input(message: types.Message, state: FSMContext):
    try:
        # Извлекаем ID фермы из сообщения
        farm_id_str = message.text.split("_")[1]  # Разделяем текст по "_" и берем вторую часть
        farm_id = int(farm_id_str)  # Преобразуем в число

        # Вызываем обработчик покупки фермы
        await handle_buy_mining_farm(message, farm_id)

    except (IndexError, ValueError):
        # Если формат неправильный (например, нет "_" или ID не число)
        await message.answer("❌ Неверный формат. Используйте: mining_номер (например, mining_2)")

    except Exception as e:
        logger.error(f"Ошибка при покупке фермы: {e}")
        await message.answer("⚠️ Произошла ошибка при покупке фермы.")

    # Возвращаем пользователя в список ферм
    await handle_view_mining_farms(message, state)  # Передаем state

@dp.message(lambda message: message.text == "📋 Доступные фермы")
async def handle_view_mining_farmsbutton(message: types.Message, state: FSMContext):
    await handle_view_mining_farms(message, state)  # Передаем state

@dp.message(lambda message: message.text == "👕 Купить одежду")
async def handle_buy_clothes_prompt(message: types.Message):
    await message.answer(
        "Введите ID одежды в формате <code>clothes_номер</code> (например, clothes_1):",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(lambda message: message.text.startswith("clothes_"))
async def handle_buy_clothes_input(message: types.Message):
    try:
        # Извлекаем ID одежды из сообщения
        clothes_id_str = message.text.split("_")[1]  # Разделяем текст по "_" и берем вторую часть
        clothes_id = int(clothes_id_str)  # Преобразуем в число

        # Вызываем обработчик покупки одежды
        await handle_buy_clothes(message, clothes_id)

    except (IndexError, ValueError):
        # Если формат неправильный (например, нет "_" или ID не число)
        await message.answer("❌ Неверный формат. Используйте: clothes_номер (например, clothes_1)")

        # Возвращаем пользователя в раздел доступной одежды
        await handle_clothes(message)

    except Exception as e:
        logger.error(f"Ошибка при покупке одежды: {e}")
        await message.answer("⚠️ Произошла ошибка при покупке одежды.")

        # Возвращаем пользователя в раздел доступной одежды
        await handle_clothes(message)

@dp.message(lambda message: message.text == "💰 Продать ферму")
async def handle_sell_mining_farmbutton(message: types.Message):
    await handle_sell_mining_farm(message)

@dp.message(lambda message: message.text == "💰 Собрать доход")
async def handle_collect_mining_incomebutton(message: types.Message):
    await handle_collect_mining_income(message)

@dp.message(lambda message: message.text == "💰 Моя ферма")
async def handle_my_mining_farmbutton(message: types.Message):
    await handle_my_mining_farm(message)

# Обработчик для кнопки "👕 Продать одежду"
@dp.message(lambda message: message.text == "👕 Продать одежду")
async def handle_sell_clothes_button(message: types.Message):
    await handle_sell_clothes(message)

# Обработчик для кнопки "👕 Продать одежду"
@dp.message(lambda message: message.text == "👕 Выбрать одежду")
async def handle_clothes_button(message: types.Message):
    await handle_clothes(message)

@dp.message(lambda message: message.text == "🏢 Купить бизнес")
async def handle_buy_business_prompt(message: types.Message):
    await message.answer(
        "Введите ID бизнеса в формате <code>b_номер</code> (например, b_1):",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(lambda message: message.text == "🚗 Купить авто")
async def handle_buy_car_prompt(message: types.Message):
    await message.answer(
        "Введите ID автомобиля в формате <code>car_номер</code> (например, car_1):",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(lambda message: message.text.startswith("car_"))
async def handle_buy_car_input(message: types.Message):
    try:
        # Извлекаем ID автомобиля из сообщения
        car_id_str = message.text.split("_")[1]  # Разделяем текст по "_" и берем вторую часть
        car_id = int(car_id_str)  # Преобразуем в число

        # Вызываем обработчик покупки автомобиля
        await handle_buycar(message, car_id)
    except (IndexError, ValueError):
        # Если формат неправильный (например, нет "_" или ID не число)
        await message.answer("❌ Неверный формат. Используйте: car_номер (например, car_1)")
    except Exception as e:
        logger.error(f"Ошибка при покупке автомобиля: {e}")
        await message.answer("⚠️ Произошла ошибка при покупке автомобиля.")

@dp.message(lambda message: message.text == "🏠 Купить дом")
async def handle_buy_house_prompt(message: types.Message):
    await message.answer(
        "Введите ID дома в формате <code>house_номер</code> (например, house_1):",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(lambda message: message.text.startswith("house_"))
async def handle_buy_house_input(message: types.Message):
    try:
        house_id_str = message.text.split("_")[1]  # Извлекаем ID дома
        house_id = int(house_id_str)  # Преобразуем в число
        await handle_buyhouse(message, house_id)  # Вызываем обработчик покупки дома
    except (IndexError, ValueError):
        await message.answer("❌ Неверный формат. Используйте: house_номер (например, house_1)")
    except Exception as e:
        logger.error(f"Ошибка при покупке дома: {e}")
        await message.answer("⚠️ Произошла ошибка при покупке дома.")

@dp.message(lambda message: message.text == "🏝 Купить остров")
async def handle_buy_island_prompt(message: types.Message):
    await message.answer(
        "Введите ID острова в формате <code>island_номер</code> (например, island_1):",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(lambda message: message.text.startswith("island_"))
async def handle_buy_island_input(message: types.Message):
    try:
        island_id_str = message.text.split("_")[1]  # Извлекаем ID острова
        island_id = int(island_id_str)  # Преобразуем в число
        await handle_buyisland(message, island_id)  # Вызываем обработчик покупки острова
    except (IndexError, ValueError):
        await message.answer("❌ Неверный формат. Используйте: island_номер (например, island_1)")
    except Exception as e:
        logger.error(f"Ошибка при покупке острова: {e}")
        await message.answer("⚠️ Произошла ошибка при покупке острова.")

@dp.message(lambda message: message.text == "✈️ Купить самолет")
async def handle_buy_plane_prompt(message: types.Message):
    await message.answer(
        "Введите ID самолета в формате <code>plane_номер</code> (например, plane_1):",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(lambda message: message.text.startswith("plane_"))
async def handle_buy_plane_input(message: types.Message):
    try:
        plane_id_str = message.text.split("_")[1]  # Извлекаем ID самолета
        plane_id = int(plane_id_str)  # Преобразуем в число
        await handle_buyplane(message, plane_id)  # Вызываем обработчик покупки самолета
    except (IndexError, ValueError):
        await message.answer("❌ Неверный формат. Используйте: plane_номер (например, plane_1)")
    except Exception as e:
        logger.error(f"Ошибка при покупке самолета: {e}")
        await message.answer("⚠️ Произошла ошибка при покупке самолета.")

@dp.message(lambda message: message.text == "🚤 Купить яхту")
async def handle_buy_yacht_prompt(message: types.Message):
    await message.answer(
        "Введите ID яхты в формате <code>yacht_номер</code> (например, yacht_1):",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(lambda message: message.text.startswith("yacht_"))
async def handle_buy_yacht_input(message: types.Message):
    try:
        yacht_id_str = message.text.split("_")[1]  # Извлекаем ID яхты
        yacht_id = int(yacht_id_str)  # Преобразуем в число
        await handle_buyyacht(message, yacht_id)  # Вызываем обработчик покупки яхты
    except (IndexError, ValueError):
        await message.answer("❌ Неверный формат. Используйте: yacht_номер (например, yacht_1)")
    except Exception as e:
        logger.error(f"Ошибка при покупке яхты: {e}")
        await message.answer("⚠️ Произошла ошибка при покупке яхты.")



@dp.message(lambda message: message.text == "💼 Устроиться на работу")
async def handle_get_job_button(message: types.Message):
    try:
        user_id = message.from_user.id

        # Получаем следующую доступную работу (id = 1 для устройства на работу)
        job_id = 1

        # Вызываем команду /getjob с ID работы
        await handle_get_job(message, job_id)
    except Exception as e:
        logger.error(f"Ошибка при обработке кнопки 'Устроиться на работу': {e}")
        await message.answer("⚠️ Произошла ошибка при устройстве на работу.")

dp.message.register(handle_break_up, lambda message: message.text == "💔 Бросить девушку")
dp.message.register(handle_confirm_break_up, BreakUpStates.confirm_break_up)
dp.message.register(handle_my_girl, lambda message: message.text == "👩 Девушка")

@dp.message(lambda message: message.text == "🏆 ТОПы")
async def handle_top_command_button(message: types.Message):
    await handle_top_command(message)

@dp.message(lambda message: message.text == "🏆 ТОП богачей")
async def handle_top_rich_button(message: types.Message):
    await handle_top(message)

@dp.message(lambda message: message.text == "🎯 ТОП уровней")
async def handle_top_level_button(message: types.Message):
    await handle_toplevel(message)

@dp.message(lambda message: message.text == "👥 ТОП рефералов")
async def handle_top_refs_button(message: types.Message):
    await handle_toprefs(message)

# Повышение
@dp.message(lambda message: message.text == "⬆️ Повышение")
async def handle_promote_job_button(message: types.Message):
    await handle_promote_job(message)

# Обработчик для кнопки "🚗 Выбрать авто"
@dp.message(lambda message: message.text == "🚗 Выбрать авто")
async def handle_choose_car(message: types.Message):
    await handle_cars(message)

# Обработчик для кнопки "🚗 Продать авто"
@dp.message(lambda message: message.text == "🚗 Продать авто")
async def handle_sell_car(message: types.Message):
    await handle_sellcar(message)

# Обработчик для кнопки "🏠 Выбрать дом"
@dp.message(lambda message: message.text == "🏠 Выбрать дом")
async def handle_choose_house(message: types.Message):
    await handle_houses(message)

# Обработчик для кнопки "🏠 Продать дом"
@dp.message(lambda message: message.text == "🏠 Продать дом")
async def handle_sell_house(message: types.Message):
    await handle_sellhouse(message)

# Обработчик для кнопки "✈️ Выбрать самолет"
@dp.message(lambda message: message.text == "✈️ Выбрать самолет")
async def handle_choose_plane(message: types.Message):
    await handle_planes(message)

# Обработчик для кнопки "✈️ Продать самолет"
@dp.message(lambda message: message.text == "✈️ Продать самолет")
async def handle_sell_plane(message: types.Message):
    await handle_sellplane(message)

# Обработчик для кнопки "🛥️ Выбрать яхту"
@dp.message(lambda message: message.text == "🛥️ Выбрать яхту")
async def handle_choose_yacht(message: types.Message):
    await handle_yachts(message)

# Обработчик для кнопки "🛥️ Продать яхту"
@dp.message(lambda message: message.text == "🛥️ Продать яхту")
async def handle_sell_yacht(message: types.Message):
    await handle_sellyacht(message)

# Обработчик для кнопки "🏝️ Выбрать остров"
@dp.message(lambda message: message.text == "🏝️ Выбрать остров")
async def handle_choose_island(message: types.Message):
    await handle_islands(message)

# Обработчик для кнопки "🏝️ Продать остров"
@dp.message(lambda message: message.text == "🏝️ Продать остров")
async def handle_sell_island(message: types.Message):
    await handle_sellisland(message)

@dp.message(lambda message: message.text == "💸 Продать бизнес")
async def handle_sell_business_button(message: types.Message):
    await handle_sell_business(message)

@dp.message(lambda message: message.text == "⬆️ Улучшить бизнес")
async def handle_upgrade_businessbutton(message: types.Message):
    await handle_upgrade_business(message)

@dp.message(lambda message: message.text == "💰 Собрать прибыль")
async def handle_collect_income_button(message: types.Message):
    await handle_collect_income(message)

@dp.message(lambda message: message.text == "🏢 Доступный бизнес")
async def handle_businesses_button(message: types.Message):
    await handle_businesses(message)

@dp.message(lambda message: message.text == "🏠 Имущество")
async def handle_assets_button(message: types.Message):
    await handle_assets(message)

@dp.message(lambda message: message.text == "‼ Помощь")
async def handle_help_button(message: types.Message):
    await handle_help(message)

@dp.message(lambda message: message.text == "📚 Пройти обучение")
async def handle_start_education_prompt(message: types.Message):
    await message.answer("Введите ID обучения, которое хотите пройти:", reply_markup=ReplyKeyboardRemove())

@dp.message(lambda message: message.text == "📈 Инвестиции")
async def handle_invests1(message: types.Message):
    await handle_invests(message)

# Обработчик для кнопки "Инвестиция 1"
@dp.message(lambda message: message.text == "Инвестиция 1")
async def handle_invest1_button(message: types.Message):
    await message.answer("Вы выбрали Инвестицию 1. Введите сумму для инвестиции:")

# Обработчик для кнопки "Инвестиция 2"
@dp.message(lambda message: message.text == "Инвестиция 2")
async def handle_invest2_button(message: types.Message):
    await message.answer("Вы выбрали Инвестицию 2. Введите сумму для инвестиции:")

# Обработчик для кнопки "Инвестиция 3"
@dp.message(lambda message: message.text == "Инвестиция 3")
async def handle_invest3_button(message: types.Message):
    await message.answer("Вы выбрали Инвестицию 3. Введите сумму для инвестиции:")

# Обработчик для кнопки "Инвестиция 4"
@dp.message(lambda message: message.text == "Инвестиция 4")
async def handle_invest4_button(message: types.Message):
    await message.answer("Вы выбрали Инвестицию 4. Введите сумму для инвестиции:")

# Обработчик для кнопки "Инвестиция 5"
@dp.message(lambda message: message.text == "Инвестиция 5")
async def handle_invest5_button(message: types.Message):
    await message.answer("Вы выбрали Инвестицию 5. Введите сумму для инвестиции:")

@dp.message(lambda message: message.text == "🏦 Банк")
async def handle_bank_button(message: types.Message):
    await handle_bank(message)  # Вызов обработчика команды /bank

@dp.message(lambda message: message.text == "💳 Собрать кэшбек")
async def handle_collect_cashback_button(message: types.Message):
    await handle_collect_cashback(message)

@dp.message(lambda message: message.text == "⛔ Уволиться с работы")
async def handle_quit_job1(message: types.Message):
    await handle_quit_job(message)

@dp.message(lambda message: message.text == "💼 Работа")
async def handle_my_job1(message: types.Message):
    await handle_my_job(message)

@dp.message(lambda message: message.text == "💵 Собрать зарплату")
async def handle_collect_jobs1(message: types.Message):
    await handle_collect_jobs(message)

@dp.message(lambda message: message.text == "👤 Профиль")
async def handle_profile1(message: types.Message):
    await handle_profile(message)

@dp.message(lambda message: message.text == "📖 Список обучений")
async def handle_education_list1(message: types.Message):
    await handle_education_list(message)

@dp.message(lambda message: message.text == "🏢 Бизнес")
async def handle_my_businesses1(message: types.Message):
    await handle_my_businesses(message)

@dp.message(lambda message: message.text == "🛠️ Доступные работы")
async def show_available_jobs1(message: types.Message):
    await show_available_jobs(message)

@dp.message(lambda message: message.text == "📩 Пригласить друзей")
async def handle_myref1(message: types.Message):
    await handle_myref(message)

@dp.message(lambda message: message.text == "💰 Забрать бонус")
async def handle_daily1(message: types.Message):
    await handle_daily(message)

@dp.message(lambda message: message.text == "🔙 Назад")
async def handle_back_wrapper(message: types.Message, state: FSMContext):
    await message.answer("Возвращаемся в главное меню...", reply_markup=ReplyKeyboardRemove())
    await handle_start(message, state)  # Передаем state






logger.info("✅ Все обработчики успешно зарегистрированы.")

@dp.message()
async def log_all_messages(message: types.Message):
    """Логирует все входящие сообщения пользователей."""
    logger.info(f"📩 Получена команда: {message.text} от пользователя: {message.from_user.id}")

async def on_startup():
    """Действия при запуске бота."""
    await init_db()  # Создание таблиц
    logger.info("🔄 Добавление данных о тренингах...")
    await add_trainings_to_db()  # Заполнение таблицы education
    logger.info("🔄 Добавление данных о работах...")
    await add_jobs_to_db()  # Заполнение таблицы jobs
    logger.info("🔄 Добавление данных о бизнесах...")
    await add_businesses_to_db()  # Заполнение таблицы businesses
    logger.info("🔄 Добавление данных о майнинг-фермах...")
    await add_mining_farms_to_db()  # Заполнение таблицы mining_farms
    logger.info("🚀 База данных инициализирована и заполнена данными.")

async def on_shutdown():
    """Действия при завершении работы."""
    logger.info("🔒 Завершение работы...")

    # Отменяем все фоновые задачи
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

    await bot.session.close()
    logger.info("🛑 Бот остановлен.")

async def main():
    """Основная функция."""
    try:
        await on_startup()
        # Запуск фоновой задачи для проверки завершения обучений
        asyncio.create_task(check_completed_trainings(bot))
        asyncio.create_task(check_business_accumulation(bot))
        asyncio.create_task(check_job_accumulation(bot))
        asyncio.create_task(check_investments(bot))
        asyncio.create_task(check_level_up(bot))

        logger.info("🚀 Бот начал polling.")
        await dp.start_polling(bot, skip_updates=True)
    except asyncio.CancelledError:
        logger.warning("⚠️ Polling был прерван.")
    finally:
        await on_shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Работа прервана пользователем.")