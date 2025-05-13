import os

# Берём значения из переменных окружения
host = os.getenv('DB_HOST', 'db')  # Имя сервиса базы данных в Docker
user = os.getenv('DB_USER', 'nikitapomogalov')
password = os.getenv('DB_PASSWORD', 'n000ppp111')
db_name = os.getenv('DB_NAME', 'bot_flat')