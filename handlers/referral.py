import sqlite3
import asyncio
import logging
import mysql.connector
from aiogram import types
from config.config import API_TOKEN, MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
from utils.helpers import get_referral_link

async def handle_myref(message, user_id=None):
    try:
        user_id = user_id or message.from_user.id

        def sync_get_referral():
            connection = mysql.connector.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE
            )
            cursor = connection.cursor()
            cursor.execute(
                'SELECT referral_code FROM users WHERE user_id = %s', (user_id,))
            result = cursor.fetchone()
            connection.close()
            return result[0] if result else None

        referral_code = await asyncio.to_thread(sync_get_referral)

        if referral_code:
            await message.answer(f"🔗 Ваша ссылка:\n\n{get_referral_link(referral_code)}")
        else:
            await message.answer("⚠️ Не удалось найти вашу реферальную ссылку.")

    except Exception as e:
        logging.error(f"Ошибка получения ссылки: {str(e)}")
        await message.answer(f"⚠️ Ошибка получения ссылки: {str(e)}")
