/*
 * ESP32 Security RFID Scanner - Система безопасности
 * 
 * Назначение: Контроль доступа на территорию/в здание
 * Подключение: 1x ESP32 + 1x RC522 RFID
 * Питание: USB кабель от телефонной зарядки (5V 1-2A)
 * Монтаж: RC522 на крышке коробки (двойной скотч изнутри)
 * 
 * Отправляет данные в: /security/api/scan/
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
const char* device_id = "ESP32-SEC-001";  // Уникальный ID устройства

// ===== КОНФИГУРАЦИЯ ПИНОВ RC522 =====
#define SS_PIN    21    // SDA/SS пин для RC522
#define RST_PIN   22    // RST пин для RC522

// ===== ИНДИКАТОРЫ =====
#define LED_GREEN  25   // Зеленый LED - вход разрешен
#define LED_RED    26   // Красный LED - вход запрещен
#define LED_BLUE   27   // Синий LED - статус системы (опционально)
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
  Serial.println("  ESP32 Security RFID Scanner v1.0");
  Serial.println("  Система контроля доступа");
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
  Serial.println("  🛡️  СИСТЕМА БЕЗОПАСНОСТИ ГОТОВА!");
  Serial.println("  Приложите RFID карту для доступа");
  Serial.println("========================================\n");
  
  // Сигнал готовности
  beep(3, 150);  // 3 средних сигнала для Security
  
  // Мигание синим LED (система готова)
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_BLUE, HIGH);
    delay(200);
    digitalWrite(LED_BLUE, LOW);
    delay(200);
  }
}

// ===== MAIN LOOP =====
void loop() {
  // Мигание синим LED раз в 5 секунд (система работает)
  static unsigned long lastBlink = 0;
  if (millis() - lastBlink > 5000) {
    digitalWrite(LED_BLUE, HIGH);
    delay(50);
    digitalWrite(LED_BLUE, LOW);
    lastBlink = millis();
  }
  
  // Проверка WiFi соединения
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("\n⚠ WiFi потеряно! Переподключение...");
    digitalWrite(LED_BLUE, HIGH);  // Синий горит = нет WiFi
    connectToWiFi();
    digitalWrite(LED_BLUE, LOW);
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
  Serial.println("\n╔═══════════════════════════════════════╗");
  Serial.println("║  🛡️  ЗАПРОС ДОСТУПА                   ║");
  Serial.println("╚═══════════════════════════════════════╝");
  Serial.print("  RFID UID: ");
  Serial.println(cardUID);
  Serial.print("  Устройство: ");
  Serial.println(device_id);
  Serial.println("  Проверка на сервере...");
  
  // Отправляем на сервер
  bool success = sendToServer(cardUID);
  
  if (success) {
    Serial.println("  ✓ ДОСТУП РАЗРЕШЕН!");
    signalSuccess(LED_GREEN);
    beep(2, 150);  // Два средних сигнала
  } else {
    Serial.println("  ✗ ДОСТУП ЗАПРЕЩЕН!");
    signalError(LED_RED);
    beep(1, 500);  // Один длинный сигнал отказа
  }
  
  Serial.println("═══════════════════════════════════════\n");
  
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
  pinMode(LED_BLUE, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  
  // Выключаем всё
  digitalWrite(LED_GREEN, LOW);
  digitalWrite(LED_RED, LOW);
  digitalWrite(LED_BLUE, LOW);
  digitalWrite(BUZZER_PIN, LOW);
  
  Serial.println("[INIT] Пины настроены:");
  Serial.println("  LED зеленый: GPIO 25");
  Serial.println("  LED красный: GPIO 26");
  Serial.println("  LED синий:   GPIO 27");
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
  
  // Формируем URL для Security API
  String url = String(server_url) + "/security/api/scan/";
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
        String employeeName = responseDoc["employee_name"] | "Неизвестный";
        String action = responseDoc["action"] | "unknown";
        
        Serial.println("\n  ╔════════════════════════════════════╗");
        Serial.print  ("  ║  👤 ");
        Serial.print(employeeName);
        for(int i = employeeName.length(); i < 31; i++) Serial.print(" ");
        Serial.println("║");
        Serial.print  ("  ║  🚪 ");
        Serial.print(action == "in" ? "ВХОД В ЗДАНИЕ" : "ВЫХОД ИЗ ЗДАНИЯ");
        for(int i = (action == "in" ? 13 : 15); i < 31; i++) Serial.print(" ");
        Serial.println("║");
        Serial.println("  ╚════════════════════════════════════╝\n");
        
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
 * GPIO 25 → 220Ω → LED зеленый → GND (доступ разрешен)
 * GPIO 26 → 220Ω → LED красный → GND (доступ запрещен)
 * GPIO 27 → 220Ω → LED синий   → GND (статус системы)
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
 * МОНТАЖ В КОРОБКЕ:
 * ─────────────────
 * 1. RC522 на крышке (изнутри двойной скотч)
 * 2. ESP32 на дне коробки (винты или скотч)
 * 3. LED на передней панели:
 *    - Зеленый (вход разрешен)
 *    - Красный (вход запрещен)
 *    - Синий (система работает)
 * 4. USB кабель через боковое отверстие
 * 5. Buzzer на боковой стенке (опционально)
 * 
 * РЕЗИСТОРЫ (на каждый LED):
 * ───────────────────────────
 * - 3x 220 Ω для LED (зеленый, красный, синий)
 * 
 * ПОВЕДЕНИЕ СИНЕГО LED:
 * ─────────────────────
 * - Мигает раз в 5 секунд = система работает нормально
 * - Горит постоянно = нет WiFi соединения
 * - Не горит = проблема с ESP32
 * 
 * ЗВУКОВЫЕ СИГНАЛЫ:
 * ─────────────────
 * - 2 средних сигнала = доступ разрешен
 * - 1 длинный сигнал = доступ запрещен
 * - 3 коротких = ошибка отправки
 * - 5 длинных = ошибка WiFi
 * 
 * НАСТРОЙКА:
 * ──────────
 * 1. Измени WiFi SSID и пароль (строки 21-22)
 * 2. Проверь server_url (строка 23)
 * 3. Измени device_id если нужно (строка 24)
 * 4. Загрузи на ESP32
 * 5. Открой Serial Monitor (115200 baud)
 * 6. Приложи RFID карту
 * 7. Должен быть зеленый или красный LED + звук
 * 
 * ТЕСТИРОВАНИЕ:
 * ─────────────
 * 1. После загрузки - синий LED должен мигать раз в 5 сек
 * 2. Приложи зарегистрированную карту:
 *    - Зеленый LED загорится на 1 сек
 *    - 2 средних звука
 *    - В Serial: "ДОСТУП РАЗРЕШЕН"
 * 3. Приложи незарегистрированную карту:
 *    - Красный LED моргает 3 раза
 *    - 1 длинный звук
 *    - В Serial: "ДОСТУП ЗАПРЕЩЕН"
 * 
 */

