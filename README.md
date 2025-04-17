# TikTok Video Creator

Dieses Python-Skript erstellt automatisch kurze Videos im Hochformat, die für Plattformen wie TikTok geeignet sind. Es kombiniert einen eingegebenen Text (der per Text-to-Speech vorgelesen wird) mit einem Hintergrundvideo von Pexels und Hintergrundmusik zu einem fertigen Video mit Untertiteln.

## Features

*   **Text-to-Speech (TTS):** Wandelt eingegebenen deutschen Text in Sprache um (verwendet gTTS).
*   **Hintergrundvideo:** Lädt automatisch ein passendes, lizenzfreies Video von Pexels basierend auf einem Stichwort herunter. Bevorzugt HD-Videos im Hochformat.
*   **Hintergrundmusik:** Ermöglicht die Auswahl einer lokalen Musikdatei, die leise im Hintergrund läuft.
*   **Untertitel:** Generiert automatisch Untertitel basierend auf den Text-Chunks und fügt sie in das Video ein.
*   **Hashtag-Vorschläge:** Generiert nach erfolgreicher Videoerstellung 7 relevante Hashtags basierend auf dem eingegebenen Text.
*   **Einfache GUI:** Bietet eine grafische Benutzeroberfläche (erstellt mit Tkinter) zur einfachen Eingabe von Text, Video-Stichwort und Musikauswahl.
*   **Status-Updates:** Zeigt den Fortschritt der Videoerstellung im GUI an.

## Einrichtung

1.  **Python:** Stelle sicher, dass Python 3 installiert ist.
2.  **Abhängigkeiten:** Installiere die benötigten Python-Bibliotheken. Es wird empfohlen, dies in einer virtuellen Umgebung zu tun:
    ```bash
    pip install -r requirements.txt
    ```
    Erstelle eine `requirements.txt`-Datei mit folgendem Inhalt:
    ```
    opencv-python-headless
    numpy
    gTTS
    pydub
    requests
    python-dotenv
    moviepy
    tk # (Normalerweise Teil der Standard-Python-Installation)
    ```
    *Hinweis: `moviepy` benötigt möglicherweise `ffmpeg`. Stelle sicher, dass ffmpeg installiert und im Systempfad verfügbar ist.*
3.  **Pexels API Key:**
    *   Erstelle einen kostenlosen Account auf [Pexels](https://www.pexels.com/api/).
    *   Erhalte deinen API-Schlüssel.
    *   Erstelle eine Datei namens `.env` im selben Verzeichnis wie das Skript (`tiktok_video_creator.py`).
    *   Füge deinen API-Schlüssel zur `.env`-Datei hinzu:
        ```env
        PEXELS_API_KEY=DEIN_PEXELS_API_SCHLUESSEL
        ```
        Ersetze `DEIN_PEXELS_API_SCHLUESSEL` durch deinen tatsächlichen Schlüssel.

## Verwendung

1.  Führe das Skript aus:
    ```bash
    python tiktok_video_creator.py
    ```
2.  Die grafische Benutzeroberfläche wird geöffnet.
3.  **Text für das Video:** Gib den Text ein, der im Video gesprochen und als Untertitel angezeigt werden soll.
4.  **Stichwort für Hintergrundvideo:** Gib ein Stichwort ein (z.B. "Natur", "Stadt", "Technologie"), nach dem auf Pexels nach einem passenden Hintergrundvideo gesucht werden soll. Wenn leer gelassen, wird "Natur" verwendet.
5.  **Hintergrundmusik:** Klicke auf "Durchsuchen..." und wähle eine lokale Audiodatei (`.mp3`, `.wav`, etc.) aus.
6.  Klicke auf "Video erstellen".
7.  Der Fortschritt wird im Statusfenster angezeigt.
8.  Nach Abschluss wird eine Erfolgsmeldung mit dem Dateinamen des Videos und vorgeschlagenen Hashtags angezeigt, oder eine Fehlermeldung, falls etwas schiefgeht.

## Ausgabe

Das fertige Video wird standardmäßig als `final_video_with_subtitles.mp4` im selben Verzeichnis wie das Skript gespeichert. Temporäre Dateien (Audio-Chunks, heruntergeladenes Video, etc.) werden nach der Verarbeitung automatisch gelöscht.
