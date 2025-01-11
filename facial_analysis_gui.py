import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import os
import asyncio
from hume import AsyncHumeClient
from hume.expression_measurement.stream import Config
from hume.expression_measurement.stream.socket_client import StreamConnectOptions
from hume.expression_measurement.stream.types import StreamFace
from translations import EMOTIONS_DE
from dotenv import load_dotenv

# Debug: Direktes Lesen der .env Datei
env_path = os.path.join(os.getcwd(), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        env_content = f.read()
        
        # Extrahiere die Keys
        import re
        api_key_match = re.search(r'HUME_API_KEY=(.+)', env_content)
        secret_key_match = re.search(r'HUME_SECRET_KEY=(.+)', env_content)
        
        if not api_key_match or not secret_key_match:
            raise ValueError("API Key oder Secret Key konnte nicht aus .env extrahiert werden")
            
        HUME_API_KEY = api_key_match.group(1).strip()
        HUME_SECRET_KEY = secret_key_match.group(1).strip()
else:
    raise FileNotFoundError(".env Datei wurde nicht gefunden")

# Lade .env mit absolutem Pfad
load_dotenv(env_path)

# Überprüfe beide Keys
if HUME_API_KEY is None or HUME_SECRET_KEY is None:
    raise ValueError(
        "Error: HUME_API_KEY und HUME_SECRET_KEY müssen in der .env Datei gesetzt sein."
    )

print(f"API Key geladen: {HUME_API_KEY[:10]}...")
print(f"Secret Key geladen: {HUME_SECRET_KEY[:10]}...")

class EmotionAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Emotions Analysator")
        
        # Hauptframe
        self.main_frame = tk.Frame(root, padx=10, pady=10)
        self.main_frame.pack(expand=True, fill='both')
        
        # Button zum Bildauswählen
        self.select_button = tk.Button(self.main_frame, text="Bild auswählen", command=self.select_image)
        self.select_button.pack(pady=5)
        
        # Bildvorschau
        self.image_label = tk.Label(self.main_frame)
        self.image_label.pack(pady=10)
        
        # Analyse Button
        self.analyze_button = tk.Button(self.main_frame, text="Analysieren", command=self.analyze_image)
        self.analyze_button.pack(pady=5)
        
        # Ergebnisfeld
        self.result_text = tk.Text(self.main_frame, height=10, width=40)
        self.result_text.pack(pady=5)
        
        self.image_path = None
        
    def select_image(self):
        self.image_path = filedialog.askopenfilename(
            filetypes=[("Bilder", "*.jpg *.jpeg *.png *.JPG")]
        )
        if self.image_path:
            # Zeige Bildvorschau
            image = Image.open(self.image_path)
            image = image.resize((200, 200))  # Größe anpassen
            photo = ImageTk.PhotoImage(image)
            self.image_label.configure(image=photo)
            self.image_label.image = photo
    
    def analyze_image(self):
        if not self.image_path:
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "Bitte wähle zuerst ein Bild aus!")
            return
            
        # Starte Analyse in separatem Thread
        asyncio.run(self.run_analysis())
    
    async def run_analysis(self):
        client = AsyncHumeClient(api_key=HUME_API_KEY)
        model_config = Config(face=StreamFace())
        stream_options = StreamConnectOptions(config=model_config)
        
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "Analysiere...\n")
        
        async with client.expression_measurement.stream.connect(options=stream_options) as socket:
            result = await socket.send_file(self.image_path)
            
            face_predictions = result.face.predictions
            if face_predictions:
                for prediction in face_predictions:
                    emotions = [
                        {'name': emotion.name, 'score': emotion.score}
                        for emotion in prediction.emotions
                    ]
                    sorted_emotions = sorted(emotions, key=lambda x: x['score'], reverse=True)
                    
                    self.result_text.delete(1.0, tk.END)
                    self.result_text.insert(tk.END, "Gefundene Emotionen:\n")
                    self.result_text.insert(tk.END, "-" * 30 + "\n")
                    
                    for emotion in sorted_emotions[:5]:
                        score_percent = round(emotion['score'] * 100, 2)
                        emotion_name_de = EMOTIONS_DE.get(emotion['name'], emotion['name'])
                        self.result_text.insert(tk.END, f"{emotion_name_de}: {score_percent}%\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = EmotionAnalyzerGUI(root)
    root.mainloop() 