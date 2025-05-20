import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import configparser
import winsound
import threading

DEFAULT_SETTINGS = {
    'Sound': {
        'enabled': 'true',
        'custom_sound': '',
        'use_custom_sound': 'false',
        'frequency': '1000',
        'duration': '100'
    }
}

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        self.title("Configurações")
        self.geometry("400x300")
        self.resizable(False, False)
        
        # Inicializa o ConfigParser
        self.config = configparser.ConfigParser()
        self.settings_file = os.path.join(os.path.dirname(__file__), "settings.ini")
        
        # Carrega as configurações
        self.load_settings()
        
        # Cria a interface
        self.create_widgets()
        
        # Configura o que acontece quando a janela é fechada
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Centraliza a janela sobre a janela principal
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.winfo_screenheight() // 2) - (300 // 2)
        self.geometry(f'400x300+{x}+{y}')
        
        # Foca na janela
        self.focus_force()
        
        # Torna a janela modal e garante que fique à frente
        self.transient(parent)
        self.grab_set()
    
    def on_close(self):
        """Método chamado quando a janela é fechada"""
        self.grab_release()  # Libera o foco
        self.destroy()  # Destroi a janela
    
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Som
        sound_frame = ttk.LabelFrame(main_frame, text="Configurações de Som", padding="5")
        sound_frame.pack(fill='x', padx=5, pady=5)
        
        # Ativar/Desativar som
        self.sound_enabled = tk.BooleanVar(value=self.config.getboolean('Sound', 'enabled'))
        ttk.Checkbutton(
            sound_frame,
            text="Ativar som ao detectar alterações",
            variable=self.sound_enabled,
            command=self.save_settings
        ).pack(fill='x')
        
        # Som personalizado
        self.use_custom_sound = tk.BooleanVar(value=self.config.getboolean('Sound', 'use_custom_sound'))
        ttk.Checkbutton(
            sound_frame,
            text="Usar som personalizado",
            variable=self.use_custom_sound,
            command=self.toggle_custom_sound
        ).pack(fill='x')
        
        # Frame para arquivo de som
        sound_file_frame = ttk.Frame(sound_frame)
        sound_file_frame.pack(fill='x', pady=5)
        
        self.sound_file_entry = ttk.Entry(sound_file_frame)
        self.sound_file_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.sound_file_entry.insert(0, self.config.get('Sound', 'custom_sound'))
        
        # Armazena a referência do botão para poder alterar seu estado depois
        self.browse_btn = ttk.Button(
            sound_file_frame,
            text="Procurar",
            command=self.browse_sound_file
        )
        self.browse_btn.pack(side='left')
        
        # Frame para botões de som
        sound_buttons_frame = ttk.Frame(sound_frame)
        sound_buttons_frame.pack(fill='x', pady=5)
        
        # Armazena a referência do botão de teste para poder atualizar seu estado
        self.test_button = ttk.Button(
            sound_buttons_frame,
            text="Testar Som",
            command=self.test_sound
        )
        self.test_button.pack(side='left', padx=5)
        
        ttk.Button(
            sound_buttons_frame,
            text="Restaurar Som Padrão",
            command=self.restore_default_sound
        ).pack(side='left')
        
        # Frame para configurações de som padrão
        default_sound_frame = ttk.Frame(sound_frame)
        default_sound_frame.pack(fill='x', pady=5)
        
        # Frequência
        ttk.Label(default_sound_frame, text="Frequência (Hz):").pack(side='left', padx=5)
        self.frequency_var = tk.StringVar(value=str(self.config.getint('Sound', 'frequency')))
        self.frequency_entry = ttk.Entry(default_sound_frame, textvariable=self.frequency_var, width=8)
        self.frequency_entry.pack(side='left')
        self.frequency_entry.bind('<FocusOut>', lambda e: self.save_settings())
        
        # Duração
        ttk.Label(default_sound_frame, text="Duração (ms):").pack(side='left', padx=(10, 5))
        self.duration_var = tk.StringVar(value=str(self.config.getint('Sound', 'duration')))
        self.duration_entry = ttk.Entry(default_sound_frame, textvariable=self.duration_var, width=6)
        self.duration_entry.pack(side='left')
        self.duration_entry.bind('<FocusOut>', lambda e: self.save_settings())
        
        # Atualiza o estado inicial dos widgets
        self.toggle_custom_sound()
        
    def toggle_custom_sound(self):
        custom_sound = self.use_custom_sound.get()
        sound_state = 'normal' if custom_sound else 'disabled'
        default_state = 'disabled' if custom_sound else 'normal'
        
        # Atualiza estado dos widgets
        self.sound_file_entry.configure(state=sound_state)
        self.browse_btn.configure(state=sound_state)  # Desabilita o botão procurar também
        self.frequency_entry.configure(state=default_state)
        self.duration_entry.configure(state=default_state)
        
        self.save_settings()
    
    def browse_sound_file(self):
        # Só permite abrir o diálogo se o som personalizado estiver ativado
        if self.use_custom_sound.get():
            filename = filedialog.askopenfilename(
                title="Selecionar arquivo de som",
                filetypes=[("Arquivos WAV", "*.wav"), ("Todos os arquivos", "*.*")]
            )
            if filename:
                self.sound_file_entry.delete(0, tk.END)
                self.sound_file_entry.insert(0, filename)
                self.save_settings()
    
    def _play_sound_thread(self, sound_file=None, frequency=None, duration=None):
        """Função executada em uma thread separada para tocar o som"""
        try:
            if sound_file:
                # Usa SND_ASYNC para tocar o som em segundo plano sem bloquear
                winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
            elif frequency and duration:
                # Limita a duração do beep para resposta mais rápida
                winsound.Beep(frequency, min(duration, 1000))
        except Exception as e:
            # Se ocorrer algum erro, mostra uma mensagem na thread principal
            self.after(0, lambda: messagebox.showerror("Erro", f"Erro ao reproduzir som: {str(e)}"))
    
    def test_sound(self):
        if not self.sound_enabled.get():
            return
        
        # Desabilita o botão temporariamente para evitar múltiplos cliques
        test_button = self.test_button
        original_text = test_button['text']
        test_button.config(text="Tocando...", state='disabled')
        
        def reenable_button():
            # Reabilita o botão após um pequeno delay
            test_button.config(text=original_text, state='normal')
        
        if self.use_custom_sound.get():
            sound_file = self.sound_file_entry.get()
            if sound_file and os.path.exists(sound_file):
                # Inicia uma nova thread para tocar o som
                thread = threading.Thread(
                    target=self._play_sound_thread,
                    args=(sound_file,),
                    daemon=True
                )
                thread.start()
                # Agenda a reativação do botão após 100ms
                self.after(100, reenable_button)
            else:
                reenable_button()
        else:
            # Para o beep, usamos uma thread para não travar a interface
            thread = threading.Thread(
                target=self._play_sound_thread,
                args=(None, self.config.getint('Sound', 'frequency'), 
                      self.config.getint('Sound', 'duration')),
                daemon=True
            )
            thread.start()
            # Como o beep é rápido, podemos reativar o botão imediatamente
            reenable_button()
    
    def restore_default_sound(self):
        """Restaura as configurações de som para os valores padrão"""
        # Obtém os valores padrão da constante DEFAULT_SETTINGS
        default_sound = DEFAULT_SETTINGS['Sound']
        
        # Atualiza a interface com os valores padrão
        self.sound_enabled.set(default_sound['enabled'].lower() == 'true')
        self.use_custom_sound.set(default_sound['use_custom_sound'].lower() == 'true')
        
        # Limpa e define o caminho do arquivo de som personalizado
        self.sound_file_entry.config(state='normal')
        self.sound_file_entry.delete(0, tk.END)
        self.sound_file_entry.insert(0, default_sound['custom_sound'])
        
        # Define os valores padrão de frequência e duração
        self.frequency_var.set(default_sound['frequency'])
        self.duration_var.set(default_sound['duration'])
        
        # Atualiza o estado dos widgets
        self.toggle_custom_sound()
        
        # Salva as configurações
        self.save_settings()
        
    def load_settings(self):
        """Carrega as configurações, criando o arquivo se necessário"""
        # Inicializa com valores padrão
        for section, options in DEFAULT_SETTINGS.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
            for option, value in options.items():
                if not self.config.has_option(section, option):
                    self.config.set(section, option, value)
        
        # Tenta carregar arquivo existente
        if os.path.exists(self.settings_file):
            self.config.read(self.settings_file)
    
    def save_settings(self):
        """Salva as configurações atuais no arquivo e atualiza o cache"""
        # Garante que a seção Sound existe
        if not self.config.has_section('Sound'):
            self.config.add_section('Sound')
        
        # Atualiza valores no config
        self.config.set('Sound', 'enabled', str(self.sound_enabled.get()).lower())
        self.config.set('Sound', 'use_custom_sound', str(self.use_custom_sound.get()).lower())
        self.config.set('Sound', 'custom_sound', self.sound_file_entry.get())
        
        # Atualiza frequência e duração
        try:
            frequency = int(self.frequency_var.get())
            self.config.set('Sound', 'frequency', str(frequency))
        except ValueError:
            self.config.set('Sound', 'frequency', DEFAULT_SETTINGS['Sound']['frequency'])
            self.frequency_var.set(DEFAULT_SETTINGS['Sound']['frequency'])
            
        try:
            duration = int(self.duration_var.get())
            self.config.set('Sound', 'duration', str(duration))
        except ValueError:
            self.config.set('Sound', 'duration', DEFAULT_SETTINGS['Sound']['duration'])
            self.duration_var.set(DEFAULT_SETTINGS['Sound']['duration'])
        
        # Salva no arquivo
        with open(self.settings_file, 'w') as configfile:
            self.config.write(configfile)
        
        # Atualiza o cache no GridView
        if hasattr(self.parent, 'load_sound_config'):
            self.parent.load_sound_config()
