import mysql.connector
import asyncio
from config.config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
import logging
from threading import Lock

logger = logging.getLogger(__name__)

# Глобальное соединение с базой данных MySQL
try:
    db_connection = mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )
    logger.info("✅ Успешное подключение к MySQL.")
except mysql.connector.Error as err:
    logger.error(f"❌ Ошибка подключения к MySQL: {err}")
    raise

db_lock = Lock()  # Блокировка для синхронизации доступа

async def get_db_connection():
    """Возвращает глобальное соединение с базой данных."""
    return db_connection

async def execute_db_query(query, params=()):
    """Выполняет SQL-запрос с синхронизацией и гарантией чтения всех результатов."""
    with db_lock:
        cursor = db_connection.cursor(buffered=True)
        cursor.execute(query, params)
        result = cursor.fetchall()  # Считываем все данные сразу
        db_connection.commit()
        cursor.close()
        return result

async def init_db():
    """Инициализирует базу данных, включая таблицы для обучений и бизнесов."""
    def sync_init():
        cursor = db_connection.cursor()

        # Создание таблицы пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id BIGINT UNIQUE,
                username VARCHAR(255),
                referral_code VARCHAR(255) UNIQUE,
                referrer_id BIGINT,
                bonus INT DEFAULT 0,
                reffer INT DEFAULT 0,
                `rank` INT DEFAULT 1,
                level INT DEFAULT 1,
                experience INT DEFAULT 0,
                balance INT DEFAULT 1000,
                bank INT DEFAULT 0,
                cashback INT DEFAULT 0,
                invest INT DEFAULT 0,
                solix INT DEFAULT 0,
                aurix INT DEFAULT 0,
                valorium INT DEFAULT 0,
                registration_date TEXT,
                last_daily DATE,
                daily_streak INT DEFAULT 0,
                banned INT DEFAULT 0,
                max_training_level INT DEFAULT 0,
                house INT DEFAULT 1,
                car INT DEFAULT 1,
                island INT DEFAULT NULL,
                yacht INT DEFAULT NULL,
                airplane INT DEFAULT NULL,
                city INT DEFAULT 1,
                clothes INT DEFAULT NULL,
                animal INT DEFAULT NULL,
                girlfriend INT DEFAULT NULL,
                mining INT DEFAULT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_mining_farms (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,  -- ID пользователя
                mining_id INT NOT NULL,  -- ID майнинг-фермы
                start_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- Дата начала работы фермы
                last_income_collection DATETIME,  -- Дата последнего сбора дохода
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(mining_id) REFERENCES mining_farms(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS investments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT NOT NULL,
                amount INT NOT NULL,
                profit INT NOT NULL,
                start_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                end_time DATETIME NOT NULL,
                claimed BOOLEAN NOT NULL DEFAULT FALSE
            )
        ''')


        # Создание таблицы обучений (тренингов)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS education (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                cost INT NOT NULL,
                duration_minutes INT NOT NULL,
                required_level INT NOT NULL,
                unlocks_jobs TEXT,  -- Список ID работ (хранится как строка)
                unlocks_businesses TEXT,  -- Список ID бизнесов (хранится как строка)
                experience_reward INT DEFAULT 0
            )
        ''')

        # Создание таблицы пройденных обучений у пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_educations (
                user_id INT NOT NULL,  -- Изменено с BIGINT на INT
                education_id INT NOT NULL,
                completion_time DATETIME NOT NULL,
                PRIMARY KEY (user_id, education_id),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(education_id) REFERENCES education(id) ON DELETE CASCADE
            )
        ''')

        # Создание таблицы бизнесов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS businesses (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(255) NOT NULL,
                levels TEXT,  -- Список уровней (хранится как строка)
                base_cost INT NOT NULL,
                base_income INT NOT NULL,
                upgrade_cost_multiplier FLOAT NOT NULL,
                income_multiplier_per_level FLOAT NOT NULL,
                max_accumulation_time INT NOT NULL,
                level_required INT NOT NULL,
                required_education_id INT,
                max_level INT NOT NULL,
                FOREIGN KEY(required_education_id) REFERENCES education(id) ON DELETE SET NULL
            )
        ''')

        # Создание таблицы владения бизнесами пользователями
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_businesses (
                user_id INT,  -- Изменено с BIGINT на INT
                business_id INT,
                level INT DEFAULT 1,
                last_collected_income DATETIME,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(business_id) REFERENCES businesses(id) ON DELETE CASCADE
            )
        ''')

        # Таблица работ
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                income INT NOT NULL,
                required_level INT NOT NULL,
                required_education_id INT,  -- Может быть NULL
                required_car_id INT,
                required_house_id INT,
                required_city_id INT,
                FOREIGN KEY(required_education_id) REFERENCES education(id) ON DELETE RESTRICT
            )
        ''')

        # Таблица для назначения работ пользователям
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_jobs (
                user_id INT NOT NULL,  -- Изменено с BIGINT на INT
                job_id INT NOT NULL,
                start_date DATETIME NOT NULL,
                last_income_collection DATETIME,
                PRIMARY KEY (user_id),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id BIGINT NOT NULL,  -- ID пользователя, создавшего тикет
                message TEXT NOT NULL,    -- Сообщение пользователя
                status ENUM('open', 'closed') DEFAULT 'open',  -- Статус тикета
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,  -- Время создания тикета
                admin_id BIGINT DEFAULT NULL,  -- ID администратора, ответившего на тикет
                admin_reply TEXT DEFAULT NULL  -- Ответ администратора
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mining_farms (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(255) NOT NULL,
                base_cost INT NOT NULL,
                base_income INT NOT NULL,
                experience_bonus INT NOT NULL,
                max_working_hours INT NOT NULL,
                is_premium BOOLEAN NOT NULL,
                level_required INT NOT NULL,
                city_required INT NOT NULL,
                house_required INT NOT NULL,
                airplane_required INT NOT NULL
            )
        ''')

        db_connection.commit()

    await asyncio.to_thread(sync_init)

async def add_trainings_to_db():
    """Добавляет данные о тренингах в таблицу education."""
    try:
        from config.trainings import TRAININGS

        def sync_add_trainings():
            cursor = db_connection.cursor()
            for training_id, training in TRAININGS.items():
                cursor.execute('''
                    INSERT INTO education 
                    (id, name, description, cost, duration_minutes, required_level, unlocks_jobs, unlocks_businesses)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        description = VALUES(description),
                        cost = VALUES(cost),
                        duration_minutes = VALUES(duration_minutes),
                        required_level = VALUES(required_level),
                        unlocks_jobs = VALUES(unlocks_jobs),
                        unlocks_businesses = VALUES(unlocks_businesses)
                ''', (
                    training_id,
                    training["name"],
                    training["description"],
                    training["cost"],
                    training["duration_minutes"],
                    training["required_level"],
                    str(training["unlocks_jobs"]),
                    str(training["unlocks_businesses"])
                ))
            db_connection.commit()

        await asyncio.to_thread(sync_add_trainings)
        logger.info("✅ Данные о тренингах успешно добавлены/обновлены в базе данных.")

    except Exception as e:
        logger.error(f"❌ Ошибка при добавлении/обновлении тренингов: {e}")

async def add_businesses_to_db():
    try:
        from config.businesses import BUSINESSES

        def sync_add_businesses():
            cursor = db_connection.cursor()
            for business_id, business in BUSINESSES.items():
                cursor.execute('''
                    INSERT INTO businesses 
                    (id, name, levels, base_cost, base_income, upgrade_cost_multiplier, 
                    income_multiplier_per_level, max_accumulation_time, level_required, 
                    required_education_id, max_level)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        levels = VALUES(levels),
                        base_cost = VALUES(base_cost),
                        base_income = VALUES(base_income),
                        upgrade_cost_multiplier = VALUES(upgrade_cost_multiplier),
                        income_multiplier_per_level = VALUES(income_multiplier_per_level),
                        max_accumulation_time = VALUES(max_accumulation_time),
                        level_required = VALUES(level_required),
                        required_education_id = VALUES(required_education_id),
                        max_level = VALUES(max_level)
                ''', (
                    business_id,
                    business["name"],
                    str(business.get("levels", [])),
                    business["base_cost"],
                    business["base_income"],
                    business["upgrade_cost_multiplier"],
                    business["income_multiplier_per_level"],
                    business["max_accumulation_time"],
                    business["level_required"],
                    business["required_education_id"],
                    business["max_level"]
                ))
            db_connection.commit()

        await asyncio.to_thread(sync_add_businesses)
        logger.info("✅ Данные о бизнесах успешно добавлены/обновлены в базе данных.")

    except Exception as e:
        logger.error(f"❌ Ошибка при добавлении/обновлении бизнесов: {e}")

async def add_jobs_to_db():
    """Добавляет данные о работах в таблицу jobs."""
    try:
        from config.jobs import JOBS

        def sync_add_jobs():
            cursor = db_connection.cursor()
            for job_id, job in JOBS.items():
                # Если required_education_id равен None, используем NULL
                required_education_id = job["required_education_id"] if job["required_education_id"] is not None else None

                cursor.execute('''
                    INSERT INTO jobs 
                    (id, name, description, income, required_level, required_education_id, required_car_id, required_house_id, required_city_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        description = VALUES(description),
                        income = VALUES(income),
                        required_level = VALUES(required_level),
                        required_education_id = VALUES(required_education_id),
                        required_car_id = VALUES(required_car_id),
                        required_house_id = VALUES(required_house_id),
                        required_city_id = VALUES(required_city_id)
                ''', (
                    job_id,
                    job["name"],
                    job["description"],
                    job["income"],
                    job["required_level"],
                    required_education_id,
                    job["required_car_id"],
                    job["required_house_id"],
                    job["required_city_id"]
                ))
            db_connection.commit()

        await asyncio.to_thread(sync_add_jobs)
        logger.info("✅ Данные о работах успешно добавлены/обновлены в базе данных.")

    except Exception as e:
        logger.error(f"❌ Ошибка при добавлении/обновлении работ: {e}")

async def add_mining_farms_to_db():
    """Добавляет данные о майнинг-фермах в таблицу mining_farms."""
    try:
        from config.mining import MINING_FARMS  # Импортируем данные о майнинг-фермах

        def sync_add_mining_farms():
            cursor = db_connection.cursor()
            for farm_id, farm in MINING_FARMS.items():
                cursor.execute('''
                    INSERT INTO mining_farms 
                    (id, name, base_cost, base_income, experience_bonus, max_working_hours, 
                    is_premium, level_required, city_required, house_required, airplane_required)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        base_cost = VALUES(base_cost),
                        base_income = VALUES(base_income),
                        experience_bonus = VALUES(experience_bonus),
                        max_working_hours = VALUES(max_working_hours),
                        is_premium = VALUES(is_premium),
                        level_required = VALUES(level_required),
                        city_required = VALUES(city_required),
                        house_required = VALUES(house_required),
                        airplane_required = VALUES(airplane_required)
                ''', (
                    farm_id,
                    farm["name"],
                    farm["base_cost"],
                    farm["base_income"],
                    farm["experience_bonus"],
                    farm["max_working_hours"],
                    farm["is_premium"],
                    farm["level_required"],
                    farm["city_required"],
                    farm["house_required"],
                    farm["airplane_required"]
                ))
            db_connection.commit()

        await asyncio.to_thread(sync_add_mining_farms)
        logger.info("✅ Данные о майнинг-фермах успешно добавлены/обновлены в базе данных.")

    except Exception as e:
        logger.error(f"❌ Ошибка при добавлении/обновлении майнинг-ферм: {e}")

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