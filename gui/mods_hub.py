"""MODS: voice settings, browser-based 3D views and public webcam search."""
from __future__ import annotations
import json
from pathlib import Path
from urllib.parse import quote
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QComboBox, QDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMessageBox, QPushButton, QTabWidget, QVBoxLayout, QWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView
from gui.theme import C
from gui.style import px_font


class ModsHubDialog(QDialog):
    """MODS dialog with embedded browser views for World and Webcams."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MODS — J.A.R.V.I.S.")
        self.setMinimumSize(780, 590)
        self.resize(960, 700)
        self.setModal(True)
        self.setStyleSheet(
            f"QDialog {{ background:{C.BG}; color:{C.TEXT}; }}"
            f"QLabel {{ color:{C.TEXT}; background:transparent; }}"
            f"QLineEdit,QComboBox,QListWidget {{ background:#07131b; color:{C.WHITE}; border:1px solid {C.PRI_DIM}; padding:7px; }}"
            f"QTabWidget::pane {{ border:1px solid {C.PRI_DIM}; }}"
            f"QTabBar::tab {{ background:#07131b; color:{C.TEXT_DIM}; padding:10px 18px; }}"
            f"QTabBar::tab:selected {{ color:{C.PRI}; border-bottom:2px solid {C.PRI}; }}"
            f"QPushButton {{ background:#0b202b; color:{C.PRI}; border:1px solid {C.PRI_DIM}; padding:8px 12px; }}"
            f"QPushButton:hover {{ background:#123444; }}"
            f"QGroupBox {{ color:{C.PRI}; border:1px solid {C.PRI_DIM}; margin-top:10px; padding:10px; }}"
        )
        self.prefs = self._get_prefs()
        root=QVBoxLayout(self)
        title=QLabel("◈  MODS CONTROL CENTER")
        title.setFont(px_font(17,QFont.Weight.DemiBold,spacing=2))
        title.setStyleSheet(f"color:{C.PRI}; padding:5px;")
        root.addWidget(title)
        self.tabs=QTabWidget()
        self.tabs.addTab(self._voice_tab(),"VOICE")
        self.tabs.addTab(self._world_tab(),"WORLD")
        self.tabs.addTab(self._webcams_tab(),"WEBCAMS")
        root.addWidget(self.tabs,1)
        row=QHBoxLayout(); row.addStretch()
        close=QPushButton("CLOSE"); close.clicked.connect(self.accept); row.addWidget(close); root.addLayout(row)

    @staticmethod
    def _get_prefs():
        try:
            from memory.config_manager import get_mods_preferences
            return get_mods_preferences()
        except Exception:
            return {}

    def _save_prefs(self, **values):
        self.prefs.update(values)
        try:
            from memory.config_manager import save_mods_preferences
            save_mods_preferences(values)
        except Exception as exc:
            QMessageBox.warning(self,"Speichern fehlgeschlagen",str(exc))

    def _open(self,url,browser=None):
        target=browser or getattr(self,"world_browser",None)
        if target is None:
            QMessageBox.warning(self,"MODS","Die interne Browserfläche ist noch nicht bereit.")
            return
        target.setUrl(QUrl(url))

    def _link(self,label,url,browser=None):
        b=QPushButton(label); b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.clicked.connect(lambda _=False,u=url,w=browser:self._open(u,w))
        return b

    def _local_view(self,name,browser=None):
        path=Path(__file__).resolve().parent/name
        if not path.is_file():
            QMessageBox.warning(self,"MODS",f"Datei fehlt: {name}"); return
        target=browser or getattr(self,"world_browser",None)
        if target is None:
            QMessageBox.warning(self,"MODS","Die interne Browserfläche ist noch nicht bereit.")
            return
        target.setUrl(QUrl.fromLocalFile(str(path)))

    def _voice_tab(self):
        page=QWidget(); layout=QVBoxLayout(page)
        intro=QLabel("Name, Standardbegrüßung und Sprache werden gespeichert und in der Sprachsitzung verwendet.")
        intro.setWordWrap(True); layout.addWidget(intro)
        group=QGroupBox("ASSISTANT IDENTITY"); form=QFormLayout(group)
        self.name=QLineEdit(); self.greeting=QLineEdit(); self.wake=QLineEdit()
        self.language=QComboBox(); self.language.addItems(["Deutsch","English","Français","Español"])
        try:
            from memory.config_manager import get_assistant_name,get_user_name
            self.name.setText(get_assistant_name()); self.user_name=get_user_name()
        except Exception:
            self.name.setText("JARVIS"); self.user_name=""
        self.greeting.setText(str(self.prefs.get("greeting","Hallo. Wie kann ich helfen?")))
        self.wake.setText(str(self.prefs.get("activation_phrase","Hey Jarvis")))
        ix=self.language.findText(str(self.prefs.get("language","Deutsch")))
        if ix>=0: self.language.setCurrentIndex(ix)
        form.addRow("Anzeigename:",self.name); form.addRow("Standardbegrüßung:",self.greeting)
        form.addRow("Gewünschtes Aktivierungswort:",self.wake); form.addRow("Standardsprache:",self.language)
        layout.addWidget(group)
        note=QLabel("Das Wake-Word-Modell ist weiterhin fest auf „Hey Jarvis“ trainiert. Ein anderes Wort wird nur gespeichert und erst erkannt, wenn ein passendes trainiertes Modell installiert ist.")
        note.setWordWrap(True); note.setStyleSheet(f"color:{C.TEXT_DIM}; padding:6px;"); layout.addWidget(note)
        save=QPushButton("SAVE VOICE SETTINGS"); save.clicked.connect(self._save_voice); layout.addWidget(save)
        layout.addStretch(); return page

    def _save_voice(self):
        try:
            from memory.config_manager import save_assistant_config
            save_assistant_config(self.name.text().strip() or "JARVIS",self.user_name)
            self._save_prefs(greeting=self.greeting.text().strip() or "Hallo. Wie kann ich helfen?",
                activation_phrase=self.wake.text().strip() or "Hey Jarvis",language=self.language.currentText())
            QMessageBox.information(self,"Gespeichert","Name, Begrüßung und Sprache sind gespeichert. Sie werden beim nächsten Sprachstart verwendet. Das erkannte Wake-Word bleibt vorerst „Hey Jarvis“.")
        except Exception as exc: QMessageBox.warning(self,"Fehler",str(exc))

    def _world_tab(self):
        page=QWidget(); layout=QVBoxLayout(page)
        intro=QLabel("Interaktiver 3D-Globus mit Orts- und Straßensuche. Der Globus und Karten werden direkt hier in Mark-LVII angezeigt.")
        intro.setWordWrap(True); layout.addWidget(intro)
        self.world_browser=QWebEngineView(page)
        globe=QPushButton("OPEN INTERACTIVE 3D GLOBE")
        globe.clicked.connect(lambda:self._local_view("mods_globe.html",self.world_browser)); layout.addWidget(globe)
        group=QGroupBox("LOCATION SEARCH"); v=QVBoxLayout(group)
        self.location=QLineEdit(); self.location.setPlaceholderText("Stadt, Land, Straße, Hausnummer oder Sehenswürdigkeit …"); v.addWidget(self.location)
        row=QHBoxLayout(); search=QPushButton("SEARCH LOCATION"); search.clicked.connect(self._search_location); row.addWidget(search)
        row.addWidget(self._link("OPEN MAP","https://www.openstreetmap.org/",self.world_browser))
        row.addWidget(self._link("SATELLITE MAP","https://www.google.com/maps/@?api=1&map_action=map",self.world_browser)); v.addLayout(row)
        row=QHBoxLayout()
        save_place=QPushButton("SAVE LOCATION"); save_place.clicked.connect(self._save_location); row.addWidget(save_place)
        self.world_favorites=QListWidget()
        for place in self._world_favorites(): self.world_favorites.addItem(place)
        self.world_favorites.itemDoubleClicked.connect(lambda item:self._open_location(item.text()))
        v.addLayout(row); v.addWidget(self.world_favorites)
        row=QHBoxLayout()
        open_place=QPushButton("OPEN SELECTED"); open_place.clicked.connect(self._open_selected_location); row.addWidget(open_place)
        remove_place=QPushButton("REMOVE SELECTED"); remove_place.clicked.connect(self._remove_location); row.addWidget(remove_place)
        v.addLayout(row); layout.addWidget(group)
        space=QGroupBox("SPACE, LIVE TRACKING & WEATHER"); v=QVBoxLayout(space)
        row=QHBoxLayout(); row.addWidget(self._link("NASA SOLAR SYSTEM","https://eyes.nasa.gov/apps/solar-system/",self.world_browser))
        solar=QPushButton("LOCAL 3D SOLAR SYSTEM"); solar.clicked.connect(lambda:self._local_view("mods_solar.html",self.world_browser)); row.addWidget(solar); v.addLayout(row)
        row=QHBoxLayout()
        for label,url in [("SATELLITES / ISS","https://www.n2yo.com/"),("AIRCRAFT","https://www.flightradar24.com/"),("SHIPS","https://www.marinetraffic.com/"),("WEATHER / RADAR","https://www.windy.com/")]:
            row.addWidget(self._link(label,url,self.world_browser))
        v.addLayout(row); layout.addWidget(space)
        note=QLabel("Echtzeitdaten für Flugzeuge, Schiffe, Satelliten und Wetter kommen von den jeweiligen öffentlichen Anbietern; Verfügbarkeit und Verzögerungen hängen von ihnen ab.")
        note.setWordWrap(True); note.setStyleSheet(f"color:{C.TEXT_DIM}; padding:6px;"); layout.addWidget(note)
        self.world_browser.setMinimumHeight(280)
        self.world_browser.setUrl(QUrl.fromLocalFile(str(Path(__file__).resolve().parent/"mods_globe.html")))
        layout.addWidget(self.world_browser,1)
        return page

    def _search_location(self):
        q=self.location.text().strip()
        if not q: QMessageBox.information(self,"Location","Bitte zuerst einen Ort eingeben."); return
        js = "const i=document.getElementById('place'); if(i){i.value="+json.dumps(q)+"; document.getElementById('search').click();}"
        self.world_browser.page().runJavaScript(js)

    def _world_favorites(self):
        try:
            raw=self.prefs.get("world_favorites","[]"); values=json.loads(raw) if isinstance(raw,str) else raw
            return [str(x) for x in values if str(x).strip()][:50]
        except Exception: return []

    def _save_location(self):
        q=self.location.text().strip()
        if not q: QMessageBox.information(self,"Location","Bitte zuerst einen Ort eingeben."); return
        vals=self._world_favorites()
        if q not in vals:
            vals.append(q); self._save_prefs(world_favorites=json.dumps(vals[-50:],ensure_ascii=False)); self.world_favorites.addItem(q)

    def _open_location(self,q):
        self.location.setText(q)
        js = "const i=document.getElementById('place'); if(i){i.value="+json.dumps(q)+"; document.getElementById('search').click();}"
        self.world_browser.page().runJavaScript(js)

    def _open_selected_location(self):
        item=self.world_favorites.currentItem()
        if item: self._open_location(item.text())

    def _remove_location(self):
        item=self.world_favorites.currentItem()
        if not item: return
        vals=[x for x in self._world_favorites() if x!=item.text()]
        self._save_prefs(world_favorites=json.dumps(vals,ensure_ascii=False))
        self.world_favorites.takeItem(self.world_favorites.row(item))

    def _webcams_tab(self):
        page=QWidget(); layout=QVBoxLayout(page)
        intro=QLabel("Suche nach öffentlich angebotenen Webcams für Städte, Sehenswürdigkeiten, Verkehr, Wetter, Strände und Natur. Private oder nicht freigegebene Kameras werden nicht gesucht.")
        intro.setWordWrap(True); layout.addWidget(intro)
        self.webcam_browser=QWebEngineView(page)
        group=QGroupBox("PUBLIC WEBCAM SEARCH"); v=QVBoxLayout(group)
        self.webcam_query=QLineEdit(); self.webcam_query.setPlaceholderText("z. B. Berlin, Alpen, Strand, Verkehr A3 …"); v.addWidget(self.webcam_query)
        row=QHBoxLayout(); search=QPushButton("SEARCH PUBLIC WEBCAMS"); search.clicked.connect(self._search_webcams); row.addWidget(search)
        save=QPushButton("SAVE SEARCH"); save.clicked.connect(self._save_favorite); row.addWidget(save); v.addLayout(row); layout.addWidget(group)
        dirs=QGroupBox("PUBLIC WEBCAM DIRECTORIES"); row=QHBoxLayout(dirs)
        row.addWidget(self._link("SKYLINE WEBCAMS","https://www.skylinewebcams.com/",self.webcam_browser))
        row.addWidget(self._link("EARTHCAM","https://www.earthcam.com/",self.webcam_browser))
        row.addWidget(self._link("WINDY WEBCAMS","https://www.windy.com/webcams",self.webcam_browser)); layout.addWidget(dirs)
        fav=QGroupBox("SAVED SEARCHES"); v=QVBoxLayout(fav); self.favorites=QListWidget()
        for q in self._favorites(): self.favorites.addItem(q)
        self.favorites.itemDoubleClicked.connect(lambda item:self._open_query(item.text())); v.addWidget(self.favorites)
        row=QHBoxLayout(); op=QPushButton("OPEN SELECTED"); op.clicked.connect(self._open_selected); row.addWidget(op)
        rm=QPushButton("REMOVE SELECTED"); rm.clicked.connect(self._remove_selected); row.addWidget(rm); v.addLayout(row)
        layout.addWidget(fav)
        self.webcam_browser.setMinimumHeight(300)
        self.webcam_browser.setUrl(QUrl("https://www.google.com/search?q=public+live+webcams"))
        layout.addWidget(self.webcam_browser,1)
        note=QLabel("Suchergebnisse und öffentliche Webcam-Seiten werden innerhalb dieses Fensters angezeigt. Verfügbarkeit und Live-Stream hängen vom Betreiber ab.")
        note.setWordWrap(True); note.setStyleSheet(f"color:{C.TEXT_DIM}; padding:6px;"); layout.addWidget(note)
        return page

    def _search_webcams(self):
        q=self.webcam_query.text().strip()
        if not q: QMessageBox.information(self,"Webcams","Bitte Ort oder Thema eingeben."); return
        self._open_query(q)

    def _open_query(self,q):
        self._open("https://www.google.com/search?q="+quote("public live webcams "+q),self.webcam_browser)

    def _favorites(self):
        try:
            raw=self.prefs.get("webcam_favorites","[]"); values=json.loads(raw) if isinstance(raw,str) else raw
            return [str(x) for x in values if str(x).strip()][:50]
        except Exception: return []

    def _save_favorite(self):
        q=self.webcam_query.text().strip()
        if not q: QMessageBox.information(self,"Webcams","Bitte zuerst eine Suche eingeben."); return
        vals=self._favorites()
        if q not in vals:
            vals.append(q); self._save_prefs(webcam_favorites=json.dumps(vals[-50:],ensure_ascii=False)); self.favorites.addItem(q)

    def _open_selected(self):
        item=self.favorites.currentItem()
        if item: self._open_query(item.text())

    def _remove_selected(self):
        item=self.favorites.currentItem()
        if not item: return
        vals=[x for x in self._favorites() if x!=item.text()]
        self._save_prefs(webcam_favorites=json.dumps(vals,ensure_ascii=False))
        self.favorites.takeItem(self.favorites.row(item))
