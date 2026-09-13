#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# CrashlogViewer Enigma2 Plugin mit Update-Funktion
# updated Lululla 05/06/2023, 30/04/2024, 30/08/2024, 22/09/2024, 17/11/2024
# updated speedy005 06/09/2025

from __future__ import print_function

import gettext
from Components.Language import language

import os
import sys
import re
import time
import glob
import io

from os import remove

from Components.ActionMap import ActionMap
from Components.ScrollLabel import ScrollLabel
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Console import Console
from Tools.Directories import SCOPE_PLUGINS, resolveFilename
from Tools.LoadPixmap import LoadPixmap

from enigma import getDesktop


# =========================================================
# Plugin
# =========================================================

PLUGIN_PATH = resolveFilename(
    SCOPE_PLUGINS,
    "Extensions/CrashlogViewer/"
)

LOCALE_DIR = os.path.join(
    PLUGIN_PATH,
    "locale"
)

DOMAIN = "CrashlogViewer"

LOG_BASE_PATH = "/home/root/logs/"

version = "2.5.1"


# =========================================================
# Locale
# =========================================================

def localeInit():

    lang = language.getLanguage()[:2]

    os.environ["LANGUAGE"] = lang

    gettext.bindtextdomain(
        DOMAIN,
        LOCALE_DIR
    )

    gettext.textdomain(
        DOMAIN
    )


def _(txt):

    t = gettext.dgettext(
        DOMAIN,
        txt
    )

    if t == txt:

        t = gettext.gettext(txt)

    return t


localeInit()

language.addCallback(localeInit)


# =========================================================
# Python 2 / 3
# =========================================================

try:

    import urllib2 as urllib_request

except Exception:

    import urllib.request as urllib_request


PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3


# =========================================================
# Logfile
# =========================================================

LOGFILE = "/tmp/CrashlogViewer.log"


def log(msg):

    try:

        with io.open(
            LOGFILE,
            "a",
            encoding="utf-8"
        ) as f:

            f.write(
                unicode(msg) if PY2 else str(msg)
            )

            f.write(
                u"\n"
            )

    except Exception:

        pass

    try:

        print(msg)

    except Exception:

        pass


# =========================================================
# Update URLs
# =========================================================

INSTALLER_URL = (
    "https://raw.githubusercontent.com/"
    "speedy005/CrashlogViewer/main/installer.sh"
)

GITHUB_VERSION_URL = (
    "https://raw.githubusercontent.com/"
    "speedy005/CrashlogViewer/main/version.txt"
)

GITHUB_CHANGELOG_URL = (
    "https://raw.githubusercontent.com/"
    "speedy005/CrashlogViewer/main/changelog.txt"
)


# =========================================================
# Version
# =========================================================

VERSION_FILE = os.path.join(
    PLUGIN_PATH,
    "version.txt"
)


