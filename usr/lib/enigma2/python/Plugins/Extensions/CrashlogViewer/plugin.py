#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# CrashlogViewer Enigma2 Plugin mit Update-Funktion
# updated Lululla 05/06/2023, 30/04/2024, 30/08/2024, 22/09/2024, 17/11/2024
# updated speedy005 06/09/2025

from __future__ import print_function
import gettext
from Components.Language import language
import os, sys, re, shutil, tempfile, zipfile, traceback
from os import remove, listdir, popen
from os.path import exists, join
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
path_folder_log = '/media/hdd/'

def localeInit():
    # Sprache aus den Box-Einstellungen holen
    lang = language.getLanguage()[:2]
    os.environ["LANGUAGE"] = lang

    # gettext initialisieren
    gettext.bindtextdomain(DOMAIN, LOCALE_DIR)
    gettext.textdomain(DOMAIN)

def _(txt):
	t = gettext.dgettext("CrashlogViewer", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t

# Initialisierung sofort und bei Sprachwechsel
localeInit()
language.addCallback(localeInit)

gettext.bindtextdomain("CrashlogViewer", LOCALE_DIR)
gettext.textdomain("CrashlogViewer")
_ = gettext.gettext

# Python 2/3 kompatibel urllib
try:
    import urllib2 as urllib_request
except Exception:
    import urllib.request as urllib_request

# --- Plugin Version & Pfade ---
version = '1.8'
VERSION_FILE = os.path.join(PLUGIN_PATH, "version.txt")
LAST_UPDATE_FILE = os.path.join(PLUGIN_PATH, "last_update_version.txt")
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/speedy005/CrashlogViewer/main/version.txt"
GITHUB_CHANGELOG_URL = "https://raw.githubusercontent.com/speedy005/CrashlogViewer/main/changelog.txt"
GITHUB_ZIP_URL = "https://github.com/speedy005/CrashlogViewer/archive/refs/heads/main.zip"
path_folder_log = '/home/root/logs/'

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

# --- Logging ---
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

# --- Update Funktionen ---
def get_current_version():
    try:
        with open(VERSION_FILE, 'r') as f:
            ver = f.read().strip()
            log("Local version: %s" % ver)
            return ver
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
        return (0, 0, 0)
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

        # Alten Plugin-Ordner löschen
        if os.path.exists(PLUGIN_PATH):
            shutil.rmtree(PLUGIN_PATH, ignore_errors=True)
            log("Old plugin folder deleted.")

        # Den extrahierten CrashlogViewer-Ordner finden
        new_plugin_folder = None
        for root, dirs, files in os.walk(tmp_dir):
            if "CrashlogViewer" in dirs:
                new_plugin_folder = os.path.join(root, "CrashlogViewer")
                break

        if not new_plugin_folder:
            raise Exception("CrashlogViewer-Ordner im ZIP nicht gefunden!")

        # Den neuen Ordner kopieren
        shutil.copytree(new_plugin_folder, PLUGIN_PATH)
        log("New plugin folder copied to %s" % PLUGIN_PATH)

        # Remote Version speichern
        remote_version = get_remote_version()
        if remote_version:
            with open(VERSION_FILE, "w") as vf:
                vf.write(remote_version + "\n")
            with open(LAST_UPDATE_FILE, "w") as lf:
                lf.write(remote_version + "\n")

        log("Update installed successfully!")

        # GUI Neustart anbieten
        def restartGUI(answer):
            if answer:
                session.open(TryQuitMainloop, 3)

        msg = _("Update installed successfully!\nDo you want to restart the GUI now?")
        session.openWithCallback(
            restartGUI,
            MessageBox,
            msg,
            type=MessageBox.TYPE_YESNO
        )

    except Exception as e:
        log("Error during update: %s" % e)
        traceback.print_exc()
        try:
            msg = _("Error during update:\n%s") % str(e)
            session.open(MessageBox, msg, type=MessageBox.TYPE_ERROR)
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
            session.openWithCallback(
                cb,
                MessageBox,
                msg,
                type=MessageBox.TYPE_YESNO
            )
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
				if len(parts) < 4:
					continue
				device, mp, fs, flags = parts[:4]
				if mp == mnt:
					return "ro" in flags
	except IOError as e:
		print("I/O error: %s" % str(e))
	except Exception as err:
		print("Error: %s" % str(err))
	return False


def paths():
	return [
		"/media/hdd", "/media/usb", "/media/mmc", "/home/root", "/home/root/logs/",
		"/media/hdd/logs", "/media/usb/logs", "/ba/", "/ba/logs"
	]


def find_log_files():
	log_files = []
	possible_paths = paths()
	for path in possible_paths:
		if exists(path) and not isMountReadonly(path):
			try:
				for file in listdir(path):
					if file.endswith(".log") and ("crashlog" in file or "twiste" in file):
						log_files.append(join(path, file))
			except OSError as e:
				print("Error %s while file access to: %s" % (str(e), path))
	return log_files


def delete_log_files(files):
	for file in files:
		try:
			remove(file)
			print('CrashLogScreen file deletedt: %s' % file)
		except OSError as e:
			print("Error while deleting %s error %s:" % (file,  str(e)))

class CrashLogScreen(Screen):
	sz_w = getDesktop(0).size().width()
	if sz_w == 2560:
		skin = """
		<screen name="crashlogscreen" position="center,center" size="1280,1000" title="%s">
		<widget source="Redkey" render="Label" position="160,900" size="250,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
		<widget source="Greenkey" render="Label" position="415,900" size="250,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
		<widget source="Yellowkey" render="Label" position="670,900" size="250,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
		<widget source="Bluekey" render="Label" position="925,900" size="250,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
		<eLabel backgroundColor="#00ff0000" position="160,948" size="250,6" zPosition="12" />
		<eLabel backgroundColor="#0000ff00" position="415,948" size="250,6" zPosition="12" />
		<eLabel backgroundColor="#00ffff00" position="670,948" size="250,6" zPosition="12" />
		<eLabel backgroundColor="#000000ff" position="925,948" size="250,6" zPosition="12" />
		<eLabel name="" position="1194,901" size="52,52" backgroundColor="#003e4b53" halign="center" valign="center" transparent="0" cornerRadius="26" font="Regular; 17" zPosition="1" text="INFO" />
		<widget source="menu" render="Listbox" position="80,67" size="1137,781" scrollbarMode="showOnDemand">
		<convert type="TemplatedMultiContent">
		{"template": [
			MultiContentEntryText(pos = (80, 5), size = (580, 46), font=0, flags = RT_HALIGN_LEFT | RT_VALIGN_CENTER, text = 0), # index 2 is the Menu Titel
			MultiContentEntryText(pos = (80, 55), size = (580, 38), font=1, flags = RT_HALIGN_LEFT | RT_VALIGN_CENTER, text = 1), # index 3 is the Description
			MultiContentEntryPixmapAlphaTest(pos = (5, 35), size = (51, 40), png = 2), # index 4 is the pixmap
				],
		"fonts": [gFont("Regular", 42),gFont("Regular", 34)],
		"itemHeight": 100
		}
				</convert>
			</widget>
		</screen>
		"""  % _("View or Remove Crashlog files")

	elif sz_w == 1920:
		skin = """
		<screen name="crashlogscreen" position="center,center" size="1000,880" title="%s">
		<widget source="Redkey" render="Label" position="0,814" size="250,45" zPosition="11" font="Regular; 26" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" />
		<widget source="Greenkey" render="Label" position="252,813" size="250,45" zPosition="11" font="Regular; 26" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="green" />
		<widget source="Yellowkey" render="Label" position="499,814" size="250,45" zPosition="11" font="Regular; 26" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="yellow" />
		<widget source="Bluekey" render="Label" position="749,814" size="250,45" zPosition="11" font="Regular; 26" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="blue" />
		<eLabel backgroundColor="#00ff0000" position="0,858" size="250,6" zPosition="12" />
		<eLabel backgroundColor="#0000ff00" position="250,858" size="250,6" zPosition="12" />
		<eLabel backgroundColor="#00ffff00" position="500,858" size="250,6" zPosition="12" />
		<eLabel backgroundColor="#000000ff" position="750,858" size="250,6" zPosition="12" />
		<eLabel name="" position="933,753" size="52,52" backgroundColor="#003e4b53" halign="center" valign="center" transparent="0" cornerRadius="26" font="Regular; 17" zPosition="1" text="INFO" />
		<widget source="menu" render="Listbox" position="20,10" size="961,781" scrollbarMode="showOnDemand">
		<convert type="TemplatedMultiContent">
		{"template": [
			MultiContentEntryText(pos = (70, 2), size = (580, 34), font=0, flags = RT_HALIGN_LEFT, text = 0), # index 2 is the Menu Titel
			MultiContentEntryText(pos = (80, 29), size = (580, 30), font=1, flags = RT_HALIGN_LEFT, text = 1), # index 3 is the Description
			MultiContentEntryPixmapAlphaTest(pos = (5, 15), size = (51, 40), png = 2), # index 4 is the pixmap
				],
		"fonts": [gFont("Regular", 30),gFont("Regular", 30)],
		"itemHeight": 70
		}
				</convert>
			</widget>
		</screen>
		"""  % _("View or Remove Crashlog files")
	else:
		skin = """
		<screen name="crashlogscreen" position="center,center" size="640,586" title="%s">
		<widget source="Redkey" render="Label" position="6,536" size="160,35" zPosition="11" font="Regular; 22" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" />
		<widget source="Greenkey" render="Label" position="166,536" size="160,35" zPosition="11" font="Regular; 22" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="green" />
		<widget source="Yellowkey" render="Label" position="325,536" size="160,35" zPosition="11" font="Regular; 22" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="yellow" />
		<widget source="Bluekey" render="Label" position="485,536" size="160,35" zPosition="11" font="Regular; 22" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="blue" />
		<eLabel backgroundColor="#00ff0000" position="5,570" size="160,6" zPosition="12" />
		<eLabel backgroundColor="#0000ff00" position="165,570" size="160,6" zPosition="12" />
		<eLabel backgroundColor="#00ffff00" position="325,570" size="160,6" zPosition="12" />
		<eLabel backgroundColor="#000000ff" position="480,570" size="160,6" zPosition="12" />
		<eLabel name="" position="586,495" size="42,35" backgroundColor="#003e4b53" halign="center" valign="center" transparent="0" cornerRadius="26" font="Regular; 14" zPosition="1" text="INFO" />
		<widget source="menu" render="Listbox" position="13,6" size="613,517" scrollbarMode="showOnDemand">
		<convert type="TemplatedMultiContent">
		{"template": [
			MultiContentEntryText(pos = (46, 1), size = (386, 22), font=0, flags = RT_HALIGN_LEFT, text = 0), # index 2 is the Menu Titel
			MultiContentEntryText(pos = (53, 19), size = (386, 20), font=1, flags = RT_HALIGN_LEFT, text = 1), # index 3 is the Description
			MultiContentEntryPixmapAlphaTest(pos = (3, 10), size = (34, 26), png = 2), # index 4 is the pixmap
				],
		"fonts": [gFont("Regular", 20),gFont("Regular", 20)],
		"itemHeight": 50
		}
				</convert>
		</widget>
		</screen>
		"""  % _("View or Remove Crashlog files")

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
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
				"info": self.infoKey,
				"epg": self.infoKey,
			}
		)
		self["Redkey"] = StaticText(_("Close"))
		self["Greenkey"] = StaticText(_("View"))
		self["Yellowkey"] = StaticText(_("Remove"))
		self["Bluekey"] = StaticText(_("Remove All"))
		self.list = []
		self["menu"] = List(self.list)
		self.CfgMenu()

	def CfgMenu(self):
		self.list = []
		path_folder_log = "/tmp/"
		log_files = find_log_files()
		if log_files:
			paths_to_search = " ".join(log_files)
		else:
			paths_to_search = (
				"%s*crash*.log "
				"%slogs/*crash*.log "
				"/home/root/*crash*.log "
				"/home/root/*debug*.log "
				"/home/root/logs/*crash*.log "
				"/home/root/logs/*debug*.log "
				"%stwisted.log "
				"/media/usb/logs/*crash*.log "
				"/media/usb/*crash*.log "
				"/media/hdd/logs/*crash*.log "
				"/media/mmc/*crash*.log "
				"/media/hdd/*crash*.log "
				"/home/root/logs/*network*.log "
				"/ba/*crash*.log "
				"/ba/logs/*crash*.log"
			) % (path_folder_log, path_folder_log, path_folder_log)

		crashfiles = popen("ls -lh " + paths_to_search).read()
		crashfiles = popen("ls -lh " + paths_to_search).read()
		sz_w = getDesktop(0).size().width()
		if sz_w == 2560:
			minipng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/CrashlogViewer/images/crashminiwq.png"))
		elif sz_w == 1920:
			minipng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/CrashlogViewer/images/crashmini.png"))
		else:
			minipng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/CrashlogViewer/images/crashmini1.png"))
		for line in crashfiles.splitlines():
			item = line.split()
			if len(item) >= 9:
				file_size = item[4]
				file_date = " ".join(item[5:8])
				file_name = item[8]
				display_name = (file_name.split("/")[-1],
								"Dimensione: %s - Data: %s" % (file_size, file_date),
								minipng,
								file_name)
				if display_name not in self.list:
					self.list.append(display_name)
		self["menu"].setList(self.list)
		self["actions"] = ActionMap(["OkCancelActions"], {"cancel": self.close}, -1)

	def Ok(self):
		item = self["menu"].getCurrent()
		# global Crashfile
		try:
			base_dir = item[3]
			# filename = item[0]
			crashfile = str(base_dir)
			self.session.openWithCallback(self.CfgMenu, LogScreen, crashfile)
		except (IndexError, TypeError, KeyError) as e:
			print('CrashLogScreen error to select: %s' % e)
			crashfile = " "

	def YellowKey(self):
		item = self["menu"].getCurrent()
		try:
			base_dir = item[3]
			file_path = str(base_dir)
			remove(file_path)
			self.mbox = self.session.open(MessageBox, (_("Removed %s") % (file_path)), MessageBox.TYPE_INFO, timeout=4)
		except (IndexError, TypeError, KeyError) as e:
			self.mbox = self.session.open(MessageBox, (_("Failed to remove file due to an error: %s") % str(e)), MessageBox.TYPE_INFO, timeout=4)
		except OSError as e:
			self.mbox = self.session.open(MessageBox, (_("Failed to remove file: %s") % str(e)), MessageBox.TYPE_INFO, timeout=4)
		except Exception as e:
			self.mbox = self.session.open(MessageBox, (_("An unexpected error occurred: %s") % str(e)), MessageBox.TYPE_INFO, timeout=4)
		self.CfgMenu()

	def BlueKey(self):
		try:
			log_files = find_log_files()
			if log_files:
				paths_to_search = ' '.join(log_files)
			else:
				paths_to_search = "%s*crash*.log %s*debug*.log %slogs/*crash*.log %slogs/*debug*.log /home/root/*crash*.log /home/root/*debug*.log /home/root/logs/*crash*.log /home/root/logs/*debug*.log %stwisted.log /media/usb/logs/*crash*.log /media/usb/logs/*debug*.log /media/usb/*crash*.log /media/usb/*debug*.log" % (path_folder_log, path_folder_log, path_folder_log, path_folder_log, path_folder_log)
			crashfiles = popen("ls -lh " + paths_to_search).read()
			for line in crashfiles.splitlines():  # Dividi l'output in linee
				item = line.split()
				if len(item) >= 9:
					file_name = item[8]
					remove(file_name)
			self.mbox = self.session.open(MessageBox, (_("Removed All Crashlog Files")), MessageBox.TYPE_INFO, timeout=4)
		except (OSError, IOError) as e:
			self.mbox = self.session.open(MessageBox, (_("Failed to remove some files: %s") % str(e)), MessageBox.TYPE_INFO, timeout=4)
		except Exception as e:
			self.mbox = self.session.open(MessageBox, (_("An unexpected error occurred: %s") % str(e)), MessageBox.TYPE_INFO, timeout=4)
		self.CfgMenu()

	def infoKey(self):
		self.session.open(MessageBox, _("Crashlog Viewer  ver. %s\n\nDeveloper: 2boom\n\nModifier: Evg77734\n\nUpdate from Lululla\nHomepage: gisclub.tv") % version, MessageBox.TYPE_INFO)

	def exit(self):
		self.close()


