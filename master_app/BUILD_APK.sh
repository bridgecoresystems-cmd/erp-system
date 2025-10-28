#!/bin/bash
# Сборка APK для Lohia Master App
# Запусти когда интернет появится!

export JAVA_HOME="$HOME/jdk-17.0.9+9"
export ANDROID_HOME="$HOME/Android"
export PATH="$JAVA_HOME/bin:$HOME/flutter/bin:$ANDROID_HOME/platform-tools:$PATH"

cd /home/batyr/projects/erp-system/master_app

echo "🚀 Сборка APK..."
flutter build apk --release

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ APK готов!"
    echo "📱 Файл: build/app/outputs/flutter-apk/app-release.apk"
    echo ""
    echo "Установи на телефон:"
    echo "  adb install build/app/outputs/flutter-apk/app-release.apk"
    echo ""
    echo "Или скопируй файл на телефон и установи вручную"
else
    echo ""
    echo "❌ Ошибка сборки"
    echo "Проверь интернет и попробуй снова"
fi

