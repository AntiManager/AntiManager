# Добавить второй push-URL для origin
git remote set-url --add --push origin https://github.com/user/repo1.git
git remote set-url --add --push origin https://github.com/user/repo2.git

# Теперь одна команда пушит в оба репозитория
git push origin main