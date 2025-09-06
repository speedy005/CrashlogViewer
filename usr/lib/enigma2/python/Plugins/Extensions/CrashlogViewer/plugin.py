#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# updated Lululla 05/06/2023
# updated Lululla 30/04/2024
# updated Lululla 30/08/2024
# updated Lululla 22/09/2024
# updated Lululla 17/11/2024
# updated speedy005 06/09/2025
# mod by speedy005

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

version = '1.8'
path_folder_log = '/media/hdd/'

def _(txt):
    if not txt:
        return txt
    t = gettext.dgettext("View or Remove Crashlog files", txt)
    if t == txt:
        t = gettext.dgettext("CrashlogViewer", txt)
    if t == txt:
        t = gettext.gettext(txt)
    return t

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
    except Exception as e:
        print("Mount check error:", e)
    return False

def paths():
    return [
        "/media/hdd", "/media/usb", "/media/mmc", "/home/root", "/home/root/logs/",
        "/media/hdd/logs", "/media/usb/logs", "/ba/", "/ba/logs"
    ]

def find_log_files():
    log_files = []
    for path in paths():
        if exists(path) and not isMountReadonly(path):
            try:
                for file in listdir(path):
                    if file.endswith(".log") and ("crashlog" in file or "twiste" in file):
                        log_files.append(join(path, file))
            except OSError as e:
                print(f"Error accessing {path}: {e}")
    return log_files

def delete_log_files(files):
    for file in files:
        try:
            remove(file)
        except OSError as e:
            print(f"Error deleting {file}: {e}")

# ---------------- CrashLogScreen ----------------
class CrashLogScreen(Screen):
    sz_w = getDesktop(0).size().width()

    skin_template = """
    <screen name="crashlogscreen" position="center,center" size="{w},{h}" title="{title}">
        <widget source="Redkey" render="Label" position="10,{r_y}" size="150,35" font="Regular; 22" transparent="1" />
        <widget source="Greenkey" render="Label" position="170,{r_y}" size="150,35" font="Regular; 22" foregroundColor="green" transparent="1" />
        <widget source="Yellowkey" render="Label" position="330,{r_y}" size="150,35" font="Regular; 22" foregroundColor="yellow" transparent="1" />
        <widget source="Bluekey" render="Label" position="490,{r_y}" size="150,35" font="Regular; 22" foregroundColor="blue" transparent="1" />
        <widget source="menu" render="Listbox" position="10,10" size="{w_m},{h_m}" scrollbarMode="showOnDemand"/>
    </screen>
    """

    def __init__(self, session):
        self.session = session
        Screen.__init__(self, session)

        self["Redkey"] = StaticText(_("Close"))
        self["Greenkey"] = StaticText(_("View"))
        self["Yellowkey"] = StaticText(_("Remove"))
        self["Bluekey"] = StaticText(_("Remove All"))

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

        self.list = []
        self["menu"] = List(self.list)
        self.CfgMenu()

    def CfgMenu(self):
        self.list = []
        log_files = find_log_files()
        for file in log_files:
            self.list.append((file.split("/")[-1], _("Size: unknown"), None, file))
        self["menu"].setList(self.list)

    def Ok(self):
        item = self["menu"].getCurrent()
        if item:
            self.session.open(LogScreen, item[3])

    def YellowKey(self):
        item = self["menu"].getCurrent()
        if item:
            try:
                remove(item[3])
                self.session.open(MessageBox, (_("Removed %s") % item[3]), MessageBox.TYPE_INFO, timeout=4)
            except Exception as e:
                self.session.open(MessageBox, (_("Error removing file: %s") % str(e)), MessageBox.TYPE_INFO, timeout=4)
        self.CfgMenu()

    def BlueKey(self):
        for f in find_log_files():
            try:
                remove(f)
            except:
                pass
        self.session.open(MessageBox, _("Removed all Crashlog files"), MessageBox.TYPE_INFO, timeout=4)
        self.CfgMenu()

    def infoKey(self):
        self.session.open(
            MessageBox,
            _("Crashlog Viewer ver. %s\nDeveloper: 2boom\nModifier: Evg77734\nUpdate: Lululla") % version,
            MessageBox.TYPE_INFO
        )

    def exit(self):
        self.close()

# ---------------- LogScreen ----------------
class LogScreen(Screen):
    sz_w = getDesktop(0).size().width()

    skin_template = """
    <screen name="crashlogview" position="center,center" size="{w},{h}" title="{title}">
        <widget source="text" render="Label" position="10,10" size="{w_m},{h_m}" font="Console; 28" foregroundColor="green"/>
        <widget source="text2" render="Label" position="10,{h_t}" size="{w_m},150" font="Console; 28" foregroundColor="#ff0000"/>
    </screen>
    """

    def __init__(self, session, crashfile):
        self.session = session
        self.crashfile = crashfile
        Screen.__init__(self, session)

        self["text"] = ScrollLabel("")
        self["text2"] = ScrollLabel("")

        self["Redkey"] = StaticText(_("Close"))
        self["Greenkey"] = StaticText(_("Restart GUI"))

        self["shortcuts"] = ActionMap(
            ["ShortcutActions", "WizardActions"],
            {"cancel": self.exit, "back": self.exit, "red": self.exit}
        )

        self.read_crashfile()

        self["actions"] = ActionMap(
            ["OkCancelActions", "DirectionActions"],
            {
                "cancel": self.exit,
                "up": self["text"].pageUp,
                "down": self["text"].pageDown
            },
            -1
        )

    def read_crashfile(self):
        main_text = ""
        error_text = ""
        try:
            with open(self.crashfile, "r") as f:
                capture = False
                for line in f:
                    if "Traceback" in line or "Backtrace:" in line:
                        capture = True
                    if capture:
                        main_text += line
                        if "Error:" in line:
                            error_text += line
                        if any(x in line for x in ["]]>","dmesg","StackTrace","FATAL SIGNAL"]):
                            if "FATAL SIGNAL" in line:
                                error_text = "FATAL SIGNAL"
                            break
        except Exception as e:
            main_text = _("No data or error opening file")
            error_text = str(e)

        self["text"].setText(main_text)
        self["text2"].setText(error_text)

    def exit(self):
        self.close()

# --- Menu entries for the Main Menu ---
def menu(menuid, **kwargs):
    # Check if the menu is the Main Menu
    if menuid == "mainmenu":
        plugin_name = _("Crashlog Viewer") + " ver. " + version  # Combine name with version
        return [
            (plugin_name, main, "crashlogviewer_mainmenu", 50)  # Menu entry with version
        ]
    return []

# The function that gets executed when the menu item is clicked
def main(session, **kwargs):
    print("Opening CrashLogScreen.")  # Debugging output in English
    session.open(CrashLogScreen)  # Opens the CrashLogScreen

# Registering the plugin in various menus
def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name=(_("Crashlog Viewer") + " ver. " + version),  # Title in English
            description=_("View and remove crashlog files"),  # Description in English
            where=[PluginDescriptor.WHERE_PLUGINMENU, PluginDescriptor.WHERE_EXTENSIONSMENU],
            icon="crash.png",
            fnc=main,
        ),
        # Here the plugin is also added to the Main Menu
        PluginDescriptor(where=PluginDescriptor.WHERE_MENU, fnc=menu),  # Menu entry for the Main Menu
    ]
