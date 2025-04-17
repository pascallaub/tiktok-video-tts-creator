import os
import cv2
import numpy as np
from gtts import gTTS
from pydub import AudioSegment
import requests
from dotenv import load_dotenv
import random
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import moviepy.editor as mp
import time
import math
import re
from collections import Counter

# Lade Umgebungsvariablen aus der .env Datei
load_dotenv()

# --- Basic German Stop Words ---
GERMAN_STOP_WORDS = set([
    'aber', 'alle', 'allem', 'allen', 'aller', 'alles', 'als', 'also', 'am', 'an', 'ander', 'andere', 'anderem',
    'anderen', 'anderer', 'anderes', 'anders', 'auch', 'auf', 'aus', 'bei', 'bin', 'bis', 'bist', 'da', 'damit',
    'dann', 'der', 'den', 'des', 'dem', 'die', 'das', 'dass', 'daß', 'derselbe', 'derselben', 'denselben',
    'desselben', 'demselben', 'dieselbe', 'dieselben', 'dasselbe', 'dazu', 'dein', 'deine', 'deinem', 'deinen',
    'deiner', 'deines', 'denn', 'derer', 'dessen', 'dich', 'dir', 'du', 'dies', 'diese', 'diesem', 'diesen',
    'dieser', 'dieses', 'doch', 'dort', 'durch', 'ein', 'eine', 'einem', 'einen', 'einer', 'eines', 'einig',
    'einige', 'einigem', 'einigen', 'einiger', 'einiges', 'einmal', 'er', 'ihn', 'ihm', 'es', 'etwas', 'euer',
    'eure', 'eurem', 'euren', 'eurer', 'eures', 'für', 'gegen', 'gewesen', 'hab', 'habe', 'haben', 'hat', 'hatte',
    'hatten', 'hier', 'hin', 'hinter', 'ich', 'mich', 'mir', 'ihr', 'ihre', 'ihrem', 'ihren', 'ihrer', 'ihres',
    'euch', 'im', 'in', 'indem', 'ins', 'ist', 'jede', 'jedem', 'jeden', 'jeder', 'jedes', 'jene', 'jenem',
    'jenen', 'jener', 'jenes', 'jetzt', 'kann', 'kein', 'keine', 'keinem', 'keinen', 'keiner', 'keines', 'können',
    'könnte', 'machen', 'man', 'manche', 'manchem', 'manchen', 'mancher', 'manches', 'mein', 'meine', 'meinem',
    'meinen', 'meiner', 'meines', 'mit', 'muss', 'musste', 'nach', 'nicht', 'nichts', 'noch', 'nun', 'nur',
    'ob', 'oder', 'ohne', 'sehr', 'sein', 'seine', 'seinem', 'seinen', 'seiner', 'seines', 'selbst', 'sich',
    'sie', 'ihnen', 'sind', 'so', 'solche', 'solchem', 'solchen', 'solcher', 'solches', 'soll', 'sollte',
    'sondern', 'sonst', 'über', 'um', 'und', 'uns', 'unsere', 'unserem', 'unseren', 'unser', 'unseres', 'unter',
    'viel', 'vom', 'von', 'vor', 'während', 'war', 'waren', 'warst', 'was', 'weg', 'weil', 'weiter', 'welche',
    'welchem', 'welchen', 'welcher', 'welches', 'wenn', 'werde', 'werden', 'wer', 'wie', 'wieder', 'will', 'wir',
    'wird', 'wirst', 'wo', 'wollen', 'wollte', 'würde', 'würden', 'zu', 'zum', 'zur', 'zwar', 'zwischen'
])

# Hilfsfunktion für GUI Status Update
def update_status_safe(status_widget, message):
    """Aktualisiert ein Tkinter-Widget sicher aus einem Thread."""
    if status_widget.winfo_exists():
        if "%" in message:
            content = status_widget.get("1.0", tk.END).strip()
            lines = content.split('\n')
            found = False
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].startswith("Fortschritt:"):
                    lines[i] = message
                    found = True
                    break
            if not found:
                lines.append(message)
            new_content = "\n".join(lines) + "\n"
            status_widget.config(state=tk.NORMAL)
            status_widget.delete("1.0", tk.END)
            status_widget.insert(tk.END, new_content)
            status_widget.config(state=tk.DISABLED)
        else:
            status_widget.config(state=tk.NORMAL)
            status_widget.insert(tk.END, message + "\n")
            status_widget.config(state=tk.DISABLED)
        status_widget.see(tk.END)

