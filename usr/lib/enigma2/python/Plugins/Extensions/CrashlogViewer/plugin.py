#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# CrashlogViewer Enigma2 Plugin mit Update-Funktion
# updated Lululla 05/06/2023, 30/04/2024, 30/08/2024,
# 22/09/2024, 17/11/2024
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
import shlex

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
# Plugin-Grunddaten
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

LOGFILE = "/tmp/CrashlogViewer.log"
UPDATE_LOGFILE = "/tmp/CrashlogViewer-update.log"
UPDATE_STATUS_FILE = "/tmp/CrashlogViewer-update.status"
INSTALLER_TMP = "/tmp/CrashlogViewer-installer.sh"


# =========================================================
# Python 2 / Python 3
# =========================================================

try:
    import urllib2 as urllib_request
except Exception:
    import urllib.request as urllib_request


PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3


# =========================================================
# Logging
# =========================================================

def log(msg):

    try:
        if PY2:
            text = unicode(msg)
        else:
            text = str(msg)

        with io.open(
            LOGFILE,
            "a",
            encoding="utf-8"
        ) as logfile:

            logfile.write(text)
            logfile.write(u"\n")

    except Exception:
        pass

    try:
        print(msg)
    except Exception:
        pass


def clear_update_files():

    for file_path in (
        UPDATE_LOGFILE,
        UPDATE_STATUS_FILE,
        INSTALLER_TMP
    ):

        try:
            if os.path.exists(file_path):
                os.remove(file_path)

        except Exception as e:

            log(
                "[CrashlogViewer] Could not remove %s: %s"
                % (
                    file_path,
                    e
                )
            )


# =========================================================
# Locale
# =========================================================

def localeInit():

    try:

        lang = language.getLanguage()[:2]

        os.environ["LANGUAGE"] = lang

        gettext.bindtextdomain(
            DOMAIN,
            LOCALE_DIR
        )

        gettext.textdomain(DOMAIN)

    except Exception as e:

        log(
            "[CrashlogViewer] Locale error: %s"
            % e
        )


def _(txt):

    try:

        translated = gettext.dgettext(
            DOMAIN,
            txt
        )

        if translated == txt:
            translated = gettext.gettext(txt)

        return translated

    except Exception:

        return txt


localeInit()
language.addCallback(localeInit)


# =========================================================
# Update-URLs
# =========================================================

INSTALLER_URL = (
    "https://raw.githubusercontent.com/"
    "speedy005/CrashlogViewer/main/installer.sh"
)

GITHUB_VERSION_URL = (
    "https://raw.githubusercontent.com/"
    "speedy005/CrashlogViewer/main/version.txt"
)

# Optional: Die Datei darf fehlen.
# Ein 404 wird nicht als Updatefehler behandelt.
GITHUB_CHANGELOG_URL = (
    "https://raw.githubusercontent.com/"
    "speedy005/CrashlogViewer/main/changelog.txt"
)


# =========================================================
# Lokale Version
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
        ) as version_file:

            local_version = version_file.read().strip()

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
# Remote-Version
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
            timeout=15
        ).read()

        if not isinstance(response, str):

            response = response.decode(
                "utf-8",
                "replace"
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
            "[CrashlogViewer] Error fetching remote version: %s"
            % e
        )

        return None


# =========================================================
# Remote-Changelog
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
            timeout=15
        ).read()

        if not isinstance(response, str):

            response = response.decode(
                "utf-8",
                "replace"
            )

        return response.strip()

    except Exception as e:

        # Changelog ist optional.
        # Ein fehlendes changelog.txt darf das Update nicht verhindern.
        log(
            "[CrashlogViewer] Changelog unavailable: %s"
            % e
        )

        return ""


# =========================================================
# Versionsvergleich
# =========================================================

