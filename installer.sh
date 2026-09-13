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
# Installationspfad
# ---------------------------------------------------------

if [ -d /usr/lib64 ]; then
    PLUGINPATH="/usr/lib64/enigma2/python/Plugins/Extensions/CrashlogViewer"
else
    PLUGINPATH="/usr/lib/enigma2/python/Plugins/Extensions/CrashlogViewer"
fi

echo "Plugin path:"
echo "$PLUGINPATH"
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

if python --version 2>&1 | grep -q '^Python 3\.'; then
    PYTHON="PY3"
    Packagesix="python3-six"

    if [ "$OSTYPE" = "DreamOs" ]; then
        Packagerequests="python3-requests"
    else
        Packagerequests="python3-requests"
    fi

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

        opkg update
        opkg install "$Packagesix"

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

if [ ! -d "$SOURCE/usr" ]; then

    echo ""
    echo "ERROR: Plugin source directory not found."
    echo ""

    rm -rf "$TMPPATH"

    exit 1

fi

echo "Source directory found."
echo ""

# ---------------------------------------------------------
# Neue Installation vorbereiten
# ---------------------------------------------------------

echo "Installing CrashlogViewer..."

# Wir entfernen NUR die alte Plugin-Installation
# unmittelbar vor dem Kopieren der bereits vollständig
# geprüften neuen Dateien.

if [ -d "$PLUGINPATH" ]; then

    echo "Removing old installation..."

    rm -rf "$PLUGINPATH"

fi

# ---------------------------------------------------------
# Neue Dateien kopieren
# ---------------------------------------------------------

cp -a "$SOURCE/usr/." "/"

# ---------------------------------------------------------
# Installation überprüfen
# ---------------------------------------------------------

echo ""
echo "Verifying installation..."

if [ ! -d "$PLUGINPATH" ]; then

    echo ""
    echo "ERROR: Plugin directory was not installed."
    echo ""

    rm -rf "$TMPPATH"

    exit 1

fi

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

if [ -n "$version" ] && [ -n "$INSTALLED_VERSION" ]; then

    if [ "$INSTALLED_VERSION" != "$version" ]; then

        echo ""
        echo "WARNING:"
        echo "Installed version does not match remote version."
        echo ""

        rm -rf "$TMPPATH"

        exit 1

    fi

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
