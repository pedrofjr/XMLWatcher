from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import time
import os
from typing import Callable
from utils.xml_parser import XMLParser
from threading import Timer

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
        self._timer = None
        self._last_content = None

    def _read_file_with_retry(self, max_retries=3, delay=0.1):
        """
        Tenta ler o arquivo com diferentes codificações e com retry
        
        Args:
            max_retries (int): Número máximo de tentativas
            delay (float): Tempo de espera entre tentativas em segundos
            
        Returns:
            str: Conteúdo do arquivo
        """
        encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
        
        for attempt in range(max_retries):
            time.sleep(delay)  # Espera um pouco antes de tentar ler
            
            for encoding in encodings:
                try:
                    with open(self.file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    print(f"Erro ao ler arquivo com encoding {encoding}: {e}")
                    continue
            
            print(f"Tentativa {attempt + 1} de {max_retries} falhou")
        
        raise Exception("Não foi possível ler o arquivo com nenhuma codificação")

    def _process_modification(self):
        """Processa a modificação do arquivo após o debounce"""
        try:
            # Tenta ler o arquivo com retry e diferentes codificações
            current_content = self._read_file_with_retry()
            
            # Se o conteúdo mudou desde a última verificação
            if current_content != self._last_content:
                xml_data = self.parser.parse_file(self.file_path)
                self.callback(xml_data)
                self._last_content = current_content
        except Exception as e:
            print(f"Erro ao processar arquivo modificado: {e}")

    def on_modified(self, event):
        """Chamado quando o arquivo é modificado"""
        if not event.is_directory and os.path.abspath(event.src_path) == self.file_path:
            with self.lock:
                # Cancela o timer anterior se existir
                if self._timer is not None:
                    self._timer.cancel()
                
                # Cria um novo timer
                self._timer = Timer(self.debounce_seconds, self._process_modification)
                self._timer.start()

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