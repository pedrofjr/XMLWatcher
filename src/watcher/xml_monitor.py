from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import time
from datetime import datetime
import os
from typing import Callable, Dict, Any, List, Optional
from queue import Queue
from utils.xml_parser import XMLParser

class XMLFileHandler(FileSystemEventHandler):
    def __init__(self, file_path: str, callback: Callable, parser: XMLParser, debounce_seconds: float = 0.1):
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
        self._last_size = 0
        self._change_count = 0
        self._last_change_time = 0
        self._last_modified = 0
        self._lock = threading.Lock()
        self._timer = None
        self._last_content = None
        self._processing = False
        self._event_buffer: List[Dict] = []
        self._buffer_size = 5
        self._buffer_timeout = 0.1
        self._buffer_timer = None
        
    def on_modified(self, event):
        """Chamado quando o arquivo é modificado"""
        if not event.is_directory and os.path.abspath(event.src_path) == self.file_path:
            current_time = time.time()
            
            # Verifica se deve processar a mudança
            if not self._should_process_change():
                return
                
            # Adiciona evento ao buffer
            with self._lock:
                self._event_buffer.append({
                    'time': current_time,
                    'type': 'modified',
                    'path': event.src_path
                })
                
                # Se o buffer está cheio ou passou tempo suficiente, processa
                if (len(self._event_buffer) >= self._buffer_size or 
                    (self._event_buffer and 
                     current_time - self._event_buffer[0]['time'] >= self._buffer_timeout)):
                    self._process_buffer()
                else:
                    # Agenda processamento futuro
                    self._schedule_buffer_processing()

    def _should_process_change(self) -> bool:
        """Verifica se a mudança deve ser processada"""
        current_time = time.time()
        try:
            current_size = os.path.getsize(self.file_path)
            current_mtime = os.path.getmtime(self.file_path)
            
            with self._lock:
                # Se o arquivo não mudou realmente
                if (current_size == self._last_size and 
                    current_mtime == self._last_modified):
                    return False
                
                # Se houve muitas mudanças em pouco tempo
                if (current_time - self._last_change_time < self.debounce_seconds and 
                    self._change_count > 5):
                    return False
                
                # Atualiza contadores
                if current_time - self._last_change_time >= 1.0:
                    self._change_count = 1
                else:
                    self._change_count += 1
                
                self._last_size = current_size
                self._last_modified = current_mtime
                self._last_change_time = current_time
                
                return True
        except Exception:
            return False

    def _schedule_buffer_processing(self):
        """Agenda o processamento do buffer"""
        if self._buffer_timer is not None:
            self._buffer_timer.cancel()
        
        self._buffer_timer = threading.Timer(
            self._buffer_timeout,
            self._process_buffer
        )
        self._buffer_timer.start()

    def _process_buffer(self):
        """Processa o buffer de eventos"""
        with self._lock:
            if not self._event_buffer:
                return
            
            # Processa apenas o evento mais recente
            self._process_change()
            self._event_buffer.clear()

    def _read_file_with_retry(self, max_retries=5, initial_delay=0.05):
        """
        Tenta ler o arquivo com diferentes codificações e com retry
        
        Args:
            max_retries (int): Número máximo de tentativas
            initial_delay (float): Tempo inicial de espera entre tentativas
            
        Returns:
            str: Conteúdo do arquivo
        """
        encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
        last_error = None
        
        for attempt in range(max_retries):
            # Delay exponencial entre tentativas
            time.sleep(initial_delay * (2 ** attempt))
            
            try:
                # Primeiro tenta ler em modo binário
                with open(self.file_path, 'rb') as f:
                    content = f.read()
                    
                # Tenta diferentes encodings
                for encoding in encodings:
                    try:
                        return content.decode(encoding)
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        last_error = e
                        continue
            except Exception as e:
                last_error = e
                continue
            
        raise Exception(f"Não foi possível ler o arquivo: {last_error}")

    def _process_change(self):
        """Processa a modificação do arquivo após o debounce"""
        if self._processing:
            self._schedule_buffer_processing()
            return

        self._processing = True
        start_time = time.time()
        
        try:
            # Tenta ler o arquivo com retry
            current_content = self._read_file_with_retry()
            
            # Se o conteúdo mudou
            if current_content != self._last_content:
                self._last_content = current_content
                xml_data = self.parser.parse_file(self.file_path)
                
                # Informações de processamento
                processing_info = {
                    'start_time': start_time,
                    'detection_time': datetime.now().strftime("%H:%M:%S")
                }
                
                # Chama o callback na thread principal
                if self.callback:
                    self.callback(xml_data, processing_info)
                    
        except Exception as e:
            print(f"Erro ao processar arquivo modificado: {e}")
            self._schedule_buffer_processing()
        finally:
            self._processing = False

class XMLFileMonitor:
    def __init__(self):
        """Inicializa o monitor de arquivos XML"""
        self.observer = None
        self.handler = None
        self.parser = XMLParser()
        self._is_monitoring = False
        self._current_file = None
        self._lock = threading.Lock()

    def start_monitoring(self, file_path: str, callback: Callable) -> None:
        """
        Inicia o monitoramento de um arquivo XML
        
        Args:
            file_path (str): Caminho do arquivo a ser monitorado
            callback (Callable): Função a ser chamada quando houver alterações
        """
        with self._lock:
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
        with self._lock:
            if self.observer:
                self.observer.stop()
                self.observer.join()
                self._is_monitoring = False
                self._current_file = None

    def is_monitoring(self) -> bool:
        """Retorna True se está monitorando um arquivo"""
        return self._is_monitoring

    @property
    def current_file(self) -> Optional[str]:
        """Retorna o caminho do arquivo atual sendo monitorado"""
        return self._current_file