def parse_version(version_str):

    if not version_str:
        return (0, 0, 0)

    value = str(version_str).strip().lower()

    if value.startswith("v"):
        value = value[1:]

    parts = re.findall(
        r"\d+",
        value
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
# Update-Status
# =========================================================

def read_update_status():

    try:

        if not os.path.exists(UPDATE_STATUS_FILE):
            return None

        with io.open(
            UPDATE_STATUS_FILE,
            "r",
            encoding="utf-8"
        ) as status_file:

            value = status_file.read().strip()

        if not value:
            return None

        return int(value)

    except Exception as e:

        log(
            "[CrashlogViewer] Could not read update status: %s"
            % e
        )

        return None


def remove_update_status():

    try:

        if os.path.exists(UPDATE_STATUS_FILE):
            os.remove(UPDATE_STATUS_FILE)

    except Exception as e:

        log(
            "[CrashlogViewer] Could not remove status file: %s"
            % e
        )


def get_result_code(result):

    try:

        if isinstance(result, (tuple, list)):

            if not result:
                return None

            return int(result[-1])

        if result is None:
            return None

        return int(result)

    except Exception as e:

        log(
            "[CrashlogViewer] Could not evaluate Console result: %s"
            % e
        )

        return None


# =========================================================
# Update starten
# =========================================================

def install_update(
    session,
    answer,
    installer_url,
    callback=None
):

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

    clear_update_files()

    tmp_file = shlex.quote(INSTALLER_TMP)
    url = shlex.quote(installer_url)
    status_file = shlex.quote(UPDATE_STATUS_FILE)
    update_log = shlex.quote(UPDATE_LOGFILE)

    # Der Console-Callback liefert auf manchen Images None.
    # Deshalb wird der echte Installer-Exitcode immer zusätzlich
    # in UPDATE_STATUS_FILE gespeichert.
    cmd = (
        "STATUS={status}; "
        "TMP={tmp}; "
        "LOG={log}; "

        "echo '[CrashlogViewer] Starting update' >> $LOG; "
        "echo '[CrashlogViewer] Installer URL: {url}' >> $LOG; "

        "rm -f $STATUS $TMP; "

        "echo '[CrashlogViewer] Downloading installer...' | tee -a $LOG; "
        "wget "
        "--no-check-certificate "
        "--timeout=30 "
        "--tries=3 "
        "{url} "
        "-O $TMP >> $LOG 2>&1; "

        "RET=$?; "

        "if [ $RET -ne 0 ]; then "
        "echo '[CrashlogViewer] Installer download failed' | tee -a $LOG; "
        "echo $RET > $STATUS; "
        "rm -f $TMP; "
        "exit 0; "
        "fi; "

        "if [ ! -s $TMP ]; then "
        "echo '[CrashlogViewer] Downloaded installer is empty' | tee -a $LOG; "
        "echo 2 > $STATUS; "
        "rm -f $TMP; "
        "exit 0; "
        "fi; "

        "echo '[CrashlogViewer] Checking installer syntax...' | tee -a $LOG; "
        "/bin/bash -n $TMP >> $LOG 2>&1; "

        "RET=$?; "

        "if [ $RET -ne 0 ]; then "
        "echo '[CrashlogViewer] Installer syntax check failed' | tee -a $LOG; "
        "echo $RET > $STATUS; "
        "rm -f $TMP; "
        "exit 0; "
        "fi; "

        "chmod 755 $TMP; "

        "RET=$?; "

        "if [ $RET -ne 0 ]; then "
        "echo '[CrashlogViewer] chmod failed' | tee -a $LOG; "
        "echo $RET > $STATUS; "
        "rm -f $TMP; "
        "exit 0; "
        "fi; "

        "echo '[CrashlogViewer] Running installer...' | tee -a $LOG; "
        "/bin/bash $TMP >> $LOG 2>&1; "

        "RET=$?; "

        "echo '[CrashlogViewer] Installer exit code: ' $RET | tee -a $LOG; "
        "echo $RET > $STATUS; "

        "rm -f $TMP; "

        # Console soll selbst erfolgreich schließen.
        # Der tatsächliche Installerstatus steht in STATUS.
        "exit 0"
    ).format(
        status=status_file,
        tmp=tmp_file,
        log=update_log,
        url=url
    )

    log(
        "[CrashlogViewer] Starting update installer."
    )

    log(
        "[CrashlogViewer] Installer URL: %s"
        % installer_url
    )

    try:

        session.open(
            Console,
            _("Updating CrashlogViewer..."),
            cmdlist=[cmd],
            finishedCallback=lambda result=None:
                update_finished(
                    session,
                    result,
                    callback
                ),
            closeOnSuccess=False
        )

    except Exception as e:

        log(
            "[CrashlogViewer] Could not start installer: %s"
            % e
        )

        session.open(
            MessageBox,
            _(
                "Could not start the update installer.\n\n%s"
            ) % e,
            MessageBox.TYPE_ERROR,
            timeout=7
        )


# =========================================================
# Update abgeschlossen
# =========================================================

def update_finished(
    session,
    result=None,
    callback=None
):

    log(
        "[CrashlogViewer] Update installer finished."
    )

    log(
        "[CrashlogViewer] Console result: %s"
        % result
    )

    # Der Status aus der Datei hat Priorität.
    # Damit funktioniert es auch auf Images, die None liefern.
    status = read_update_status()

    if status is None:

        status = get_result_code(result)

    remove_update_status()

    log(
        "[CrashlogViewer] Effective installer status: %s"
        % status
    )

    if status != 0:

        if status is None:
            status_text = _("unknown")

        else:
            status_text = str(status)

        log(
            "[CrashlogViewer] Update failed with code: %s"
            % status_text
        )

        session.open(
            MessageBox,
            _(
                "The update could not be installed.\n\n"
                "Installer return code: %s\n\n"
                "See %s and %s for more information."
            ) % (
                status_text,
                LOGFILE,
                UPDATE_LOGFILE
            ),
            MessageBox.TYPE_ERROR,
            timeout=10
        )

        return

    log(
        "[CrashlogViewer] Update installed successfully."
    )

    def restart_gui_callback(answer):

        if answer:

            log(
                "[CrashlogViewer] Restarting Enigma2 GUI."
            )

            try:

                from enigma import quitMainloop

                quitMainloop(3)

            except Exception as e:

                log(
                    "[CrashlogViewer] GUI restart failed: %s"
                    % e
                )

                session.open(
                    MessageBox,
                    _(
                        "The GUI could not be restarted "
                        "automatically.\n\n%s"
                    ) % e,
                    MessageBox.TYPE_ERROR,
                    timeout=7
                )

        else:

            log(
                "[CrashlogViewer] User declined GUI restart."
            )

            session.open(
                MessageBox,
                _(
                    "Update installed successfully.\n\n"
                    "Please restart the Enigma2 GUI manually "
                    "to load the new version."
                ),
                MessageBox.TYPE_INFO,
                timeout=7
            )

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

    if not remote_version:

        session.open(
            MessageBox,
            _("Could not fetch update information."),
            MessageBox.TYPE_ERROR,
            timeout=5
        )

        if callback:
            callback()

        return

    current_parsed = parse_version(current_version)
    remote_parsed = parse_version(remote_version)

    if remote_parsed > current_parsed:

        changelog = get_remote_changelog()

        message = _(
            "New version {version} is available."
        ).format(
            version=remote_version
        )

        if changelog:

            message += (
                "\n\n"
                + _("Changelog:")
                + "\n"
                + changelog
            )

        message += (
            "\n\n"
            + _("Do you want to install it now?")
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
            message,
            MessageBox.TYPE_YESNO
        )

        return

    if remote_parsed == current_parsed:

        message = _(
            "You already have version {version} installed."
        ).format(
            version=remote_version
        )

        message += (
            "\n\n"
            + _("Do you want to reinstall it?")
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
            message,
            MessageBox.TYPE_YESNO
        )

        return

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
# Crashlog-Funktionen
# =========================================================

def isMountReadonly(mnt):

    try:

        with io.open(
            "/proc/mounts",
            "r",
            encoding="utf-8"
        ) as mounts:

            for line in mounts:

                parts = line.split()

                if len(parts) < 4:
                    continue

                mountpoint = parts[1]
                flags = parts[3]

                if mountpoint == mnt:
                    return "ro" in flags.split(",")

    except Exception:
        pass

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
        "/media/hdd/logs/*network*.log"

    ]

    log_files = []

    for pattern in patterns:
        log_files.extend(glob.glob(pattern))

    return sorted(
        list(set(log_files))
    )


