#!/bin/bash

######### Only These 2 lines to edit with new version ######

version=$(curl -fsSL \
    https://raw.githubusercontent.com/speedy005/CrashlogViewer/main/version.txt)

changelog=$(curl -fsSL \
    https://raw.githubusercontent.com/speedy005/CrashlogViewer/main/changelog.txt)

##############################################################

set -e

TMPPATH="/tmp/CrashlogViewer"
ARCHIVE="$TMPPATH/main.tar.gz"
SOURCE="$TMPPATH/CrashlogViewer-main"

echo ""
echo "========================================================="
echo " CrashlogViewer Installer"
echo "========================================================="
echo ""

echo "Remote version: $version"
echo ""

# ---------------------------------------------------------
# Python / OS
# ---------------------------------------------------------

if [ -f /var/lib/dpkg/status ]; then
    STATUS="/var/lib/dpkg/status"
    OSTYPE="DreamOs"
else
    STATUS="/var/lib/opkg/status"
    OSTYPE="Dream"
fi

echo "OS type: $OSTYPE"

if python --version 2>&1 | grep -q '^Python 3\.'; then

    PYTHON="PY3"
    Packagesix="python3-six"
    Packagerequests="python3-requests"

    echo "Python3 image detected."

else

    PYTHON="PY2"
    Packagerequests="python-requests"

    echo "Python2 image detected."

fi

echo ""

# ---------------------------------------------------------
# Benötigte Pakete
# ---------------------------------------------------------

if [ "$PYTHON" = "PY3" ]; then

    if ! grep -qs "Package: $Packagesix" "$STATUS"; then

        echo "Installing $Packagesix..."

        if [ "$OSTYPE" = "DreamOs" ]; then
            apt-get update
            apt-get install "$Packagesix" -y
        else
            opkg update
            opkg install "$Packagesix"
        fi

    fi

fi

if ! grep -qs "Package: $Packagerequests" "$STATUS"; then

    echo "Installing $Packagerequests..."

    if [ "$OSTYPE" = "DreamOs" ]; then

        apt-get update
        apt-get install "$Packagerequests" -y

    else

        opkg update
        opkg install "$Packagerequests"

    fi

fi

echo ""

# ---------------------------------------------------------
# Temporäres Verzeichnis
# ---------------------------------------------------------

rm -rf "$TMPPATH"

mkdir -p "$TMPPATH"

cd "$TMPPATH"

# ---------------------------------------------------------
# Download
# ---------------------------------------------------------

echo "Downloading CrashlogViewer..."

wget \
    -q \
    --no-check-certificate \
    --timeout=30 \
    --tries=3 \
    "https://github.com/speedy005/CrashlogViewer/archive/refs/heads/main.tar.gz" \
    -O "$ARCHIVE"

if [ ! -s "$ARCHIVE" ]; then

    echo ""
    echo "ERROR: Download failed."
    echo ""

    rm -rf "$TMPPATH"

    exit 1

fi

echo "Download successful."
echo ""

# ---------------------------------------------------------
# Archiv prüfen
# ---------------------------------------------------------

echo "Checking archive..."

if ! tar -tzf "$ARCHIVE" >/dev/null 2>&1; then

    echo ""
    echo "ERROR: Invalid archive."
    echo ""

    rm -rf "$TMPPATH"

    exit 1

fi

echo "Archive OK."
echo ""

# ---------------------------------------------------------
# Entpacken
# ---------------------------------------------------------

echo "Extracting..."

tar -xzf "$ARCHIVE"

if [ ! -d "$SOURCE" ]; then

    echo ""
    echo "ERROR: Extracted source directory not found."
    echo ""

    rm -rf "$TMPPATH"

    exit 1

fi

echo "Source directory found:"
echo "$SOURCE"
echo ""

# ---------------------------------------------------------
# Plugin-Verzeichnis im Archiv suchen
# ---------------------------------------------------------

echo "Searching for CrashlogViewer plugin..."

PLUGIN_SOURCE=$(find "$SOURCE/usr" \
    -type d \
    -name "CrashlogViewer" \
    2>/dev/null | head -n 1)

if [ -z "$PLUGIN_SOURCE" ]; then

    echo ""
    echo "ERROR: CrashlogViewer plugin directory not found"
    echo "inside the downloaded archive."
    echo ""

    echo "Archive structure:"
    find "$SOURCE" -maxdepth 8 -type d 2>/dev/null

    rm -rf "$TMPPATH"

    exit 1

fi

echo "Plugin source found:"
echo "$PLUGIN_SOURCE"
echo ""

# ---------------------------------------------------------
# Tatsächlichen Installationspfad ermitteln
# ---------------------------------------------------------

PLUGIN_RELATIVE="${PLUGIN_SOURCE#$SOURCE/usr/}"

PLUGINPATH="/$PLUGIN_RELATIVE"

echo "Plugin installation path:"
echo "$PLUGINPATH"
echo ""

# ---------------------------------------------------------
# Alte Installation sichern
# ---------------------------------------------------------

BACKUPPATH="${PLUGINPATH}.backup"

if [ -d "$BACKUPPATH" ]; then

    echo "Removing old backup..."

    rm -rf "$BACKUPPATH"

fi

if [ -d "$PLUGINPATH" ]; then

    echo "Backing up existing installation..."

    mv "$PLUGINPATH" "$BACKUPPATH"

    echo "Backup created:"
    echo "$BACKUPPATH"
    echo ""

fi

# ---------------------------------------------------------
# Neue Dateien installieren
# ---------------------------------------------------------

echo "Installing CrashlogViewer..."

if ! cp -a "$SOURCE/usr/." "/"; then

    echo ""
    echo "ERROR: Failed to copy plugin files."
    echo ""

    # Neue Installation entfernen
    if [ -d "$PLUGINPATH" ]; then
        rm -rf "$PLUGINPATH"
    fi

    # Alte Installation wiederherstellen
    if [ -d "$BACKUPPATH" ]; then
        mv "$BACKUPPATH" "$PLUGINPATH"
    fi

    rm -rf "$TMPPATH"

    exit 1

fi

echo "Files copied."
echo ""

# ---------------------------------------------------------
# Installation überprüfen
# ---------------------------------------------------------

echo "Verifying installation..."

if [ ! -d "$PLUGINPATH" ]; then

    echo ""
    echo "ERROR: Plugin directory was not installed."
    echo ""
    echo "Expected:"
    echo "$PLUGINPATH"
    echo ""

    # Neue Installation entfernen
    rm -rf "$PLUGINPATH"

    # Alte Installation wiederherstellen
    if [ -d "$BACKUPPATH" ]; then
        mv "$BACKUPPATH" "$PLUGINPATH"
    fi

    rm -rf "$TMPPATH"

    exit 1

fi

echo "Plugin directory successfully installed."
echo ""

# ---------------------------------------------------------
# Version überprüfen
# ---------------------------------------------------------

INSTALLED_VERSION=""

if [ -f "$PLUGINPATH/version.txt" ]; then

    INSTALLED_VERSION=$(cat "$PLUGINPATH/version.txt" | tr -d '\r\n ')

fi

echo "Installed version: $INSTALLED_VERSION"
echo "Expected version:  $version"
echo ""

if [ -z "$INSTALLED_VERSION" ]; then

    echo ""
    echo "WARNING: version.txt was not found."
    echo ""

else

    if [ -n "$version" ] && [ "$INSTALLED_VERSION" != "$version" ]; then

        echo ""
        echo "ERROR:"
        echo "Installed version does not match remote version."
        echo ""
        echo "Installed: $INSTALLED_VERSION"
        echo "Expected:  $version"
        echo ""

        # Neue Installation entfernen
        rm -rf "$PLUGINPATH"

        # Alte Installation wiederherstellen
        if [ -d "$BACKUPPATH" ]; then
            mv "$BACKUPPATH" "$PLUGINPATH"
        fi

        rm -rf "$TMPPATH"

        exit 1

    fi

fi

# ---------------------------------------------------------
# Backup löschen
# ---------------------------------------------------------

if [ -d "$BACKUPPATH" ]; then

    echo "Removing old backup..."

    rm -rf "$BACKUPPATH"

fi

# ---------------------------------------------------------
# Aufräumen
# ---------------------------------------------------------

rm -rf "$TMPPATH"

sync

# ---------------------------------------------------------
# Erfolg
# ---------------------------------------------------------

echo ""
echo "#########################################################"
echo "#                                                       #"
echo "#              INSTALLED SUCCESSFULLY                  #"
echo "#                                                       #"
echo "#                  CrashlogViewer                      #"
echo "#                                                       #"
echo "#                  Version: $INSTALLED_VERSION"
echo "#                                                       #"
echo "#       Enigma2 GUI will NOT restart automatically      #"
echo "#                                                       #"
echo "#########################################################"
echo ""

echo "Installation finished successfully."
echo "No automatic Enigma2 GUI restart performed."
echo ""

exit 0
