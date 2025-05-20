import tkinter as tk
from tkinter import ttk, filedialog
from tkinter.scrolledtext import ScrolledText
from datetime import datetime
from typing import List, Dict, Any, Optional
import os
import configparser
import winsound
import time
import threading
from .settings_dialog import SettingsDialog, DEFAULT_SETTINGS

class XMLGridView(tk.Frame):
    def __init__(self, master: tk.Tk, xml_parser: Any, xml_monitor: Any):
        """
        Inicializa a interface gráfica principal
        
        Args:
            master (tk.Tk): Janela principal
            xml_parser (XMLParser): Parser para processar arquivos XML
            xml_monitor (XMLFileMonitor): Monitor para detectar alterações
        """
        super().__init__(master)
        self.xml_parser = xml_parser
        self.xml_monitor = xml_monitor
        self.initial_state: Dict = {}
        
        # Cache de configurações
        self.sound_config = {
            'enabled': True,
            'frequency': 1000,
            'duration': 100,
            'use_custom_sound': False,
            'custom_sound': ''
        }
        
        # Índices para navegação entre alterações
        self._current_change_index = -1
        self._changed_items = []
        
        self.load_sound_config()
        self.setup_gui()
        self.setup_bindings()
        
    def setup_bindings(self) -> None:
        """Configura os atalhos de teclado"""
        self.master.bind('<Up>', lambda e: self.navigate_changes('up'))
        self.master.bind('<Down>', lambda e: self.navigate_changes('down'))

    def setup_gui(self) -> None:
        """Configura os elementos da interface gráfica"""
        # Frame superior para botões
        self.button_frame = ttk.Frame(self)
        self.button_frame.pack(fill='x', padx=5, pady=5)
        
        # Botão para selecionar arquivo
        self.select_btn = ttk.Button(
            self.button_frame, 
            text="Selecionar XML",
            command=self.select_file
        )
        self.select_btn.pack(side='left', padx=5)
        
        # Botão para pausar/retomar monitoramento
        self.monitor_btn = ttk.Button(
            self.button_frame,
            text="Pausar Monitoramento",
            command=self.toggle_monitoring,
            state='disabled'
        )
        self.monitor_btn.pack(side='left', padx=5)
        
        # Botão para redefinir estado
        self.reset_btn = ttk.Button(
            self.button_frame,
            text="Redefinir Estado",
            command=self.reset_state,
            state='disabled'
        )
        self.reset_btn.pack(side='left', padx=5)
        
        # Botão de configurações
        self.settings_btn = ttk.Button(
            self.button_frame,
            text="Configurações",
            command=self.show_settings
        )
        self.settings_btn.pack(side='left', padx=5)
        
        # Label para mostrar o arquivo selecionado
        self.file_label = ttk.Label(
            self.button_frame,
            text="Nenhum arquivo selecionado",
            wraplength=400
        )
        self.file_label.pack(side='left', padx=5)
        
        # Frame para o grid
        self.grid_frame = ttk.Frame(self)
        self.grid_frame.pack(expand=True, fill='both', padx=5, pady=5)
        
        # Treeview para mostrar os dados XML
        columns = ('Linha', 'Tag', 'Atributos', 'Valor Original', 'Valor Atual', 'xpath')
        self.tree = ttk.Treeview(
            self.grid_frame,
            columns=columns,
            show='headings',
            selectmode='none'  # Desabilita a seleção
        )
        
        # Configura as colunas
        column_widths = {
            'Linha': 60,
            'Tag': 150,
            'Atributos': 200,
            'Valor Original': 200,
            'Valor Atual': 200,
            'xpath': 0  # Coluna oculta
        }
        
        for col, width in column_widths.items():
            self.tree.heading(col, text=col)
            # Configuração especial para a coluna xpath
            if col == 'xpath':
                self.tree.column(col, width=0, minwidth=0, stretch=False)
            else:
                self.tree.column(col, width=width, minwidth=100)
        
        # Configura scrollbars
        vsb = ttk.Scrollbar(
            self.grid_frame,
            orient="vertical",
            command=self.tree.yview
        )
        hsb = ttk.Scrollbar(
            self.grid_frame,
            orient="horizontal",
            command=self.tree.xview
        )
        self.tree.configure(
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        
        # Posiciona os elementos usando grid
        self.tree.grid(column=0, row=0, sticky='nsew')
        vsb.grid(column=1, row=0, sticky='ns')
        hsb.grid(column=0, row=1, sticky='ew')
        
        self.grid_frame.grid_columnconfigure(0, weight=1)
        self.grid_frame.grid_rowconfigure(0, weight=1)
        
        # Frame para o log e navegação
        self.log_container = ttk.Frame(self)
        self.log_container.pack(fill='x', padx=5, pady=5)
        
        # Frame para o título e botões
        self.log_header = ttk.Frame(self.log_container)
        self.log_header.pack(fill='x', pady=(0, 5))
        
        # Label para o título
        self.log_title = ttk.Label(self.log_header, text="Log de Alterações")
        self.log_title.pack(side='left')
        
        # Frame para os botões de navegação
        self.nav_frame = ttk.Frame(self.log_header)
        self.nav_frame.pack(side='right')
        
        # Botão para navegar para cima
        self.up_btn = ttk.Button(
            self.nav_frame,
            text="Anterior (↑)",
            width=12,
            command=lambda: self.navigate_changes('up'),
            state='disabled'
        )
        self.up_btn.pack(side='left', padx=2)
        
        # Botão para navegar para baixo
        self.down_btn = ttk.Button(
            self.nav_frame,
            text="Próxima (↓)",
            width=12,
            command=lambda: self.navigate_changes('down'),
            state='disabled'
        )
        self.down_btn.pack(side='left', padx=2)
        
        # Frame para a área de log com borda
        self.log_frame = ttk.Frame(self.log_container, relief='groove', borderwidth=1)
        self.log_frame.pack(fill='x')
        
        # Área de log
        self.log_area = ScrolledText(
            self.log_frame,
            height=5,
            wrap=tk.WORD,
            state='disabled'  # Torna o log somente leitura
        )
        self.log_area.pack(fill='x', padx=1, pady=1)
        
        # Configura o estilo para itens alterados
        self.tree.tag_configure('changed', background='lightgreen')
        
    def show_settings(self) -> None:
        """Mostra a janela de configurações"""
        # Cria a janela de diálogo
        dialog = SettingsDialog(self)
        
        # Configura o diálogo para bloquear a janela principal
        dialog.transient(self.master)
        dialog.grab_set()
        
        # Centraliza a janela
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'400x300+{x}+{y}')
        
        # Foca na janela de diálogo
        dialog.focus_force()
        
        # Aguarda o fechamento da janela
        self.wait_window(dialog)

    def reset_state(self) -> None:
        """Redefine o estado atual como o estado inicial"""
        if self.xml_monitor.current_file:
            try:
                # Recarrega o XML atual como estado inicial
                self.xml_parser.initial_state = None
                xml_data = self.xml_parser.parse_file(self.xml_monitor.current_file)
                self.initial_state = xml_data
                self.update_grid(xml_data)
                self.log_message("Estado redefinido com sucesso")
            except Exception as e:
                self.log_message(f"Erro ao redefinir estado: {str(e)}")
    
    def select_file(self) -> None:
        """Abre diálogo para selecionar arquivo XML"""
        filename = filedialog.askopenfilename(
            title="Selecione um arquivo XML",
            filetypes=[
                ("Arquivos XML", "*.xml"),
                ("Todos os arquivos", "*.*")
            ]
        )
        
        if filename:
            try:
                self.xml_parser.initial_state = None  # Reseta o estado inicial
                self.load_xml(filename)
                self.start_monitoring(filename)
                self.file_label.config(text=filename)
                self.monitor_btn.config(state='normal')
                self.reset_btn.config(state='normal')
            except Exception as e:
                self.log_message(f"Erro ao abrir arquivo: {str(e)}")
    
    def load_xml(self, filename: str) -> None:
        """
        Carrega o arquivo XML e atualiza o grid
        
        Args:
            filename (str): Caminho do arquivo XML
        """
        try:
            xml_data = self.xml_parser.parse_file(filename)
            self.initial_state = xml_data
            self.update_grid(xml_data)
            self.log_message(f"Arquivo carregado: {os.path.basename(filename)}")
        except Exception as e:
            raise Exception(f"Erro ao carregar arquivo: {str(e)}")
    
    def update_grid(self, xml_data: List[Dict[str, Any]]) -> None:
        """
        Atualiza o grid com os dados XML
        
        Args:
            xml_data (List[Dict]): Lista de elementos XML
        """
        try:
            # Mapeia os itens atuais por xpath
            current_items = {}
            modified_items = []
            for item in self.tree.get_children():
                try:
                    values = self.tree.item(item)['values']
                    if len(values) >= 5:  # Garante que tem todos os valores necessários
                        xpath = values[5] if len(values) > 5 else None  # xpath é a sexta coluna (invisível)
                        if xpath:
                            current_items[xpath] = item
                except Exception:
                    continue

            # Atualiza ou insere itens
            last_modified_item = None
            for element in xml_data:
                try:
                    tag = element['tag']
                    attrs = str(element.get('attributes', ''))
                    original = element.get('initial_value', element.get('value', ''))
                    current = element.get('value', '')
                    parent_number = element.get('parent_number', '')
                    xpath = element.get('xpath', '')
                    
                    values = (parent_number, tag, attrs, original, current, xpath)  # xpath como coluna oculta
                    
                    # Se o item já existe, atualiza
                    if xpath in current_items:
                        item_id = current_items[xpath]
                        self.tree.item(item_id, values=values)
                        if element.get('modified', False):
                            self.tree.item(item_id, tags=('changed',))
                            last_modified_item = item_id
                        else:
                            self.tree.item(item_id, tags=())
                        del current_items[xpath]  # Remove do dict para saber quais sobraram
                    else:
                        # Se não existe, insere novo
                        item_id = self.tree.insert('', 'end', values=values)
                        if element.get('modified', False):
                            self.tree.item(item_id, tags=('changed',))
                            last_modified_item = item_id
                    
                except Exception as e:
                    self.log_message(f"Erro ao atualizar elemento {tag}: {str(e)}")
            
            # Remove itens que não existem mais
            for item_id in current_items.values():
                try:
                    self.tree.delete(item_id)
                except Exception:
                    continue
            
            # Se houver item modificado, rola para ele
            if last_modified_item:
                self.tree.yview_moveto(0)  # Força o scroll para o topo primeiro
                self.tree.see(last_modified_item)  # Rola para mostrar o item
                
            # Atualiza estado dos botões de navegação
            has_changes = any(element.get('modified', False) for element in xml_data)
            self.up_btn.configure(state='normal' if has_changes else 'disabled')
            self.down_btn.configure(state='normal' if has_changes else 'disabled')
            
            # Reseta o índice de navegação quando o grid é atualizado
            self._current_change_index = -1
            self._changed_items = []
            
        except Exception as e:
            self.log_message(f"Erro ao atualizar grid: {str(e)}")
                
        # Ajusta a largura da coluna Linha para ser menor
        self.tree.column('Linha', width=60, minwidth=50)
    
    def start_monitoring(self, filename: str) -> None:
        """
        Inicia o monitoramento do arquivo
        
        Args:
            filename (str): Caminho do arquivo a ser monitorado
        """
        self.xml_monitor.start_monitoring(
            filename,
            callback=self.on_file_changed
        )
        self.monitor_btn.config(
            text="Pausar Monitoramento",
            state='normal'
        )
    
    def toggle_monitoring(self) -> None:
        """Alterna entre pausar e retomar o monitoramento"""
        if self.xml_monitor.is_monitoring():
            self.xml_monitor.stop_monitoring()
            self.monitor_btn.config(text="Retomar Monitoramento")
            self.log_message("Monitoramento pausado")
        else:
            filename = self.file_label.cget("text")
            if filename != "Nenhum arquivo selecionado":
                self.start_monitoring(filename)
                self.log_message("Monitoramento retomado")

    def load_sound_config(self):
        """Carrega configurações de som em cache"""
        try:
            config = configparser.ConfigParser()
            settings_file = os.path.join(os.path.dirname(__file__), "settings.ini")
            
            if os.path.exists(settings_file):
                config.read(settings_file)
                self.sound_config.update({
                    'enabled': config.getboolean('Sound', 'enabled'),
                    'frequency': config.getint('Sound', 'frequency'),
                    'duration': config.getint('Sound', 'duration'),
                    'use_custom_sound': config.getboolean('Sound', 'use_custom_sound'),
                    'custom_sound': config.get('Sound', 'custom_sound')
                })
        except Exception:
            pass  # Mantém os valores padrão em caso de erro

    def _play_sound(self) -> None:
        """Reproduz o som de notificação de forma assíncrona"""
        if not self.sound_config['enabled']:
            return

        def play_async():
            try:
                if self.sound_config['use_custom_sound'] and self.sound_config['custom_sound']:
                    if os.path.exists(self.sound_config['custom_sound']):
                        winsound.PlaySound(
                            self.sound_config['custom_sound'],
                            winsound.SND_FILENAME | winsound.SND_ASYNC
                        )
                        return
                
                # Som padrão ou fallback
                winsound.Beep(
                    self.sound_config['frequency'],
                    min(self.sound_config['duration'], 100)  # Limita a duração para resposta mais rápida
                )
            except Exception:
                winsound.Beep(1000, 50)  # Fallback ultra-rápido em caso de erro

        threading.Thread(target=play_async, daemon=True).start()

    def on_file_changed(self, xml_data: List[Dict[str, Any]], processing_info: Dict[str, Any] = None) -> None:
        """Callback chamado quando o arquivo é modificado"""
        # Toca o som imediatamente ao detectar mudança
        self._play_sound()
        
        # Processa as alterações em uma thread separada
        def process_changes():
            try:
                data, changes = self.xml_parser.parse_file_and_get_changes(self.xml_monitor.current_file)
                
                # Atualiza a interface na thread principal
                self.after(0, lambda: self.update_grid(data))
                
                if changes:
                    for change in changes:
                        try:
                            message = self.xml_parser.format_change_message(change)
                            self.after(0, lambda m=message: self.log_message(m, processing_info))
                        except Exception as e:
                            error_msg = str(e)
                            self.after(0, lambda: self.log_message(f"Erro ao formatar mensagem de alteração: {error_msg}"))
            except Exception as e:
                error_msg = str(e)
                self.after(0, lambda: self.log_message(f"Erro ao processar alterações: {error_msg}"))
        
        threading.Thread(target=process_changes, daemon=True).start()

    def log_message(self, message: str, processing_info: Dict[str, Any] = None) -> None:
        """
        Adiciona mensagem ao log com timestamp e tempo de processamento
        
        Args:
            message (str): Mensagem a ser registrada
            processing_info (Dict): Informações sobre o processamento (tempos)
        """
        current_time = time.time()
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Habilita temporariamente para inserir o texto
        self.log_area.configure(state='normal')
        
        if processing_info and 'start_time' in processing_info:
            processing_time = current_time - processing_info['start_time']
            detection_time = processing_info.get('detection_time', timestamp)
            self.log_area.insert('end', f"[{timestamp}] {message} (Detectado às {detection_time}, processado em {processing_time:.3f}s)\n")
        else:
            self.log_area.insert('end', f"[{timestamp}] {message}\n")
        
        self.log_area.see('end')
        # Desabilita novamente para manter somente leitura
        self.log_area.configure(state='disabled')
        
        # Força o foco de volta para a janela principal para permitir navegação por Tab
        self.focus_set()

    def navigate_changes(self, direction: str) -> None:
        """
        Navega entre os itens alterados
        
        Args:
            direction (str): Direção da navegação ('up' ou 'down')
        """
        # Atualiza lista de itens alterados
        self._changed_items = [
            item for item in self.tree.get_children()
            if 'changed' in self.tree.item(item)['tags']
        ]
        
        if not self._changed_items:
            return
        
        # Ajusta o índice baseado na direção
        if direction == 'up':
            self._current_change_index -= 1
            if self._current_change_index < 0:
                self._current_change_index = len(self._changed_items) - 1
        else:  # down
            self._current_change_index += 1
            if self._current_change_index >= len(self._changed_items):
                self._current_change_index = 0
        
        # Seleciona e mostra o item
        item_id = self._changed_items[self._current_change_index]
        self.tree.see(item_id)
        
        # Destaca brevemente o item
        self.flash_item(item_id)
    
    def flash_item(self, item_id: str) -> None:
        """
        Destaca visualmente um item por um breve momento
        
        Args:
            item_id (str): ID do item no Treeview
        """
        original_bg = self.tree.tag_configure('changed')['background']
        
        # Muda a cor para um tom mais forte
        self.tree.tag_configure('changed', background='#90EE90')  # Verde mais forte
        
        # Agenda o retorno à cor original
        self.after(500, lambda: self.tree.tag_configure('changed', background=original_bg))