#!/usr/bin/env python3
"""
Простой тест WebSocket соединений для ERP системы.
"""

import asyncio
import websockets
import json
import sys

async def test_websocket(url, name):
    """Тестирование WebSocket соединения."""
    try:
        print(f"🔌 Подключение к {name}: {url}")
        
        async with websockets.connect(url) as websocket:
            print(f"✅ {name} подключен успешно!")
            
            # Отправляем тестовое сообщение
            test_message = {
                "type": "get_machine_status" if "lohia" in url else "get_employee_data"
            }
            
            await websocket.send(json.dumps(test_message))
            print(f"📤 Отправлено: {test_message}")
            
            # Ждем ответ
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"📨 Получено: {data}")
                print(f"✅ {name} работает корректно!\n")
                return True
            except asyncio.TimeoutError:
                print(f"⏰ {name} - таймаут ожидания ответа\n")
                return False
                
    except Exception as e:
        print(f"❌ {name} ошибка: {e}\n")
        return False

async def main():
    """Основная функция тестирования."""
    print("🚀 Тестирование WebSocket соединений ERP системы\n")
    
    base_url = "ws://localhost:8000"
    
    # Список WebSocket endpoints для тестирования
    endpoints = [
        (f"{base_url}/ws/lohia/machine1/", "Lohia Machine Monitor"),
        (f"{base_url}/ws/employees/", "Employee Monitor"),
        (f"{base_url}/ws/notifications/", "Notifications"),
        (f"{base_url}/ws/security/", "Security Monitor"),
    ]
    
    results = []
    
    for url, name in endpoints:
        result = await test_websocket(url, name)
        results.append((name, result))
    
    # Итоговый отчет
    print("📊 ИТОГОВЫЙ ОТЧЕТ:")
    print("=" * 50)
    
    success_count = 0
    for name, result in results:
        status = "✅ РАБОТАЕТ" if result else "❌ НЕ РАБОТАЕТ"
        print(f"{name}: {status}")
        if result:
            success_count += 1
    
    print("=" * 50)
    print(f"Успешно: {success_count}/{len(results)}")
    
    if success_count == len(results):
        print("🎉 Все WebSocket соединения работают!")
        return 0
    else:
        print("⚠️  Некоторые WebSocket соединения не работают")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)
