from aiogram import types
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.dispatcher.event.bases import SkipHandler  # Используем SkipHandler вместо StopPropagation
from datetime import datetime
from collections import defaultdict
from config.rate_limits import RATE_LIMITS


class RateLimiterMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.user_data = defaultdict(lambda: defaultdict(lambda: {
            "count": 0,
            "last_update": datetime.min
        }))

    async def __call__(self, handler, event, data: dict):
        user_id = None
        cmd = None

        # 🔹 Обработка текстовых сообщений
        if isinstance(event, types.Message):
            if not event.text:
                return await handler(event, data)  # Пропускаем, если текста нет
            user_id = event.from_user.id
            cmd = event.text.split()[0]  # Получаем команду из текста сообщения

        # 🔹 Обработка CallbackQuery
        elif isinstance(event, types.CallbackQuery):
            if not event.data:
                return await handler(event, data)  # Пропускаем, если нет callback data
            user_id = event.from_user.id
            cmd = event.data  # Используем callback_data в качестве команды

        # Если событие не подходит, пропускаем
        if not user_id or not cmd:
            return await handler(event, data)

        # 🔒 Проверяем, что команда начинается с "/" для сообщений
        if isinstance(event, types.Message) and not cmd.startswith("/"):
            return await handler(event, data)

        # 🔧 Настройка лимитов
        limit_config = RATE_LIMITS.get(cmd, RATE_LIMITS["default"])
        limit = limit_config["limit"]
        interval = limit_config["interval"]

        now = datetime.now()
        user_entry = self.user_data[user_id][cmd]

        # 🔄 Сброс счетчика, если интервал истек
        if (now - user_entry["last_update"]).total_seconds() > interval:
            user_entry["count"] = 0
            user_entry["last_update"] = now

        # 🚫 Проверка превышения лимита
        if user_entry["count"] >= limit:
            warning_text = (
                f"⚠️ Слишком много запросов!\n"
                f"Лимит: {limit} раз(а) в {interval} секунд."
            )
            if isinstance(event, types.Message):
                await event.answer(warning_text)
            elif isinstance(event, types.CallbackQuery):
                await event.answer(warning_text, show_alert=True)

            raise SkipHandler()  # ⛔ Останавливаем дальнейшую обработку

        user_entry["count"] += 1
        return await handler(event, data)
