GIRLS = {
    # Обычные девушки (1–30 уровни)
    1: {"name": "🪀 Надувная кукла", "level_required": 1, "monthly_cost": 100, "bonus": None},
    2: {"name": "🍻 Местная пьяница Светка", "level_required": 2, "monthly_cost": 200, "bonus": None},
    3: {"name": "💅 Селфи-королева ИнстаДиана", "level_required": 3, "monthly_cost": 300, "bonus": None},
    4: {"name": "🏓 Фитнес-тренер Настя", "level_required": 4, "monthly_cost": 400, "bonus": None},
    5: {"name": "🍰 Пекарь Алина", "level_required": 5, "monthly_cost": 500, "bonus": {"income": 0.01}},  # +1% к доходу
    6: {"name": "🐾 Любительница кошек Оля", "level_required": 6, "monthly_cost": 600, "bonus": {"experience": 0.02}},  # +2% к опыту
    7: {"name": "🎨 Художница Ксюша", "level_required": 7, "monthly_cost": 700, "bonus": {"experience": 0.02}},  # +2% к опыту
    8: {"name": "💃 Танцовщица Жанна", "level_required": 8, "monthly_cost": 800, "bonus": {"income": 0.03}},  # +3% к доходу
    9: {"name": "💼 Секретарь Лера", "level_required": 9, "monthly_cost": 900, "bonus": {"income": 0.03}},  # +3% к доходу
    10: {"name": "🎧 DJ Виктория", "level_required": 10, "monthly_cost": 1000, "bonus": {"income": 0.02}},  # +2% к доходу
    11: {"name": "🌊 Серферша Карина", "level_required": 11, "monthly_cost": 1100, "bonus": {"experience": 0.03}},  # +3% к опыту
    12: {"name": "🎯 Маркетолог Мира", "level_required": 12, "monthly_cost": 1200, "bonus": {"income": 0.04}},  # +4% к доходу
    13: {"name": "💄 Бьюти-блогер Мария", "level_required": 13, "monthly_cost": 1300, "bonus": {"income": 0.03}},  # +3% к доходу
    14: {"name": "🚀 Геймерша Саша", "level_required": 14, "monthly_cost": 1400, "bonus": {"experience": 0.04}},  # +4% к опыту
    15: {"name": "🧁 Кондитер Даша", "level_required": 15, "monthly_cost": 1500, "bonus": {"income": 0.05}},  # +5% к доходу
    16: {"name": "🎬 Актриса София", "level_required": 16, "monthly_cost": 1600, "bonus": {"experience": 0.05}},  # +5% к опыту
    17: {"name": "🏖 Путешественница Ира", "level_required": 17, "monthly_cost": 1700, "bonus": {"income": 0.03}},  # +3% к доходу
    18: {"name": "🔧 Механик Тина", "level_required": 18, "monthly_cost": 1800, "bonus": {"experience": 0.06}},  # +6% к опыту
    19: {"name": "🎲 Инвестор Кира", "level_required": 19, "monthly_cost": 1900, "bonus": {"income": 0.07}},  # +7% к доходу
    20: {"name": "💡 IT-специалист Ева", "level_required": 20, "monthly_cost": 2000, "bonus": {"experience": 0.08}},  # +8% к опыту
    21: {"name": "🏋 Фитоняшка Лина", "level_required": 21, "monthly_cost": 2100, "bonus": {"income": 0.09}},  # +9% к доходу
    22: {"name": "🍷 Сомелье Лана", "level_required": 22, "monthly_cost": 2200, "bonus": {"experience": 0.10}},  # +10% к опыту
    23: {"name": "🎹 Музыкантка Рита", "level_required": 23, "monthly_cost": 2300, "bonus": {"income": 0.11}},  # +11% к доходу
    24: {"name": "🏛 Адвокат Марта", "level_required": 24, "monthly_cost": 2400, "bonus": {"experience": 0.12}},  # +12% к опыту
    25: {"name": "🕶 Модель Виола", "level_required": 25, "monthly_cost": 2500, "bonus": {"income": 0.13}},  # +13% к доходу
    26: {"name": "🏢 Бизнес-леди Диана", "level_required": 26, "monthly_cost": 2600, "bonus": {"experience": 0.14}},  # +14% к опыту
    27: {"name": "💻 Фрилансер Ника", "level_required": 27, "monthly_cost": 2700, "bonus": {"income": 0.15}},  # +15% к доходу
    28: {"name": "🏟 Продюсер Лана", "level_required": 28, "monthly_cost": 2800, "bonus": {"experience": 0.16}},  # +16% к опыту
    29: {"name": "🏦 Финансист Элина", "level_required": 29, "monthly_cost": 2900, "bonus": {"income": 0.17}},  # +17% к доходу
    30: {"name": "👑 Принцесса Валерия", "level_required": 30, "monthly_cost": 3000, "bonus": {"experience": 0.20, "income": 0.10}},  # +20% к опыту и +10% к доходу

    # Донатные девушки (31–35 уровни)
    31: {"name": "🌟 Инфлюенсер Милана", "level_required": 31, "monthly_cost": 5000, "bonus": {"experience": 0.25, "income": 0.15}},  # +25% к опыту и +15% к доходу
    32: {"name": "💃 Поп-звезда Арина", "level_required": 32, "monthly_cost": 6000, "bonus": {"experience": 0.30, "income": 0.20}},  # +30% к опыту и +20% к доходу
    33: {"name": "🧬 Стартапер Кира", "level_required": 33, "monthly_cost": 7000, "bonus": {"experience": 0.35, "income": 0.25}},  # +35% к опыту и +25% к доходу
    34: {"name": "🛰 Техногуру Элла", "level_required": 34, "monthly_cost": 8000, "bonus": {"experience": 0.40, "income": 0.30}},  # +40% к опыту и +30% к доходу
    35: {"name": "👸 Королева Империи Аделина", "level_required": 35, "monthly_cost": 10000, "bonus": {"experience": 0.50, "income": 0.50}},  # +50% к опыту и +50% к доходу
}