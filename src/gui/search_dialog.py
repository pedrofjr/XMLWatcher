import tkinter as tk
from tkinter import ttk
from typing import Callable

class SearchDialog(tk.Toplevel):
    def __init__(self, parent: tk.Widget, search_callback: Callable[[str, str], None]):
        """
        Inicializa o diálogo de busca
        
        Args:
            parent (tk.Widget): Widget pai
            search_callback (Callable): Função a ser chamada com o texto e direção da busca
        """
        super().__init__(parent)
        self.search_callback = search_callback
        self.title("Buscar Tag")
        self.transient(parent)
        
        # Centraliza o diálogo
        self.geometry("280x90")
        self.resizable(False, False)
        
        # Frame principal
        main_frame = ttk.Frame(self, padding="8")
        main_frame.pack(fill='both', expand=True)
        
        # Label e entrada
        ttk.Label(main_frame, text="Nome da Tag:").pack(anchor='w')
        self.search_entry = ttk.Entry(main_frame, width=35)
        self.search_entry.pack(fill='x', pady=(0, 8))
        self.search_entry.focus_set()
        
        # Frame para os botões com padding mínimo
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x')
        
        # Configura o grid para centralizar os botões
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        
        # Botão anterior
        self.prev_btn = ttk.Button(
            btn_frame,
            text="Anterior (Shift+Enter)",
            width=20,
            command=lambda: self.search('up')
        )
        self.prev_btn.grid(row=0, column=0, padx=1)
        
        # Botão próximo
        self.next_btn = ttk.Button(
            btn_frame,
            text="Próxima (Enter)",
            width=20,
            command=lambda: self.search('down')
        )
        self.next_btn.grid(row=0, column=1, padx=1)
        
        # Bindings
        self.bind('<Return>', lambda e: self.search('down'))
        self.bind('<Shift-Return>', lambda e: self.search('up'))
        self.bind('<Escape>', lambda e: self.destroy())
        
        # Centraliza na tela
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        # Evento ao fechar a janela
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def search(self, direction: str) -> None:
        """
        Executa a busca com o texto inserido
        
        Args:
            direction (str): Direção da busca ('up' ou 'down')
        """
        search_text = self.search_entry.get().strip()
        if search_text:
            self.search_callback(search_text, direction)
    
    def on_close(self) -> None:
        """Chamado quando a janela é fechada"""
        self.search_callback("", "clear")  # Sinaliza para limpar as marcações
        self.destroy() 