def get_local_version():

    try:

        with io.open(
            VERSION_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            local_version = f.read().strip()

            if local_version:

                return local_version

    except Exception as e:

        log(
            "[CrashlogViewer] Error reading local version: %s"
            % e
        )

    return version


def get_current_version():

    return get_local_version()


# =========================================================
# Remote Version
# =========================================================

def get_remote_version():

    try:

        request = urllib_request.Request(
            GITHUB_VERSION_URL,
            headers={
                "User-Agent":
                    "CrashlogViewer-Updater/2.5.1"
            }
        )

        response = urllib_request.urlopen(
            request,
            timeout=10
        ).read()

        if PY3:

            response = response.decode(
                "utf-8"
            )

        else:

            response = response.decode(
                "utf-8"
            )

        response = response.strip()

        if not response:

            return None

        remote_version = response.split()[0]

        log(
            "[CrashlogViewer] Remote version: %s"
            % remote_version
        )

        return remote_version

    except Exception as e:

        log(
            "[CrashlogViewer] Error fetching "
            "remote version: %s"
            % e
        )

        return None


# =========================================================
# Remote Changelog
# =========================================================

def get_remote_changelog():

    try:

        request = urllib_request.Request(
            GITHUB_CHANGELOG_URL,
            headers={
                "User-Agent":
                    "CrashlogViewer-Updater/2.5.1"
            }
        )

        response = urllib_request.urlopen(
            request,
            timeout=10
        ).read()

        if PY3:

            response = response.decode(
                "utf-8"
            )

        else:

            response = response.decode(
                "utf-8"
            )

        return response.strip()

    except Exception as e:

        log(
            "[CrashlogViewer] Error fetching "
            "changelog: %s"
            % e
        )

        return ""


# =========================================================
# Version vergleichen
# =========================================================

def parse_version(version_str):

    if not version_str:

        return (
            0,
            0,
            0
        )

    v = version_str.strip().lower()

    if v.startswith("v"):

        v = v[1:]

    parts = re.findall(
        r"\d+",
        v
    )

    while len(parts) < 3:

        parts.append("0")

    return tuple(
        map(
            int,
            parts[:3]
        )
    )


# =========================================================
# Installer Ergebnis prüfen
# =========================================================

def installer_success(result):

    """
    Enigma2 Console liefert je nach Image meistens eine
    Liste oder ein Tuple mit den Returncodes der ausgeführten
    Befehle.

    Beispiel:

        (0,)     = erfolgreich
        (1,)     = Fehler
        (8,)     = Fehler

    Wir akzeptieren Erfolg ausschließlich bei Returncode 0.
    """

    log(
        "[CrashlogViewer] Checking installer result: %s"
        % result
    )

    if result is None:

        log(
            "[CrashlogViewer] Installer result is None."
        )

        return False

    try:

        if isinstance(
            result,
            (tuple, list)
        ):

            if len(result) == 0:

                return False

            for ret in result:

                try:

                    if int(ret) != 0:

                        log(
                            "[CrashlogViewer] "
                            "Installer returned error: %s"
                            % ret
                        )

                        return False

                except Exception:

                    return False

            return True

        return int(result) == 0

    except Exception as e:

        log(
            "[CrashlogViewer] Could not evaluate "
            "installer result: %s"
            % e
        )

        return False


# =========================================================
# Update starten
# =========================================================

def install_update(
    session,
    answer,
    installer_url,
    callback=None
):

    """
    Starts the external CrashlogViewer installer.

    IMPORTANT:
    The installer itself MUST NOT restart Enigma2.

    The installer must exit with:

        0 = successful installation
        !=0 = installation failed

    Only after a successful installation does
    update_finished() ask for a GUI restart.
    """

    # =====================================================
    # Update abgebrochen
    # =====================================================

    if not answer:

        log(
            "[CrashlogViewer] Update canceled by user."
        )

        if callback:

            callback()

        else:

            session.open(
                MessageBox,
                _("Update canceled."),
                MessageBox.TYPE_INFO,
                timeout=3
            )

        return


    # =====================================================
    # Temporärer Installer
    # =====================================================

    installer_tmp = (
        "/tmp/CrashlogViewer-installer.sh"
    )


    # =====================================================
    # Installer Befehl
    # =====================================================

    cmd = (
        "rm -f \"%s\"; "
        "wget -q --no-check-certificate "
        "--timeout=30 "
        "--tries=3 "
        "\"%s\" -O \"%s\"; "
        "RET=$?; "
        "if [ $RET -ne 0 ]; then "
        "echo 'ERROR: Could not download installer'; "
        "rm -f \"%s\"; "
        "exit $RET; "
        "fi; "
        "chmod 755 \"%s\"; "
        "if [ $? -ne 0 ]; then "
        "echo 'ERROR: Could not make installer executable'; "
        "rm -f \"%s\"; "
        "exit 1; "
        "fi; "
        "/bin/bash \"%s\"; "
        "RET=$?; "
        "rm -f \"%s\"; "
        "exit $RET"
    ) % (
        installer_tmp,
        installer_url,
        installer_tmp,
        installer_tmp,
        installer_tmp,
        installer_tmp,
        installer_tmp,
        installer_tmp
    )


    log(
        "[CrashlogViewer] Starting update installer..."
    )

    log(
        "[CrashlogViewer] Installer URL: %s"
        % installer_url
    )


    # =====================================================
    # Console öffnen
    # =====================================================

    try:

        session.open(
            Console,

            _("Updating..."),

            cmdlist=[
                cmd
            ],

            finishedCallback=lambda result=None:
                update_finished(
                    session,
                    result,
                    callback
                ),

            closeOnSuccess=True
        )

    except Exception as e:

        log(
            "[CrashlogViewer] Could not start "
            "update installer: %s"
            % e
        )

        session.open(
            MessageBox,
            _(
                "Could not start the update installer."
            ),
            MessageBox.TYPE_ERROR,
            timeout=5
        )


# =========================================================
# Update abgeschlossen
# =========================================================

def update_finished(
    session,
    result=None,
    callback=None
):

    """
    Called after the external installer has finished.

    IMPORTANT:
    This is a normal function, NOT a class method.
    Therefore there is NO self here.
    """

    log(
        "[CrashlogViewer] Update installer finished."
    )

    log(
        "[CrashlogViewer] Installer result: %s"
        % result
    )


    # =====================================================
    # Installer Ergebnis prüfen
    # =====================================================

    if not installer_success(result):

        log(
            "[CrashlogViewer] Update installer FAILED."
        )


        session.open(
            MessageBox,
            _(
                "The update could not be installed."
            ),
            MessageBox.TYPE_ERROR,
            timeout=7
        )

        return


    # =====================================================
    # Installer erfolgreich
    # =====================================================

    log(
        "[CrashlogViewer] Update installer completed "
        "successfully."
    )


    # =====================================================
    # GUI Neustart Callback
    # =====================================================

    def restart_gui_callback(answer):

        # =================================================
        # JA
        # =================================================

        if answer:

            log(
                "[CrashlogViewer] User chose to restart "
                "the Enigma2 GUI."
            )

            try:

                from enigma import quitMainloop

                log(
                    "[CrashlogViewer] Restarting "
                    "Enigma2 GUI..."
                )

                quitMainloop(3)

            except Exception as e:

                log(
                    "[CrashlogViewer] Could not restart "
                    "Enigma2 GUI: %s"
                    % e
                )

                session.open(
                    MessageBox,
                    _(
                        "The GUI could not be restarted "
                        "automatically."
                    ),
                    MessageBox.TYPE_ERROR,
                    timeout=5
                )

        # =================================================
        # NEIN
        # =================================================

        else:

            log(
                "[CrashlogViewer] User chose NOT to restart "
                "the Enigma2 GUI."
            )

            session.open(
                MessageBox,
                _(
                    "Update installed successfully.\n\n"
                    "The Enigma2 GUI was not restarted."
                ),
                MessageBox.TYPE_INFO,
                timeout=5
            )


    # =====================================================
    # YES / NO Dialog
    # =====================================================

    session.openWithCallback(
        restart_gui_callback,

        MessageBox,

        _(
            "The update has been installed successfully.\n\n"
            "Would you like to restart the Enigma2 GUI now?"
        ),

        MessageBox.TYPE_YESNO
    )


# =========================================================
# Update prüfen
# =========================================================

def check_for_update(
    session,
    callback=None
):

    current_version = get_current_version()

    log(
        "[CrashlogViewer] Current version: %s"
        % current_version
    )


    remote_version = get_remote_version()


    # =====================================================
    # Remote Version konnte nicht geladen werden
    # =====================================================

    if not remote_version:

        session.open(
            MessageBox,
            _(
                "Could not fetch update information."
            ),
            MessageBox.TYPE_ERROR,
            timeout=5
        )

        if callback:

            callback()

        return


    log(
        "[CrashlogViewer] Remote version: %s"
        % remote_version
    )


    # =====================================================
    # Neue Version vorhanden
    # =====================================================

    if parse_version(remote_version) > parse_version(
        current_version
    ):

        remote_changelog = get_remote_changelog()


        msg = _(
            "New version {version} is available."
        ).format(
            version=remote_version
        )


        if remote_changelog:

            msg += (
                "\n\n"
                +
                _("Changelog:")
                +
                "\n"
                +
                remote_changelog
            )


        msg += (
            "\n\n"
            +
            _("Do you want to install it now?")
        )


        session.openWithCallback(

            lambda answer:
                install_update(
                    session,
                    answer,
                    INSTALLER_URL,
                    callback
                ),

            MessageBox,

            msg,

            MessageBox.TYPE_YESNO
        )

        return


    # =====================================================
    # Gleiche Version
    # =====================================================

    elif parse_version(remote_version) == parse_version(
        current_version
    ):

        msg = _(
            "You already have version {version} installed."
        ).format(
            version=remote_version
        )


        msg += (
            "\n\n"
            +
            _("Do you want to reinstall it?")
        )


        session.openWithCallback(

            lambda answer:
                install_update(
                    session,
                    answer,
                    INSTALLER_URL,
                    callback
                ),

            MessageBox,

            msg,

            MessageBox.TYPE_YESNO
        )

        return


    # =====================================================
    # Remote Version älter
    # =====================================================

    else:

        session.open(
            MessageBox,

            _(
                "The remote version ({remote}) is older "
                "than the current one ({current})."
            ).format(
                remote=remote_version,
                current=current_version
            ),

            MessageBox.TYPE_INFO,

            timeout=5
        )

        if callback:

            callback()


# =========================================================
# Crashlog Funktionen
# =========================================================

def isMountReadonly(mnt):

    try:

        with io.open(
            "/proc/mounts",
            "r",
            encoding="utf-8"
        ) as f:

            for line in f:

                parts = line.split()

                if len(parts) < 4:

                    continue

                device, mp, fs, flags = parts[:4]

                if mp == mnt:

                    return "ro" in flags

    except Exception:

        return False

    return False


def find_log_files(
    base_path=LOG_BASE_PATH
):

    patterns = [

        os.path.join(
            base_path,
            "*crash*.log"
        ),

        os.path.join(
            base_path,
            "*debug*.log"
        ),

        os.path.join(
            base_path,
            "*network*.log"
        ),

        "/media/usb/logs/*crash*.log",
        "/media/usb/logs/*debug*.log",
        "/media/usb/logs/*network*.log",

        "/media/hdd/logs/*crash*.log",
        "/media/hdd/logs/*debug*.log",
        "/media/hdd/logs/*network*.log",

    ]


    log_files = []


    for pattern in patterns:

        log_files.extend(
            glob.glob(pattern)
        )


    return sorted(
        list(
            set(log_files)
        )
    )


def delete_log_files(files):

    for file in files:

        try:

            remove(file)

        except OSError as e:

            log(
                "Error deleting %s: %s"
                % (
                    file,
                    e
                )
            )


# =========================================================
# CrashLogScreen
# =========================================================

class CrashLogScreen(Screen):

    sz_w = getDesktop(0).size().width()


    if sz_w == 1920:

        # -------------------------------------------------
        # Full HD Skin
        # -------------------------------------------------

        skin = """<screen name="crashlogscreen" position="260,100" size="1400,880" title="%s">
        <eLabel name="button info" font="Regular; 30" position="1063,821" size="103,48" cornerRadius="4" halign="center" valign="center" text="INFO" backgroundColor="black" zPosition="3" foregroundColor="red" />
        <eLabel name="button ext" font="Regular; 30" position="1173,821" size="103,48" cornerRadius="4" halign="center" valign="center" text="EXIT" backgroundColor="black" zPosition="3" foregroundColor="red" />
        <eLabel name="button ok" font="Regular; 30" position="1287,821" size="103,48" cornerRadius="4" halign="center" valign="center" text="OK" backgroundColor="black" zPosition="3" foregroundColor="red" />
        <eLabel backgroundColor="listRecording" position="0,858" size="250,6" zPosition="12" />
        <eLabel backgroundColor="green" position="260,858" size="250,6" zPosition="12" />
        <eLabel backgroundColor="yellow" position="520,858" size="250,6" zPosition="12" />
        <eLabel backgroundColor="blue" position="780,858" size="250,6" zPosition="12" />
        <widget source="Redkey" render="Label" position="0,814" size="250,45" font="Regular;26" />
        <widget source="Greenkey" render="Label" position="260,813" size="250,45" font="Regular;26" foregroundColor="green" />
        <widget source="Yellowkey" render="Label" position="520,814" size="250,45" font="Regular;26" foregroundColor="yellow" />
        <widget source="Bluekey" render="Label" position="780,814" size="250,45" font="Regular;26" foregroundColor="blue" />
        <widget source="menu" render="Listbox" position="4,7" size="1390,800" scrollbarMode="showOnDemand">
            <convert type="TemplatedMultiContent">
                {"template":[
                    MultiContentEntryText(pos=(70,2),size=(1300,50),font=0,flags=RT_HALIGN_LEFT,text=0),
                    MultiContentEntryText(pos=(80,35),size=(1300,50),font=1,flags=RT_HALIGN_LEFT,text=1),
                    MultiContentEntryPixmapAlphaTest(pos=(5,20),size=(45,32),png=2)],
                "fonts":[gFont("Regular",35),gFont("Regular",35)],
                "itemHeight":90}
            </convert>
        </widget>
        </screen>""" % _(
            "View or Remove Crashlog files"
        )


    else:

        # -------------------------------------------------
        # HD / Fallback Skin
        # -------------------------------------------------

        skin = """<screen name="crashlogscreen" position="center,center" size="1000,880" title="%s">
        <eLabel name="button info" font="Regular; 30" position="881,761" size="103,48" cornerRadius="4" halign="center" valign="center" text="INFO" backgroundColor="black" zPosition="3" foregroundColor="red" />
        <eLabel name="button ext" font="Regular; 30" position="773,761" size="103,48" cornerRadius="4" halign="center" valign="center" text="EXIT" backgroundColor="black" zPosition="3" foregroundColor="red" />
        <eLabel name="button ok" font="Regular; 30" position="663,761" size="103,48" cornerRadius="4" halign="center" valign="center" text="OK" backgroundColor="black" zPosition="3" foregroundColor="red" />
        <eLabel backgroundColor="listRecording" position="0,858" size="250,6" zPosition="12" />
        <eLabel backgroundColor="green" position="250,858" size="250,6" zPosition="12" />
        <eLabel backgroundColor="yellow" position="500,858" size="250,6" zPosition="12" />
        <eLabel backgroundColor="blue" position="750,858" size="250,6" zPosition="12" />
        <widget source="Redkey" render="Label" position="0,814" size="250,45" font="Regular;26" />
        <widget source="Greenkey" render="Label" position="252,813" size="250,45" font="Regular;26" foregroundColor="green" />
        <widget source="Yellowkey" render="Label" position="499,814" size="250,45" font="Regular;26" foregroundColor="yellow" />
        <widget source="Bluekey" render="Label" position="749,814" size="250,45" font="Regular;26" foregroundColor="blue" />
        <widget source="menu" render="Listbox" position="20,10" size="961,740" scrollbarMode="showOnDemand">
            <convert type="TemplatedMultiContent">
                {"template":[
                    MultiContentEntryText(pos=(70,2),size=(880,50),font=0,flags=RT_HALIGN_LEFT,text=0),
                    MultiContentEntryText(pos=(80,29),size=(880,50),font=1,flags=RT_HALIGN_LEFT,text=1),
                    MultiContentEntryPixmapAlphaTest(pos=(5,20),size=(45,32),png=2)],
                "fonts":[gFont("Regular",35),gFont("Regular",35)],
                "itemHeight":90}
            </convert>
        </widget>
        </screen>""" % _(
            "View or Remove Crashlog files"
        )


    def __init__(
        self,
        session
    ):

        self.session = session

        Screen.__init__(
            self,
            session
        )

        self.setTitle(
            _("View or Remove Crashlog files")
        )


        self["Redkey"] = StaticText(
            _("Close")
        )

        self["Greenkey"] = StaticText(
            _("View")
        )

        self["Yellowkey"] = StaticText(
            _("Remove")
        )

        self["Bluekey"] = StaticText(
            _("Remove All")
        )


        self.list = []


        self["menu"] = List(
            self.list
        )


        self["shortcuts"] = ActionMap(
            [
                "ShortcutActions",
                "WizardActions",
                "EPGSelectActions"
            ],
            {
                "ok": self.Ok,
                "cancel": self.exit,
                "back": self.exit,
                "red": self.exit,
                "green": self.Ok,
                "yellow": self.YellowKey,
                "blue": self.BlueKey,
                "epg": self.infoKey,
            }
        )


        self.CfgMenu()


    def CfgMenu(self):

        self.list = []

        log_files = find_log_files()


        if not log_files:

            self["menu"].setList([])

            return


        sz_w = getDesktop(0).size().width()


        minipng = LoadPixmap(
            cached=True,
            path=resolveFilename(
                SCOPE_PLUGINS,
                "Extensions/CrashlogViewer/images/crashmini.png"
            )
            if sz_w >= 1920
            else
            resolveFilename(
                SCOPE_PLUGINS,
                "Extensions/CrashlogViewer/images/crashmini1.png"
            )
        )


        for file_path in log_files:

            try:

                stat = os.stat(
                    file_path
                )

                file_size = stat.st_size

                file_date = time.strftime(
                    "%Y-%m-%d %H:%M",
                    time.localtime(
                        stat.st_mtime
                    )
                )


                self.list.append(
                    (
                        os.path.basename(
                            file_path
                        ),

                        "Size: %s - Date: %s"
                        % (
                            file_size,
                            file_date
                        ),

                        minipng,

                        file_path
                    )
                )


            except Exception as e:

                log(
                    "Error accessing file %s: %s"
                    % (
                        file_path,
                        e
                    )
                )


        self["menu"].setList(
            self.list
        )


    def Ok(self):

        item = self["menu"].getCurrent()


        if not item or len(item) < 4:

            self.session.open(
                MessageBox,
                _("No log file selected!"),
                MessageBox.TYPE_INFO,
                timeout=4
            )

            return


        self.session.openWithCallback(
            self.CfgMenu,
            LogScreen,
            str(
                item[3]
            )
        )


    def YellowKey(self):

        item = self["menu"].getCurrent()


        if not item or len(item) < 4:

            return


        try:

            os.remove(
                str(
                    item[3]
                )
            )

            self.session.open(
                MessageBox,
                _("Removed %s")
                % item[3],
                MessageBox.TYPE_INFO,
                timeout=4
            )


        except Exception as e:

            self.session.open(
                MessageBox,
                _("Failed to remove file:\n%s")
                % e,
                MessageBox.TYPE_INFO,
                timeout=4
            )


        self.CfgMenu()


    def BlueKey(self):

        log_files = find_log_files()

        deleted_files = 0

        failed_files = []


        for f in log_files:

            if not isMountReadonly(
                os.path.dirname(f)
            ):

                try:

                    os.remove(f)

                    deleted_files += 1

                except Exception as e:

                    failed_files.append(
                        "%s (%s)"
                        % (
                            f,
                            e
                        )
                    )


        if deleted_files:

            msg = _(
                "Removed %d log files"
            ) % deleted_files

        else:

            msg = _(
                "No log files found to remove"
            )


        if failed_files:

            msg += (
                "\n"
                +
                _(
                    "Failed to remove some files:\n"
                )
                +
                "\n".join(
                    failed_files
                )
            )


        self.session.open(
            MessageBox,
            msg,
            MessageBox.TYPE_INFO,
            timeout=6
        )


        self.CfgMenu()


    def infoKey(self):

        self.session.open(
            MessageBox,
            _(
                "Crashlog Viewer  ver. %s\n\n"
                "Developer: 2boom\n\n"
                "Modifier: Evg77734\n\n"
                "Update from Lululla\n"
                "Homepage: gisclub.tv"
            ) % get_local_version(),
            MessageBox.TYPE_INFO
        )


    def exit(self):

        self.close()


# =========================================================
# LogScreen
# =========================================================

class LogScreen(Screen):

    sz_w = getDesktop(0).size().width()


    if sz_w == 1920:

        # -------------------------------------------------
        # Full HD
        # -------------------------------------------------

        skin = """<screen name="LogScreen" position="70,68" size="1780,980" title="%s" flags="wfBorder">
            <eLabel name="button info" font="Regular; 30" position="1667,924" size="103,48" cornerRadius="4" halign="center" valign="center" text="INFO" backgroundColor="black" zPosition="3" foregroundColor="red" />
            <eLabel name="button ext" font="Regular; 30" position="1555,924" size="103,48" cornerRadius="4" halign="center" valign="center" text="EXIT" backgroundColor="black" zPosition="3" foregroundColor="red" />
            <eLabel name="button ok" font="Regular; 30" position="1444,924" size="103,48" cornerRadius="4" halign="center" valign="center" text="OK" backgroundColor="black" zPosition="3" foregroundColor="red" />
            <widget source="Redkey" render="Label" position="7,921" size="250,45" zPosition="11" font="Regular; 26" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" />
            <widget source="Greenkey" render="Label" position="269,921" size="250,45" zPosition="11" font="Regular; 26" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="green" />
            <eLabel backgroundColor="#00ff0000" position="6,969" size="250,6" zPosition="12" />
            <eLabel backgroundColor="#0000ff00" position="269,969" size="250,6" zPosition="12" />
            <widget name="text" position="2,1" size="1770,800" font="Console; 28" foregroundColor="green" />
            <widget name="text2" position="3,805" size="1770,110" font="Console; 28" foregroundColor="#ff0000" />
            <eLabel position="3,801" size="1770,2" backgroundColor="#555555" zPosition="1" />
        </screen>""" % _(
            "View Crashlog file"
        )


    else:

        # -------------------------------------------------
        # HD / Fallback
        # -------------------------------------------------

        skin = """<screen name="LogScreen" position="240,140" size="1440,800" title="%s" flags="wfBorder">
            <eLabel name="button info" font="Regular; 30" position="1323,741" size="103,48" cornerRadius="4" halign="center" valign="center" text="INFO" backgroundColor="black" zPosition="3" foregroundColor="red" />
            <eLabel name="button ext" font="Regular; 30" position="1206,741" size="103,48" cornerRadius="4" halign="center" valign="center" text="EXIT" backgroundColor="black" zPosition="3" foregroundColor="red" />
            <eLabel name="button ok" font="Regular; 30" position="1092,741" size="103,48" cornerRadius="4" halign="center" valign="center" text="OK" backgroundColor="black" zPosition="3" foregroundColor="red" />
            <widget source="Redkey" render="Label" position="7,742" size="250,45" zPosition="11" font="Regular; 26" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" />
            <widget source="Greenkey" render="Label" position="266,742" size="250,45" zPosition="11" font="Regular; 26" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="green" />
            <eLabel backgroundColor="#00ff0000" position="8,790" size="250,6" zPosition="12" />
            <eLabel backgroundColor="#0000ff00" position="267,790" size="250,6" zPosition="12" />
            <widget name="text" position="3,3" size="1430,610" font="Console; 28" foregroundColor="green" />
            <widget name="text2" position="3,619" size="1430,110" font="Console; 28" foregroundColor="#ff0000" />
            <eLabel position="3,615" size="1430,2" backgroundColor="#555555" zPosition="1" />
        </screen>""" % _(
            "View Crashlog file"
        )


    def __init__(
        self,
        session,
        crashfile
    ):

        Screen.__init__(
            self,
            session
        )

        self.session = session

        self.crashfile = crashfile


        self.setTitle(
            _("View Crashlog file")
        )


        self["Redkey"] = StaticText(
            _("Close")
        )

        self["Greenkey"] = StaticText(
            _("Restart GUI")
        )


        self["text"] = ScrollLabel(
            ""
        )

        self["text2"] = ScrollLabel(
            ""
        )


        self["actions"] = ActionMap(
            [
                "OkCancelActions",
                "DirectionActions",
                "ColorActions"
            ],
            {
                "cancel": self.exit,
                "ok": self.exit,
                "red": self.exit,

                "green": self.restartGUI,

                "up": self.scrollUp,
                "down": self.scrollDown,

                "left": self.scrollPageUp,
                "right": self.scrollPageDown,
            },
            -1
        )


        self.loadLogFile()


    def loadLogFile(self):

        full_text = ""

        error_text = ""


        try:

            if not os.path.exists(
                self.crashfile
            ):

                full_text = _(
                    "File not found: %s"
                ) % self.crashfile


            else:

                # -------------------------------------------------
                # io.open verwenden, damit Python 2 ebenfalls
                # encoding/errors unterstützt.
                # -------------------------------------------------

                with io.open(
                    self.crashfile,
                    "r",
                    encoding="utf-8",
                    errors="replace"
                ) as f:

                    for line in f:

                        full_text += line


                        if (
                            "Error:" in line
                            or
                            "FATAL SIGNAL" in line
                        ):

                            error_text += line


        except Exception as e:

            full_text = _(
                "Error opening file:\n%s"
            ) % e


        self["text"].setText(
            full_text
        )

        self["text2"].setText(
            error_text
        )


    # =====================================================
    # Scroll
    # =====================================================

    def scrollUp(self):

        self["text"].moveUp()

        self["text2"].moveUp()


    def scrollDown(self):

        self["text"].moveDown()

        self["text2"].moveDown()


    def scrollPageUp(self):

        self["text"].pageUp()

        self["text2"].pageUp()


    def scrollPageDown(self):

        self["text"].pageDown()

        self["text2"].pageDown()


    # =====================================================
    # GUI Neustart über grüne Taste
    # =====================================================

    def restartGUI(self):

        try:

            from enigma import quitMainloop

            log(
                "[CrashlogViewer] Manual GUI restart."
            )

            quitMainloop(3)

        except Exception as e:

            log(
                "[CrashlogViewer] Could not restart "
                "Enigma2 GUI: %s"
                % e
            )


    def exit(self):

        self.close()


# =========================================================
# Menü
# =========================================================

def menu(
    menuid,
    **kwargs
):

    if menuid == "mainmenu":

        plugin_name = (
            _("Crashlog Viewer")
            +
            " ver. "
            +
            get_local_version()
        )


        return [
            (
                plugin_name,
                main,
                "CrashlogViewer_mainmenu",
                50
            )
        ]


    return []


# =========================================================
# Main
# =========================================================

def main(
    session,
    **kwargs
):

    check_for_update(
        session,

        lambda:
            session.open(
                CrashLogScreen
            )
    )


# =========================================================
# Plugin Descriptor
# =========================================================

def Plugins(
    **kwargs
):

    return [

        PluginDescriptor(
            name=(
                _("Crashlog Viewer")
                +
                " ver. "
                +
                get_local_version()
            ),

            description=_(
                "View and remove crashlog files"
            ),

            where=[
                PluginDescriptor.WHERE_PLUGINMENU,
                PluginDescriptor.WHERE_EXTENSIONSMENU
            ],

            icon="crash.png",

            fnc=main,
        ),


        PluginDescriptor(
            where=PluginDescriptor.WHERE_MENU,
            fnc=menu
        ),

    ]
