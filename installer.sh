#!/bin/bash

# =========================================================
# CrashlogViewer Installer
# =========================================================

# Locale-Warnungen auf älteren Images vermeiden
export LC_ALL=C
export LANG=C

# ---------------------------------------------------------
# Nur diese beiden Variablen bei Bedarf ändern
# ---------------------------------------------------------

VERSION_URL="https://raw.githubusercontent.com/speedy005/CrashlogViewer/main/version.txt"
ARCHIVE_URL="https://github.com/speedy005/CrashlogViewer/archive/refs/heads/main.tar.gz"

# ---------------------------------------------------------
# Feste Pfade
# ---------------------------------------------------------

TARGET_BASE="/usr/lib/enigma2/python/Plugins/Extensions"
TARGET_PLUGIN_PATH="$TARGET_BASE/CrashlogViewer"

TMPPATH="/tmp/CrashlogViewer"
ARCHIVE="$TMPPATH/main.tar.gz"
SOURCE="$TMPPATH/CrashlogViewer-main"

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP="/tmp/CrashlogViewer-backup-$TIMESTAMP"

# ---------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------

cleanup() {
    rm -rf "$TMPPATH"
}

error_exit() {
    echo ""
    echo "========================================================="
    echo " ERROR"
    echo "========================================================="
    echo ""
    echo "$1"
    echo ""

    cleanup

    exit 1
}

download_file() {

    URL="$1"
    OUTPUT="$2"

    echo "Downloading:"
    echo "$URL"
    echo ""

    # -----------------------------------------------------
    # wget bevorzugen
    # -----------------------------------------------------

    if command -v wget >/dev/null 2>&1; then

        wget \
            --no-check-certificate \
            --timeout=30 \
            --tries=3 \
            -O "$OUTPUT" \
            "$URL"

        RESULT=$?

        if [ "$RESULT" -eq 0 ] && [ -s "$OUTPUT" ]; then
            return 0
        fi

    fi

    # -----------------------------------------------------
    # curl nur als Fallback
    # -----------------------------------------------------

    if command -v curl >/dev/null 2>&1; then

        curl \
            -k \
            -L \
            --connect-timeout 30 \
            --max-time 60 \
            -o "$OUTPUT" \
            "$URL"

        RESULT=$?

        if [ "$RESULT" -eq 0 ] && [ -s "$OUTPUT" ]; then
            return 0
        fi

    fi

    echo ""
    echo "ERROR: Download failed."
    echo "Neither wget nor curl could download the file."
    echo ""

    return 1
}

# ---------------------------------------------------------
# Start
# ---------------------------------------------------------

echo ""
echo "========================================================="
echo " CrashlogViewer Installer"
echo "========================================================="
echo ""

# ---------------------------------------------------------
# Remote Version ermitteln
# ---------------------------------------------------------

echo "Checking remote version..."

VERSION_FILE_TMP="/tmp/CrashlogViewer-remote-version.txt"

rm -f "$VERSION_FILE_TMP"

if download_file "$VERSION_URL" "$VERSION_FILE_TMP"; then

    version=$(cat "$VERSION_FILE_TMP" | tr -d '\r\n ')

else

    version=""

fi

rm -f "$VERSION_FILE_TMP"

if [ -z "$version" ]; then

    echo "WARNING: Could not determine remote version."
    echo "Installation will continue."
    echo ""

else

    echo "Remote version: $version"
    echo ""

fi

# ---------------------------------------------------------
# Python / OS erkennen
# ---------------------------------------------------------

if [ -f /var/lib/dpkg/status ]; then

    STATUS="/var/lib/dpkg/status"
    OSTYPE="DreamOS"

else

    STATUS="/var/lib/opkg/status"
    OSTYPE="Dream"

fi

echo "OS type: $OSTYPE"

# ---------------------------------------------------------
# Python-Version
# ---------------------------------------------------------

if python --version 2>&1 | grep -q '^Python 3\.'; then

    PYTHON="PY3"

    Packagesix="python3-six"
    Packagerequests="python3-requests"

    echo "Python3 image detected."

else

    PYTHON="PY2"

    Packagesix=""
    Packagerequests="python-requests"

    echo "Python2 image detected."

fi

echo ""

# ---------------------------------------------------------
# Benötigte Pakete
# ---------------------------------------------------------

# python-six nur für Python 3
if [ "$PYTHON" = "PY3" ] && [ -n "$Packagesix" ]; then

    if ! grep -qs "Package: $Packagesix" "$STATUS" 2>/dev/null; then

        echo "Installing $Packagesix..."
        echo ""

        if [ "$OSTYPE" = "DreamOS" ]; then

            apt-get update

            if ! apt-get install "$Packagesix" -y; then
                error_exit "Could not install $Packagesix."
            fi

        else

            opkg update

            if ! opkg install "$Packagesix"; then
                error_exit "Could not install $Packagesix."
            fi

        fi

        echo ""

    else

        echo "$Packagesix already installed."

    fi

