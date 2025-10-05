# Загрузка проекта на GitHub

## 🚀 Пошаговая инструкция

### 1. Создание репозитория на GitHub

1. Зайдите на [https://github.com](https://github.com)
2. Нажмите кнопку **"New repository"** (зеленая кнопка)
3. Заполните форму:
   - **Repository name**: `erp-system` (или другое имя)
   - **Description**: `ERP System - Factory Management`
   - **Visibility**: Public или Private (на ваш выбор)
   - **НЕ создавайте README.md** (у нас уже есть)
   - **НЕ добавляйте .gitignore** (у нас уже есть)
   - **НЕ добавляйте лицензию**
4. Нажмите **"Create repository"**

### 2. Загрузка проекта

#### Вариант 1: Автоматический скрипт
```bash
./push_to_github.sh
```

#### Вариант 2: Ручная загрузка
```bash
# Добавить удаленный репозиторий
git remote add origin https://github.com/ВАШ_USERNAME/erp-system.git

# Загрузить проект
git push -u origin main
```

### 3. Настройка аутентификации

#### Вариант A: Personal Access Token (рекомендуется)
1. GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Выберите срок действия и права доступа
4. Используйте токен вместо пароля при `git push`

#### Вариант B: SSH ключи
```bash
# Создать SSH ключ
ssh-keygen -t ed25519 -C "your_email@example.com"

# Показать публичный ключ
cat ~/.ssh/id_ed25519.pub

# Добавить ключ в GitHub Settings → SSH and GPG keys
```

## 🔧 Полезные команды

### Основные Git команды
```bash
git status                  # Проверить статус
git add .                   # Добавить все изменения
git commit -m "описание"    # Создать коммит
git push                    # Загрузить на GitHub
git pull                    # Скачать с GitHub
```

### Работа с ветками
```bash
git branch                  # Показать ветки
git checkout -b feature     # Создать новую ветку
git merge feature           # Объединить ветки
```

### История изменений
```bash
git log --oneline           # Краткая история
git log --graph             # История с графиком
git show HEAD               # Показать последний коммит
```

## 📁 Структура проекта на GitHub

После загрузки ваш репозиторий будет содержать:
```
erp-system/
├── .gitignore              # Исключения для Git
├── README.md               # Документация проекта
├── requirements.txt        # Python зависимости
├── backup_db.sh           # Скрипт резервного копирования
├── restore_db.sh          # Скрипт восстановления
├── setup_backup_schedule.sh # Настройка автоматических бэкапов
├── backup_management.sh   # Управление бэкапами
├── create_db.sh           # Создание БД
├── push_to_github.sh      # Загрузка на GitHub
├── esp32_lohia_monitor.ino # ESP32 код
└── factory_erp/           # Django проект
    ├── employees/         # Модуль сотрудников
    ├── security/          # Модуль безопасности
    ├── lohia_monitor/     # Мониторинг станка
    └── factory_erp/       # Настройки Django
```

## 🔐 Безопасность

### Что НЕ загружается на GitHub
- `venv/` - виртуальное окружение
- `backups/` - резервные копии БД
- `__pycache__/` - кэш Python
- `*.log` - логи
- `media/` - загруженные файлы
- `staticfiles/` - собранные статические файлы

### Секретные данные
- Пароли БД
- API ключи
- Персональные данные
- Конфигурационные файлы с секретами

## 🚀 После загрузки

### Клонирование на другом компьютере
```bash
git clone https://github.com/ВАШ_USERNAME/erp-system.git
cd erp-system
```

### Обновление проекта
```bash
git pull origin main
```

### Загрузка изменений
```bash
git add .
git commit -m "Описание изменений"
git push origin main
```

## 🆘 Решение проблем

### Ошибка аутентификации
```bash
# Настроить Git с вашими данными
git config --global user.name "Ваше Имя"
git config --global user.email "ваш@email.com"
```

### Конфликт с существующим репозиторием
```bash
# Принудительная загрузка (ОСТОРОЖНО!)
git push -f origin main
```

### Отмена последнего коммита
```bash
git reset --soft HEAD~1
```

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте URL репозитория
2. Убедитесь в правильности аутентификации
3. Проверьте права доступа к репозиторию
4. Обратитесь к документации GitHub

---

**Удачи с загрузкой проекта! 🎉**
