#!/bin/bash

######### Only This 2 lines to edit with new version ######
# Version und changelog aus der version.txt-Datei herunterladen
version=$(curl -s https://raw.githubusercontent.com/speedy005/CrashlogViewer/main/version.txt)
changelog=$(curl -s https://raw.githubusercontent.com/speedy005/CrashlogViewer/main/changelog.txt)
##############################################################

TMPPATH=/tmp/CrashlogViewer

# ---------------------------------------------------------
# Bestimmen des Installationspfads basierend auf dem
# Systemtyp
# ---------------------------------------------------------

if [ ! -d /usr/lib64 ]; then
    PLUGINPATH=/usr/lib/enigma2/python/Plugins/Extensions/CrashlogViewer
else
    PLUGINPATH=/usr/lib64/enigma2/python/Plugins/Extensions/CrashlogViewer
fi


# ---------------------------------------------------------
# Überprüfung des OS-Typs
# ---------------------------------------------------------

if [ -f /var/lib/dpkg/status ]; then

    STATUS=/var/lib/dpkg/status
    OSTYPE=DreamOs

else

    STATUS=/var/lib/opkg/status
    OSTYPE=Dream

fi


echo ""


# ---------------------------------------------------------
# Python-Version feststellen
# ---------------------------------------------------------

if python --version 2>&1 | grep -q '^Python 3\.'; then

    echo "You have Python3 image"

    PYTHON=PY3
    Packagesix=python3-six
    Packagerequests=python3-requests

else

    echo "You have Python2 image"

    PYTHON=PY2
    Packagerequests=python-requests

fi


# ---------------------------------------------------------
# Benötigte Pakete überprüfen und installieren
# ---------------------------------------------------------

if [ "$PYTHON" = "PY3" ]; then

    if ! grep -qs "Package: $Packagesix" "$STATUS"; then

        echo "Need to install $Packagesix"

        opkg update && opkg install python3-six

    fi

fi


echo ""


if ! grep -qs "Package: $Packagerequests" "$STATUS"; then

    echo "Need to install $Packagerequests"

    if [ "$OSTYPE" = "DreamOs" ]; then

        apt-get update && apt-get install python-requests -y

    elif [ "$PYTHON" = "PY3" ]; then

        opkg update && opkg install python3-requests

    elif [ "$PYTHON" = "PY2" ]; then

        opkg update && opkg install python-requests

    fi

fi


echo ""


# ---------------------------------------------------------
# Temporäres Verzeichnis und altes Plugin entfernen
# ---------------------------------------------------------

if [ -d "$TMPPATH" ]; then
    rm -rf "$TMPPATH" > /dev/null 2>&1
fi


if [ -d "$PLUGINPATH" ]; then
    rm -rf "$PLUGINPATH"
fi


# ---------------------------------------------------------
# Temporäres Verzeichnis erstellen
# ---------------------------------------------------------

mkdir -p "$TMPPATH"

cd "$TMPPATH" || exit 1

set -e


# ---------------------------------------------------------
# Image-Typ anzeigen
# ---------------------------------------------------------

if [ -f /var/lib/dpkg/status ]; then

    echo "# Your image is OE2.5/2.6 #"

else

    echo "# Your image is OE2.0 #"

fi


# ---------------------------------------------------------
# Plugin herunterladen
# ---------------------------------------------------------

echo ""
echo "Downloading CrashlogViewer..."

wget -q --no-check-certificate \
    https://github.com/speedy005/CrashlogViewer/archive/refs/heads/main.tar.gz \
    -O main.tar.gz


if [ ! -f main.tar.gz ]; then

    echo ""
    echo "Download failed."
    echo ""

    rm -rf "$TMPPATH"

    exit 1

fi


# ---------------------------------------------------------
# Archiv entpacken
# ---------------------------------------------------------

echo "Extracting CrashlogViewer..."

tar -xzf main.tar.gz


# ---------------------------------------------------------
# Überprüfen, ob das Quellverzeichnis vorhanden ist
# ---------------------------------------------------------

if [ ! -d "$TMPPATH/CrashlogViewer-main/usr" ]; then

    echo ""
    echo "Something went wrong."
    echo "Plugin source files not found."
    echo ""

    rm -rf "$TMPPATH"

    exit 1

fi


# ---------------------------------------------------------
# Plugin installieren
# ---------------------------------------------------------

echo "Installing CrashlogViewer..."

cp -r "$TMPPATH/CrashlogViewer-main/usr" "/"


set +e

cd

sleep 2


# ---------------------------------------------------------
# Überprüfen, ob das Plugin korrekt installiert wurde
# ---------------------------------------------------------

if [ ! -d "$PLUGINPATH" ]; then

    echo ""
    echo "Something went wrong .. Plugin not installed"
    echo ""

    rm -rf "$TMPPATH"

    exit 1

fi


# ---------------------------------------------------------
# Temporäre Dateien entfernen
# ---------------------------------------------------------

rm -rf "$TMPPATH" > /dev/null 2>&1

sync


# ---------------------------------------------------------
# Installation erfolgreich
# ---------------------------------------------------------

echo ""
echo "#########################################################"
echo "#                  INSTALLED SUCCESSFULLY               #"
echo "#                  developed by speedy005               #"
echo "#                   Big thanks speedy005                #"
echo "#                  .::CrashlogViewer::.                 #"
echo "#                  https://github.com/speedy005         #"
echo "#########################################################"
echo "#                                                       #"
echo "#       Enigma2 GUI will NOT restart automatically      #"
echo "#                                                       #"
echo "#       The plugin will ask if the GUI should restart.  #"
echo "#                                                       #"
echo "#########################################################"
echo ""

sync >/dev/null 2>&1 || true

echo "Installation finished successfully."
echo "No automatic Enigma2 GUI restart performed."
echo ""

exit 0
