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
import traceback
import time
import glob

from os import remove

from Components.ActionMap import ActionMap
from Components.ScrollLabel import ScrollLabel
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.Directories import SCOPE_PLUGINS, resolveFilename
from Tools.LoadPixmap import LoadPixmap

from enigma import getDesktop


# =========================================================
# Plugin
# =========================================================

PLUGIN_PATH = "/usr/lib/enigma2/python/Plugins/Extensions/CrashlogViewer/"
LOCALE_DIR = os.path.join(PLUGIN_PATH, "locale")

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

    gettext.textdomain(DOMAIN)


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

        with open(LOGFILE, "a") as f:
            f.write(msg + "\n")

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
    "speedy005/CrashlogViewer/main/install.sh"
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

LAST_UPDATE_FILE = os.path.join(
    PLUGIN_PATH,
    "last_update_version.txt"
)


def get_local_version():

    try:

        with open(VERSION_FILE, "r") as f:
            return f.read().strip()

    except Exception:

        return version


def get_current_version():

    try:

        with open(VERSION_FILE, "r") as f:
            return f.read().strip()

    except Exception:

        return version


# =========================================================
# Remote Version
# =========================================================

def get_remote_version():

    try:

        request = urllib_request.Request(
            GITHUB_VERSION_URL,
            headers={
                "User-Agent": "CrashlogViewer-Updater/2.5.0"
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

        remote_version = response.strip().split()[0]

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
                "User-Agent": "CrashlogViewer-Updater/2.5.0"
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
# Update starten
# =========================================================

def install_update(session, answer, installer_url):

    """Runs the update installer if the user confirmed."""

    if answer:

        # -------------------------------------------------
        # Installer herunterladen und mit Bash ausführen
        # -------------------------------------------------

        cmd = (
            "TMP=/tmp/CrashlogViewer-installer.sh; "
            "wget -q --no-check-certificate "
            "\"%s\" -O \"$TMP\" && "
            "chmod 755 \"$TMP\" && "
            "/bin/bash \"$TMP\"; "
            "RET=$?; "
            "rm -f \"$TMP\"; "
            "exit $RET"
        ) % installer_url

        try:

            from Screens.Console import Console

        except Exception as e:

            log(
                "[CrashlogViewer] Could not import Console: %s"
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

            return

        log(
            "[CrashlogViewer] Starting update installer..."
        )

        session.open(
            Console,
            _("Updating..."),
            cmdlist=[
                cmd
            ],
            finishedCallback=lambda result=None:
                update_finished(
                    session,
                    result
                ),
            closeOnSuccess=True
        )

    else:

        log(
            "[CrashlogViewer] Update canceled by user."
        )

        session.open(
            MessageBox,
            _("Update canceled."),
            MessageBox.TYPE_INFO,
            timeout=3
        )


# =========================================================
# Update abgeschlossen
# =========================================================

def update_finished(session, result=None):

    """Callback executed when the installation finishes."""

    log(
        "[CrashlogViewer] Update installer finished."
    )

    # -----------------------------------------------------
    # GUI Neustart Abfrage
    # -----------------------------------------------------

    def restart_gui_callback(answer):

        # -------------------------------------------------
        # YES
        # -------------------------------------------------

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

        # -------------------------------------------------
        # NO
        # -------------------------------------------------

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

    # -----------------------------------------------------
    # YES / NO Dialog
    # -----------------------------------------------------

    session.openWithCallback(
        restart_gui_callback,
        MessageBox,
        _(
            "The update has been installed successfully.\n\n"
            "Would you like to restart the Enigma2 GUI now?"
        ),
        MessageBox.TYPE_YESNO
    )

    # -----------------------------------------------------
    # GUI Neustart Abfrage
    # -----------------------------------------------------

    def restart_gui_callback(answer):

        # -------------------------------------------------
        # YES
        # -------------------------------------------------

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

                self.session.open(
                    MessageBox,
                    _(
                        "The GUI could not be restarted "
                        "automatically."
                    ),
                    MessageBox.TYPE_ERROR,
                    timeout=5
                )

        # -------------------------------------------------
        # NO
        # -------------------------------------------------

        else:

            log(
                "[CrashlogViewer] User chose NOT to restart "
                "the Enigma2 GUI."
            )

            self.session.open(
                MessageBox,
                _(
                    "Update installed successfully.\n\n"
                    "The Enigma2 GUI was not restarted."
                ),
                MessageBox.TYPE_INFO,
                timeout=5
            )

    # -----------------------------------------------------
    # YES / NO Dialog
    # -----------------------------------------------------

    self.session.openWithCallback(
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

def check_for_update(session, callback=None):

    current_version = get_current_version()

    log(
        "[CrashlogViewer] Current version: %s"
        % current_version
    )

    remote_version = get_remote_version()

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

    # -----------------------------------------------------
    # Neue Version vorhanden
    # -----------------------------------------------------

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
                "\n\n" +
                _("Changelog:") +
                "\n" +
                remote_changelog
            )

        msg += (
            "\n\n" +
            _("Do you want to install it now?")
        )

        session.openWithCallback(
            lambda answer:
                install_update(
                    session,
                    answer,
                    INSTALLER_URL
                ),
            MessageBox,
            msg,
            MessageBox.TYPE_YESNO
        )

        return

    # -----------------------------------------------------
    # Gleiche Version
    # -----------------------------------------------------

    elif parse_version(remote_version) == parse_version(
        current_version
    ):

        msg = _(
            "You already have version {version} installed."
        ).format(
            version=remote_version
        )

        msg += (
            "\n\n" +
            _("Do you want to reinstall it?")
        )

        session.openWithCallback(
            lambda answer:
                install_update(
                    session,
                    answer,
                    INSTALLER_URL
                ),
            MessageBox,
            msg,
            MessageBox.TYPE_YESNO
        )

        return

    # -----------------------------------------------------
    # Remote Version älter
    # -----------------------------------------------------

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

        with open(
            "/proc/mounts",
            "r"
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

        # Full HD Skin

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
        </screen>""" % _("View or Remove Crashlog files")

    else:

        # HD / Fallback Skin

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
        </screen>""" % _("View or Remove Crashlog files")


    def __init__(self, session):

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
            if sz_w >= 1920 else
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
            str(item[3])
        )


    def YellowKey(self):

        item = self["menu"].getCurrent()

        if not item or len(item) < 4:

            return

        try:

            os.remove(
                str(item[3])
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
                "\n" +
                _(
                    "Failed to remove some files:\n"
                ) +
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
            ) % version,
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

        # Full HD Skin

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
        </screen>""" % _("View Crashlog file")

    else:

        # HD / Fallback Skin

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
        </screen>""" % _("View Crashlog file")


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

        # -------------------------------------------------
        # Scroll- und Farb-Tasten
        # -------------------------------------------------

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

                with open(
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


    # -----------------------------------------------------
    # Scrollsteuerung
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # GUI Neustart über grüne Taste
    # -----------------------------------------------------

    def restartGUI(self):

        try:

            from enigma import quitMainloop

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
# Menü & Plugins
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
            name=_("Crashlog Viewer")
            +
            " ver. "
            +
            get_local_version(),

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