fi

# python-requests / python3-requests
if [ -n "$Packagerequests" ]; then

    if ! grep -qs "Package: $Packagerequests" "$STATUS" 2>/dev/null; then

        echo "Installing $Packagerequests..."
        echo ""

        if [ "$OSTYPE" = "DreamOS" ]; then

            apt-get update

            if ! apt-get install "$Packagerequests" -y; then
                error_exit "Could not install $Packagerequests."
            fi

        else

            opkg update

            if ! opkg install "$Packagerequests"; then
                error_exit "Could not install $Packagerequests."
            fi

        fi

        echo ""

    else

        echo "$Packagerequests already installed."

    fi

fi

echo ""

# ---------------------------------------------------------
# Temporäres Verzeichnis vorbereiten
# ---------------------------------------------------------

echo "Preparing temporary directory..."

rm -rf "$TMPPATH"

if ! mkdir -p "$TMPPATH"; then
    error_exit "Could not create temporary directory."
fi

echo "Temporary directory:"
echo "$TMPPATH"
echo ""

# ---------------------------------------------------------
# Archiv herunterladen
# ---------------------------------------------------------

echo "Downloading CrashlogViewer archive..."
echo ""

if ! download_file "$ARCHIVE_URL" "$ARCHIVE"; then
    error_exit "CrashlogViewer archive download failed."
fi

echo "Download successful."
echo ""

# ---------------------------------------------------------
# Archiv prüfen
# ---------------------------------------------------------

echo "Checking archive..."

if ! tar -tzf "$ARCHIVE" >/dev/null 2>&1; then
    error_exit "Downloaded archive is invalid."
fi

echo "Archive OK."
echo ""

# ---------------------------------------------------------
# Archiv entpacken
# ---------------------------------------------------------

echo "Extracting archive..."
echo ""

if ! tar -xzf "$ARCHIVE" -C "$TMPPATH"; then
    error_exit "Extraction failed."
fi

echo "Extraction successful."
echo ""

# ---------------------------------------------------------
# Source-Verzeichnis prüfen
# ---------------------------------------------------------

if [ ! -d "$SOURCE" ]; then

    echo "Default source directory not found:"
    echo "$SOURCE"
    echo ""

    echo "Searching extracted files..."

    FOUND_SOURCE=$(find "$TMPPATH" \
        -maxdepth 3 \
        -type d \
        -name "CrashlogViewer-main" \
        2>/dev/null | head -n 1)

    if [ -n "$FOUND_SOURCE" ]; then

        SOURCE="$FOUND_SOURCE"

        echo ""
        echo "Source directory found:"
        echo "$SOURCE"

    else

        error_exit "CrashlogViewer source directory not found."

    fi

fi

echo "Source directory:"
echo "$SOURCE"
echo ""

# ---------------------------------------------------------
# Plugin-Quellverzeichnis suchen
# ---------------------------------------------------------

echo "Searching for CrashlogViewer plugin..."

PLUGIN_SOURCE=$(find "$SOURCE" \
    -type d \
    -path "*/usr/lib/enigma2/python/Plugins/Extensions/CrashlogViewer" \
    2>/dev/null | head -n 1)

# Fallback für andere Archivstrukturen
if [ -z "$PLUGIN_SOURCE" ]; then

    PLUGIN_SOURCE=$(find "$SOURCE" \
        -type d \
        -name "CrashlogViewer" \
        2>/dev/null | head -n 1)

fi

if [ -z "$PLUGIN_SOURCE" ]; then
    error_exit "CrashlogViewer plugin directory was not found in the archive."
fi

echo ""
echo "Plugin source found:"
echo "$PLUGIN_SOURCE"
echo ""

# ---------------------------------------------------------
# Quelle prüfen
# ---------------------------------------------------------

if [ ! -f "$PLUGIN_SOURCE/plugin.py" ]; then

    echo "WARNING: plugin.py not found in source directory."
    echo "$PLUGIN_SOURCE"
    echo ""

fi

if [ ! -f "$PLUGIN_SOURCE/version.txt" ]; then

    echo "WARNING: version.txt not found in source directory."
    echo ""

fi

# ---------------------------------------------------------
# Zielpfad
# ---------------------------------------------------------

echo "Target plugin path:"
echo "$TARGET_PLUGIN_PATH"
echo ""

# ---------------------------------------------------------
# Backup der bestehenden Installation
# ---------------------------------------------------------

