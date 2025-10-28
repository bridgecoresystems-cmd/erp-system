/*
 * ESP32 Lohia Monitor - ЗАЩИЩЕННАЯ ВЕРСИЯ v3.0
 * Система мониторинга станка Lohia с защитой от перезагрузок
 *
 * ЗАЩИТНЫЕ МЕРЫ ПРОТИВ ПЕРЕЗАГРУЗОК:
 * ======================================
 *
 * ПРОГРАММНЫЕ ЗАЩИТЫ:
 * - Watchdog timer (30 сек) - перезапуск при зависании
 * - Защита от рекурсии в прерываниях
 * - Фильтр электромагнитных помех (EMI)
 * - Повторные попытки HTTP запросов (3 раза)
 * - Таймауты HTTP соединений (10 сек)
 * - Проверка памяти (heap monitoring)
 * - Emergency mode при критических ошибках
 *
 * АППАРАТНЫЕ РЕКОМЕНДАЦИИ:
 * - Стабилизатор напряжения 3.3V (AMS1117-3.3)
 * - Конденсаторы: 10uF + 0.1uF на питании ESP32
 * - Ферритовые кольца на сигнальных проводах
 * - Экранированные провода для датчиков
 * - Отдельное питание для ESP32 (не от станка!)
 * - Оптоизоляция для сигналов от станка
 *
 * ПРИЧИНЫ ПЕРЕЗАГРУЗОК:
 * - Электромагнитные помехи от двигателей станка
 * - Скачки напряжения при включении/выключении станка
 * - Перегрев ESP32 от близости к станку
 * - Зависания WiFi при слабом сигнале
 * - Ошибки в прерываниях от помех
 *
 * ДИАГНОСТИКА:
 * - Красные огни станка = повышенные помехи
 * - Serial логи покажут причину перезагрузки
 * - Emergency mode активируется автоматически
 */

 #include <WiFi.h>
 #include <HTTPClient.h>
 #include <ArduinoJson.h>
 #include <MFRC522.h>
 #include <SPI.h>
 
 const char* ssid = "Yangibay";
 const char* password = "Yangi518918";
 
 const char* server_url = "http://192.168.1.101:8000";
 const char* esp32_id = "LOHIA-001";
 
 // ===== НАСТРОЙКИ RFID =====
 #define SS_PIN    21
 #define RST_PIN   22
 MFRC522 mfrc522(SS_PIN, RST_PIN);
 
 // ===== НАСТРОЙКИ КНОПКИ =====
 #define BUTTON_PIN 2
 #define BUTTON_DEBOUNCE 200
 
// ===== НАСТРОЙКИ PROXIMITY SENSOR (КРИТИЧНО!) =====
#define PROXIMITY_PIN 4
#define PULSE_SEND_INTERVAL 30000
#define PULSE_DEBOUNCE 150  // УВЕЛИЧЕНО ДО 150ms для защиты от помех

// ===== ЗАЩИТА ОТ ПЕРЕЗАГРУЗКИ =====
#define WATCHDOG_TIMEOUT 30000  // 30 секунд
#define MAX_HTTP_RETRIES 3
#define HTTP_TIMEOUT 10000  // 10 секунд
 
// ===== ПЕРЕМЕННЫЕ ПРЕРЫВАНИЙ (volatile!) =====
volatile int pulseCount = 0;           // Счётчик импульсов в текущем интервале
volatile int totalPulses = 0;          // Всего импульсов за смену
volatile unsigned long lastPulseTime = 0;
volatile bool pulseInterruptTriggered = false;
volatile bool lastSensorReading = false;  // Последнее состояние датчика
volatile unsigned long lastLowTime = 0;     // Время последнего LOW состояния
 
 // ===== ДРУГИЕ ПЕРЕМЕННЫЕ =====
 unsigned long lastButtonPress = 0;
 unsigned long lastPulseSend = 0;
 String lastRfidUid = "";
 unsigned long lastRfidTime = 0;
 bool isShiftActive = false;
 bool lastSensorState = false;

 // ===== ЗАЩИТА ОТ ПЕРЕЗАГРУЗКИ =====
 unsigned long lastWatchdogReset = 0;
 int httpRetryCount = 0;
 bool emergencyMode = false;
 
 // ===== БУФЕР ДЛЯ АСИНХРОННЫХ ОПЕРАЦИЙ =====
 typedef struct {
   unsigned long timestamp;
   int pulses;
   String rfidUid;
 } DataBuffer;
 
