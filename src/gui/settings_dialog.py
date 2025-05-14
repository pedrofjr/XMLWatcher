import tkinter as tk
from tkinter import ttk
import json
import os

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("Configurações")
        self.geometry("300x200")
        self.resizable(False, False)
        
        # Torna a janela modal
        self.transient(parent)
        self.grab_set()
        
        self.config_file = os.path.join(os.path.dirname(__file__), "config.json")
        self.settings = self.load_settings()
        
        self.setup_gui()
        
    def setup_gui(self):
        # Frame principal
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Som
        self.sound_enabled = tk.BooleanVar(value=self.settings.get('sound_enabled', True))
        sound_check = ttk.Checkbutton(
            main_frame,
            text="Emitir som ao detectar alterações",
            variable=self.sound_enabled
        )
        sound_check.pack(anchor='w', pady=5)
        
        # Botões
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(side='bottom', fill='x', pady=10)
        
        save_btn = ttk.Button(
            btn_frame,
            text="Salvar",
            command=self.save_settings
        )
        save_btn.pack(side='right', padx=5)
        
        cancel_btn = ttk.Button(
            btn_frame,
            text="Cancelar",
            command=self.destroy
        )
        cancel_btn.pack(side='right', padx=5)
        
    def load_settings(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {'sound_enabled': True}
        
    def save_settings(self):
        settings = {
            'sound_enabled': self.sound_enabled.get()
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(settings, f)
        except Exception:
            pass
            
        self.destroy()
