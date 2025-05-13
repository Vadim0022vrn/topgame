import string
import random
from cachetools import TTLCache
from config.config import BOT_USERNAME

USER_CACHE = TTLCache(maxsize=1000, ttl=300)
REFERRAL_CACHE = TTLCache(maxsize=500, ttl=600)

def generate_referral_code(length=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def get_referral_link(code: str) -> str:
    return f"https://t.me/{BOT_USERNAME}?start={code}"
