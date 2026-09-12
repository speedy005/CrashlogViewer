# 💥 CrashlogViewer for Enigma2

> **Ein moderner und benutzerfreundlicher Crashlog-Viewer für Enigma2-basierte Receiver.**
> **A modern and user-friendly crash log viewer for Enigma2-based receivers.**

[![Enigma2](https://img.shields.io/badge/Enigma2-Plugin-blue.svg)](#) [![Python](https://img.shields.io/badge/Python-2%20%7C%203-yellow.svg)](#) [![License](https://img.shields.io/badge/License-GPL--v2-green.svg)](#lizenz--license)

---

# 🇩🇪 Deutsch

## 📖 Über das Projekt

**CrashlogViewer** ist ein Enigma2-Plugin zur einfachen Anzeige und Analyse von Crashlogs.

Das Plugin wurde speziell für **Dreamboxen und andere Enigma2-basierte Receiver** entwickelt und hilft dabei, Systemabstürze und Fehler schneller zu analysieren.

Statt Crashlogs manuell über FTP, SSH oder das Dateisystem suchen zu müssen, bietet CrashlogViewer eine übersichtliche Oberfläche direkt auf dem Receiver.

### 🎯 Ziel

**CrashlogViewer soll die Fehlersuche so einfach wie möglich machen.**

```text
Crash
  ↓
CrashlogViewer öffnen
  ↓
Crashlog auswählen
  ↓
Log analysieren
  ↓
Fehlerursache finden
```

---

## ✨ Funktionen

* 💥 **Crashlog-Übersicht**
  Alle verfügbaren Crashlogs übersichtlich anzeigen.

* 🔎 **Einfache Analyse**
  Crashlogs direkt auf dem Receiver öffnen und untersuchen.

* 🌍 **Mehrsprachigkeit**
  Unterstützung verschiedener Sprachen und Anpassung an die Enigma2-Systemsprache.

* 📺 **Enigma2-Integration**
  Nahtlose Integration in das Enigma2-System.

* ⭐ **Dreambox-Unterstützung**
  Optimiert für Dreamboxen, aber auch für andere Enigma2-Receiver geeignet.

* 🎨 **Übersichtliche Benutzeroberfläche**
  Einfaches und intuitives Design für eine schnelle Fehlersuche.

* 🧩 **Erweiterbar**
  Die übersichtliche Projektstruktur erleichtert zukünftige Erweiterungen und Anpassungen.

---

## 🚀 Warum CrashlogViewer?

Wenn Enigma2 abstürzt, ist die Ursache häufig in einem Crashlog zu finden.

CrashlogViewer macht den Zugriff darauf deutlich einfacher.

Keine komplizierte Dateisuche und kein SSH notwendig:

**Öffnen → Auswählen → Lesen → Analysieren**

Das Plugin kann unter anderem bei der Untersuchung von folgenden Problemen helfen:

* Enigma2-Abstürzen
* Plugin-Abstürzen
* Python-Exceptions
* GUI-Problemen
* Treiberproblemen
* unerwartetem Systemverhalten

---

## 📦 Installation

### Voraussetzungen

* Enigma2-basierter Receiver
* Dreambox oder kompatibler Enigma2-Receiver
* Python 2 oder Python 3, abhängig von der verwendeten Enigma2-Version

### Installation über den Plugin-Feed

Falls CrashlogViewer über den verwendeten Plugin-Feed verfügbar ist:

1. Enigma2 **Plugin-Browser** öffnen
2. Nach **CrashlogViewer** suchen
3. Plugin installieren
4. Falls erforderlich, Enigma2 neu starten

### Manuelle Installation

Das Plugin kann auch manuell auf den Receiver kopiert werden.

Installationspfad:

```text
/usr/lib/enigma2/python/Plugins/Extensions/CrashlogViewer/
```

Nach der Installation sollte Enigma2 gegebenenfalls neu gestartet werden.

---

## 📁 Projektstruktur

```text
CrashlogViewer/
├── CrashlogViewer.py
├── utils.py
├── locale/
│   ├── de/
│   ├── en/
│   └── ...
└── ...
```

### Wichtige Dateien

| Datei / Verzeichnis | Beschreibung                                    |
| ------------------- | ----------------------------------------------- |
| `CrashlogViewer.py` | Hauptlogik und Benutzeroberfläche               |
| `utils.py`          | Hilfsfunktionen für Verarbeitung und Verwaltung |
| `locale/`           | Übersetzungen und Sprachdateien                 |

---

## 🌍 Übersetzungen

CrashlogViewer unterstützt verschiedene Sprachen.

Die Übersetzungen befinden sich im Verzeichnis:

```text
locale/
```

Neue Übersetzungen können einfach hinzugefügt oder bestehende Übersetzungen verbessert werden.

**Du möchtest bei einer Übersetzung helfen? Contributions are welcome! ❤️**

---

## 🖥️ Verwendung

Nach der Installation kann CrashlogViewer über das Enigma2-Menü gestartet werden.

Beim Start wird eine Liste der verfügbaren Crashlogs angezeigt.

Anschließend kann ein Crashlog ausgewählt und detailliert betrachtet werden.

```text
┌───────────────────────┐
│   CrashlogViewer      │
├───────────────────────┤
│ 📄 crashlog_01        │
│ 📄 crashlog_02        │
│ 📄 crashlog_03        │
│ 📄 crashlog_04        │
└───────────────────────┘
          ↓
     🔍 Analysieren
```

---

## 📸 Screenshots

Screenshots können hier ergänzt werden:

```text
docs/
└── screenshots/
    ├── main.png
    ├── crashlog.png
    └── viewer.png
```

Beispiel:

```markdown
![CrashlogViewer](docs/screenshots/main.png)
```

---

## 🤝 Mitmachen

Beiträge zur Weiterentwicklung sind jederzeit willkommen.

Besonders hilfreich sind:

* 🐛 Bugfixes
* 💡 neue Funktionen
* 🎨 Verbesserungen der Benutzeroberfläche
* 🌍 neue Übersetzungen
* ⚡ Performance-Optimierungen
* 📺 Verbesserungen der Receiver-Kompatibilität

### 🐛 Fehler gefunden?

Bitte erstelle ein **GitHub Issue** und füge möglichst folgende Informationen hinzu:

* Receiver-Modell
* verwendetes Enigma2-Image
* Plugin-Version
* Beschreibung des Problems
* Schritte zur Reproduktion
* relevanter Crashlog
* Screenshots, falls vorhanden

---

## 💬 Support

Bei Problemen oder Fragen kann das **GitHub Issues-System** verwendet werden.

Bitte überprüfe zunächst, ob bereits ein ähnliches Issue existiert.

Je mehr Informationen bereitgestellt werden, desto einfacher ist es, ein Problem nachzustellen und zu beheben.

---

## 📜 Lizenz

CrashlogViewer wird unter der **GNU General Public License v2.0 (GPL-2.0)** veröffentlicht.

Der Quellcode darf entsprechend den Bedingungen der GPL-v2:

* ✅ verwendet
* ✅ untersucht
* ✅ verändert
* ✅ weitergegeben

werden.

---

# 🇬🇧 English

## 📖 About

**CrashlogViewer** is an Enigma2 plugin designed to make viewing and analyzing crash logs simple and convenient.

It was developed specifically for **Dreambox and other Enigma2-based receivers** and helps users investigate system crashes and errors quickly.

Instead of manually searching through files via FTP, SSH or the filesystem, CrashlogViewer provides a clean interface directly on the receiver.

### 🎯 Goal

**CrashlogViewer makes troubleshooting as simple as possible.**

```text
Crash
  ↓
Open CrashlogViewer
  ↓
Select crash log
  ↓
Inspect log
  ↓
Find the problem
```

---

## ✨ Features

* 💥 **Crash Log Browser**
  Browse all available crash logs in one place.

* 🔎 **Easy Log Analysis**
  Open and inspect crash logs directly on your receiver.

* 🌍 **Multi-Language Support**
  Supports multiple languages and follows the Enigma2 system language.

* 📺 **Enigma2 Integration**
  Seamlessly integrates into the Enigma2 environment.

* ⭐ **Dreambox Support**
  Optimized for Dreambox receivers while remaining suitable for other Enigma2 devices.

* 🎨 **Clean User Interface**
  Simple and intuitive interface focused on fast troubleshooting.

* 🧩 **Easy to Extend**
  A clean project structure makes future improvements and extensions easier.

---

## 🚀 Why CrashlogViewer?

When Enigma2 crashes, the cause can often be found in the generated crash log.

CrashlogViewer makes accessing these logs much easier.

No complicated file browsing and no SSH required:

**Open → Select → Read → Analyze**

CrashlogViewer can help investigate issues such as:

* Enigma2 crashes
* Plugin crashes
* Python exceptions
* GUI problems
* Driver-related issues
* Unexpected system behavior

---

## 📦 Installation

### Requirements

* An Enigma2-based receiver
* Dreambox or compatible Enigma2 set-top box
* Python 2 or Python 3, depending on your Enigma2 version

### Installation via Plugin Feed

If CrashlogViewer is available through your image's plugin feed:

1. Open the **Enigma2 Plugin Browser**
2. Search for **CrashlogViewer**
3. Install the plugin
4. Restart Enigma2 if required

### Manual Installation

The plugin can also be copied manually to the receiver.

Installation path:

```text
/usr/lib/enigma2/python/Plugins/Extensions/CrashlogViewer/
```

Restart Enigma2 after installation if required.

---

## 📁 Project Structure

```text
CrashlogViewer/
├── CrashlogViewer.py
├── utils.py
├── locale/
│   ├── de/
│   ├── en/
│   └── ...
└── ...
```

### Important Files

| File / Directory    | Description                                       |
| ------------------- | ------------------------------------------------- |
| `CrashlogViewer.py` | Main plugin logic and user interface              |
| `utils.py`          | Helper functions for processing and handling data |
| `locale/`           | Translation and localization files                |

---

## 🌍 Translations

CrashlogViewer supports multiple languages.

Translation files are stored in:

```text
locale/
```

New languages can easily be added, and existing translations can be improved.

**Want to help with translations? Contributions are welcome! ❤️**

---

## 🖥️ Usage

After installation, CrashlogViewer can be launched from the Enigma2 menu.

The plugin displays a list of available crash logs.

Select a crash log to open and inspect its contents.

```text
┌───────────────────────┐
│   CrashlogViewer      │
├───────────────────────┤
│ 📄 crashlog_01        │
│ 📄 crashlog_02        │
│ 📄 crashlog_03        │
│ 📄 crashlog_04        │
└───────────────────────┘
          ↓
      🔍 Analyze
```

---

## 📸 Screenshots

Screenshots can be added here:

```text
docs/
└── screenshots/
    ├── main.png
    ├── crashlog.png
    └── viewer.png
```

Example:

```markdown
![CrashlogViewer](docs/screenshots/main.png)
```

---

## 🤝 Contributing

Contributions are always welcome!

Especially useful contributions include:

* 🐛 Bug fixes
* 💡 New features
* 🎨 UI improvements
* 🌍 New translations
* ⚡ Performance improvements
* 📺 Compatibility improvements

### 🐛 Found a Bug?

Please open a **GitHub Issue** and provide as much information as possible:

* Receiver model
* Enigma2 image
* Plugin version
* Description of the problem
* Steps to reproduce
* Relevant crash log
* Screenshots, if available

---

## 💬 Support

For problems, questions or suggestions, please use the **GitHub Issues** system.

Before opening a new issue, please check whether a similar issue already exists.

The more information you provide, the easier it is to reproduce and fix the problem.

---

## 📜 License

CrashlogViewer is released under the **GNU General Public License v2.0 (GPL-2.0)**.

Under the terms of the GPL-v2 license, the software may be:

* ✅ Used
* ✅ Studied
* ✅ Modified
* ✅ Redistributed

as long as the license requirements are respected.

---

## ⭐ Support the Project

If you find **CrashlogViewer** useful:

⭐ **Star the repository**
🐛 **Report bugs**
💡 **Suggest improvements**
🔧 **Contribute code**
🌍 **Improve translations**

Every contribution helps make CrashlogViewer better for the Enigma2 community.

---

# 🚀 Crash less. Understand more.

### CrashlogViewer

**Making Enigma2 crash logs easier to find, read and understand.**




<img width="1920" height="1080" alt="screenshot" src="https://github.com/user-attachments/assets/94533891-2b37-454c-8506-25647ed2a220" />
<img width="1920" height="1080" alt="ssss" src="https://github.com/user-attachments/assets/52723445-c417-4b79-9bef-76af61adb078" />

wget -qO /tmp/installer.sh "https://raw.githubusercontent.com/speedy005/CrashlogViewer/main/installer.sh" && chmod 777 /tmp/installer.sh && /tmp/installer.sh
