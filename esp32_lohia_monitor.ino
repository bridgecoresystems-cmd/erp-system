/*
 * ESP32 Lohia Monitor
 * Система мониторинга станка Lohia
 * 
 * Компоненты:
 * - ESP32
 * - RC522 RFID Reader
 * - Кнопка вызова мастера
 * - Proximity sensor для импульсов
 * 
 * Автор: AI Assistant
 * Версия: 1.1 (Исправлено)
 */

 #include <WiFi.h>
 #include <HTTPClient.h>
 #include <ArduinoJson.h>
 #include <MFRC522.h>
 #include <SPI.h>
 
 // ===== НАСТРОЙКИ WIFI =====
 const char* ssid = "Yangibay";
 const char* password = "Yangi518918";
 
 // ===== НАСТРОЙКИ СЕРВЕРА =====
 const char* server_url = "http://192.168.1.101:8000";
 const char* esp32_id = "LOHIA-001";
 
 // ===== НАСТРОЙКИ RFID =====
 #define SS_PIN    21
 #define RST_PIN   22
 MFRC522 mfrc522(SS_PIN, RST_PIN);
 
 // ===== НАСТРОЙКИ КНОПКИ =====
 #define BUTTON_PIN 2
 #define BUTTON_DEBOUNCE 200
 
 // ===== НАСТРОЙКИ PROXIMITY SENSOR =====
 #define PROXIMITY_PIN 4
 #define PULSE_SEND_INTERVAL 30000
 #define PULSE_DEBOUNCE 100
 
 // ===== ПЕРЕМЕННЫЕ =====
 unsigned long lastButtonPress = 0;
 unsigned long lastPulseSend = 0;
 unsigned long lastPulseTime = 0;
 int pulseCount = 0;
 int totalPulses = 0;
 String lastRfidUid = "";
 unsigned long lastRfidTime = 0;
 bool isShiftActive = false;
 bool lastSensorState = false;
 
 void setup() {
   Serial.begin(115200);
   Serial.println("ESP32 Lohia Monitor Starting...");
   
   // Инициализация SPI для RFID
   SPI.begin();
   mfrc522.PCD_Init();
   
   // Настройка пинов
   pinMode(BUTTON_PIN, INPUT_PULLUP);
   pinMode(PROXIMITY_PIN, INPUT_PULLUP);
   
   Serial.println("Proximity sensor: Voltage Divider mode");
   
   // Инициализируем состояние датчика
   delay(100);
   bool initialState = digitalRead(PROXIMITY_PIN);
   lastSensorState = (initialState == HIGH);
   
   Serial.print("Initial sensor state - Raw: ");
   Serial.print(initialState ? "HIGH" : "LOW");
   Serial.print(", Active: ");
   Serial.println(lastSensorState ? "YES" : "NO");
   
   // Подключение к WiFi
   connectToWiFi();
   
   Serial.println("ESP32 Lohia Monitor Ready!");
   Serial.println("RFID card: Start/End shift");
   Serial.println("Button: Call master");
   Serial.println("Proximity sensor: Count pulses");
 }
 
 void loop() {
   if (WiFi.status() != WL_CONNECTED) {
     connectToWiFi();
   }
   
   handleRFID();
   handleButton();
   handleProximitySensor();
   
   delay(100);
 }
 
 void connectToWiFi() {
   Serial.print("Connecting to WiFi: ");
   Serial.println(ssid);
   
   WiFi.begin(ssid, password);
   
   int attempts = 0;
   while (WiFi.status() != WL_CONNECTED && attempts < 20) {
     delay(500);
     Serial.print(".");
     attempts++;
   }
   
   if (WiFi.status() == WL_CONNECTED) {
     Serial.println();
     Serial.println("WiFi connected!");
     Serial.print("IP address: ");
     Serial.println(WiFi.localIP());
   } else {
     Serial.println();
     Serial.println("WiFi connection failed!");
   }
 }
 
 void handleRFID() {
   if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) {
     return;
   }
   
   String rfidUid = "";
   for (byte i = 0; i < mfrc522.uid.size; i++) {
     if (mfrc522.uid.uidByte[i] < 0x10) rfidUid += "0";
     rfidUid += String(mfrc522.uid.uidByte[i], HEX);
   }
   rfidUid.toUpperCase();
   
   if (rfidUid == lastRfidUid && millis() - lastRfidTime < 2000) {
     return;
   }
   
   lastRfidUid = rfidUid;
   lastRfidTime = millis();
   
   Serial.print("RFID detected: ");
   Serial.println(rfidUid);
   
   sendRfidScanRequest(rfidUid);
   
   mfrc522.PICC_HaltA();
   mfrc522.PCD_StopCrypto1();
 }
 
 void handleButton() {
   if (digitalRead(BUTTON_PIN) == LOW) {
     if (millis() - lastButtonPress > BUTTON_DEBOUNCE) {
       lastButtonPress = millis();
       Serial.println("Master call button pressed!");
       sendMasterCallRequest();
     }
   }
 }
 
 void handleProximitySensor() {
   bool currentSensorState = digitalRead(PROXIMITY_PIN);
   
   // Для делителя напряжения: HIGH = активен, LOW = неактивен
   bool isActive = (currentSensorState == HIGH);
   
   // Отладочная информация каждые 2 секунды
   static unsigned long lastDebugTime = 0;
   if (millis() - lastDebugTime > 2000) {
     Serial.print("Sensor Debug - Raw: ");
     Serial.print(currentSensorState ? "HIGH" : "LOW");
     Serial.print(", Active: ");
     Serial.print(isActive ? "YES" : "NO");
     Serial.println(", Type: Voltage Divider");
     lastDebugTime = millis();
   }
   
   // Обнаруживаем переход от неактивного к активному (импульс)
   if (isActive && !lastSensorState && (millis() - lastPulseTime > PULSE_DEBOUNCE)) {
     pulseCount++;
     totalPulses++;
     lastPulseTime = millis();
     
     Serial.print("Pulse detected! Count: ");
     Serial.print(pulseCount);
     Serial.print(", Total: ");
     Serial.println(totalPulses);
   }
   
   // Показываем изменения состояния
   if (isActive != lastSensorState) {
     Serial.print("Sensor state changed: ");
     Serial.print(lastSensorState ? "ACTIVE" : "INACTIVE");
     Serial.print(" -> ");
     Serial.println(isActive ? "ACTIVE" : "INACTIVE");
   }
   
   lastSensorState = isActive;
   
   // Отправляем импульсы каждые 30 секунд
   if (millis() - lastPulseSend > PULSE_SEND_INTERVAL) {
     if (pulseCount > 0) {
       sendPulseUpdateRequest();
       pulseCount = 0;
     }
     lastPulseSend = millis();
   }
 }
 
 void sendRfidScanRequest(String rfidUid) {
   Serial.println("Sending RFID scan request...");
   
   HTTPClient http;
   http.begin(String(server_url) + "/employees/api/rfid-scan/");
   http.addHeader("Content-Type", "application/json");
   
   DynamicJsonDocument doc(1024);
   doc["device_id"] = esp32_id;
   doc["rfid_uid"] = rfidUid;
   
   String jsonString;
   serializeJson(doc, jsonString);
   
   Serial.print("Sending JSON: ");
   Serial.println(jsonString);
   
   int httpResponseCode = http.POST(jsonString);
   
   Serial.print("HTTP Response Code: ");
   Serial.println(httpResponseCode);
   
   if (httpResponseCode > 0) {
     String response = http.getString();
     Serial.print("RFID scan response: ");
     Serial.println(response);
     
     DynamicJsonDocument responseDoc(1024);
     deserializeJson(responseDoc, response);
     
     if (responseDoc["success"]) {
       String action = responseDoc["action"];
       Serial.print("Action: ");
       Serial.println(action);
       
       if (action == "shift_started") {
         isShiftActive = true;
         totalPulses = 0;
         Serial.println("Shift started!");
       } else if (action == "shift_ended") {
         isShiftActive = false;
         Serial.println("Shift ended!");
       } else if (action == "maintenance_started") {
         Serial.println("Maintenance started!");
       } else if (action == "maintenance_completed") {
         Serial.println("Maintenance completed!");
       }
     } else {
       Serial.print("Server error: ");
       Serial.println(responseDoc["error"].as<String>());
     }
   } else {
     Serial.print("HTTP request failed: ");
     Serial.println(httpResponseCode);
   }
   
   http.end();
 }
 
 void sendPulseUpdateRequest() {
   if (!isShiftActive) return;
   
   Serial.print("Sending pulse update: ");
   Serial.println(pulseCount);
   
   HTTPClient http;
   http.begin(String(server_url) + "/lohia/api/pulse/update/");
   http.addHeader("Content-Type", "application/json");
   
   DynamicJsonDocument doc(1024);
   doc["esp32_id"] = esp32_id;
   doc["pulse_count"] = pulseCount;
   
   String jsonString;
   serializeJson(doc, jsonString);
   
   int httpResponseCode = http.POST(jsonString);
   
   if (httpResponseCode > 0) {
     String response = http.getString();
     Serial.print("Pulse update response: ");
     Serial.println(response);
   } else {
     Serial.print("Pulse update failed: ");
     Serial.println(httpResponseCode);
   }
   
   http.end();
 }
 
 void sendMasterCallRequest() {
   if (!isShiftActive) {
     Serial.println("Cannot call master - no active shift");
     return;
   }
   
   Serial.println("Calling master...");
   
   HTTPClient http;
   http.begin(String(server_url) + "/lohia/api/maintenance/call/");
   http.addHeader("Content-Type", "application/json");
   
   DynamicJsonDocument doc(1024);
   doc["esp32_id"] = esp32_id;
   
   String jsonString;
   serializeJson(doc, jsonString);
   
   Serial.print("Sending JSON: ");
   Serial.println(jsonString);
   
   int httpResponseCode = http.POST(jsonString);
   
   if (httpResponseCode > 0) {
     String response = http.getString();
     Serial.print("Master call response: ");
     Serial.println(response);
     
     DynamicJsonDocument responseDoc(1024);
     deserializeJson(responseDoc, response);
     
     if (responseDoc["success"]) {
       Serial.println("Master called successfully!");
     } else {
       Serial.print("Server error: ");
       Serial.println(responseDoc["error"].as<String>());
     }
   } else {
     Serial.print("HTTP request failed: ");
     Serial.println(httpResponseCode);
   }
   
   http.end();
 }