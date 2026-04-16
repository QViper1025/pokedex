import tkinter as tk
from tkinter import messagebox, ttk
import requests
from PIL import Image, ImageTk
from io import BytesIO
import pygame
import os
import atexit
import tempfile
import threading

class PokemonCodex:
    def __init__(self, root):
        self.root = root
        self.root.title("Pokémon Codex")
        self.root.geometry("450x750")
        self.root.configure(bg="#f0f0f0")

        # Initialize audio and cleanup variables
        pygame.mixer.init()
        self.temp_audio_path = os.path.join(tempfile.gettempdir(), "pokedex_cry.ogg")
        self.current_cry_url = None
        atexit.register(self.cleanup)

        # Main Navigation and Container
        self.top_nav = tk.Frame(self.root, bg="#cc0000", pady=5)
        self.top_nav.pack(fill=tk.X)

        self.main_container = tk.Frame(self.root, bg="#f0f0f0")
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self.create_nav()
        self.show_detail_view() 

    def create_nav(self):
        btn_style = {"bg": "#ffffff", "font": ("Helvetica", 10, "bold"), "padx": 10}
        
        detail_btn = tk.Button(self.top_nav, text="Search View", command=self.show_detail_view, **btn_style)
        detail_btn.pack(side=tk.LEFT, padx=10)

        library_btn = tk.Button(self.top_nav, text="Pokedex Library", command=self.show_library_view, **btn_style)
        library_btn.pack(side=tk.LEFT, padx=5)

    def clear_container(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    # --- DETAIL VIEW ---
    def show_detail_view(self, name_to_fetch=None):
        self.clear_container()
        
        search_frame = tk.Frame(self.main_container, bg="#f0f0f0")
        search_frame.pack(pady=15)

        self.entry = tk.Entry(search_frame, font=("Helvetica", 14), width=15)
        self.entry.pack(side=tk.LEFT, padx=10)
        self.entry.bind('<Return>', lambda e: self.fetch_data())

        search_btn = tk.Button(search_frame, text="Search", command=self.fetch_data, bg="#ff0000", fg="white")
        search_btn.pack(side=tk.LEFT)

        self.img_label = tk.Label(self.main_container, bg="#f0f0f0")
        self.img_label.pack()

        self.cry_btn = tk.Button(self.main_container, text="🔊 Play Cry", command=self.play_cry, 
                                 state=tk.DISABLED, bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold"))
        self.cry_btn.pack(pady=5)

        self.name_label = tk.Label(self.main_container, text="Search a Pokémon!", font=("Helvetica", 18, "bold"), bg="#f0f0f0")
        self.name_label.pack()

        self.type_label = tk.Label(self.main_container, text="", font=("Helvetica", 12), bg="#f0f0f0", fg="#555555")
        self.type_label.pack()

        self.desc_label = tk.Label(self.main_container, text="", font=("Helvetica", 10, "italic"), 
                                   bg="#f0f0f0", wraplength=380, justify=tk.CENTER)
        self.desc_label.pack(pady=10)

        self.stats_label = tk.Label(self.main_container, text="", font=("Helvetica", 11), bg="#f0f0f0")
        self.stats_label.pack()

        if name_to_fetch:
            self.entry.insert(0, name_to_fetch)
            self.fetch_data()

    # --- LIBRARY VIEW ---
    def show_library_view(self):
        self.clear_container()

        canvas = tk.Canvas(self.main_container, bg="#f0f0f0")
        scrollbar = ttk.Scrollbar(self.main_container, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, bg="#f0f0f0")

        self.scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Range 1-1025 covers all modern Pokémon
        threading.Thread(target=self.load_library_batch, args=(1, 1025), daemon=True).start()

    def load_library_batch(self, start, end):
        session = requests.Session() # Reuse connection for speed
        for i in range(start, end + 1):
            try:
                res = session.get(f"https://pokeapi.co/api/v2/pokemon/{i}", timeout=5)
                data = res.json()
                
                img_url = data['sprites']['front_default']
                if img_url:
                    img_res = session.get(img_url, timeout=5)
                    img = Image.open(BytesIO(img_res.content)).resize((70, 70))
                    photo = ImageTk.PhotoImage(img)

                    # Update UI in main thread
                    self.root.after(0, self.add_library_item, data['name'], i, photo)
            except:
                continue

    def add_library_item(self, name, p_id, photo):
        frame = tk.Frame(self.scroll_frame, bg="white", bd=1, relief="flat")
        col = (p_id - 1) % 4 
        row = (p_id - 1) // 4
        frame.grid(row=row, column=col, padx=5, pady=5)

        btn = tk.Button(frame, image=photo, command=lambda n=name: self.show_detail_view(n), 
                        borderwidth=0, bg="white", activebackground="#eeeeee")
        btn.image = photo 
        btn.pack()

        lbl = tk.Label(frame, text=f"#{p_id}\n{name.capitalize()}", font=("Helvetica", 7), bg="white")
        lbl.pack()

    # --- SHARED LOGIC ---
    def fetch_data(self):
        name = self.entry.get().lower().strip()
        if not name: return
        try:
            res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name}")
            if res.status_code == 404: return
            data = res.json()
            spec_res = requests.get(data['species']['url']).json()
            self.display_pokemon(data, spec_res)
        except: pass

    def display_pokemon(self, data, spec_data):
        self.current_cry_url = data['cries'].get('latest')
        self.cry_btn.config(state=tk.NORMAL if self.current_cry_url else tk.DISABLED)
        
        desc = "No description found."
        for e in spec_data['flavor_text_entries']:
            if e['language']['name'] == 'en':
                desc = e['flavor_text'].replace('\f', ' ').replace('\n', ' ')
                break

        self.name_label.config(text=f"#{data['id']} {data['name'].upper()}")
        self.type_label.config(text=" | ".join([t['type']['name'].upper() for t in data['types']]))
        self.desc_label.config(text=desc)
        self.stats_label.config(text=f"H: {data['height']/10}m | W: {data['weight']/10}kg")

        img_url = data['sprites']['front_default']
        if img_url:
            img_res = requests.get(img_url)
            img = Image.open(BytesIO(img_res.content)).resize((200, 200))
            photo = ImageTk.PhotoImage(img)
            self.img_label.config(image=photo)
            self.img_label.image = photo

    def play_cry(self):
        """Downloads the cry and plays it with proper file release."""
        if self.current_cry_url:
            try:
                # 1. Stop and Unload any current audio to release Windows file handle
                pygame.mixer.music.stop()
                pygame.mixer.music.unload() 
                
                # 2. Fetch and overwrite temp file
                response = requests.get(self.current_cry_url)
                with open(self.temp_audio_path, "wb") as f:
                    f.write(response.content)
                
                # 3. Load and play
                pygame.mixer.music.load(self.temp_audio_path)
                pygame.mixer.music.play()
            except Exception as e:
                print(f"Audio Error: {e}")

    def cleanup(self):
        """Failsafe to clean up temp files on exit."""
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            pygame.mixer.quit()
            if os.path.exists(self.temp_audio_path):
                os.remove(self.temp_audio_path)
        except:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = PokemonCodex(root)
    root.mainloop()