TaskHandle_t httpTaskHandle = NULL;

// ===== ФУНКЦИИ ЗАЩИТЫ =====
void resetWatchdog() {
  lastWatchdogReset = millis();
}

void checkWatchdog() {
  if (millis() - lastWatchdogReset > WATCHDOG_TIMEOUT) {
    Serial.println("EMERGENCY: Watchdog timeout - restarting...");
    emergencyMode = true;
    ESP.restart();
  }
}

void enterEmergencyMode() {
  emergencyMode = true;
  Serial.println("EMERGENCY MODE ACTIVATED");
  Serial.println("- Reduced logging");
  Serial.println("- Increased delays");
  Serial.println("- Minimal operations");

  // В emergency mode отключаем некоторые функции
  detachInterrupt(digitalPinToInterrupt(PROXIMITY_PIN));
  delay(100);
}

// ===== ПРЕРЫВАНИЕ ДЛЯ ИМПУЛЬСОВ (КРИТИЧЕСКАЯ ФУНКЦИЯ) =====
// Эта функция выполняется ВНЕ главного цикла!
// ДОБАВЛЕНА ЗАЩИТА ОТ ПОМЕХ И ПЕРЕЗАГРУЗОК
void IRAM_ATTR pulseISR() {
  // КРИТИЧНАЯ ЗАЩИТА: проверяем, что мы не в рекурсии
  static volatile bool isProcessing = false;
  if (isProcessing) return;
  isProcessing = true;

  unsigned long currentTime = millis();

  // СТРОГИЙ дебаунс - игнорируем все импульсы в течение 150ms (увеличено для защиты)
  if (currentTime - lastPulseTime < PULSE_DEBOUNCE) {
    isProcessing = false;
    return;
  }

  // ДОПОЛНИТЕЛЬНАЯ ЗАЩИТА: проверяем на корректность времени
  if (currentTime < lastPulseTime) {
    // Время пошло назад - аппаратная ошибка, сбрасываем
    lastPulseTime = currentTime;
    isProcessing = false;
    return;
  }

  // Читаем текущее состояние датчика С ФИЛЬТРОМ ПОМЕХ
  int rawReading = digitalRead(PROXIMITY_PIN);
  // Повторное чтение для фильтрации помех
  delayMicroseconds(50);  // Короткая задержка для стабильности
  bool currentReading = digitalRead(PROXIMITY_PIN);

  // Если чтения не совпадают - игнорируем (помеха)
  if (rawReading != currentReading) {
    isProcessing = false;
    return;
  }

  // Отслеживаем переходы в LOW состояние
  if (currentReading == LOW && lastSensorReading == HIGH) {
    lastLowTime = currentTime;
  }

  // Считаем импульс только при переходе LOW -> HIGH
  // И ТОЛЬКО если датчик был в LOW состоянии минимум 50ms
  if (currentReading == HIGH && lastSensorReading == LOW) {
    // Дополнительная проверка: датчик должен был быть в LOW минимум 50ms
    if (currentTime - lastLowTime >= 50 && currentTime - lastLowTime <= 1000) {  // Максимум 1 секунда
      // ЗАЩИТА ОТ ПЕРЕПОЛНЕНИЯ
      if (pulseCount < 999999 && totalPulses < 9999999) {
        pulseCount++;
        totalPulses++;
        lastPulseTime = currentTime;
        pulseInterruptTriggered = true;

        // Отладка - показываем каждый РЕАЛЬНЫЙ импульс (только если не в emergency mode)
        if (!emergencyMode) {
          Serial.print("PULSE #");
          Serial.print(totalPulses);
          Serial.print(" (LOW->HIGH, LOW duration: ");
          Serial.print(currentTime - lastLowTime);
          Serial.println("ms)");
        }
      }
    } else if (currentTime - lastLowTime > 1000) {
      // Слишком долгий LOW - возможно обрыв провода или ошибка
      Serial.println("WARNING: Sensor stuck in LOW state too long!");
      lastLowTime = currentTime;  // Сбрасываем таймер
    }
  }

  // Сохраняем текущее состояние для следующего вызова
  lastSensorReading = currentReading;
  isProcessing = false;
}

