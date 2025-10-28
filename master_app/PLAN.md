# Flutter App для мастера - План

## Функционал приложения:

### 1. Авторизация
- RFID карта (автоматически по первому касанию)
- Сохранение токена в локальном хранилище

### 2. Главный экран
- Список всех станков
- Статус каждого станка
- Активные вызовы (красным!)

### 3. Уведомления
- WebSocket в реальном времени
- Звук при новом вызове
- Вибрация
- Push уведомления (даже когда app закрыт)

### 4. Действия
- "Принять вызов" - автоматически по RFID
- "Завершить ремонт" - автоматически по RFID

## Технологии:

- Flutter 3.24
- WebSocket (web_socket_channel)
- FCM (firebase_messaging)
- Local notifications (flutter_local_notifications)
- HTTP (dio или http)

## Структура:

```
master_app/
├── lib/
│   ├── main.dart
│   ├── screens/
│   │   ├── login_screen.dart
│   │   ├── dashboard_screen.dart
│   │   └── machine_detail_screen.dart
│   ├── services/
│   │   ├── websocket_service.dart
│   │   ├── api_service.dart
│   │   └── notification_service.dart
│   ├── models/
│   │   ├── machine.dart
│   │   └── maintenance_call.dart
│   └── widgets/
│       ├── machine_card.dart
│       └── active_call_card.dart
├── android/
├── ios/
└── pubspec.yaml
```

## API Endpoints:

- `GET /lohia/api/dashboard-status-all/` - список станков
- `WebSocket ws://server/ws/lohia/dashboard/` - real-time
- `POST /lohia/api/maintenance/start/` - начало ремонта
- `POST /lohia/api/maintenance/end/` - конец ремонта

## Установка:

1. Flutter SDK
2. Android SDK
3. `flutter create master_app`
4. Добавить зависимости в pubspec.yaml
5. Написать код
6. `flutter run` на телефоне
7. `flutter build apk` для установки

Готово к разработке после установки Flutter SDK!

