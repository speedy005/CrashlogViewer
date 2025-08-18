#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# updated Lululla 05/06/2023
# updated Lululla 30/04/2024
# updated Lululla 30/08/2024
# updated Lululla 22/09/2024
# updated Lululla 17/11/2024
# updated Lululla 26/05/2025
# by 2boom 4bob@ua.fm

from __future__ import print_function  # Kompatibilität zwischen Python 2 und 3
import gettext
from os import remove, listdir, popen
from os.path import exists, join
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

# Version
version = '1.6'
path_folder_log = '/media/hdd/'

# gettext Setup für Python 2 und 3 Kompatibilität
def _(txt):
    t = gettext.dgettext("CrashlogViewer", txt)
    if t == txt:
        t = gettext.gettext(txt)
    return t

# Mount Status prüfen
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

# Pfade für Log-Dateien
def paths():
    return [
        "/media/hdd", "/media/usb", "/media/mmc", "/home/root", "/home/root/logs/",
        "/media/hdd/logs", "/media/usb/logs", "/ba/", "/ba/logs"
    ]

# Logs finden
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

# Logs löschen
def delete_log_files(files):
    for file in files:
        try:
            remove(file)
            print('CrashLogScreen file deleted: %s' % file)
        except OSError as e:
            print("Error while deleting %s error %s:" % (file,  str(e)))

# Hauptklasse für das Crash-Log-Viewer-Screen
class CrashLogScreen(Screen):
    sz_w = getDesktop(0).size().width()
    
    # Skin entsprechend der Bildschirmauflösung
    if sz_w == 2560:
        skin = """
        <screen name="crashlogscreen" position="center,center" size="1280,1000" title="View or Remove Crashlog files">
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
        """
    else:
        skin = """
        <screen name="crashlogscreen" position="center,center" size="960,800" title="View or Remove Crashlog files">
        <widget source="Redkey" render="Label" position="160,710" size="250,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
        <widget source="Greenkey" render="Label" position="415,710" size="250,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
        <widget source="Yellowkey" render="Label" position="670,710" size="250,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
        <widget source="Bluekey" render="Label" position="925,710" size="250,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
        <eLabel backgroundColor="#00ff0000" position="160,758" size="250,6" zPosition="12" />
        <eLabel backgroundColor="#0000ff00" position="415,758" size="250,6" zPosition="12" />
        <eLabel backgroundColor="#00ffff00" position="670,758" size="250,6" zPosition="12" />
        <eLabel backgroundColor="#000000ff" position="925,758" size="250,6" zPosition="12" />
        <eLabel name="" position="1194,711" size="52,52" backgroundColor="#003e4b53" halign="center" valign="center" transparent="0" cornerRadius="26" font="Regular; 17" zPosition="1" text="INFO" />
        <widget source="menu" render="Listbox" position="80,67" size="800,600" scrollbarMode="showOnDemand">
        <convert type="TemplatedMultiContent">
        {"template": [
            MultiContentEntryText(pos = (80, 5), size = (580, 46), font=0, flags = RT_HALIGN_LEFT | RT_VALIGN_CENTER, text = 0),
            MultiContentEntryText(pos = (80, 55), size = (580, 38), font=1, flags = RT_HALIGN_LEFT | RT_VALIGN_CENTER, text = 1),
            MultiContentEntryPixmapAlphaTest(pos = (5, 35), size = (51, 40), png = 2),
                ],
        "fonts": [gFont("Regular", 32),gFont("Regular", 24)],
        "itemHeight": 100
        }
                </convert>
            </widget>
        </screen>
        """
    
    def __init__(self, session, args=None):
        Screen.__init__(self, session)
        self.session = session
        self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "ColorActions"],
        {
            "ok": self.Ok,
            "cancel": self.Cancel,
            "red": self.Delete,
            "green": self.Open,
            "yellow": self.Restart,
            "blue": self.Close,
        }, -1)

        # Menüeinträge für die Logs
        self.log_entries = List([])
        self["menu"] = self.log_entries
        self.onLayoutFinish.append(self._setup_log_entries)
    
    def _setup_log_entries(self):
        log_files = find_log_files()
        if log_files:
            log_list = []
            for file in log_files:
                log_list.append((file, file, None))  # Hier könnten mehr Details zum Log angezeigt werden
            self.log_entries.setList(log_list)

    def Ok(self):
        pass  # Hier könnte Log-Detailansicht kommen

    def Cancel(self):
        self.close()

    def Delete(self):
        selected_logs = self.log_entries.getSelectedList()
        delete_log_files([log[0] for log in selected_logs])
        self.close()

    def Open(self):
        pass  # Hier könnte das Öffnen des Logs umgesetzt werden

    def Restart(self):
        pass  # Hier könnte ein Neustart nach Log-Analyse erfolgen

    def Close(self):
        self.close()

# Plugin-Deskriptor
def main(session, **kwargs):
    session.open(CrashLogScreen)

# Plugin-Descriptor für Enigma2
def Plugins(**kwargs):
    return PluginDescriptor(name="CrashLogViewer", description="Viewer and Remover for Crash Logs", where=PluginDescriptor.WHERE_PLUGINMENU, icon="plugin.png", main=main)