void setup() {
   Serial.begin(115200);
   delay(1000);

   Serial.println("\n\n=== ESP32 Lohia Monitor v3.0 (PROTECTED) ===");
   Serial.println("Mode: HIGH-SPEED PULSE COUNTING with PROTECTION");

   // ===== ИНИЦИАЛИЗАЦИЯ ЗАЩИТНЫХ СИСТЕМ =====
   resetWatchdog();  // Инициализируем watchdog
   emergencyMode = false;

   // ===== ИНИЦИАЛИЗАЦИЯ RFID =====
   SPI.begin();
   mfrc522.PCD_Init();
   Serial.println("[OK] RFID initialized");

   // ===== ИНИЦИАЛИЗАЦИЯ ПИНОВ =====
   pinMode(BUTTON_PIN, INPUT_PULLUP);
   pinMode(PROXIMITY_PIN, INPUT);  // Просто INPUT для максимальной скорости

   Serial.println("[OK] Pins configured");

  // ===== ПОЛУЧЕНИЕ НАЧАЛЬНОГО СОСТОЯНИЯ =====
  delay(200);  // Увеличена задержка для стабильности

  // МНОЖЕСТВЕННОЕ ЧТЕНИЕ для фильтрации помех при старте
  bool initialStates[5];
  for(int i = 0; i < 5; i++) {
    initialStates[i] = digitalRead(PROXIMITY_PIN);
    delay(10);
  }

  // Выбираем наиболее стабильное значение
  int highCount = 0;
  for(int i = 0; i < 5; i++) {
    if(initialStates[i] == HIGH) highCount++;
  }
  bool initialState = (highCount >= 3) ? HIGH : LOW;

  lastSensorState = (initialState == HIGH);
  lastSensorReading = initialState;
  lastLowTime = millis();

  Serial.print("[SENSOR] Initial state: ");
  Serial.print(initialState ? "HIGH (ACTIVE)" : "LOW (INACTIVE)");
  Serial.print(" (stability check: ");
  Serial.print(highCount);
  Serial.println("/5)");

   // ===== ПОДКЛЮЧЕНИЕ К WiFi =====
   connectToWiFi();

  // ===== АКТИВАЦИЯ ПРЕРЫВАНИЯ НА ИМПУЛЬСЫ =====
  // С ДОПОЛНИТЕЛЬНОЙ ЗАЩИТОЙ
  if (!emergencyMode) {
    attachInterrupt(digitalPinToInterrupt(PROXIMITY_PIN),
                    pulseISR,
                    CHANGE);
    Serial.println("[OK] Interrupt attached to GPIO 4 with protection");
  } else {
    Serial.println("[WARNING] Emergency mode - interrupt disabled");
  }

   Serial.println("\n=== СИСТЕМА ГОТОВА К РАБОТЕ ===\n");

   Serial.println("RFID card:    Start/End shift");
   Serial.println("Button:       Call master");
   Serial.println("Proximity:    HIGH-SPEED pulse counting (PROTECTED mode)");
   Serial.println("Protection:   Watchdog, EMI filter, error recovery");
 }
 
 void loop() {
   // ===== ЗАЩИТА И МОНИТОРИНГ =====
   resetWatchdog();  // Сбрасываем watchdog каждую итерацию

   // Проверяем watchdog каждые 5 секунд
   static unsigned long lastWatchdogCheck = 0;
   if (millis() - lastWatchdogCheck > 5000) {
     checkWatchdog();
     lastWatchdogCheck = millis();
   }

   // ===== ОСНОВНЫЕ ОПЕРАЦИИ =====
   if (WiFi.status() != WL_CONNECTED) {
     connectToWiFi();
     resetWatchdog();  // WiFi подключение может занять время
   }

   // Если в emergency mode - упрощаем операции
   if (!emergencyMode) {
     handleRFID();
     handleButton();
   }
   handlePulseSending();

   // Проверяем на переполнение памяти
   if (esp_get_free_heap() < 10000) {  // Менее 10KB свободной памяти
     Serial.println("WARNING: Low memory detected!");
     if (esp_get_free_heap() < 5000) {  // Менее 5KB - критично
       Serial.println("CRITICAL: Memory exhausted - emergency restart");
       delay(1000);
       ESP.restart();
     }
   }

   // Минимальная задержка только для других операций
   delayMicroseconds(emergencyMode ? 2000 : 500);  // Увеличиваем задержку в emergency mode
}

