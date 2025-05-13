JOBS = {
    # 🍽 Сфера: Ресторанный бизнес (1–10)
    1: {
        "name": "🧹 Уборщик в кафе",
        "description": "Работа уборщиком в кафе или магазине.",
        "income": 50,
        "required_level": 1,
        "required_education_id": None,
        "required_car_id": None,  # Автомобиль не требуется
        "required_house_id": None,  # Дом не требуется
        "required_city_id": 1  # Требуется город с ID 1
    },
    2: {
        "name": "🍽 Официант",
        "description": "Работа официантом в ресторане.",
        "income": 100,
        "required_level": 2,
        "required_education_id": None,
        "required_car_id": None,
        "required_house_id": None,
        "required_city_id": 1
    },
    3: {
        "name": "🍳 Повар на кухне",
        "description": "Работа поваром на кухне ресторана.",
        "income": 200,
        "required_level": 3,
        "required_education_id": 1,
        "required_car_id": 2,
        "required_house_id": None,
        "required_city_id": 1
    },
    4: {
        "name": "🧾 Кассир ресторана",
        "description": "Работа кассиром в ресторане.",
        "income": 400,
        "required_level": 4,
        "required_education_id": 2,
        "required_car_id": 2,
        "required_house_id": 2,
        "required_city_id": 1
    },
    5: {
        "name": "🛒 Менеджер по закупкам",
        "description": "Работа менеджером по закупкам в ресторане.",
        "income": 700,
        "required_level": 5,
        "required_education_id": 3,
        "required_car_id": 3,  # Требуется автомобиль с ID 1
        "required_house_id": 3,
        "required_city_id": 1
    },
    6: {
        "name": "🏬 Администратор смены",
        "description": "Работа администратором смены в ресторане.",
        "income": 1100,
        "required_level": 6,
        "required_education_id": 4,
        "required_car_id": 4,
        "required_house_id": 4,  # Требуется дом с ID 1
        "required_city_id": 1
    },
    7: {
        "name": "🎭 Менеджер по мероприятиям",
        "description": "Работа менеджером по мероприятиям в ресторане.",
        "income": 700,
        "required_level": 7,
        "required_education_id": 7,
        "required_car_id": 2,  # Требуется автомобиль с ID 2
        "required_house_id": 1,
        "required_city_id": 1
    },
    8: {
        "name": "🏨 Управляющий рестораном",
        "description": "Работа управляющим рестораном.",
        "income": 800,
        "required_level": 8,
        "required_education_id": 8,
        "required_car_id": 2,
        "required_house_id": 2,  # Требуется дом с ID 2
        "required_city_id": 1
    },
    9: {
        "name": "💼 Директор ресторана",
        "description": "Работа директором ресторана.",
        "income": 900,
        "required_level": 9,
        "required_education_id": 9,
        "required_car_id": 3,  # Требуется автомобиль с ID 3
        "required_house_id": 2,
        "required_city_id": 1
    },
    10: {
        "name": "👑 Владелец ресторана",
        "description": "Работа владельцем ресторана.",
        "income": 1000,
        "required_level": 10,
        "required_education_id": 10,
        "required_car_id": 3,
        "required_house_id": 3,  # Требуется дом с ID 3
        "required_city_id": 1
    },

    # 🏢 Сфера: Управление сетями ресторанов (11–20)
    11: {
        "name": "🏛 Генеральный директор нескольких ресторанов",
        "description": "Работа генеральным директором нескольких ресторанов.",
        "income": 1100,
        "required_level": 11,
        "required_education_id": 11,
        "required_car_id": 4,
        "required_house_id": 3,
        "required_city_id": 2  # Требуется город с ID 2
    },
    12: {
        "name": "🏗 Руководитель отдела развития ресторанной сети",
        "description": "Работа руководителем отдела развития ресторанной сети.",
        "income": 1200,
        "required_level": 12,
        "required_education_id": 11,
        "required_car_id": 4,
        "required_house_id": 4,
        "required_city_id": 2
    },
    13: {
        "name": "📊 Директор по маркетингу ресторанной сети",
        "description": "Работа директором по маркетингу в сети ресторанов.",
        "income": 1200,
        "required_level": 12,
        "required_education_id": 11,
        "required_car_id": 5,  # Требуется автомобиль с ID 5
        "required_house_id": 5,  # Требуется дом с ID 5
        "required_city_id": 2  # Требуется город с ID 2
    },
    14: {
        "name": "💰 Финансовый директор сети ресторанов",
        "description": "Работа финансовым директором в сети ресторанов.",
        "income": 1300,
        "required_level": 13,
        "required_education_id": 11,
        "required_car_id": 5,
        "required_house_id": 5,
        "required_city_id": 2
    },
    15: {
        "name": "🏙 Директор по операционным вопросам сети в городе",
        "description": "Работа директором по операционным вопросам в городе.",
        "income": 1400,
        "required_level": 14,
        "required_education_id": 11,
        "required_car_id": 6,  # Требуется автомобиль с ID 6
        "required_house_id": 6,  # Требуется дом с ID 6
        "required_city_id": 2
    },
    16: {
        "name": "🏘 Региональный управляющий сетью ресторанов",
        "description": "Работа региональным управляющим в сети ресторанов.",
        "income": 1500,
        "required_level": 15,
        "required_education_id": 11,
        "required_car_id": 6,
        "required_house_id": 6,
        "required_city_id": 3  # Требуется город с ID 3
    },
    17: {
        "name": "🏛 Генеральный директор сети ресторанов в регионе",
        "description": "Работа генеральным директором в регионе.",
        "income": 1600,
        "required_level": 16,
        "required_education_id": 11,
        "required_car_id": 7,  # Требуется автомобиль с ID 7
        "required_house_id": 7,  # Требуется дом с ID 7
        "required_city_id": 3
    },
    18: {
        "name": "🌆 Управляющий сетью ресторанов в нескольких регионах",
        "description": "Работа управляющим в нескольких регионах.",
        "income": 1700,
        "required_level": 17,
        "required_education_id": 11,
        "required_car_id": 7,
        "required_house_id": 7,
        "required_city_id": 3
    },
    19: {
        "name": "🏛 Генеральный директор сети ресторанов по стране",
        "description": "Работа генеральным директором по всей стране.",
        "income": 1800,
        "required_level": 18,
        "required_education_id": 11,
        "required_car_id": 8,  # Требуется автомобиль с ID 8
        "required_house_id": 8,  # Требуется дом с ID 8
        "required_city_id": 4  # Требуется город с ID 4
    },
    20: {
        "name": "👑 Владелец сети ресторанов по всей стране",
        "description": "Работа владельцем сети ресторанов по всей стране.",
        "income": 1900,
        "required_level": 19,
        "required_education_id": 11,
        "required_car_id": 8,
        "required_house_id": 8,
        "required_city_id": 4
    },
    21: {
        "name": "🌍 Генеральный директор сети ресторанов по стране",
        "description": "Работа генеральным директором по всей стране.",
        "income": 2000,
        "required_level": 20,
        "required_education_id": 11,
        "required_car_id": 9,  # Требуется автомобиль с ID 9
        "required_house_id": 9,  # Требуется дом с ID 9
        "required_city_id": 4
    },
    22: {
        "name": "🌎 Управляющий сетью ресторанов на континенте",
        "description": "Работа управляющим на континенте.",
        "income": 2100,
        "required_level": 21,
        "required_education_id": 11,
        "required_car_id": 9,
        "required_house_id": 9,
        "required_city_id": 5  # Требуется город с ID 5
    },
    23: {
        "name": "✈ Директор по международным операциям сети",
        "description": "Работа директором по международным операциям.",
        "income": 2300,
        "required_level": 23,
        "required_education_id": 11,
        "required_car_id": 10,  # Требуется автомобиль с ID 10
        "required_house_id": 10,  # Требуется дом с ID 10
        "required_city_id": 6  # Требуется город с ID 6
    },
    24: {
        "name": "🏦 Глобальный финансовый директор международной сети",
        "description": "Работа глобальным финансовым директором.",
        "income": 2400,
        "required_level": 24,
        "required_education_id": 11,
        "required_car_id": 10,
        "required_house_id": 10,
        "required_city_id": 6
    },
    25: {
        "name": "🎯 Директор по стратегическому развитию международной сети",
        "description": "Работа директором по стратегическому развитию.",
        "income": 2500,
        "required_level": 25,
        "required_education_id": 11,
        "required_car_id": 11,  # Требуется автомобиль с ID 11
        "required_house_id": 11,  # Требуется дом с ID 11
        "required_city_id": 6
    },
    26: {
        "name": "🏙 Региональный директор сети ресторанов на международном уровне",
        "description": "Работа региональным директором на международном уровне.",
        "income": 2600,
        "required_level": 26,
        "required_education_id": 11,
        "required_car_id": 11,
        "required_house_id": 11,
        "required_city_id": 7  # Требуется город с ID 7
    },
    27: {
        "name": "🏢 Исполнительный директор международной сети",
        "description": "Работа исполнительным директором международной сети.",
        "income": 2700,
        "required_level": 27,
        "required_education_id": 11,
        "required_car_id": 12,  # Требуется автомобиль с ID 12
        "required_house_id": 12,  # Требуется дом с ID 12
        "required_city_id": 7
    },
    28: {
        "name": "💼 Главный операционный директор глобальной сети",
        "description": "Работа главным операционным директором.",
        "income": 2800,
        "required_level": 28,
        "required_education_id": 11,
        "required_car_id": 12,
        "required_house_id": 12,
        "required_city_id": 7
    },
    29: {
        "name": "🌍 Президент международной сети ресторанов",
        "description": "Работа президентом международной сети.",
        "income": 2900,
        "required_level": 29,
        "required_education_id": 11,
        "required_car_id": 13,  # Требуется автомобиль с ID 13
        "required_house_id": 13,  # Требуется дом с ID 13
        "required_city_id": 8  # Требуется город с ID 8
    },
    30: {
        "name": "👑 Владелец международной сети ресторанов",
        "description": "Работа владельцем международной сети.",
        "income": 3000,
        "required_level": 30,
        "required_education_id": 11,
        "required_car_id": 13,
        "required_house_id": 13,
        "required_city_id": 8
    },
    31: {
        "name": "🏛 Генеральный директор глобальной холдинговой компании",
        "description": "Работа генеральным директором глобальной холдинговой компании.",
        "income": 3100,
        "required_level": 31,
        "required_education_id": 11,
        "required_car_id": 14,  # Требуется автомобиль с ID 14
        "required_house_id": 14,  # Требуется дом с ID 14
        "required_city_id": 9  # Требуется город с ID 9
    },
    32: {
        "name": "💰 Инвестиционный директор глобальной ресторанной корпорации",
        "description": "Работа инвестиционным директором глобальной корпорации.",
        "income": 3200,
        "required_level": 32,
        "required_education_id": 11,
        "required_car_id": 14,
        "required_house_id": 14,
        "required_city_id": 9
    },
    33: {
        "name": "🏦 Глобальный директор по стратегическим альянсам",
        "description": "Работа глобальным директором по стратегическим альянсам.",
        "income": 3300,
        "required_level": 33,
        "required_education_id": 11,
        "required_car_id": 15,  # Требуется автомобиль с ID 15
        "required_house_id": 15,  # Требуется дом с ID 15
        "required_city_id": 9
    },
    34: {
        "name": "🌐 Глава департамента международных инвестиций",
        "description": "Работа главой департамента международных инвестиций.",
        "income": 3400,
        "required_level": 34,
        "required_education_id": 11,
        "required_car_id": 16,  # Требуется автомобиль с ID 16
        "required_house_id": 16,  # Требуется дом с ID 16
        "required_city_id": 10  # Требуется город с ID 10
    },
    35: {
        "name": "📈 Исполнительный директор глобальной корпорации",
        "description": "Работа исполнительным директором глобальной корпорации.",
        "income": 3500,
        "required_level": 35,
        "required_education_id": 11,
        "required_car_id": 16,
        "required_house_id": 16,
        "required_city_id": 10
    },
    36: {
        "name": "🌎 Президент транснациональной ресторанной империи",
        "description": "Работа президентом транснациональной империи.",
        "income": 3600,
        "required_level": 36,
        "required_education_id": 11,
        "required_car_id": 17,  # Требуется автомобиль с ID 17
        "required_house_id": 17,  # Требуется дом с ID 17
        "required_city_id": 10
    },
    37: {
        "name": "🚢 Глобальный управляющий флотилией ресторанов на круизных лайнерах",
        "description": "Работа управляющим флотилией ресторанов на круизных лайнерах.",
        "income": 3700,
        "required_level": 37,
        "required_education_id": 11,
        "required_car_id": 17,
        "required_house_id": 17,
        "required_city_id": 11  # Требуется город с ID 11
    },
    38: {
        "name": "🏝 Владелец сети ресторанов на элитных островах",
        "description": "Работа владельцем сети ресторанов на элитных островах.",
        "income": 3800,
        "required_level": 38,
        "required_education_id": 11,
        "required_car_id": 18,  # Требуется автомобиль с ID 18
        "required_house_id": 18,  # Требуется дом с ID 18
        "required_city_id": 11
    },
    39: {
        "name": "🏛 Глава международного консорциума элитных ресторанов",
        "description": "Работа главой международного консорциума элитных ресторанов.",
        "income": 3900,
        "required_level": 39,
        "required_education_id": 11,
        "required_car_id": 18,
        "required_house_id": 18,
        "required_city_id": 11
    },
    40: {
        "name": "👑 Создатель глобальной ресторанной империи (№1 в мире)",
        "description": "Работа создателем глобальной ресторанной империи.",
        "income": 4000,
        "required_level": 40,
        "required_education_id": 12,
        "required_car_id": 19,  # Требуется автомобиль с ID 19
        "required_house_id": 19,  # Требуется дом с ID 19
        "required_city_id": 12  # Требуется город с ID 12
    },

    # 💎 Привилегии за донат (41–45)
    41: {
        "name": "🏛 Владелец ресторана с мишленовскими звездами по всему миру",
        "description": "Эксклюзивная работа для донатеров.",
        "income": 5000,
        "required_level": 20,
        "required_education_id": None,
        "required_car_id": 10,  # Требуется автомобиль с ID 10
        "required_house_id": 10,  # Требуется дом с ID 10
        "required_city_id": 5  # Требуется город с ID 5
    },
    42: {
        "name": "🏝 Создатель эксклюзивных ресторанов на частных островах",
        "description": "Эксклюзивная работа для донатеров.",
        "income": 6000,
        "required_level": 20,
        "required_education_id": None,
        "required_car_id": 10,
        "required_house_id": 10,
        "required_city_id": 5
    },
    43: {
        "name": "🚀 Основатель ресторана на орбитальной станции",
        "description": "Эксклюзивная работа для донатеров.",
        "income": 5000,
        "required_level": 40,
        "required_education_id": None,
        "required_car_id": 20,  # Требуется автомобиль с ID 20
        "required_house_id": 20,  # Требуется дом с ID 20
        "required_city_id": 13  # Требуется город с ID 13
    },
    44: {
        "name": "🏦 Инвестор в элитные рестораны будущего",
        "description": "Эксклюзивная работа для донатеров.",
        "income": 6000,
        "required_level": 40,
        "required_education_id": None,
        "required_car_id": 20,
        "required_house_id": 20,
        "required_city_id": 13
    },
    45: {
        "name": "🐉 Легенда ресторанного бизнеса — миллиардер, меняющий индустрию",
        "description": "Эксклюзивная работа для донатеров.",
        "income": 7000,
        "required_level": 40,
        "required_education_id": None,
        "required_car_id": 21,  # Требуется автомобиль с ID 21
        "required_house_id": 21,  # Требуется дом с ID 21
        "required_city_id": 13
    },
}