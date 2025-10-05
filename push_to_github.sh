#!/bin/bash

# Скрипт для загрузки проекта на GitHub
# ERP System - Factory Management

echo "🚀 Загрузка проекта на GitHub"
echo "=============================="
echo ""

# Проверяем, что мы в Git репозитории
if [ ! -d ".git" ]; then
    echo "❌ Ошибка: Это не Git репозиторий"
    exit 1
fi

echo "📋 Инструкции для создания репозитория на GitHub:"
echo ""
echo "1. Зайдите на https://github.com"
echo "2. Нажмите кнопку 'New repository' (зеленая кнопка)"
echo "3. Заполните форму:"
echo "   - Repository name: erp-system (или другое имя)"
echo "   - Description: ERP System - Factory Management"
echo "   - Visibility: Public или Private (на ваш выбор)"
echo "   - НЕ создавайте README.md (у нас уже есть)"
echo "   - НЕ добавляйте .gitignore (у нас уже есть)"
echo "   - НЕ добавляйте лицензию"
echo "4. Нажмите 'Create repository'"
echo ""

read -p "Создали репозиторий на GitHub? (y/n): " created

if [ "$created" != "y" ]; then
    echo "❌ Сначала создайте репозиторий на GitHub, затем запустите скрипт снова"
    exit 1
fi

echo ""
read -p "Введите URL вашего GitHub репозитория (например: https://github.com/username/erp-system.git): " repo_url

if [ -z "$repo_url" ]; then
    echo "❌ URL репозитория не может быть пустым"
    exit 1
fi

echo ""
echo "🔧 Настройка удаленного репозитория..."

# Добавляем удаленный репозиторий
git remote add origin "$repo_url"

if [ $? -eq 0 ]; then
    echo "✅ Удаленный репозиторий добавлен: $repo_url"
else
    echo "❌ Ошибка при добавлении удаленного репозитория"
    exit 1
fi

echo ""
echo "📤 Загрузка проекта на GitHub..."

# Переименовываем ветку в main (если нужно)
git branch -M main

# Загружаем проект
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Проект успешно загружен на GitHub!"
    echo ""
    echo "📋 Ваш проект доступен по адресу:"
    echo "   https://github.com/$(echo $repo_url | sed 's/.*github.com\///' | sed 's/\.git$//')"
    echo ""
    echo "💡 Полезные команды для дальнейшей работы:"
    echo "   git push                    - загрузить изменения"
    echo "   git pull                    - скачать изменения"
    echo "   git status                  - проверить статус"
    echo "   git log --oneline           - история коммитов"
    echo ""
    echo "🔗 Для клонирования на другом компьютере:"
    echo "   git clone $repo_url"
else
    echo ""
    echo "❌ Ошибка при загрузке проекта"
    echo ""
    echo "🔍 Возможные причины:"
    echo "   - Неправильный URL репозитория"
    echo "   - Проблемы с аутентификацией"
    echo "   - Репозиторий уже содержит файлы"
    echo ""
    echo "💡 Решения:"
    echo "   1. Проверьте URL репозитория"
    echo "   2. Настройте SSH ключи или используйте Personal Access Token"
    echo "   3. Убедитесь, что репозиторий пустой"
    echo ""
    echo "🛠️ Для настройки SSH ключей:"
    echo "   ssh-keygen -t ed25519 -C 'your_email@example.com'"
    echo "   cat ~/.ssh/id_ed25519.pub"
    echo "   # Добавьте ключ в GitHub Settings > SSH and GPG keys"
fi
