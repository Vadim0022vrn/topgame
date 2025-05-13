RATE_LIMITS = {
    "default": {"limit": 5, "interval": 10},
    "/start": {"limit": 2, "interval": 60},
    "/daily": {"limit": 1, "interval": 86400},
    "/myref": {"limit": 3, "interval": 30}
}