# New function to generate speech chunks and timestamps
def generate_speech_chunks_and_timestamps(text, base_filename="speech_chunk", status_callback=None, words_per_chunk=5):
    """
    Splits text into chunks, generates TTS for each, measures duration,
    concatenates audio, and returns timestamps and total duration.
    """
    timestamps = []
    chunk_files = []
    total_duration = 0.0
    combined_audio = AudioSegment.empty()
    output_concatenated_audio_filename = f"{base_filename}_full.mp3"

    # Simple word splitting
    words = text.split()
    num_chunks = math.ceil(len(words) / words_per_chunk)

    if status_callback: status_callback(f"Aufteilen des Textes in {num_chunks} Teile...")

    for i in range(num_chunks):
        start_word_index = i * words_per_chunk
        end_word_index = min((i + 1) * words_per_chunk, len(words))
        text_chunk = " ".join(words[start_word_index:end_word_index])
        chunk_filename = f"{base_filename}_{i}.mp3"

        try:
            if status_callback: status_callback(f"Erstelle Audio für Chunk {i+1}/{num_chunks}: '{text_chunk[:30]}...'")
            tts = gTTS(text=text_chunk, lang='de')
            tts.save(chunk_filename)
            audio_chunk = AudioSegment.from_mp3(chunk_filename)
            chunk_duration = len(audio_chunk) / 1000.0

            timestamps.append({
                "text": text_chunk,
                "start": total_duration,
                "duration": chunk_duration
            })
            chunk_files.append(chunk_filename)
            combined_audio += audio_chunk
            total_duration += chunk_duration

            if status_callback: status_callback(f"Audio-Chunk {i+1} gespeichert (Dauer: {chunk_duration:.2f}s).")

        except Exception as e:
            error_msg = f"Fehler bei der Sprachsynthese für Chunk {i+1}: {e}"
            if status_callback: status_callback(error_msg)
            else: print(error_msg)
            # Cleanup partial files on error
            for f in chunk_files:
                if os.path.exists(f): os.remove(f)
            return None, 0, None, [] # Indicate failure

    try:
        if status_callback: status_callback("Kombiniere Audio-Chunks...")
        combined_audio.export(output_concatenated_audio_filename, format="mp3")
        if status_callback: status_callback(f"Kombinierte Audiodatei '{output_concatenated_audio_filename}' gespeichert (Gesamtdauer: {total_duration:.2f}s).")
    except Exception as e:
        error_msg = f"Fehler beim Kombinieren der Audio-Chunks: {e}"
        if status_callback: status_callback(error_msg)
        # Cleanup partial files on error
        for f in chunk_files:
            if os.path.exists(f): os.remove(f)
        if os.path.exists(output_concatenated_audio_filename): os.remove(output_concatenated_audio_filename)
        return None, 0, None, [] # Indicate failure
    finally:
        # Clean up individual chunk files after successful concatenation
        if status_callback: status_callback("Lösche einzelne Audio-Chunk-Dateien...")
        for f in chunk_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError as e_rem:
                     if status_callback: status_callback(f"Warnung: Konnte temporäre Chunk-Datei '{f}' nicht löschen: {e_rem}")


    return output_concatenated_audio_filename, total_duration, timestamps, chunk_files # Return chunk_files list for potential later cleanup if main process fails

# Modified generate_video_frames to remove text overlay
def generate_video_frames(video_file, output_video_only_filename, audio_duration, status_callback=None):
    if status_callback: status_callback(f"Öffne Hintergrundvideo: {video_file}")
    cap = cv2.VideoCapture(video_file)
    if not cap.isOpened():
        error_msg = f"Fehler: Konnte Videodatei nicht öffnen: {video_file}"
        if status_callback: status_callback(error_msg)
        else: print(error_msg)
        return False, None

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30
        if status_callback: status_callback(f"Warnung: Ungültiger FPS-Wert vom Video erhalten, verwende Standard {fps} FPS.")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if status_callback: status_callback(f"Video-Eigenschaften: {width}x{height} @ {fps:.2f} FPS")

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_only_filename, fourcc, fps, (width, height))

    total_frames_needed = int(fps * audio_duration)
    if status_callback: status_callback(f"Benötigte Frames für {audio_duration:.2f}s Audio: {total_frames_needed}")

    frame_counter = 0
    last_progress_update_time = time.time()
    if status_callback: status_callback("Beginne Frame-Verarbeitung (ohne Text)...")

    while frame_counter < total_frames_needed:
        ret, frame = cap.read()
        if not ret:
            if status_callback: status_callback("Hintergrundvideo wird geloopt.")
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
            if not ret:
                error_msg = "Fehler: Konnte Frame nach dem Zurücksetzen des Videos nicht lesen."
                if status_callback: status_callback(error_msg)
                else: print(error_msg)
                break

        out.write(frame) # Write the original frame without text
        frame_counter += 1

        current_time = time.time()
        if current_time - last_progress_update_time > 0.5:
            progress = int((frame_counter / total_frames_needed) * 100)
            if status_callback: status_callback(f"Fortschritt: {progress}%")
            last_progress_update_time = current_time

    if status_callback: status_callback("Fortschritt: 100%")
    if status_callback: status_callback("Frame-Verarbeitung abgeschlossen.")
    cap.release()
    out.release()
    if status_callback: status_callback(f"Temporäre Videodatei '{output_video_only_filename}' erstellt.")
    return True, output_video_only_filename

