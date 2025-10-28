#!/bin/bash
# Проверка статуса сборки APK

echo "🔍 Проверка статуса сборки..."
echo ""

# Проверяем процессы
if ps aux | grep "gradle" | grep -v grep > /dev/null; then
    echo "⏳ Gradle работает - сборка продолжается"
    echo ""
    echo "Процессы:"
    ps aux | grep -E "gradle|flutter.*build" | grep -v grep
    echo ""
    echo "Подожди еще 2-3 минуты..."
else
    echo "❌ Gradle не работает"
fi

echo ""

# Проверяем APK
if [ -f "build/app/outputs/flutter-apk/app-release.apk" ]; then
    echo "✅ APK ГОТОВ!"
    echo ""
    ls -lh build/app/outputs/flutter-apk/app-release.apk
    echo ""
    echo "📱 Установи на телефон:"
    echo "   adb install build/app/outputs/flutter-apk/app-release.apk"
    echo ""
    echo "Или скопируй файл build/app/outputs/flutter-apk/app-release.apk на телефон"
else
    echo "⏳ APK еще не готов - дождись завершения сборки"
fi

