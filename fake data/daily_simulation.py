import random
import requests
from faker import Faker

fake = Faker()
API_URL = "http://localhost:8000"

def run_daily_activity():
    # Создаем 2-5 новых пользователей сегодня
    for _ in range(random.randint(2, 5)):
        email = fake.email()
        username = fake.user_name()[:20]
        password = "Password123!"

        # Регистрация
        reg_res = requests.post(f"{API_URL}/auth/register", json={
            "email": email,
            "username": username,
            "password": password
        })
        
        if reg_res.status_code not in (200, 201):
            continue

        # Авторизация (получение токена)
        login_res = requests.post(f"{API_URL}/auth/login", data={
            "username": email,
            "password": password
        })
        
        token = login_res.json().get("access_token")
        if not token:
            continue
            
        headers = {"Authorization": f"Bearer {token}"}

        # Создание разговора
        conv_res = requests.post(
            f"{API_URL}/conversations/", 
            json={"title": f"Маршрут {fake.city()}"}, 
            headers=headers
        )
        conv_id = conv_res.json().get("id")

        # Отправка сообщений
        if conv_id:
            requests.post(
                f"{API_URL}/conversations/{conv_id}/messages",
                json={"content": "Посоветуй интересные места для посещения"},
                headers=headers
            )

if __name__ == "__main__":
    print("🔄 Запуск ежедневной генерации активности...")
    run_daily_activity()
    print("✅ Активность сгенерирована.")