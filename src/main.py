#!/usr/bin/env python3
"""
XMLWatcher - Aplicação para monitorar alterações em arquivos XML em tempo real
"""

import os
import sys
import tkinter as tk
import winsound
import threading
from queue import Queue

# Adiciona o diretório src ao PYTHONPATH
src_path = os.path.dirname(os.path.abspath(__file__))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from gui.grid_view import XMLGridView
from watcher.xml_monitor import XMLFileMonitor
from utils.xml_parser import XMLParser
from utils.resource_manager import ConfigManager, AsyncLogger

class Application:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("XMLWatcher")
        self.root.geometry("800x600")
        
        # Define o ícone da janela
        try:
            if getattr(sys, 'frozen', False):
                # Se estiver rodando como executável
                base_path = sys._MEIPASS
            else:
                # Se estiver rodando como script
                base_path = os.path.dirname(__file__)
            
            icon_path = os.path.join(base_path, 'resources', 'icone.ico')
            if os.path.exists(icon_path):
                # Define o ícone tanto para a janela quanto para a classe da aplicação
                self.root.iconbitmap(default=icon_path)
                self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Erro ao carregar ícone: {e}")
        
        # Inicializa gerenciadores
        self.config_manager = ConfigManager(
            os.path.join(os.path.dirname(__file__), "gui", "settings.ini")
        )
        
        self.logger = AsyncLogger()
        self.logger.add_handler(self._log_handler)
        
        # Inicializa o sistema de áudio com um beep imperceptível
        winsound.Beep(1000, 1)
        
        # Inicializa componentes principais
        self.xml_parser = XMLParser()
        self.xml_monitor = XMLFileMonitor()
        
        # Cria a interface gráfica
        self.app = XMLGridView(self.root, self.xml_parser, self.xml_monitor)
        self.app.pack(expand=True, fill='both')
        
        # Configura finalização limpa
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _log_handler(self, log_entry):
        """Handler para processar logs assíncronos"""
        if hasattr(self.app, 'log_message'):
            self.app.log_message(
                log_entry['message'],
                {'timestamp': log_entry.get('timestamp')}
            )
    
    def _on_closing(self):
        """Limpa recursos ao fechar a aplicação"""
        if self.xml_monitor:
            self.xml_monitor.stop_monitoring()
        if hasattr(self.logger, 'shutdown'):
            self.logger.shutdown()
        self.root.destroy()
    
    def run(self):
        """Inicia a aplicação"""
        self.root.mainloop()

def main():
    """Função principal que inicia a aplicação XMLWatcher"""
    app = Application()
    app.run()

if __name__ == "__main__":
    main()