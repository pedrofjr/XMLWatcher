from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import time
import os
from typing import Callable
from utils.xml_parser import XMLParser

class XMLFileHandler(FileSystemEventHandler):
    def __init__(self, file_path: str, callback: Callable, parser: XMLParser, debounce_seconds: float = 0.5):
        """
        Inicializa o handler de eventos do arquivo
        
        Args:
            file_path (str): Caminho do arquivo a ser monitorado
            callback (Callable): Função a ser chamada quando houver alterações
            parser (XMLParser): Parser XML para processar o arquivo
            debounce_seconds (float): Tempo mínimo entre notificações
        """
        self.file_path = os.path.abspath(file_path)
        self.callback = callback
        self.parser = parser
        self.debounce_seconds = debounce_seconds
        self.last_modified = 0
        self.lock = threading.Lock()

    def on_modified(self, event):
        """Chamado quando o arquivo é modificado"""
        if not event.is_directory and os.path.abspath(event.src_path) == self.file_path:
            current_time = time.time()
            
            with self.lock:
                # Verifica se passou tempo suficiente desde a última modificação
                if (current_time - self.last_modified) > self.debounce_seconds:
                    try:
                        xml_data = self.parser.parse_file(self.file_path)
                        self.callback(xml_data)
                        self.last_modified = current_time
                    except Exception as e:
                        print(f"Erro ao processar arquivo modificado: {e}")

class XMLFileMonitor:
    def __init__(self):
        """Inicializa o monitor de arquivos XML"""
        self.observer = None
        self.handler = None
        self.parser = XMLParser()
        self._is_monitoring = False
        self._current_file = None

    def start_monitoring(self, file_path: str, callback: Callable) -> None:
        """
        Inicia o monitoramento de um arquivo XML
        
        Args:
            file_path (str): Caminho do arquivo a ser monitorado
            callback (Callable): Função a ser chamada quando houver alterações
        """
        if self._is_monitoring:
            self.stop_monitoring()

        self._current_file = os.path.abspath(file_path)
        self.handler = XMLFileHandler(
            file_path=self._current_file,
            callback=callback,
            parser=self.parser
        )
        
        self.observer = Observer()
        self.observer.schedule(
            self.handler,
            path=os.path.dirname(self._current_file),
            recursive=False
        )
        
        self.observer.start()
        self._is_monitoring = True

    def stop_monitoring(self) -> None:
        """Para o monitoramento do arquivo"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self._is_monitoring = False
            self._current_file = None

    def is_monitoring(self) -> bool:
        """Retorna True se está monitorando um arquivo"""
        return self._is_monitoring

    @property
    def current_file(self) -> str:
        """Retorna o caminho do arquivo atual sendo monitorado"""
        return self._current_file