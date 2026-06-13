#!/bin/bash
set -e

GRADLE_USER_HOME="${GRADLE_USER_HOME:-$HOME/.gradle}"
WRAPPER_DIR="$GRADLE_USER_HOME/wrapper/dists/gradle-8.5-bin"
GRADLE_ZIP="$WRAPPER_DIR/gradle-8.5-bin.zip"
GRADLE_HOME="$WRAPPER_DIR/gradle-8.5"

if [ ! -d "$GRADLE_HOME" ]; then
    mkdir -p "$WRAPPER_DIR"
    echo "Downloading Gradle 8.5..."
    rm -f "$GRADLE_ZIP"
    wget -q --show-progress -O "$GRADLE_ZIP" https://services.gradle.org/distributions/gradle-8.5-bin.zip
    echo "Extracting..."
    unzip -q "$GRADLE_ZIP" -d "$WRAPPER_DIR"
fi

export ANDROID_HOME="${ANDROID_HOME:-/usr/lib/android-sdk}"
export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-/usr/lib/android-sdk}"

exec "$GRADLE_HOME/bin/gradle" "$@"
