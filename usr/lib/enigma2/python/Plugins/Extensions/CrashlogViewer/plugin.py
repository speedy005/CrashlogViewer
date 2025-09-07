#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# CrashlogViewer Enigma2 Plugin mit Update-Funktion
# updated Lululla 05/06/2023, 30/04/2024, 30/08/2024, 22/09/2024, 17/11/2024
# updated speedy005 06/09/2025

from __future__ import print_function
import gettext
from Components.Language import language
import os, sys, re, shutil, tempfile, zipfile, traceback, time, glob
from os import remove
from Components.ActionMap import ActionMap
from Components.ScrollLabel import ScrollLabel
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Tools.Directories import SCOPE_PLUGINS, resolveFilename
from Tools.LoadPixmap import LoadPixmap
from enigma import getDesktop

PLUGIN_PATH = "/usr/lib/enigma2/python/Plugins/Extensions/CrashlogViewer/"
LOCALE_DIR = os.path.join(PLUGIN_PATH, "locale")
DOMAIN = "CrashlogViewer"
LOG_BASE_PATH = "/home/root/logs/"
version = "2.0" 
# --- Locale ---
def localeInit():
    lang = language.getLanguage()[:2]
    os.environ["LANGUAGE"] = lang
    gettext.bindtextdomain(DOMAIN, LOCALE_DIR)
    gettext.textdomain(DOMAIN)

def _(txt):
    t = gettext.dgettext(DOMAIN, txt)
    if t == txt:
        t = gettext.gettext(txt)
    return t

localeInit()
language.addCallback(localeInit)

# --- Python 2/3 urllib ---
try:
    import urllib2 as urllib_request
except Exception:
    import urllib.request as urllib_request

# --- Update URLs & Files ---
VERSION_FILE = os.path.join(PLUGIN_PATH, "version.txt")
LAST_UPDATE_FILE = os.path.join(PLUGIN_PATH, "last_update_version.txt")
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/speedy005/CrashlogViewer/main/version.txt"
GITHUB_CHANGELOG_URL = "https://raw.githubusercontent.com/speedy005/CrashlogViewer/main/changelog.txt"
GITHUB_ZIP_URL = "https://github.com/speedy005/CrashlogViewer/archive/refs/heads/main.zip"

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
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

def get_local_version():
    try:
        with open(VERSION_FILE, 'r') as f:
            return f.read().strip()
    except Exception:
        return "0.0"

# --- Update Funktionen ---
def get_current_version():
    try:
        with open(VERSION_FILE, 'r') as f:
            return f.read().strip()
    except Exception:
        return "0.0"

def get_remote_version():
    try:
        response = urllib_request.urlopen(GITHUB_VERSION_URL, timeout=5).read()
        if PY3:
            response = response.decode("utf-8")
        return response.strip().split()[0]
    except Exception as e:
        log("Error fetching remote version: %s" % e)
        return None

def parse_version(version_str):
    if not version_str:
        return (0,0,0)
    v = version_str.strip().lower()
    if v.startswith("v"):
        v = v[1:]
    parts = re.findall(r"\d+", v)
    while len(parts) < 3:
        parts.append("0")
    return tuple(map(int, parts[:3]))