# Modified combine_video_audio to include subtitles and background music
def combine_video_audio(video_only_file, speech_audio_file, music_file, final_output_filename, timestamps, status_callback=None):
    video_clip = None
    speech_clip = None
    music_clip = None
    final_clip = None
    text_clips = []
    try:
        if status_callback: status_callback(f"Kombiniere Video '{video_only_file}', Sprache '{speech_audio_file}', Musik '{music_file}' und Untertitel...")
        video_clip = mp.VideoFileClip(video_only_file)
        speech_clip = mp.AudioFileClip(speech_audio_file)
        music_clip = mp.AudioFileClip(music_file)

        video_duration = speech_clip.duration # Use speech duration as the target duration
        video_clip = video_clip.set_duration(video_duration) # Ensure video clip matches audio duration

        # Loop music and adjust volume
        looped_music = music_clip.fx(mp.afx.audio_loop, duration=video_duration).fx(mp.afx.volumex, 0.20)

        # Combine speech and music
        combined_audio = mp.CompositeAudioClip([speech_clip.set_duration(video_duration), looped_music])

        # Create TextClips for subtitles
        if status_callback: status_callback("Erstelle Untertitel-Clips...")
        for i, chunk in enumerate(timestamps):
            if status_callback: status_callback(f"  - Untertitel {i+1}: '{chunk['text'][:30]}...' (Start: {chunk['start']:.2f}s, Dauer: {chunk['duration']:.2f}s)")
            # Use method='label' and simplify font name, increase font size
            txt_clip = mp.TextClip(chunk['text'], fontsize=60, color='white', font='Arial', # Increased fontsize to 60
                                   method='label', stroke_color='black', stroke_width=2) # Added stroke for better visibility
            txt_clip = txt_clip.set_position(('center', 0.8), relative=True)
            txt_clip = txt_clip.set_start(chunk['start'])
            clip_end_time = chunk['start'] + chunk['duration']
            actual_duration = min(chunk['duration'], video_duration - chunk['start'])
            if actual_duration < 0: actual_duration = 0

            if clip_end_time > video_duration:
                 if status_callback: status_callback(f"Warnung: Untertitel '{chunk['text'][:20]}...' endet ({clip_end_time:.2f}s) nach Videoende ({video_duration:.2f}s). Kürze Dauer.")

            txt_clip = txt_clip.set_duration(actual_duration)
            text_clips.append(txt_clip)

        # Composite video with text clips
        if status_callback: status_callback("Kombiniere Video mit Untertiteln...")
        video_with_subtitles = mp.CompositeVideoClip([video_clip] + text_clips)

        # Set the combined audio to the video clip with subtitles
        final_clip = video_with_subtitles.set_audio(combined_audio)
        final_clip = final_clip.set_duration(video_duration)

        if status_callback: status_callback("Schreibe finale Videodatei...")
        final_clip.write_videofile(final_output_filename,
                                   codec='libx264',
                                   audio_codec='aac',
                                   temp_audiofile='temp-audio.m4a',
                                   remove_temp=True,
                                   preset='medium',
                                   fps=video_clip.fps if video_clip.fps else 24,
                                   threads=4,
                                   logger='bar' if status_callback is None else None)

        if status_callback: status_callback(f"Finale Videodatei '{final_output_filename}' erfolgreich erstellt.")
        return True
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        error_msg = f"Fehler beim Kombinieren von Video, Audio, Musik und Untertiteln: {e}\n{traceback_str}"
        if status_callback: status_callback(error_msg)
        else: print(error_msg)
        return False
    finally:
        if video_clip: video_clip.close()
        if speech_clip: speech_clip.close()
        if music_clip: music_clip.close()
        if final_clip: final_clip.close()
        for tc in text_clips:
            try:
                tc.close()
            except Exception:
                pass

