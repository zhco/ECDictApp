#!/bin/bash
set -e

# ECDict App APK 构建脚本
# 使用命令行工具构建 Android APK

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查 Java 版本
JAVA_VERSION=$(java -version 2>&1 | grep -oP 'version "\K[^"]+')
echo "Java version: $JAVA_VERSION"

# 下载 Gradle Wrapper 如果缺失
if [ ! -f "gradlew" ]; then
    echo "Downloading Gradle Wrapper..."
    mkdir -p gradle/wrapper

    cat > gradle/wrapper/gradle-wrapper.properties << 'EOF'
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\://services.gradle.org/distributions/gradle-8.5-bin.zip
networkTimeout=10000
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
EOF

    curl -L -o gradle/wrapper/gradle-wrapper.jar \
        https://raw.githubusercontent.com/gradle/gradle/v8.5.0/gradle/wrapper/gradle-wrapper.jar

    cat > gradlew << 'EOF'
#!/bin/sh
exec java -cp "$(dirname "$0")/gradle/wrapper/gradle-wrapper.jar" org.gradle.wrapper.GradleWrapperMain "$@"
EOF
    chmod +x gradlew
fi

# 下载 Android SDK 如果缺失
if [ -z "$ANDROID_HOME" ] && [ -z "$ANDROID_SDK_ROOT" ]; then
    if [ -d "/usr/lib/android-sdk" ]; then
        export ANDROID_HOME="/usr/lib/android-sdk"
        export ANDROID_SDK_ROOT="/usr/lib/android-sdk"
    fi
fi

echo "ANDROID_HOME: $ANDROID_HOME"

# 构建 APK
echo "Building APK..."
./gradlew assembleRelease --no-daemon --stacktrace

echo "Build complete!"
echo "APK location: app/build/outputs/apk/release/app-release-unsigned.apk"