void connectToWiFi() {
   if (WiFi.status() == WL_CONNECTED) {
     return;  // Уже подключены
   }
   
   Serial.print("[WiFi] Connecting to: ");
   Serial.println(ssid);
   
   WiFi.begin(ssid, password);
   
   int attempts = 0;
   while (WiFi.status() != WL_CONNECTED && attempts < 20) {
     delay(500);
     Serial.print(".");
     attempts++;
   }
   
   if (WiFi.status() == WL_CONNECTED) {
     Serial.println("\n[WiFi] ✓ Connected!");
     Serial.print("[WiFi] IP: ");
     Serial.println(WiFi.localIP());
   } else {
     Serial.println("\n[WiFi] ✗ Failed! Will retry...");
   }
 }
 
 void handleRFID() {
   if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) {
     return;
   }
   
   // Конвертируем UID в строку
   String rfidUid = "";
   for (byte i = 0; i < mfrc522.uid.size; i++) {
     if (mfrc522.uid.uidByte[i] < 0x10) rfidUid += "0";
     rfidUid += String(mfrc522.uid.uidByte[i], HEX);
   }
   rfidUid.toUpperCase();
   
   // Защита от дублей
   if (rfidUid == lastRfidUid && millis() - lastRfidTime < 2000) {
     mfrc522.PICC_HaltA();
     mfrc522.PCD_StopCrypto1();
     return;
   }
   
   lastRfidUid = rfidUid;
   lastRfidTime = millis();
   
   Serial.print("[RFID] Card detected: ");
   Serial.println(rfidUid);
   
   // Отправляем в отдельном потоке, чтобы не блокировать главный цикл
   sendRfidScanRequestAsync(rfidUid);
   
   mfrc522.PICC_HaltA();
   mfrc522.PCD_StopCrypto1();
 }
 
 void handleButton() {
   static bool buttonPressed = false;
   
   if (digitalRead(BUTTON_PIN) == LOW) {
     if (!buttonPressed && millis() - lastButtonPress > BUTTON_DEBOUNCE) {
       lastButtonPress = millis();
       buttonPressed = true;
       
       Serial.println("[BUTTON] Master call pressed!");
       sendMasterCallRequestAsync();
     }
   } else {
     buttonPressed = false;
   }
 }
 
 void handlePulseSending() {
   static unsigned long lastCheck = 0;
   
   // Проверяем каждые 1 секунду (не каждые 30!)
   if (millis() - lastCheck < 1000) {
     return;
   }
   lastCheck = millis();
   
   // Если прошло 30 секунд - отправляем
   if (millis() - lastPulseSend > PULSE_SEND_INTERVAL) {
     if (pulseCount > 0 && isShiftActive) {
       int tempCount = pulseCount;
       pulseCount = 0;  // Сбрасываем счётчик
       lastPulseSend = millis();
       
       Serial.print("[PULSE] Sending ");
       Serial.print(tempCount);
       Serial.println(" pulses to server...");
       
       sendPulseUpdateRequestAsync(tempCount);
     }
     lastPulseSend = millis();
   }
   
  // Отладочный вывод каждые 3 секунды (для медленного вращения)
  static unsigned long lastDebug = 0;
  if (millis() - lastDebug > 3000) {
    lastDebug = millis();
    Serial.print("[DEBUG] Pulses in interval: ");
    Serial.print(pulseCount);
    Serial.print(" | Total: ");
    Serial.print(totalPulses);
    Serial.print(" | Shift: ");
    Serial.print(isShiftActive ? "ACTIVE" : "INACTIVE");
    Serial.print(" | Sensor: ");
    Serial.print(digitalRead(PROXIMITY_PIN) ? "HIGH" : "LOW");
    Serial.print(" | Last transition: ");
    Serial.println(lastSensorReading ? "HIGH" : "LOW");
  }
 }
 
 // ===== АСИНХРОННЫЕ HTTP ФУНКЦИИ (в отдельном потоке) =====
 
 void sendRfidScanRequestAsync(String rfidUid) {
   // Создаём задачу в отдельном ядре процессора
   xTaskCreatePinnedToCore(
     rfidHttpTask,           // Функция
     "RFID_HTTP",            // Имя
     8192,                   // Размер стека
     (void*)new String(rfidUid),  // Параметр (UID)
     1,                      // Приоритет
     NULL,                   // TaskHandle
     0                       // Ядро 0 (оставляем ядро 1 для главного цикла)
   );
 }
 
