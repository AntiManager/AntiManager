# Добавить второй push-URL для origin
git remote set-url --add --push origin https://github.com/user/repo1.git
git remote set-url --add --push origin https://github.com/user/repo2.git

# Теперь одна команда пушит в оба репозитория
git push origin main

# Показать зависимости
uv tree

# Обновить зависимости
uv pip compile --upgrade

# Заморозить зависимости
uv pip freeze > requirements.txt

# Запуск Python скриптов напрямую
uv run python script.py

# Управление Python версиями
uv python pin 3.11

# 1. Создать проект
mkdir myproject && cd myproject
uv init

# 2. Добавить зависимости
uv add pandas numpy
uv add --dev jupyter

# 3. Установить
uv sync

# 4. Активировать окружение
.venv\Scripts\activate на Windows

# 5. Работать как обычно