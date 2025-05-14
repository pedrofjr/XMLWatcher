#!/usr/bin/env python3
"""
XMLWatcher - Aplicação para monitorar alterações em arquivos XML em tempo real
"""

import tkinter as tk
from gui.grid_view import XMLGridView
from watcher.xml_monitor import XMLFileMonitor
from utils.xml_parser import XMLParser

def main():
    """Função principal que inicia a aplicação XMLWatcher"""
    root = tk.Tk()
    root.title("XMLWatcher")
    root.geometry("800x600")

    # Inicializa o parser XML
    xml_parser = XMLParser()
    
    # Inicializa o monitor de arquivos
    xml_monitor = XMLFileMonitor()
    
    # Cria a interface gráfica
    app = XMLGridView(root, xml_parser, xml_monitor)
    app.pack(expand=True, fill='both')
    
    root.mainloop()

if __name__ == "__main__":
    main()