if [ -d "$TARGET_PLUGIN_PATH" ]; then

    echo "Existing installation detected."
    echo ""

    echo "Creating backup:"
    echo "$BACKUP"
    echo ""

    rm -rf "$BACKUP"

    if ! cp -a "$TARGET_PLUGIN_PATH" "$BACKUP"; then
        error_exit "Could not create backup of existing installation."
    fi

    echo "Backup created successfully."
    echo ""

fi

# ---------------------------------------------------------
# Zielverzeichnis erstellen
# ---------------------------------------------------------

echo "Preparing target directory..."

if ! mkdir -p "$TARGET_PLUGIN_PATH"; then
    error_exit "Could not create target plugin directory."
fi

echo ""

# ---------------------------------------------------------
# Plugin installieren
# ---------------------------------------------------------

echo "Installing CrashlogViewer..."
echo ""

if ! cp -a "$PLUGIN_SOURCE/." "$TARGET_PLUGIN_PATH/"; then

    echo ""
    echo "ERROR: Plugin installation failed."
    echo ""

    # Backup wiederherstellen
    if [ -d "$BACKUP" ]; then

        echo "Restoring backup..."

        rm -rf "$TARGET_PLUGIN_PATH"

        if cp -a "$BACKUP" "$TARGET_PLUGIN_PATH"; then
            echo "Backup restored successfully."
        else
            echo "WARNING: Backup restoration failed!"
        fi

    fi

    cleanup

    exit 1

fi

echo "Plugin files copied successfully."
echo ""

# ---------------------------------------------------------
# Version.txt sicherstellen
# ---------------------------------------------------------

if [ -n "$version" ]; then

    echo "$version" > "$TARGET_PLUGIN_PATH/version.txt"

    if [ $? -ne 0 ]; then
        error_exit "Could not write version.txt."
    fi

fi

# ---------------------------------------------------------
# Installation überprüfen
# ---------------------------------------------------------

echo "Verifying installation..."
echo ""

if [ ! -d "$TARGET_PLUGIN_PATH" ]; then
    error_exit "Plugin directory does not exist after installation."
fi

echo "Plugin directory OK."

if [ ! -f "$TARGET_PLUGIN_PATH/plugin.py" ]; then
    error_exit "plugin.py does not exist after installation."
fi

echo "plugin.py OK."

# ---------------------------------------------------------
# Version überprüfen
# ---------------------------------------------------------

INSTALLED_VERSION=""

if [ -f "$TARGET_PLUGIN_PATH/version.txt" ]; then

    INSTALLED_VERSION=$(cat "$TARGET_PLUGIN_PATH/version.txt" | tr -d '\r\n ')

fi

echo ""
echo "Installed version: $INSTALLED_VERSION"

if [ -n "$version" ]; then

    echo "Expected version:  $version"
    echo ""

    if [ "$INSTALLED_VERSION" != "$version" ]; then

        echo "ERROR: Version mismatch."
        echo ""
        echo "Installed: $INSTALLED_VERSION"
        echo "Expected:  $version"
        echo ""

        # Backup wiederherstellen
        if [ -d "$BACKUP" ]; then

            echo "Restoring previous installation..."

            rm -rf "$TARGET_PLUGIN_PATH"

            if cp -a "$BACKUP" "$TARGET_PLUGIN_PATH"; then
                echo "Previous installation restored."
            else
                echo "WARNING: Could not restore previous installation!"
            fi

        fi

        cleanup

        exit 1

    fi

    echo "Version check OK."

else

    echo ""
    echo "WARNING: Remote version unavailable."
    echo "Version comparison skipped."

fi

echo ""

# ---------------------------------------------------------
# Backup löschen
# ---------------------------------------------------------

if [ -d "$BACKUP" ]; then

    echo "Removing temporary backup..."
    rm -rf "$BACKUP"

    echo "Backup removed."
    echo ""

fi

# ---------------------------------------------------------
# Aufräumen
# ---------------------------------------------------------

echo "Cleaning temporary files..."

cleanup

echo "Cleanup finished."
echo ""

sync

# ---------------------------------------------------------
# Erfolg
# ---------------------------------------------------------

echo ""
echo "#########################################################"
echo "#                                                       #"
echo "#          CRASHLOGVIEWER INSTALLED SUCCESSFULLY        #"
echo "#                                                       #"
echo "#                 Version: $INSTALLED_VERSION"
echo "#                                                       #"
echo "#        Target: /usr/lib/enigma2/python/Plugins/       #"
echo "#               Extensions/CrashlogViewer              #"
echo "#                                                       #"
echo "#        Enigma2 GUI will NOT restart automatically     #"
echo "#                                                       #"
echo "#########################################################"
echo ""

echo "Installation finished successfully."
echo "No automatic Enigma2 GUI restart performed."
echo ""

exit 0

