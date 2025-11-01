/*
 * ESP32 HR RFID Scanner - Учет рабочего времени
 * 
 * Назначение: Сканирование RFID карт сотрудников для учета рабочего времени
 * Подключение: 1x ESP32 + 1x RC522 RFID
 * Питание: USB кабель от телефонной зарядки (5V 1-2A)
 * Монтаж: RC522 на крышке коробки (двойной скотч изнутри)
 * 
 * Отправляет данные в: /employees/api/rfid-scan/
 * Сервер: https://erp.bridgecore.tech
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <MFRC522.h>
#include <SPI.h>

// ===== КОНФИГУРАЦИЯ СЕТИ =====
const char* ssid = "Yangibay";
const char* password = "Yangi518918";
const char* server_url = "https://erp.bridgecore.tech";  // Твой VPS!
const char* device_id = "ESP32-HR-001";  // Уникальный ID устройства

// ===== КОНФИГУРАЦИЯ ПИНОВ RC522 =====
#define SS_PIN    21    // SDA/SS пин для RC522
#define RST_PIN   22    // RST пин для RC522

// ===== ИНДИКАТОРЫ =====
#define LED_GREEN  16   // Зеленый LED - успешное сканирование
#define LED_RED    17   // Красный LED - ошибка
#define BUZZER_PIN 23   // Buzzer для звука (опционально)

// ===== ОБЪЕКТ РИДЕРА =====
MFRC522 rfidReader(SS_PIN, RST_PIN);

// ===== ЗАЩИТА ОТ ПОВТОРНЫХ СКАНИРОВАНИЙ =====
unsigned long lastScanTime = 0;
String lastCardUID = "";
const unsigned long SCAN_COOLDOWN = 3000;  // 3 секунды между одной картой

// ===== SETUP =====
void setup() {
  Serial.begin(115200);
  delay(100);
  
  Serial.println("\n\n");
  Serial.println("========================================");
  Serial.println("  ESP32 HR RFID Scanner v1.0");
  Serial.println("  Учет рабочего времени сотрудников");
  Serial.println("========================================");
  
  // Инициализация пинов
  setupPins();
  
  // Инициализация SPI и RFID ридера
  SPI.begin();
  rfidReader.PCD_Init();
  delay(100);
  
  // Проверка ридера
  Serial.println("\n[INIT] Проверка RC522 ридера...");
  byte version = rfidReader.PCD_ReadRegister(MFRC522::VersionReg);
  if (version == 0x00 || version == 0xFF) {
    Serial.println("✗ ОШИБКА: RC522 не найден!");
    Serial.println("Проверьте подключение:");
    Serial.println("  SDA  → GPIO 21");
    Serial.println("  SCK  → GPIO 18");
    Serial.println("  MOSI → GPIO 23");
    Serial.println("  MISO → GPIO 19");
    Serial.println("  RST  → GPIO 22");
    Serial.println("  3.3V → 3.3V");
    Serial.println("  GND  → GND");
    signalError(LED_RED);
    while(1) { delay(1000); }  // Останавливаем выполнение
  }
  
  Serial.print("✓ RC522 найден! Версия: 0x");
  Serial.println(version, HEX);
  signalSuccess(LED_GREEN);
  
  // Подключение к WiFi
  connectToWiFi();
  
  Serial.println("\n========================================");
  Serial.println("  СИСТЕМА ГОТОВА К РАБОТЕ!");
  Serial.println("  Приложите RFID карту к считывателю");
  Serial.println("========================================\n");
  
  // Сигнал готовности
  beep(2, 200);
}

// ===== MAIN LOOP =====
void loop() {
  // Проверка WiFi соединения
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("\n⚠ WiFi потеряно! Переподключение...");
    connectToWiFi();
  }
  
  // Проверяем наличие карты
  if (!rfidReader.PICC_IsNewCardPresent()) {
    delay(50);
    return;
  }
  
  // Читаем карту
  if (!rfidReader.PICC_ReadCardSerial()) {
    delay(50);
    return;
  }
  
  // Получаем UID карты
  String cardUID = getCardUID();
  unsigned long currentTime = millis();
  
  // Защита от повторных сканирований (дебаунсинг)
  if (currentTime - lastScanTime < SCAN_COOLDOWN && cardUID == lastCardUID) {
    rfidReader.PICC_HaltA();
    rfidReader.PCD_StopCrypto1();
    delay(50);
    return;
  }
  
  // Обновляем данные последнего сканирования
  lastScanTime = currentTime;
  lastCardUID = cardUID;
  
  // Выводим информацию
  Serial.println("\n┌─────────────────────────────────────┐");
  Serial.println("│  RFID КАРТА ОБНАРУЖЕНА              │");
  Serial.println("└─────────────────────────────────────┘");
  Serial.print("  UID: ");
  Serial.println(cardUID);
  Serial.print("  Устройство: ");
  Serial.println(device_id);
  Serial.println("  Отправка на сервер...");
  
  // Отправляем на сервер
  bool success = sendToServer(cardUID);
  
  if (success) {
    Serial.println("  ✓ УСПЕШНО отправлено!");
    signalSuccess(LED_GREEN);
    beep(1, 200);  // Один короткий сигнал
  } else {
    Serial.println("  ✗ ОШИБКА отправки!");
    signalError(LED_RED);
    beep(3, 100);  // Три коротких сигнала
  }
  
  Serial.println("─────────────────────────────────────\n");
  
  // Завершаем работу с картой
  rfidReader.PICC_HaltA();
  rfidReader.PCD_StopCrypto1();
  
  delay(100);
}

// ===== ФУНКЦИИ =====

void setupPins() {
  // LED индикаторы
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  
  // Выключаем всё
  digitalWrite(LED_GREEN, LOW);
  digitalWrite(LED_RED, LOW);
  digitalWrite(BUZZER_PIN, LOW);
  
  Serial.println("[INIT] Пины настроены:");
  Serial.println("  LED зеленый: GPIO 16");
  Serial.println("  LED красный: GPIO 17");
  Serial.println("  Buzzer:      GPIO 23");
}

void connectToWiFi() {
  Serial.println("\n[WiFi] Подключение к сети...");
  Serial.print("  SSID: ");
  Serial.println(ssid);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
    
    if (attempts % 10 == 0) {
      Serial.println();
      Serial.print("  Попытка " + String(attempts) + "/30...");
    }
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✓ WiFi подключен!");
    Serial.print("  IP адрес: ");
    Serial.println(WiFi.localIP());
    Serial.print("  Сигнал: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
    signalSuccess(LED_GREEN);
    beep(2, 100);
  } else {
    Serial.println("\n✗ WiFi НЕ подключен!");
    Serial.println("  Проверьте SSID и пароль");
    signalError(LED_RED);
    beep(5, 200);
  }
}

String getCardUID() {
  String uid = "";
  for (byte i = 0; i < rfidReader.uid.size; i++) {
    if (rfidReader.uid.uidByte[i] < 0x10) {
      uid += "0";
    }
    uid += String(rfidReader.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();
  return uid;
}

bool sendToServer(String cardUID) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("  ✗ WiFi не подключен!");
    return false;
  }
  
  HTTPClient http;
  
  // Формируем URL
  String url = String(server_url) + "/employees/api/rfid-scan/";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(10000);  // 10 секунд таймаут
  
  // Создаем JSON payload
  StaticJsonDocument<512> doc;
  doc["rfid_uid"] = cardUID;
  doc["device_id"] = device_id;
  
  String payload;
  serializeJson(doc, payload);
  
  Serial.print("  URL: ");
  Serial.println(url);
  Serial.print("  Payload: ");
  Serial.println(payload);
  
  // Отправляем POST запрос
  int httpCode = http.POST(payload);
  
  if (httpCode > 0) {
    Serial.print("  HTTP код: ");
    Serial.println(httpCode);
    
    String response = http.getString();
    Serial.print("  Ответ: ");
    Serial.println(response);
    
    if (httpCode == 200) {
      // Парсим ответ
      StaticJsonDocument<2048> responseDoc;
      DeserializationError error = deserializeJson(responseDoc, response);
      
      if (!error && responseDoc["success"] == true) {
        // Выводим информацию о сотруднике
        if (responseDoc.containsKey("employee")) {
          String name = responseDoc["employee"]["full_name"] | "Неизвестный";
          String action = responseDoc["action"] | "unknown";
          
          Serial.println("\n  ╔════════════════════════════════════╗");
          Serial.print  ("  ║  Сотрудник: ");
          Serial.print(name);
          for(int i = name.length(); i < 23; i++) Serial.print(" ");
          Serial.println("║");
          Serial.print  ("  ║  Действие: ");
          Serial.print(action == "in" ? "ВХОД" : "ВЫХОД");
          Serial.print("                     ║");
          Serial.println();
          Serial.println("  ╚════════════════════════════════════╝\n");
        }
        
        http.end();
        return true;
      }
    }
  } else {
    Serial.print("  ✗ HTTP ошибка: ");
    Serial.println(httpCode);
    Serial.print("  Описание: ");
    Serial.println(http.errorToString(httpCode));
  }
  
  http.end();
  return false;
}

void signalSuccess(int ledPin) {
  digitalWrite(ledPin, HIGH);
  delay(1000);
  digitalWrite(ledPin, LOW);
}

void signalError(int ledPin) {
  for (int i = 0; i < 3; i++) {
    digitalWrite(ledPin, HIGH);
    delay(200);
    digitalWrite(ledPin, LOW);
    delay(200);
  }
}

void beep(int count, int duration) {
  for (int i = 0; i < count; i++) {
    digitalWrite(BUZZER_PIN, HIGH);
    delay(duration);
    digitalWrite(BUZZER_PIN, LOW);
    if (i < count - 1) {
      delay(duration / 2);
    }
  }
}

/*
 * ========================================
 * СХЕМА ПОДКЛЮЧЕНИЯ RC522 к ESP32:
 * ========================================
 * 
 * RC522 → ESP32
 * ─────────────
 * SDA   → GPIO 21
 * SCK   → GPIO 18
 * MOSI  → GPIO 23
 * MISO  → GPIO 19
 * IRQ   → не подключать
 * GND   → GND
 * RST   → GPIO 22
 * 3.3V  → 3.3V
 * 
 * LED индикаторы (с резисторами 220 Ω):
 * ──────────────────────────────────────
 * GPIO 16 → 220Ω → LED зеленый → GND
 * GPIO 17 → 220Ω → LED красный → GND
 * 
 * Buzzer (опционально):
 * ─────────────────────
 * GPIO 23 → Buzzer+ → Buzzer- → GND
 * 
 * ПИТАНИЕ:
 * ────────
 * USB кабель от телефонной зарядки
 * 5V 1A минимум, 5V 2A рекомендуется
 * 
 * МОНТАЖ:
 * ───────
 * 1. RC522 на крышке коробки (изнутри двойной скотч)
 * 2. ESP32 на дне коробки
 * 3. LED на передней панели (просверлить 2 дырки 5мм)
 * 4. USB кабель через боковое отверстие
 * 5. Провода RC522 → ESP32 аккуратно уложить
 * 
 * РЕЗИСТОРЫ:
 * ──────────
 * - 2x 220 Ω для LED
 * 
 * НАСТРОЙКА:
 * ──────────
 * 1. Измени WiFi SSID и пароль (строки 21-22)
 * 2. Проверь server_url (строка 23)
 * 3. Измени device_id если нужно (строка 24)
 * 4. Загрузи на ESP32
 * 5. Открой Serial Monitor (115200 baud)
 * 6. Приложи RFID карту
 * 7. Должен быть зеленый LED и звук
 * 
 */