# --- Restore get_pexels_video_url function ---
def get_pexels_video_url(api_key, query="Natur", per_page=15, orientation="portrait", status_callback=None):
    headers = {"Authorization": api_key}
    search_url = f"https://api.pexels.com/videos/search?query={query}&per_page={per_page}&orientation={orientation}&size=medium"
    try:
        if status_callback: status_callback(f"Suche Pexels Video für '{query}' (Orientierung: {orientation})...")
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        videos = data.get("videos", [])
        if not videos:
            if status_callback: status_callback(f"Keine Videos für '{query}' gefunden. Versuche populäre Videos.")
            popular_url = f"https://api.pexels.com/videos/popular?per_page={per_page}&orientation={orientation}&size=medium"
            response = requests.get(popular_url, headers=headers)
            response.raise_for_status()
            data = response.json()
            videos = data.get("videos", [])
            if not videos:
                error_msg = "Fehler: Konnte keine Videos von Pexels abrufen (weder Suche noch Populär)."
                if status_callback: status_callback(error_msg)
                else: print(error_msg)
                return None

        suitable_videos = []
        for video in videos:
            for vf in video.get("video_files", []):
                if vf.get("quality") == "hd" and vf.get("width") and 1000 < vf.get("width") < 1200:
                    suitable_videos.append(vf["link"])
                    break

        if suitable_videos:
            chosen_link = random.choice(suitable_videos)
            if status_callback: status_callback(f"Gefundenes HD Video: {chosen_link}")
            return chosen_link
        else:
            if status_callback: status_callback("Kein ideales HD-Format (1080p Portrait) gefunden.")
            if videos and videos[0].get("video_files"):
                fallback_link = videos[0]["video_files"][0]["link"]
                if status_callback: status_callback(f"Nehme erstes verfügbares Video: {fallback_link}")
                return fallback_link
            else:
                error_msg = "Fehler: Keine Videodateien in den gefundenen Pexels-Videos."
                if status_callback: status_callback(error_msg)
                else: print(error_msg)
                return None

    except requests.exceptions.RequestException as e:
        error_msg = f"Fehler bei der Pexels API-Anfrage: {e}"
        if status_callback: status_callback(error_msg)
        else: print(error_msg)
        return None
    except Exception as e:
        error_msg = f"Ein unerwarteter Fehler ist bei der Pexels-Suche aufgetreten: {e}"
        if status_callback: status_callback(error_msg)
        else: print(error_msg)
        return None

# --- New function to generate hashtags ---
def generate_hashtags(text, num_hashtags=7):
    """Generates relevant hashtags from the input text."""
    if not text:
        return ["#video", "#tiktok", "#neu", "#foryou", "#fyp", "#viral", "#trending"]

    # Clean text: lowercase, remove punctuation (keep German umlauts)
    text_clean = re.sub(r'[^\w\säöüÄÖÜß]', '', text.lower())
    words = text_clean.split()

    # Filter stop words and short words
    filtered_words = [word for word in words if word not in GERMAN_STOP_WORDS and len(word) > 2]

    if not filtered_words:
        # Fallback if no meaningful words are left
        return ["#video", "#tiktok", "#content", "#foryou", "#fyp", "#viral", "#erstellung"]

    # Count word frequency
    word_counts = Counter(filtered_words)
    most_common_words = [word for word, count in word_counts.most_common(num_hashtags)]

    # Create hashtags
    hashtags = [f"#{word}" for word in most_common_words]

    # Add generic hashtags if needed to reach num_hashtags
    generic_hashtags = ["#tiktok", "#video", "#fyp", "#foryou", "#viral", "#trending", "#content"]
    current_hashtags = len(hashtags)
    needed = num_hashtags - current_hashtags

    if needed > 0:
        for gen_tag in generic_hashtags:
            if len(hashtags) < num_hashtags and gen_tag not in hashtags:
                hashtags.append(gen_tag)
            if len(hashtags) == num_hashtags:
                break

    # Ensure exactly num_hashtags, trim if necessary (unlikely with the logic above, but safe)
    return hashtags[:num_hashtags]