def download_and_install_update(session):
    tmp_dir = None
    try:
        tmp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(tmp_dir, "plugin_update.zip")
        log("Downloading update...")
        req = urllib_request.urlopen(GITHUB_ZIP_URL)
        data = req.read()
        with open(zip_path, "wb") as f:
            f.write(data)
        log("Download complete: %s" % zip_path)

        log("Extracting update...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmp_dir)

        # GitHub ZIP enthält oft CrashlogViewer-main/usr/lib/...
        extracted_folder = None
        for root, dirs, files in os.walk(tmp_dir):
            if "CrashlogViewer" in dirs and "Extensions" in root:
                extracted_folder = os.path.join(root, "CrashlogViewer")
                break

        if not extracted_folder:
            extracted_folder = os.path.join(tmp_dir, "CrashlogViewer-main", "usr", "lib", "enigma2", "python", "Plugins", "Extensions", "CrashlogViewer")
            if not os.path.exists(extracted_folder):
                raise Exception("CrashlogViewer folder not found in extracted ZIP!")

        log("Found new plugin folder: %s" % extracted_folder)

        if os.path.exists(PLUGIN_PATH):
            shutil.rmtree(PLUGIN_PATH)

        shutil.copytree(extracted_folder, PLUGIN_PATH)
        log("New plugin folder copied to %s" % PLUGIN_PATH)

        remote_version = get_remote_version()
        if remote_version:
            with open(VERSION_FILE, "w") as vf:
                vf.write(remote_version + "\n")
            with open(LAST_UPDATE_FILE, "w") as lf:
                lf.write(remote_version + "\n")

        def restartGUI(answer):
            if answer:
                session.open(TryQuitMainloop, 3)

        msg = _("Update installed successfully!\nDo you want to restart the GUI now?")
        session.openWithCallback(restartGUI, MessageBox, msg, type=MessageBox.TYPE_YESNO)

    except Exception as e:
        log("Error during update: %s" % e)
        traceback.print_exc()
        try:
            session.open(MessageBox, _("Error during update:\n%s") % str(e), type=MessageBox.TYPE_ERROR)
        except Exception:
            pass
    finally:
        if tmp_dir:
            try:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass

def check_for_update(session, callback=None):
    current_version = get_current_version()
    remote_version = get_remote_version()
    def proceed():
        if callback:
            callback()
    try:
        if remote_version and parse_version(remote_version) > parse_version(current_version):
            def cb(choice):
                if choice:
                    download_and_install_update(session)
                else:
                    proceed()
            msg = _("A new version %s is available.\nDo you want to install the update?") % remote_version
            session.openWithCallback(cb, MessageBox, msg, type=MessageBox.TYPE_YESNO)
        else:
            session.open(MessageBox, _("Kein Update verfügbar"), type=MessageBox.TYPE_INFO, timeout=4)
            proceed()
    except Exception as e:
        log("Error during update check: %s" % e)
        proceed()

# --- Crashlog Funktionen ---
def isMountReadonly(mnt):
    try:
        with open("/proc/mounts", "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) < 4: continue
                device, mp, fs, flags = parts[:4]
                if mp == mnt:
                    return "ro" in flags
    except Exception:
        return False
    return False

def find_log_files(base_path=LOG_BASE_PATH):
    patterns = [
        os.path.join(base_path, "*crash*.log"),
        os.path.join(base_path, "*debug*.log"),
        os.path.join(base_path, "*network*.log"),
        "/media/usb/logs/*crash*.log",
        "/media/usb/logs/*debug*.log",
        "/media/usb/logs/*network*.log",
        "/media/hdd/logs/*crash*.log",
        "/media/hdd/logs/*debug*.log",
        "/media/hdd/logs/*network*.log",
    ]
    log_files = []
    for pattern in patterns:
        log_files.extend(glob.glob(pattern))
    return sorted(list(set(log_files)))

def delete_log_files(files):
    for file in files:
        try:
            remove(file)
        except OSError as e:
            log("Error deleting %s: %s" % (file, e))

# --- CrashLogScreen ---
class CrashLogScreen(Screen):
    sz_w = getDesktop(0).size().width()

    if sz_w == 2560:
        skin = """
<screen name="crashlogscreen" position="320,40" size="1280,1000" title="%s">
  <eLabel name="button ok" font="Regular; 30" position="1177,928" size="103,48" cornerRadius="4" halign="center" valign="center" text="OK" backgroundColor="black" zPosition="3" foregroundColor="red" />
  <eLabel name="button info" font="Regular; 30" position="1068,930" size="103,48" cornerRadius="4" halign="center" valign="center" text="INFO" backgroundColor="black" zPosition="3" foregroundColor="red" />
  <eLabel name="button ext" font="Regular; 30" position="1121,874" size="103,48" cornerRadius="4" halign="center" valign="center" text="EXIT" backgroundColor="black" zPosition="3" foregroundColor="red" />
  <eLabel backgroundColor="listRecording" position="25,976" size="250,6" zPosition="12" />
  <eLabel backgroundColor="green" position="285,974" size="250,6" zPosition="12" foregroundColor="green" />
  <eLabel backgroundColor="yellow" position="547,974" size="250,6" zPosition="12" />
  <eLabel backgroundColor="blue" position="807,974" size="250,8" zPosition="12" foregroundColor="blue" />
  <widget source="Redkey" render="Label" position="25,928" size="250,45" font="Regular;30" />
  <widget source="Greenkey" render="Label" position="283,928" size="250,45" font="Regular;30" foregroundColor="green" />
  <widget source="Yellowkey" render="Label" position="544,928" size="250,45" font="Regular;30" foregroundColor="yellow" />
  <widget source="Bluekey" render="Label" position="806,928" size="250,45" font="Regular;30" foregroundColor="blue" />
  <widget source="menu" render="Listbox" position="80,67" size="1137,781" scrollbarMode="showOnDemand">
    <convert type="TemplatedMultiContent">
        {"template":[
            MultiContentEntryText(pos=(80,5),size=(580,46),font=0,flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER,text=0),
            MultiContentEntryText(pos=(80,55),size=(580,38),font=1,flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER,text=1),
            MultiContentEntryPixmapAlphaTest(pos=(5,35),size=(51,40),png=2)],
        "fonts":[gFont("Regular",42),gFont("Regular",34)],
        "itemHeight":100}
        </convert>
  </widget>
</screen>
""" % _("View or Remove Crashlog files")

    elif sz_w == 1920:
        skin = """
<screen name="crashlogscreen" position="center,center" size="1000,880" title="%s">
  <eLabel name="button info" font="Regular; 30" position="881,761" size="103,48" cornerRadius="4" halign="center" valign="center" text="INFO" backgroundColor="black" zPosition="3" foregroundColor="red" />
  <eLabel name="button ext" font="Regular; 30" position="773,761" size="103,48" cornerRadius="4" halign="center" valign="center" text="EXIT" backgroundColor="black" zPosition="3" foregroundColor="red" />
  <eLabel name="button ok" font="Regular; 30" position="663,761" size="103,48" cornerRadius="4" halign="center" valign="center" text="OK" backgroundColor="black" zPosition="3" foregroundColor="red" />
  <eLabel backgroundColor="listRecording" position="0,858" size="250,6" zPosition="12" />
  <eLabel backgroundColor="unff00" position="250,858" size="250,6" zPosition="12" />
  <eLabel backgroundColor="yellow" position="500,858" size="250,6" zPosition="12" />
  <eLabel backgroundColor="unff" position="750,858" size="250,6" zPosition="12" />
  <widget source="Redkey" render="Label" position="0,814" size="250,45" font="Regular;26" />
  <widget source="Greenkey" render="Label" position="252,813" size="250,45" font="Regular;26" foregroundColor="green" />
  <widget source="Yellowkey" render="Label" position="499,814" size="250,45" font="Regular;26" foregroundColor="yellow" />
  <widget source="Bluekey" render="Label" position="749,814" size="250,45" font="Regular;26" foregroundColor="blue" />
  <widget source="menu" render="Listbox" position="20,10" size="961,740" scrollbarMode="showOnDemand">
    <convert type="TemplatedMultiContent">
        {"template":[
            MultiContentEntryText(pos=(70,2),size=(580,34),font=0,flags=RT_HALIGN_LEFT,text=0),
            MultiContentEntryText(pos=(80,29),size=(580,30),font=1,flags=RT_HALIGN_LEFT,text=1),
            MultiContentEntryPixmapAlphaTest(pos=(5,20),size=(45,32),png=2)],
        "fonts":[gFont("Regular",28),gFont("Regular",24)],
        "itemHeight":75}
        </convert>
  </widget>
</screen>
""" % _("View or Remove Crashlog files")

    else:
        skin = """
<screen name="crashlogscreen" position="center,center" size="900,600" title="%s">
  <eLabel name="button info" font="Regular; 30" position="793,488" size="103,48" cornerRadius="4" halign="center" valign="center" text="INFO" backgroundColor="black" zPosition="3" foregroundColor="red" />
  <eLabel name="button ext" font="Regular; 30" position="687,489" size="103,48" cornerRadius="4" halign="center" valign="center" text="EXIT" backgroundColor="black" zPosition="3" foregroundColor="red" />
  <eLabel name="button ok" font="Regular; 30" position="580,490" size="103,48" cornerRadius="4" halign="center" valign="center" text="OK" backgroundColor="black" zPosition="3" foregroundColor="red" />
  <eLabel backgroundColor="listRecording" position="5,586" size="200,6" zPosition="12" />
  <eLabel backgroundColor="green" position="215,586" size="200,6" zPosition="12" foregroundColor="green" />
  <eLabel backgroundColor="yellow" position="421,586" size="200,6" zPosition="12" />
  <eLabel backgroundColor="blue" position="626,586" size="200,6" zPosition="12" foregroundColor="blue" />
  <widget source="Redkey" render="Label" position="4,540" size="200,45" font="Regular;26" />
  <widget source="Greenkey" render="Label" position="212,540" size="200,45" font="Regular;26" foregroundColor="green" />
  <widget source="Yellowkey" render="Label" position="418,540" size="200,45" font="Regular;26" foregroundColor="yellow" />
  <widget source="Bluekey" render="Label" position="626,538" size="200,45" font="Regular;26" foregroundColor="blue" />
  <widget source="menu" render="Listbox" position="7,8" size="861,480" scrollbarMode="showOnDemand">
    <convert type="TemplatedMultiContent">
        {"template":[
            MultiContentEntryText(pos=(70,2),size=(580,34),font=0,flags=RT_HALIGN_LEFT,text=0),
            MultiContentEntryText(pos=(80,29),size=(580,30),font=1,flags=RT_HALIGN_LEFT,text=1),
            MultiContentEntryPixmapAlphaTest(pos=(5,20),size=(45,32),png=2)],
        "fonts":[gFont("Regular",28),gFont("Regular",24)],
        "itemHeight":75}
        </convert>
  </widget>
</screen>
""" % _("View or Remove Crashlog files")

    def __init__(self, session):
        self.session = session
        Screen.__init__(self, session)

        self["Redkey"] = StaticText(_("Close"))
        self["Greenkey"] = StaticText(_("View"))
        self["Yellowkey"] = StaticText(_("Remove"))
        self["Bluekey"] = StaticText(_("Remove All"))

        self.list = []
        self["menu"] = List(self.list)

        self["shortcuts"] = ActionMap(
            ["ShortcutActions", "WizardActions", "EPGSelectActions"],
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
            path=resolveFilename(SCOPE_PLUGINS, "Extensions/CrashlogViewer/images/crashmini.png")
            if sz_w >= 1920 else
            resolveFilename(SCOPE_PLUGINS, "Extensions/CrashlogViewer/images/crashmini1.png")
        )

        for file_path in log_files:
            try:
                stat = os.stat(file_path)
                file_size = stat.st_size
                file_date = time.strftime("%Y-%m-%d %H:%M", time.localtime(stat.st_mtime))
                self.list.append((os.path.basename(file_path),
                                  "Size: %s - Date: %s" % (file_size, file_date),
                                  minipng,
                                  file_path))
            except Exception as e:
                log("Error accessing file %s: %s" % (file_path, e))
        self["menu"].setList(self.list)

    def Ok(self):
        item = self["menu"].getCurrent()
        if not item or len(item) < 4:
            self.session.open(MessageBox, _("No log file selected!"), MessageBox.TYPE_INFO, timeout=4)
            return
        self.session.openWithCallback(self.CfgMenu, LogScreen, str(item[3]))

    def YellowKey(self):
        item = self["menu"].getCurrent()
        if not item or len(item) < 4:
            return
        try:
            os.remove(str(item[3]))
            self.session.open(MessageBox, _("Removed %s") % item[3], MessageBox.TYPE_INFO, timeout=4)
        except Exception as e:
            self.session.open(MessageBox, _("Failed to remove file:\n%s") % e, MessageBox.TYPE_INFO, timeout=4)
        self.CfgMenu()

    def BlueKey(self):
        log_files = find_log_files()
        deleted_files = 0
        failed_files = []
        for f in log_files:
            if not isMountReadonly(os.path.dirname(f)):
                try:
                    os.remove(f)
                    deleted_files += 1
                except Exception as e:
                    failed_files.append(f"{f} ({e})")
        msg = _("Removed %d log files") % deleted_files if deleted_files else _("No log files found to remove")
        if failed_files:
            msg += "\n" + _("Failed to remove some files:\n") + "\n".join(failed_files)
        self.session.open(MessageBox, msg, MessageBox.TYPE_INFO, timeout=6)
        self.CfgMenu()

    def infoKey(self):
        self.session.open(
            MessageBox,
            _("Crashlog Viewer  ver. %s\n\nDeveloper: 2boom\n\nModifier: Evg77734\n\nUpdate from Lululla\nHomepage: gisclub.tv") % version,
            MessageBox.TYPE_INFO
        )

    def exit(self):
        self.close()




# --- LogScreen ---
class LogScreen(Screen):
    sz_w = getDesktop(0).size().width()

    if sz_w == 2560:
        skin = """<screen name="crashlogview" position="center,center" size="2560,1440" title="%s">
        <widget source="Redkey" render="Label" position="32,1326" size="250,69" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" />
        <widget source="Greenkey" render="Label" position="321,1326" size="250,69" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="green" />
        <eLabel backgroundColor="#00ff0000" position="32,1394" size="250,6" zPosition="12" />
        <eLabel backgroundColor="#0000ff00" position="321,1396" size="250,6" zPosition="12" />
        <widget name="text" position="0,10" size="2560,1092" font="Console; 42" text="text" foregroundColor="green" />
        <widget name="text2" position="-279,1123" size="2560,190" font="Console; 42" text="text2" foregroundColor="#ff0000" />
        <eLabel position="10,1110" size="2560,4" backgroundColor="#555555" zPosition="1" />
        </screen>""" % _("View Crashlog file")
    elif sz_w == 1920:
        skin = """<screen name="crashlogview" position="17,73" size="1880,980" title="%s">
        <widget source="Redkey" render="Label" position="30,915" size="250,45" zPosition="11" font="Regular; 26" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" />
        <widget source="Greenkey" render="Label" position="282,915" size="250,45" zPosition="11" font="Regular; 26" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="green" />
        <eLabel backgroundColor="#00ff0000" position="32,962" size="250,6" zPosition="12" />
        <eLabel backgroundColor="#0000ff00" position="284,962" size="250,6" zPosition="12" />
        <widget name="text" position="10,10" size="1860,695" font="Console; 28" text="text" foregroundColor="green" />
        <widget name="text2" position="10,720" size="1860,190" font="Console; 28" text="text2" foregroundColor="#ff0000" />
        <eLabel position="10,710" size="1860,2" backgroundColor="#555555" zPosition="1" />
        </screen>""" % _("View Crashlog file")
    else:
        skin = """<screen name="crashlogview" position="center,center" size="1253,653" title="%s">
        <widget source="Redkey" render="Label" position="30,608" size="160,35" zPosition="11" font="Regular; 22" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" />
        <widget source="Greenkey" render="Label" position="192,608" size="160,35" zPosition="11" font="Regular; 22" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="green" />
        <eLabel backgroundColor="#00ff0000" position="33,642" size="160,6" zPosition="12" />
        <eLabel backgroundColor="#0000ff00" position="195,642" size="160,6" zPosition="12" />
        <widget name="text" position="8,4" size="1240,463" font="Console; 20" text="text" foregroundColor="green" />
        <widget name="text2" position="6,480" size="1240,126" font="Console; 20" text="text2" foregroundColor="#ff0000" />
        <eLabel position="6,473" size="1240,1" backgroundColor="#555555" zPosition="1" />
        </screen>""" % _("View Crashlog file")

    def __init__(self, session, crashfile):
        self.session = session
        Screen.__init__(self, session)
        self.crashfile = crashfile

        self["Redkey"] = StaticText(_("Close"))
        self["Greenkey"] = StaticText(_("Restart GUI"))
        self["text"] = ScrollLabel("")
        self["text2"] = ScrollLabel("")

        self["shortcuts"] = ActionMap(
            ["ShortcutActions", "WizardActions"],
            {
                "cancel": self.exit,
                "back": self.exit,
                "red": self.exit,
                "green": self.restartGUI,
            }
        )

        self.loadLogFile()

    def loadLogFile(self):
        full_text = ""
        error_text = ""
        try:
            if not os.path.exists(self.crashfile):
                full_text = _("File not found: %s") % self.crashfile
            else:
                with open(self.crashfile, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        full_text += line
                        if "Error:" in line or "FATAL SIGNAL" in line:
                            error_text += line
        except Exception as e:
            full_text = _("Error opening file:\n%s") % e
        self["text"].setText(full_text)
        self["text2"].setText(error_text)

    def restartGUI(self):
        self.session.open(TryQuitMainloop, 3)

    def exit(self):
        self.close()

# --- Menü & Plugins ---
def menu(menuid, **kwargs):
    if menuid == "mainmenu":
        plugin_name = _("Crashlog Viewer") + " ver. " + get_local_version()
        return [(plugin_name, main, "CrashlogViewer_mainmenu", 50)]
    return []

def main(session, **kwargs):
    check_for_update(session, lambda: session.open(CrashLogScreen))

def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name=_("Crashlog Viewer") + " ver. " + get_local_version(),
            description=_("View and remove crashlog files"),
            where=[PluginDescriptor.WHERE_PLUGINMENU, PluginDescriptor.WHERE_EXTENSIONSMENU],
            icon="crash.png",
            fnc=main,
        ),
        PluginDescriptor(where=PluginDescriptor.WHERE_MENU, fnc=menu),
    ]
