#!/usr/bin/env python3
"""
Тестовый скрипт для проверки API RFID
"""
import requests
import json

# Настройки
SERVER_URL = "http://127.0.0.1:8000"
ESP32_ID = "LOHIA-001"

# Тестовые RFID UID из базы данных
TEST_RFID_UIDs = [
    "A38B3B1C",      # Akmuradow Batyr
    "F1D31804",      # Akmuradowa Enejan  
    "049178C92B0289", # Мастеров Петр
    "0134FE03",      # Начальников Сергей
]

def test_shift_start(rfid_uid):
    """Тест начала смены"""
    url = f"{SERVER_URL}/lohia/api/shift/start/"
    data = {
        "esp32_id": ESP32_ID,
        "rfid_uid": rfid_uid
    }
    
    print(f"\n🚀 Тестируем начало смены с RFID: '{rfid_uid}'")
    print(f"📤 Отправляем: {json.dumps(data, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=data)
        print(f"📥 Ответ: {response.status_code}")
        print(f"📄 Содержимое: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Успешно!")
                return True
            else:
                print(f"❌ Ошибка: {result.get('error')}")
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Исключение: {e}")
    
    return False

def test_shift_end(rfid_uid):
    """Тест окончания смены"""
    url = f"{SERVER_URL}/lohia/api/shift/end/"
    data = {
        "esp32_id": ESP32_ID,
        "rfid_uid": rfid_uid
    }
    
    print(f"\n🏁 Тестируем окончание смены с RFID: '{rfid_uid}'")
    print(f"📤 Отправляем: {json.dumps(data, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=data)
        print(f"📥 Ответ: {response.status_code}")
        print(f"📄 Содержимое: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Успешно!")
                return True
            else:
                print(f"❌ Ошибка: {result.get('error')}")
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Исключение: {e}")
    
    return False

if __name__ == "__main__":
    print("🧪 Тестирование API RFID")
    print("=" * 50)
    
    for rfid_uid in TEST_RFID_UIDs:
        print(f"\n{'='*20} RFID: {rfid_uid} {'='*20}")
        
        # Тест начала смены
        start_success = test_shift_start(rfid_uid)
        
        if start_success:
            # Если начало смены успешно, тестируем окончание
            test_shift_end(rfid_uid)
        
        print("-" * 50)