# Modified function to use Pexels video and local music file
def create_video_with_speech_and_music(text, video_query="Natur", music_filepath=None, status_callback=None):
    pexels_api_key = os.getenv("PEXELS_API_KEY")
    if not pexels_api_key:
        error_msg = "Fehler: PEXELS_API_KEY nicht in der .env Datei gefunden."
        if status_callback: status_callback(error_msg)
        else: print(error_msg)
        messagebox.showerror("Fehler", error_msg + "\nBitte .env Datei prüfen.")
        return

    if not music_filepath or not os.path.exists(music_filepath):
        error_msg = f"Fehler: Ausgewählte Musikdatei nicht gefunden: {music_filepath}"
        if status_callback: status_callback(error_msg)
        messagebox.showerror("Fehler", error_msg)
        return

    speech_base_filename = "speech_chunk"
    background_video_filename = "background_video.mp4"
    video_only_filename = "temp_video_only.mp4"
    output_video_filename = "final_video_with_subtitles.mp4"

    files_to_delete = [background_video_filename, video_only_filename]
    generated_chunk_files = []

    concatenated_audio_file, total_audio_duration, timestamps, generated_chunk_files = generate_speech_chunks_and_timestamps(
        text, speech_base_filename, status_callback
    )

    if not concatenated_audio_file or total_audio_duration <= 0:
        error_msg = "Fehler bei der Audioerstellung oder ungültige Audiodauer."
        if status_callback: status_callback(error_msg)
        messagebox.showerror("Fehler", error_msg)
        for f in generated_chunk_files:
            if os.path.exists(f): os.remove(f)
        return

    files_to_delete.append(concatenated_audio_file)

    video_url = get_pexels_video_url(pexels_api_key, query=video_query, status_callback=status_callback)
    if not video_url:
        if os.path.exists(concatenated_audio_file): os.remove(concatenated_audio_file)
        for f in generated_chunk_files:
             if os.path.exists(f): os.remove(f)
        return

    try:
        if status_callback: status_callback(f"Lade Video von {video_url} herunter...")
        video_response = requests.get(video_url, stream=True, timeout=60)
        video_response.raise_for_status()
        with open(background_video_filename, 'wb') as f:
            for chunk in video_response.iter_content(chunk_size=8192):
                f.write(chunk)
        if status_callback: status_callback(f"Video '{background_video_filename}' heruntergeladen.")
    except requests.exceptions.RequestException as e:
        error_msg = f"Fehler beim Herunterladen des Videos: {e}"
        if status_callback: status_callback(error_msg)
        if os.path.exists(concatenated_audio_file): os.remove(concatenated_audio_file)
        for f in generated_chunk_files:
             if os.path.exists(f): os.remove(f)
        return
    except Exception as e:
        error_msg = f"Fehler beim Speichern des heruntergeladenen Videos: {e}"
        if status_callback: status_callback(error_msg)
        if os.path.exists(concatenated_audio_file): os.remove(concatenated_audio_file)
        for f in generated_chunk_files:
             if os.path.exists(f): os.remove(f)
        if os.path.exists(background_video_filename): os.remove(background_video_filename)
        return

    frames_success, generated_video_file = generate_video_frames(
        background_video_filename, video_only_filename, total_audio_duration, status_callback
    )

    final_success = False
    generated_hashtags = [] # Initialize hashtag list

    if frames_success and generated_video_file:
        final_success = combine_video_audio(
            generated_video_file,
            concatenated_audio_file,
            music_filepath,
            output_video_filename,
            timestamps,
            status_callback
        )

    if status_callback: status_callback("Lösche temporäre Dateien...")
    files_to_delete.extend(generated_chunk_files)
    unique_files_to_delete = set(files_to_delete)

    for ftd in unique_files_to_delete:
        if os.path.exists(ftd):
            try:
                os.remove(ftd)
                if status_callback: status_callback(f"Temporäre Datei '{ftd}' gelöscht.")
            except OSError as e:
                if status_callback: status_callback(f"Warnung: Konnte temporäre Datei '{ftd}' nicht löschen: {e}")

    if final_success:
        if status_callback: status_callback("Generiere Hashtags...")
        generated_hashtags = generate_hashtags(text)
        hashtags_str = " ".join(generated_hashtags)
        if status_callback: status_callback(f"Vorgeschlagene Hashtags: {hashtags_str}")

        final_msg = f"Das Video '{output_video_filename}' wurde erfolgreich erstellt!\n\nVorgeschlagene Hashtags:\n{hashtags_str}"
        if status_callback: status_callback("Videoerstellung erfolgreich abgeschlossen.")
        messagebox.showinfo("Fertig", final_msg)
    else:
        error_msg = "Videoerstellung fehlgeschlagen. Überprüfe die Statusmeldungen für Details."
        if status_callback: status_callback(error_msg)
        messagebox.showerror("Fehler", error_msg)