def delete_log_files(files):

    for file_path in files:

        try:

            remove(file_path)

        except OSError as e:

            log(
                "Error deleting %s: %s"
                % (
                    file_path,
                    e
                )
            )


# =========================================================
# CrashLogScreen
# =========================================================

class CrashLogScreen(Screen):

    sz_w = getDesktop(0).size().width()

    if sz_w == 1920:

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

    def __init__(self, session):

        Screen.__init__(
            self,
            session
        )

        self.session = session

        self.setTitle(
            _("View or Remove Crashlog files")
        )

        self["Redkey"] = StaticText(_("Close"))
        self["Greenkey"] = StaticText(_("View"))
        self["Yellowkey"] = StaticText(_("Remove"))
        self["Bluekey"] = StaticText(_("Remove All"))

        self.list = []

        self["menu"] = List(self.list)

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
                "epg": self.infoKey
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

        if sz_w >= 1920:

            image_name = "crashmini.png"

        else:

            image_name = "crashmini1.png"

        minipng = LoadPixmap(
            cached=True,
            path=resolveFilename(
                SCOPE_PLUGINS,
                "Extensions/CrashlogViewer/images/%s"
                % image_name
            )
        )

        for file_path in log_files:

            try:

                stat = os.stat(file_path)

                file_size = stat.st_size

                file_date = time.strftime(
                    "%Y-%m-%d %H:%M",
                    time.localtime(stat.st_mtime)
                )

                self.list.append(
                    (
                        os.path.basename(file_path),
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

        self["menu"].setList(self.list)

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

        file_path = str(item[3])

        try:

            os.remove(file_path)

            self.session.open(
                MessageBox,
                _("Removed %s") % file_path,
                MessageBox.TYPE_INFO,
                timeout=4
            )

        except Exception as e:

            self.session.open(
                MessageBox,
                _("Failed to remove file:\n%s") % e,
                MessageBox.TYPE_ERROR,
                timeout=5
            )

        self.CfgMenu()

    def BlueKey(self):

        log_files = find_log_files()

        deleted_files = 0
        failed_files = []

        for file_path in log_files:

            if isMountReadonly(
                os.path.dirname(file_path)
            ):

                continue

            try:

                os.remove(file_path)
                deleted_files += 1

            except Exception as e:

                failed_files.append(
                    "%s (%s)"
                    % (
                        file_path,
                        e
                    )
                )

        if deleted_files:

            message = _(
                "Removed %d log files"
            ) % deleted_files

        else:

            message = _(
                "No log files found to remove"
            )

        if failed_files:

            message += (
                "\n\n"
                + _("Failed to remove some files:")
                + "\n"
                + "\n".join(failed_files)
            )

        self.session.open(
            MessageBox,
            message,
            MessageBox.TYPE_INFO,
            timeout=7
        )

        self.CfgMenu()

    def infoKey(self):

        self.session.open(
            MessageBox,
            _(
                "Crashlog Viewer ver. %s\n\n"
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

    def __init__(self, session, crashfile):

        Screen.__init__(
            self,
            session
        )

        self.session = session
        self.crashfile = crashfile

        self.setTitle(_("View Crashlog file"))

        self["Redkey"] = StaticText(_("Close"))
        self["Greenkey"] = StaticText(_("Restart GUI"))

        self["text"] = ScrollLabel("")
        self["text2"] = ScrollLabel("")

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
                "right": self.scrollPageDown
            },
            -1
        )

        self.loadLogFile()

    def loadLogFile(self):

        full_text = ""
        error_text = ""

        try:

            if not os.path.exists(self.crashfile):

                full_text = _(
                    "File not found: %s"
                ) % self.crashfile

            else:

                with io.open(
                    self.crashfile,
                    "r",
                    encoding="utf-8",
                    errors="replace"
                ) as logfile:

                    for line in logfile:

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

        self["text"].setText(full_text)
        self["text2"].setText(error_text)

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

    def restartGUI(self):

        try:

            from enigma import quitMainloop

            log("[CrashlogViewer] Manual GUI restart.")

            quitMainloop(3)

        except Exception as e:

            log(
                "[CrashlogViewer] Could not restart GUI: %s"
                % e
            )

    def exit(self):
        self.close()


# =========================================================
# Menü
# =========================================================

def menu(menuid, **kwargs):

    if menuid == "mainmenu":

        plugin_name = (
            _("Crashlog Viewer")
            + " ver. "
            + get_local_version()
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

def main(session, **kwargs):

    check_for_update(
        session,
        lambda: session.open(CrashLogScreen)
    )


# =========================================================
# Plugin-Descriptor
# =========================================================

def Plugins(**kwargs):

    return [

        PluginDescriptor(
            name=(
                _("Crashlog Viewer")
                + " ver. "
                + get_local_version()
            ),
            description=_(
                "View and remove crashlog files"
            ),
            where=[
                PluginDescriptor.WHERE_PLUGINMENU,
                PluginDescriptor.WHERE_EXTENSIONSMENU
            ],
            icon="crash.png",
            fnc=main
        ),

        PluginDescriptor(
            where=PluginDescriptor.WHERE_MENU,
            fnc=menu
        )

    ]
