# Lohia Master App - Flutter приложение для мастера

## Описание
Мобильное приложение для мастеров станков Lohia.
Получает уведомления о вызовах в реальном времени.

## Функционал
- ✅ Real-time мониторинг через WebSocket
- ✅ Push уведомления (звук + вибрация)
- ✅ Список всех станков
- ✅ Активные вызовы
- ✅ Работает в фоне

## Установка Flutter (когда скачается)

```bash
cd ~
tar xf flutter_linux.tar.xz
echo 'export PATH="$HOME/flutter/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
flutter doctor
```

## Создание проекта

```bash
cd /home/batyr/projects/erp-system/master_app
flutter create .
```

## Запуск

```bash
# Подключи телефон через USB
# Включи "Отладка по USB" в настройках телефона

flutter run
```

## Сборка APK

```bash
flutter build apk --release
# Файл: build/app/outputs/flutter-apk/app-release.apk
```

## Конфигурация

Сервер: `http://192.168.1.101:8000`
WebSocket: `ws://192.168.1.101:8000/ws/lohia/dashboard/`

Все готово! Жду установки Flutter SDK...