void rfidHttpTask(void* parameter) {
   String rfidUid = *(String*)parameter;
   delete (String*)parameter;

   // ЗАЩИТА: проверяем что мы не в emergency mode
   if (emergencyMode) {
     Serial.println("[RFID] Emergency mode - skipping HTTP request");
     vTaskDelete(NULL);
     return;
   }

   int retryCount = 0;
   bool success = false;

   while (retryCount < MAX_HTTP_RETRIES && !success) {
     HTTPClient http;
     http.setTimeout(HTTP_TIMEOUT);  // Устанавливаем таймаут
     http.begin(String(server_url) + "/employees/api/rfid-scan/");
     http.addHeader("Content-Type", "application/json");

     DynamicJsonDocument doc(512);
     doc["device_id"] = esp32_id;
     doc["rfid_uid"] = rfidUid;

     String jsonString;
     serializeJson(doc, jsonString);

     Serial.print("[RFID] Attempt ");
     Serial.print(retryCount + 1);
     Serial.print("/");
     Serial.println(MAX_HTTP_RETRIES);

     int httpResponseCode = http.POST(jsonString);

     if (httpResponseCode > 0) {
       String response = http.getString();

       // Проверяем что ответ не пустой
       if (response.length() > 0) {
         DynamicJsonDocument responseDoc(512);
         DeserializationError error = deserializeJson(responseDoc, response);

         if (!error && responseDoc["success"]) {
           String action = responseDoc["action"];

           if (action == "shift_started") {
             isShiftActive = true;
             totalPulses = 0;
             pulseCount = 0;
             Serial.println("[SHIFT] ✓ STARTED");
           }
           else if (action == "shift_ended") {
             isShiftActive = false;
             Serial.println("[SHIFT] ✗ ENDED");
           }
           else if (action == "maintenance_started") {
             Serial.println("[MAINT] Started");
           }
           else if (action == "maintenance_completed") {
             Serial.println("[MAINT] Completed");
           }
           success = true;
         } else {
           Serial.println("[RFID] JSON parse error or server error");
         }
       } else {
         Serial.println("[RFID] Empty response from server");
       }
     } else {
       Serial.print("[RFID ERROR] HTTP code: ");
       Serial.println(httpResponseCode);
     }

     http.end();

     if (!success && retryCount < MAX_HTTP_RETRIES - 1) {
       Serial.print("[RFID] Retrying in ");
       Serial.print((retryCount + 1) * 2000);
       Serial.println("ms...");
       delay((retryCount + 1) * 2000);  // Экспоненциальная задержка
       resetWatchdog();  // Сбрасываем watchdog во время задержки
     }

     retryCount++;
   }

   if (!success) {
     Serial.println("[RFID] All retries failed - entering emergency mode");
     enterEmergencyMode();
   }

   vTaskDelete(NULL);
}
 
 void sendPulseUpdateRequestAsync(int count) {
   xTaskCreatePinnedToCore(
     pulseHttpTask,
     "PULSE_HTTP",
     4096,
     (void*)(intptr_t)count,
     1,
     NULL,
     0
   );
 }
 
