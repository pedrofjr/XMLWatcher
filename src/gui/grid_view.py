import tkinter as tk
from tkinter import ttk, filedialog
from tkinter.scrolledtext import ScrolledText
from datetime import datetime
from typing import List, Dict, Any, Optional
import os
import json
import winsound
from .settings_dialog import SettingsDialog

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
        self.config_file = os.path.join(os.path.dirname(__file__), "config.json")
        self.setup_gui()
        
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
        
        # Área de log
        self.log_frame = ttk.LabelFrame(self, text="Log de Alterações")
        self.log_frame.pack(fill='x', padx=5, pady=5)
        
        self.log_area = ScrolledText(
            self.log_frame,
            height=5,
            wrap=tk.WORD
        )
        self.log_area.pack(fill='x', padx=5, pady=5)
        
        # Configura o estilo para itens alterados
        self.tree.tag_configure('changed', background='lightgreen')
    
    def show_settings(self) -> None:
        """Mostra a janela de configurações"""
        SettingsDialog(self)

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
                self.tree.see(last_modified_item)  # Rola para mostrar o item
                
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

    def _should_play_sound(self) -> bool:
        """Verifica se o som deve ser reproduzido"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    settings = json.load(f)
                    return settings.get('sound_enabled', True)
        except Exception:
            pass
        return True
    
    def on_file_changed(self, xml_data: List[Dict[str, Any]]) -> None:
        """
        Callback chamado quando o arquivo é modificado
        
        Args:
            xml_data (List[Dict]): Novos dados XML
        """
        try:
            data, changes = self.xml_parser.parse_file_and_get_changes(self.xml_monitor.current_file)
            self.update_grid(data)
            
            if changes:
                for change in changes:
                    try:
                        message = self.xml_parser.format_change_message(change)
                        self.log_message(message)
                    except Exception as e:
                        self.log_message(f"Erro ao formatar mensagem de alteração: {str(e)}")
                        self.log_message(f"Dados da alteração: {change}")
        except Exception as e:
            self.log_message(f"Erro ao processar alterações: {str(e)}")
            if hasattr(e, '__traceback__'):
                import traceback
                self.log_message(f"Detalhes: {traceback.format_exc()}")
    
    def log_message(self, message: str) -> None:
        """
        Adiciona mensagem ao log com timestamp
        
        Args:
            message (str): Mensagem a ser registrada
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.insert('end', f"[{timestamp}] {message}\n")
        self.log_area.see('end')