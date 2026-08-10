import requests
from faker import Faker
import random
import time

fake = Faker()
API_URL = "http://localhost:8000"

def simulate_user_journey():
    # 1. Регистрация нового пользователя (соответствует схеме UserCreate)
    user_data = {
        "email": fake.email(),
        "username": fake.user_name()[:20],  # Ограничение по длине, если есть
        "password": "Password123!"
    }
    
    # Предполагаем, что у тебя есть роут /auth/register
    reg_response = requests.post(f"{API_URL}/auth/register", json=user_data)
    
    if reg_response.status_code not in (200, 201):
        print(f"Ошибка регистрации: {reg_response.text}")
        return

    # 2. Логин и получение токена (соответствует схеме UserLogin / OAuth2)
    login_data = {
        "username": user_data["email"], # OAuth2 обычно использует поле username для email
        "password": user_data["password"]
    }
    auth_response = requests.post(f"{API_URL}/auth/login", data=login_data)
    token = auth_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    print(f"Пользователь {user_data['email']} зашел на платформу.")

    # 3. Создание разговора (ConversationCreate)
    conv_data = {"title": f"Поездка в {fake.city()}"}
    conv_response = requests.post(f"{API_URL}/conversations/", json=conv_data, headers=headers)
    conv_id = conv_response.json().get("id")

    # 4. Отправка сообщений в чат (MessageCreate)
    questions = [
        "Какие там лучшие рестораны?",
        "Нужна ли виза?",
        "Составь маршрут на 3 дня.",
        "Что взять с собой из одежды?"
    ]
    
    # Имитируем от 1 до 4 вопросов в одном диалоге
    for _ in range(random.randint(1, 4)):
        msg_data = {"content": random.choice(questions)}
        requests.post(f"{API_URL}/conversations/{conv_id}/messages", json=msg_data, headers=headers)
        time.sleep(random.uniform(1.0, 3.0)) # Имитация задержки печати

    # 5. (Опционально) Загрузка документа
    if random.random() > 0.7: # 30% пользователей загружают документы
        doc_data = {
            "title": f"Билеты {fake.country()}",
            "content": fake.text(max_nb_chars=500)
        }
        requests.post(f"{API_URL}/documents/", json=doc_data, headers=headers)

if __name__ == "__main__":
    # Генерируем 5-10 новых пользователей за запуск
    users_to_create = random.randint(5, 10)
    for i in range(users_to_create):
        simulate_user_journey()
        print(f"Сгенерировано {i+1}/{users_to_create} сессий")