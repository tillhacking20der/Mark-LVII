"""MODS hub for Mark-LVII.

This first version provides persistent voice preferences and safe launch points
for public mapping, weather, tracking and webcam services. It deliberately
does not embed remote pages or require WebGL/QtWebEngine.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFont
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from gui.theme import C
from gui.style import px_font


class ModsHubDialog(QDialog):
    """Small MODS window with VOICE, WORLD and WEBCAMS sections."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MODS — J.A.R.V.I.S.")
        self.setMinimumSize(760, 560)
        self.resize(900, 650)
        self.setModal(True)
        self.setStyleSheet(
            f"QDialog {{ background: {C.BG}; color: {C.TEXT}; }}"
            f"QLabel {{ color: {C.TEXT}; background: transparent; }}"
            f"QLineEdit, QComboBox {{ background: #07131b; color: {C.WHITE}; "
            f"border: 1px solid {C.PRI_DIM}; padding: 7px; border-radius: 4px; }}"
            f"QTabWidget::pane {{ border: 1px solid {C.PRI_DIM}; }}"
            f"QTabBar::tab {{ background: #07131b; color: {C.TEXT_DIM}; "
            f"padding: 10px 18px; }}"
            f"QTabBar::tab:selected {{ color: {C.PRI}; border-bottom: 2px solid {C.PRI}; }}"
            f"QPushButton {{ background: #0b202b; color: {C.PRI}; "
            f"border: 1px solid {C.PRI_DIM}; padding: 8px 12px; border-radius: 4px; }}"
            f"QPushButton:hover {{ background: #123444; }}"
            f"QGroupBox {{ color: {C.PRI}; border: 1px solid {C.PRI_DIM}; "
            f"margin-top: 10px; padding: 10px; }}"
            f"QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}"
        )

        root = QVBoxLayout(self)
        title = QLabel("◈  MODS CONTROL CENTER")
        title.setFont(px_font(17, QFont.Weight.DemiBold, spacing=2))
        title.setStyleSheet(f"color: {C.PRI}; padding: 5px;")
        root.addWidget(title)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._voice_tab(), "VOICE")
        self.tabs.addTab(self._world_tab(), "WORLD")
        self.tabs.addTab(self._webcams_tab(), "WEBCAMS")
        root.addWidget(self.tabs, 1)
        close_row = QHBoxLayout()
        close_row.addStretch()
        close = QPushButton("CLOSE")
        close.clicked.connect(self.accept)
        close_row.addWidget(close)
        root.addLayout(close_row)

    def _open(self, url: str):
        QDesktopServices.openUrl(QUrl(url))

    def _link_button(self, label: str, url: str) -> QPushButton:
        button = QPushButton(label)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(lambda _checked=False, target=url: self._open(target))
        return button

    def _voice_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        info = QLabel(
            "Lege Name und Sprachpräferenzen fest. Die Einstellungen werden lokal "
            "in deiner JARVIS-Konfiguration gespeichert."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        group = QGroupBox("ASSISTANT IDENTITY")
        form = QFormLayout(group)
        self.name_edit = QLineEdit()
        self.greeting_edit = QLineEdit()
        self.wake_edit = QLineEdit()
        self.language_box = QComboBox()
        self.language_box.addItems(["Deutsch", "English", "Français", "Español"])
        try:
            from memory.config_manager import (
                get_assistant_name, get_mods_preferences, get_user_name,
            )
            prefs = get_mods_preferences()
            self.name_edit.setText(get_assistant_name())
            self.greeting_edit.setText(prefs.get("greeting", "Hallo. Wie kann ich helfen?"))
            self.wake_edit.setText(prefs.get("activation_phrase", "Hey Jarvis"))
            language = prefs.get("language", "Deutsch")
            index = self.language_box.findText(language)
            if index >= 0:
                self.language_box.setCurrentIndex(index)
            self._user_name = get_user_name()
        except Exception:
            self.name_edit.setText("JARVIS")
            self.greeting_edit.setText("Hallo. Wie kann ich helfen?")
            self.wake_edit.setText("Hey Jarvis")
            self._user_name = ""

        form.addRow("Anzeigename:", self.name_edit)
        form.addRow("Begrüßung (gespeicherte Präferenz):", self.greeting_edit)
        form.addRow("Gewünschtes Aktivierungswort:", self.wake_edit)
        form.addRow("Bevorzugte Sprache:", self.language_box)
        layout.addWidget(group)

        note = QLabel(
            "Hinweis: Die aktuelle lokale Wake-Word-Erkennung verwendet weiterhin "
            "das fest trainierte Modell „Hey Jarvis“. Ein frei eingegebenes "
            "Aktivierungswort wird hier gespeichert, aber noch nicht von der "
            "Erkennung ausgelöst. Begrüßung und Sprache sind ebenfalls zunächst "
            "gespeicherte Präferenzen; die laufende Sprachsitzung wird dadurch "
            "nicht automatisch umgestellt."
        )
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {C.TEXT_DIM}; padding: 6px;")
        layout.addWidget(note)

        save = QPushButton("SAVE VOICE PREFERENCES")
        save.clicked.connect(self._save_voice)
        layout.addWidget(save)
        layout.addStretch()
        return page

    def _save_voice(self):
        name = self.name_edit.text().strip() or "JARVIS"
        greeting = self.greeting_edit.text().strip() or "Hallo. Wie kann ich helfen?"
        phrase = self.wake_edit.text().strip() or "Hey Jarvis"
        language = self.language_box.currentText()
        try:
            from memory.config_manager import save_assistant_config, save_mods_preferences
            save_assistant_config(name, self._user_name)
            save_mods_preferences({
                "greeting": greeting,
                "activation_phrase": phrase,
                "language": language,
            })
            QMessageBox.information(
                self, "Gespeichert",
                "Die Voice-Präferenzen wurden gespeichert. Einige davon benötigen "
                "noch eine spätere Anbindung an die aktive Sprach-Engine."
            )
        except Exception as exc:
            QMessageBox.warning(self, "Speichern fehlgeschlagen", str(exc))

    def _world_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        intro = QLabel(
            "Öffentliche Karten- und Weltraumdienste. Die Ansichten öffnen sich "
            "im Standardbrowser; dadurch umgehen wir die WebGL-Probleme des "
            "eingebetteten Qt-Browsers."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        search_group = QGroupBox("LOCATION SEARCH")
        search_layout = QVBoxLayout(search_group)
        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("Stadt, Land, Straße oder Sehenswürdigkeit eingeben …")
        search_layout.addWidget(self.location_edit)
        row = QHBoxLayout()
        row.addWidget(self._link_button("OPEN STREET MAP", "https://www.openstreetmap.org/"))
        search = QPushButton("SEARCH LOCATION")
        search.clicked.connect(self._search_location)
        row.addWidget(search)
        search_layout.addLayout(row)
        layout.addWidget(search_group)

        map_group = QGroupBox("EARTH & WEATHER")
        map_layout = QVBoxLayout(map_group)
        row = QHBoxLayout()
        row.addWidget(self._link_button("MAP VIEW", "https://www.openstreetmap.org/"))
        row.addWidget(self._link_button("SATELLITE VIEW", "https://www.google.com/maps/@?api=1&map_action=map"))
        row.addWidget(self._link_button("WEATHER MAP", "https://www.windy.com/"))
        map_layout.addLayout(row)
        layout.addWidget(map_group)

        space_group = QGroupBox("SPACE & LIVE TRACKING")
        space_layout = QVBoxLayout(space_group)
        row = QHBoxLayout()
        row.addWidget(self._link_button("SOLAR SYSTEM — NASA EYES", "https://eyes.nasa.gov/apps/solar-system/"))
        row.addWidget(self._link_button("SATELLITES / ISS", "https://www.n2yo.com/"))
        row.addWidget(self._link_button("AIRCRAFT", "https://www.flightradar24.com/"))
        row.addWidget(self._link_button("SHIPS", "https://www.marinetraffic.com/"))
        space_layout.addLayout(row)
        layout.addWidget(space_group)
        note = QLabel(
            "Live-Flugzeuge, Schiffe und Satelliten werden von den jeweiligen "
            "öffentlichen Anbietern dargestellt. Verfügbarkeit, Verzögerungen "
            "und Nutzungsbedingungen hängen vom Anbieter ab. Diese Version "
            "enthält noch keine eigene 3D-Globus- oder Orbit-Engine."
        )
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {C.TEXT_DIM}; padding: 6px;")
        layout.addWidget(note)
        layout.addStretch()
        return page

    def _search_location(self):
        query = self.location_edit.text().strip()
        if not query:
            QMessageBox.information(self, "Location", "Bitte gib zuerst einen Ort ein.")
            return
        from urllib.parse import quote
        self._open("https://www.openstreetmap.org/search?query=" + quote(query))

    def _webcams_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        intro = QLabel(
            "Hier findest du öffentlich angebotene Webcam-Verzeichnisse. "
            "Es werden keine privaten Kameras gesucht oder eingebunden."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        groups = [
            ("CITIES & LANDMARKS", [
                ("EARTHCAM — PUBLIC CITY CAMS", "https://www.earthcam.com/"),
                ("SKYLINEWEBCAMS", "https://www.skylinewebcams.com/"),
            ]),
            ("TRAFFIC & WEATHER", [
                ("WINDY WEBCAMS", "https://www.windy.com/webcams"),
                ("TRAFFIC CAMERAS", "https://www.google.com/search?q=official+public+traffic+webcams"),
            ]),
            ("BEACHES & NATURE", [
                ("PUBLIC BEACH WEBCAMS", "https://www.google.com/search?q=public+beach+webcams"),
                ("NATURE WEBCAMS", "https://www.google.com/search?q=public+nature+webcams"),
            ]),
        ]
        for heading, links in groups:
            group = QGroupBox(heading)
            row = QHBoxLayout(group)
            for label, url in links:
                row.addWidget(self._link_button(label, url))
            layout.addWidget(group)

        note = QLabel(
            "Die Verzeichnisse können eigene Konten, Werbung oder regionale "
            "Einschränkungen haben. Nur Streams verwenden, die der Betreiber "
            "ausdrücklich öffentlich bereitstellt."
        )
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {C.TEXT_DIM}; padding: 6px;")
        layout.addWidget(note)
        layout.addStretch()
        return page