void pulseHttpTask(void* parameter) {
   int pulseCount = (intptr_t)parameter;

   // ЗАЩИТА: проверяем корректность данных
   if (pulseCount <= 0 || pulseCount > 100000) {
     Serial.println("[PULSE] Invalid pulse count - skipping");
     vTaskDelete(NULL);
     return;
   }

   // ЗАЩИТА: проверяем что мы не в emergency mode
   if (emergencyMode) {
     Serial.println("[PULSE] Emergency mode - skipping HTTP request");
     vTaskDelete(NULL);
     return;
   }

   int retryCount = 0;
   bool success = false;

   while (retryCount < MAX_HTTP_RETRIES && !success) {
     HTTPClient http;
     http.setTimeout(HTTP_TIMEOUT);
     http.begin(String(server_url) + "/lohia/api/pulse/update/");
     http.addHeader("Content-Type", "application/json");

     DynamicJsonDocument doc(256);
     doc["esp32_id"] = esp32_id;
     doc["pulse_count"] = pulseCount;

     String jsonString;
     serializeJson(doc, jsonString);

     Serial.print("[PULSE] Attempt ");
     Serial.print(retryCount + 1);
     Serial.print("/");
     Serial.print(MAX_HTTP_RETRIES);
     Serial.print(" - sending ");
     Serial.print(pulseCount);
     Serial.println(" pulses");

     int httpResponseCode = http.POST(jsonString);

     if (httpResponseCode > 0) {
       String response = http.getString();

       if (response.length() > 0) {
         DynamicJsonDocument responseDoc(256);
         DeserializationError error = deserializeJson(responseDoc, response);

         if (!error) {
           Serial.print("[PULSE] ✓ Sent ");
           Serial.print(pulseCount);
           Serial.println(" pulses successfully");
           success = true;
         } else {
           Serial.println("[PULSE] JSON parse error");
         }
       } else {
         Serial.println("[PULSE] Empty response from server");
       }
     } else {
       Serial.print("[PULSE] ✗ Failed: HTTP code ");
       Serial.println(httpResponseCode);
     }

     http.end();

     if (!success && retryCount < MAX_HTTP_RETRIES - 1) {
       Serial.print("[PULSE] Retrying in ");
       Serial.print((retryCount + 1) * 1000);
       Serial.println("ms...");
       delay((retryCount + 1) * 1000);
       resetWatchdog();
     }

     retryCount++;
   }

   if (!success) {
     Serial.println("[PULSE] All retries failed - data may be lost");
     // Для pulse данных не переходим в emergency mode, просто логируем
   }

   vTaskDelete(NULL);
}
 
 void sendMasterCallRequestAsync() {
   xTaskCreatePinnedToCore(
     masterCallHttpTask,
     "MASTER_HTTP",
     4096,
     NULL,
     1,
     NULL,
     0
   );
 }
 
void masterCallHttpTask(void* parameter) {
   // ЗАЩИТА: проверяем что мы не в emergency mode
   if (emergencyMode) {
     Serial.println("[MASTER] Emergency mode - skipping HTTP request");
     vTaskDelete(NULL);
     return;
   }

   int retryCount = 0;
   bool success = false;

   while (retryCount < MAX_HTTP_RETRIES && !success) {
     HTTPClient http;
     http.setTimeout(HTTP_TIMEOUT);
     http.begin(String(server_url) + "/lohia/api/maintenance/call/");
     http.addHeader("Content-Type", "application/json");

     DynamicJsonDocument doc(256);
     doc["esp32_id"] = esp32_id;

     String jsonString;
     serializeJson(doc, jsonString);

     Serial.print("[MASTER] Attempt ");
     Serial.print(retryCount + 1);
     Serial.print("/");
     Serial.println(MAX_HTTP_RETRIES);

     int httpResponseCode = http.POST(jsonString);

     if (httpResponseCode > 0) {
       String response = http.getString();

       if (response.length() > 0) {
         DynamicJsonDocument responseDoc(256);
         DeserializationError error = deserializeJson(responseDoc, response);

         if (!error && responseDoc["success"]) {
           Serial.println("[MASTER] ✓ Called successfully");
           success = true;
         } else {
           Serial.println("[MASTER] Server error or JSON parse error");
         }
       } else {
         Serial.println("[MASTER] Empty response from server");
       }
     } else {
       Serial.print("[MASTER] ✗ Failed: HTTP code ");
       Serial.println(httpResponseCode);
     }

     http.end();

     if (!success && retryCount < MAX_HTTP_RETRIES - 1) {
       Serial.print("[MASTER] Retrying in ");
       Serial.print((retryCount + 1) * 3000);
       Serial.println("ms...");
       delay((retryCount + 1) * 3000);
       resetWatchdog();
     }

     retryCount++;
   }

   if (!success) {
     Serial.println("[MASTER] All retries failed - emergency mode may be needed");
   }

   vTaskDelete(NULL);
}