class LogScreen(Screen):
	sz_w = getDesktop(0).size().width()
	if sz_w == 2560:
		skin = """
		<screen name="crashlogview" position="center,center" size="2560,1440" title="%s">
		<widget source="Redkey" render="Label" position="32,1326" size="250,69" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
		<widget source="Greenkey" render="Label" position="321,1326" size="250,69" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
		<eLabel backgroundColor="#00ff0000" position="32,1394" size="250,6" zPosition="12" />
		<eLabel backgroundColor="#0000ff00" position="321,1396" size="250,6" zPosition="12" />
		<widget name="text" position="0,10" size="2560,1092" font="Console; 42" text="text" />
		<widget name="text2" position="-279,1123" size="2560,190" font="Console; 42" text="text2" foregroundColor="#ff0000" />
		<eLabel position="10,1110" size="2560,4" backgroundColor="#555555" zPosition="1" />
		</screen>
		"""  % _("View Crashlog file")

	elif sz_w == 1920:
		skin = """
		<screen name="crashlogview" position="center,center" size="1880,980" title="%s">
		<widget source="Redkey" render="Label" position="30,915" size="250,45" zPosition="11" font="Regular; 26" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" />
		<widget source="Greenkey" render="Label" position="282,915" size="250,45" zPosition="11" font="Regular; 26" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="green" />
		<eLabel backgroundColor="#00ff0000" position="32,962" size="250,6" zPosition="12" />
		<eLabel backgroundColor="#0000ff00" position="284,962" size="250,6" zPosition="12" />
		<widget name="text" position="10,10" size="1860,695" font="Console; 28" text="text" foregroundColor="green" />
		<widget name="text2" position="10,720" size="1860,190" font="Console; 28" text="text2" foregroundColor="#ff0000" />
		<eLabel position="10,710" size="1860,2" backgroundColor="#555555" zPosition="1" />
		</screen>
		"""  % _("View Crashlog file")
	else:
		skin = """
		<screen name="crashlogview" position="center,center" size="1253,653" title="%s">
		<widget source="Redkey" render="Label" position="30,608" size="160,35" zPosition="11" font="Regular; 22" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" />
		<widget source="Greenkey" render="Label" position="192,608" size="160,35" zPosition="11" font="Regular; 22" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="green" />
		<eLabel backgroundColor="#00ff0000" position="33,642" size="160,6" zPosition="12" />
		<eLabel backgroundColor="#0000ff00" position="195,642" size="160,6" zPosition="12" />
		<widget name="text" position="8,4" size="1240,463" font="Console; 20" text="text" foregroundColor="green" />
		<widget name="text2" position="6,480" size="1240,126" font="Console; 20" text="text2" foregroundColor="#ff0000" />
		<eLabel position="6,473" size="1240,1" backgroundColor="#555555" zPosition="1" />
		</screen>
		"""  % _("View Crashlog file")

	def __init__(self, session, crashfile):
		self.session = session
		Screen.__init__(self, session)
		# global Crashfile
		self.crashfile = crashfile
		self.setTitle('View Crashlog file:  ' + str(self.crashfile))
		self["shortcuts"] = ActionMap(
			["ShortcutActions", "WizardActions"],
			{
				"cancel": self.exit,
				"back": self.exit,
				"red": self.exit,
			}
		)
		self["Redkey"] = StaticText(_("Close"))
		self["Greenkey"] = StaticText(_("Restart GUI"))
		self["text"] = ScrollLabel("")
		self["text2"] = ScrollLabel("")
		self.list = []
		self["menu"] = List(self.list)
		self.listcrah()

	def exit(self):
		self.close()

	def listcrah(self):
		# global Crashfile
		list = "No data error"
		list2 = "No data error"
		try:
			crashfiles = open(self.crashfile, "r")
			for line in crashfiles:
				if line.find("Traceback (most recent call last):") != -1 or line.find("Backtrace:") != -1:
					list = " "
					list2 = " "
					for line in crashfiles:
						list += line
						if line.find("Error: ") != -1:
							list2 += line
						if line.find("]]>") != -1 or line.find("dmesg") != -1 or line.find("StackTrace") != -1 or line.find("FATAL SIGNAL") != -1:
							if line.find("FATAL SIGNAL") != -1:
								list2 = "FATAL SIGNAL"
							break
			self["text"].setText(list)
			crashfiles.close()
		except Exception as e:
			print('error to open crashfile: %s' % e)
		self["text2"].setText(list2)
		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions"], {"cancel": self.close, "up": self["text"].pageUp, "left": self["text"].pageUp, "down": self["text"].pageDown, "right": self["text"].pageDown}, -1)

# --- Menüeinträge & Main ---
def menu(menuid, **kwargs):
    if menuid == "mainmenu":
        plugin_name = _("Crashlog Viewer") + " ver. " + version
        return [(plugin_name, main, "CrashlogViewer_mainmenu", 50)]
    return []

def main(session, **kwargs):
    check_for_update(session, lambda: session.open(CrashLogScreen))

def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name=(_("Crashlog Viewer") + " ver. " + version),
            description=_("View and remove crashlog files"),
            where=[PluginDescriptor.WHERE_PLUGINMENU, PluginDescriptor.WHERE_EXTENSIONSMENU],
            icon="crash.png",
            fnc=main,
        ),
        PluginDescriptor(where=PluginDescriptor.WHERE_MENU, fnc=menu),
    ]
