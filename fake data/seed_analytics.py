import random
from datetime import datetime, timedelta
import psycopg2
from faker import Faker

fake = Faker()

# Параметры подключения к локальному Postgres
DB_PARAMS = {
    "dbname": "travel_ai",
    "user": "dev",
    "password": "dev123",
    "host": "localhost",
    "port": "5432"
}

# Шаблоны вопросов для имитации реальных диалогов
TRAVEL_PROMPTS = [
    "Составь маршрут на 3 дня по Риму с бюджетом $500",
    "Нужна ли виза в Японию для граждан Казахстана?",
    "Какие лучшие локальные рестораны в Барселоне?",
    "Посоветуй отели рядом с центром в Токио",
    "Как добраться из аэропорта Орли в центр Парижа?",
    "Что посмотреть в Алматы за два дня?",
    "Какие документы нужны для поездки с ребенком в Грузию?",
]

AI_RESPONSES = [
    "Вот отличный вариант маршрута: День 1 — Колизей и Римский форум...",
    "Для уточнения визовых требований укажите ваш тип паспорта и планируемый срок пребывания...",
    "Рекомендую посетить район Грасия, там расположены лучшие тапас-бары...",
    "Отличный выбор! Из аэропорта удобнее всего доехать на Orlyval или автобусе Orlybus..."
]

def seed_database(users_count=50):
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()
    
    print("🚀 Начинаем заполнение базы историческими данными...")

    now = datetime.now()

    for i in range(users_count):
        # 1. Генерируем случайную дату регистрации за последние 30 дней
        days_ago = random.randint(0, 30)
        user_created_at = now - timedelta(days=days_ago, hours=random.randint(0, 23))
        
        email = fake.email()
        username = fake.user_name()[:20]
        # Используем простые хеши или заглушку (для аналитики важна структура)
        password_hash = "pbkdf2_sha256$hashed_password_placeholder"

        # Вставляем пользователя
        cursor.execute(
            """
            INSERT INTO users (email, username, hashed_password, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (email, username, password_hash, True, user_created_at)
        )
        user_id = cursor.fetchone()[0]

        # 2. Генерируем от 1 до 4 диалогов для каждого пользователя
        for _ in range(random.randint(1, 4)):
            conv_created_at = user_created_at + timedelta(hours=random.randint(1, 48))
            if conv_created_at > now:
                conv_created_at = now

            title = f"Поездка в {fake.city()}"
            cursor.execute(
                """
                INSERT INTO conversations (user_id, title, created_at, updated_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
                """,
                (user_id, title, conv_created_at, conv_created_at)
            )
            conv_id = cursor.fetchone()[0]

            # 3. Генерируем сообщения внутри диалога (вопрос-ответ)
            msg_time = conv_created_at
            for _ in range(random.randint(1, 3)):
                prompt = random.choice(TRAVEL_PROMPTS)
                answer = random.choice(AI_RESPONSES)

                # Сообщение пользователя
                cursor.execute(
                    """
                    INSERT INTO messages (conversation_id, role, content, created_at)
                    VALUES (%s, %s, %s, %s);
                    """,
                    (conv_id, "user", prompt, msg_time)
                )
                
                # Сообщение ассистента через 5 секунд
                msg_time += timedelta(seconds=5)
                cursor.execute(
                    """
                    INSERT INTO messages (conversation_id, role, content, created_at)
                    VALUES (%s, %s, %s, %s);
                    """,
                    (conv_id, "assistant", answer, msg_time)
                )
                msg_time += timedelta(minutes=random.randint(2, 30))

      # 4. Опционально: загрузка документа (30% пользователей)
        if random.random() < 0.3:
            doc_created_at = user_created_at + timedelta(hours=random.randint(1, 12))
            cursor.execute(
                """
                INSERT INTO documents (user_id, title, created_at)
                VALUES (%s, %s, %s);
                """,
                (
                    user_id,
                    f"Маршрут_{fake.country()}.pdf",
                    doc_created_at
                )
            )

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ База успешно заполнена! Добавлено пользователей: {users_count}")

if __name__ == "__main__":
    seed_database(50)