# Pass video query widget and music file path entry
def start_video_creation_thread(text_widget, video_query_widget, music_path_entry, status_widget, button_widget):
    text = text_widget.get("1.0", tk.END).strip()
    video_query = video_query_widget.get().strip()
    music_filepath = music_path_entry.get().strip()

    if not text:
        messagebox.showwarning("Eingabe fehlt", "Bitte gib einen Text für das Video ein.")
        return

    if not video_query:
        video_query = "Natur"

    if not music_filepath:
        messagebox.showwarning("Eingabe fehlt", "Bitte wähle eine Musikdatei als Hintergrund aus.")
        return
    if not os.path.exists(music_filepath):
         messagebox.showwarning("Datei nicht gefunden", f"Die ausgewählte Musikdatei wurde nicht gefunden:\n{music_filepath}")
         return

    button_widget.config(state=tk.DISABLED)
    status_widget.config(state=tk.NORMAL)
    status_widget.delete("1.0", tk.END)
    status_widget.config(state=tk.DISABLED)

    def status_updater(message):
        status_widget.after(0, update_status_safe, status_widget, message)

    thread = threading.Thread(target=run_creation_logic, args=(text, video_query, music_filepath, status_updater, button_widget), daemon=True)
    thread.start()

# Accept video_query and music_filepath
def run_creation_logic(text, video_query, music_filepath, status_updater, button_widget):
    try:
        status_updater("Starte Videoerstellung...")
        create_video_with_speech_and_music(text, video_query, music_filepath, status_updater)
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        error_msg = f"Unerwarteter Fehler im Hauptprozess: {e}\n{traceback_str}"
        status_updater(error_msg)
        messagebox.showerror("Schwerwiegender Fehler", f"Ein unerwarteter Fehler ist aufgetreten: {e}")
    finally:
        button_widget.after(0, lambda: button_widget.config(state=tk.NORMAL))
        status_updater("Prozess beendet.")

# Function to handle music file browsing
def browse_music_file(entry_widget):
    filepath = filedialog.askopenfilename(
        title="Wähle Hintergrundmusik",
        filetypes=(("Audio files", "*.mp3 *.wav *.aac *.m4a"), ("All files", "*.*"))
    )
    if filepath:
        entry_widget.config(state=tk.NORMAL)
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, filepath)
        entry_widget.config(state=tk.DISABLED)

def create_gui():
    root = tk.Tk()
    root.title("TikTok Video Creator")

    main_frame = ttk.Frame(root, padding="10")
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    ttk.Label(main_frame, text="Text für das Video:").grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
    text_input = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, width=60, height=10, font=("Arial", 10))
    text_input.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

    ttk.Label(main_frame, text="Stichwort für Hintergrundvideo (Pexels):").grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
    video_query_input = ttk.Entry(main_frame, width=60, font=("Arial", 10))
    video_query_input.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
    video_query_input.insert(0, "Natur")

    ttk.Label(main_frame, text="Hintergrundmusik:").grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
    music_path_entry = ttk.Entry(main_frame, width=50, font=("Arial", 10), state=tk.DISABLED)
    music_path_entry.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
    browse_music_button = ttk.Button(main_frame, text="Durchsuchen...", command=lambda: browse_music_file(music_path_entry))
    browse_music_button.grid(row=5, column=2, sticky=tk.W, padx=(5, 0), pady=(0, 10))

    start_button = ttk.Button(main_frame, text="Video erstellen")
    start_button.grid(row=6, column=0, columnspan=3, sticky=tk.E, padx=(0, 0), pady=(10, 10))

    ttk.Label(main_frame, text="Status:").grid(row=7, column=0, columnspan=3, sticky=tk.W, pady=(5, 5))
    status_output = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, width=60, height=15, state=tk.DISABLED, font=("Consolas", 9))
    status_output.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
    main_frame.rowconfigure(8, weight=1)

    main_frame.columnconfigure(0, weight=1)
    main_frame.columnconfigure(1, weight=1)
    main_frame.columnconfigure(2, weight=0)

    start_button.config(command=lambda: start_video_creation_thread(text_input, video_query_input, music_path_entry, status_output, start_button))

    for child in main_frame.winfo_children():
        child.grid_configure(padx=5, pady=5)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
