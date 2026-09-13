#!/bin/bash

######### Only These 2 lines to edit with new version ######

version=$(curl -fsSL \
    https://raw.githubusercontent.com/speedy005/CrashlogViewer/main/version.txt)

changelog=$(curl -fsSL \
    https://raw.githubusercontent.com/speedy005/CrashlogViewer/main/changelog.txt)

##############################################################

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

        if [ $? -ne 0 ]; then
            echo ""
            echo "ERROR: Could not install $Packagesix."
            echo ""
            exit 1
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

    if [ $? -ne 0 ]; then
        echo ""
        echo "ERROR: Could not install $Packagerequests."
        echo ""
        exit 1
    fi
fi

echo ""

# ---------------------------------------------------------
# Temporäres Verzeichnis
# ---------------------------------------------------------

echo "Preparing temporary directory..."

rm -rf "$TMPPATH"

mkdir -p "$TMPPATH"

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Could not create temporary directory."
    echo ""
    exit 1
fi

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

if [ $? -ne 0 ] || [ ! -s "$ARCHIVE" ]; then

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

tar -tzf "$ARCHIVE" >/dev/null 2>&1

if [ $? -ne 0 ]; then

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

if [ $? -ne 0 ]; then

    echo ""
    echo "ERROR: Extraction failed."
    echo ""

    rm -rf "$TMPPATH"

    exit 1
fi

if [ ! -d "$SOURCE" ]; then

    echo ""
    echo "ERROR: Extracted source directory not found:"
    echo "$SOURCE"
    echo ""

    rm -rf "$TMPPATH"

    exit 1
fi

echo "Source directory found:"
echo "$SOURCE"
echo ""

# ---------------------------------------------------------
# usr prüfen
# ---------------------------------------------------------

if [ ! -d "$SOURCE/usr" ]; then

    echo ""
    echo "ERROR: usr directory not found."
    echo ""

    echo "Archive structure:"
    find "$SOURCE" -maxdepth 8 -type d 2>/dev/null

    rm -rf "$TMPPATH"

    exit 1
fi

echo "usr directory found."
echo ""

# ---------------------------------------------------------
# CrashlogViewer im Archiv suchen
# ---------------------------------------------------------

echo "Searching for CrashlogViewer plugin..."

PLUGIN_SOURCE=$(find "$SOURCE/usr" \
    -type d \
    -name "CrashlogViewer" \
    2>/dev/null | head -n 1)

if [ -z "$PLUGIN_SOURCE" ]; then

    echo ""
    echo "ERROR: CrashlogViewer plugin directory not found."
    echo ""

    echo "Archive structure:"
    find "$SOURCE/usr" -maxdepth 10 -type d 2>/dev/null

    rm -rf "$TMPPATH"

    exit 1
fi

echo "Plugin source found:"
echo "$PLUGIN_SOURCE"
echo ""

# ---------------------------------------------------------
# Zielpfad bestimmen
# ---------------------------------------------------------

PLUGIN_RELATIVE="${PLUGIN_SOURCE#$SOURCE/usr/}"
PLUGINPATH="/$PLUGIN_RELATIVE"

echo "Target plugin path:"
echo "$PLUGINPATH"
echo ""

# ---------------------------------------------------------
# Prüfen ob Plugin-Quelldateien vorhanden sind
# ---------------------------------------------------------

if [ ! -f "$PLUGIN_SOURCE/plugin.py" ]; then

    echo ""
    echo "WARNING: plugin.py not found in source directory."
    echo ""

fi

# ---------------------------------------------------------
# Alte Installation NICHT vorher löschen
# ---------------------------------------------------------

echo "Installing new files..."
echo ""

cp -a "$SOURCE/usr/." "/"

if [ $? -ne 0 ]; then

    echo ""
    echo "ERROR: Copy operation failed."
    echo ""

    rm -rf "$TMPPATH"

    exit 1
fi

echo "Files copied successfully."
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

    rm -rf "$TMPPATH"

    exit 1
fi

echo "Plugin directory found."
echo ""

# ---------------------------------------------------------
# plugin.py prüfen
# ---------------------------------------------------------

if [ ! -f "$PLUGINPATH/plugin.py" ]; then

    echo ""
    echo "ERROR: plugin.py was not installed."
    echo ""

    rm -rf "$TMPPATH"

    exit 1
fi

echo "plugin.py found."
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

    echo "WARNING: version.txt was not found."
    echo ""

else

    if [ -n "$version" ] && [ "$INSTALLED_VERSION" != "$version" ]; then

        echo ""
        echo "ERROR: Version mismatch."
        echo ""
        echo "Installed: $INSTALLED_VERSION"
        echo "Expected:  $version"
        echo ""

        rm -rf "$TMPPATH"

        exit 1
    fi

    echo "Version check OK."
    echo ""
fi

# ---------------------------------------------------------
# Aufräumen
# ---------------------------------------------------------

echo "Cleaning temporary files..."

rm -rf "$TMPPATH"

echo "Cleanup finished."
echo ""

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
