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
        self.config_file = os.path.join(os.path.dirname(__file__), "..", "gui", "config.json")
        self._processing = False

    def _read_file_with_retry(self, max_retries=5, initial_delay=0.05):
        """
        Tenta ler o arquivo com diferentes codificações e com retry
        
        Args:
            max_retries (int): Número máximo de tentativas
            initial_delay (float): Tempo inicial de espera entre tentativas em segundos
            
        Returns:
            str: Conteúdo do arquivo
        """
        encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
        last_error = None
        
        for attempt in range(max_retries):
            # Delay exponencial entre tentativas
            time.sleep(initial_delay * (2 ** attempt))
            
            try:
                # Primeiro tenta ler em modo binário para verificar se o arquivo está disponível
                with open(self.file_path, 'rb') as f:
                    content = f.read()
                    
                # Se conseguiu ler em binário, tenta os diferentes encodings
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
            
            print(f"Tentativa {attempt + 1} de {max_retries} falhou")
        
        raise Exception(f"Não foi possível ler o arquivo: {last_error}")

    def _should_play_sound(self) -> bool:
        """Verifica se o som deve ser reproduzido baseado na configuração"""
        try:
            import json
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('sound_enabled', True)
        except Exception:
            pass
        return True

    def _process_modification(self):
        """Processa a modificação do arquivo após o debounce"""
        if self._processing:
            # Se já está processando, agenda nova verificação
            self._schedule_next_check()
            return

        self._processing = True
        try:
            # Tenta ler o arquivo com retry e diferentes codificações
            current_content = self._read_file_with_retry()
            
            # Se o conteúdo mudou desde a última verificação
            if current_content != self._last_content:
                self._last_content = current_content  # Atualiza antes de processar
                xml_data = self.parser.parse_file(self.file_path)
                self.callback(xml_data)
        except Exception as e:
            print(f"Erro ao processar arquivo modificado: {e}")
            self._schedule_next_check(error_retry=True)
        finally:
            self._processing = False

    def _schedule_next_check(self, error_retry=False):
        """Agenda a próxima verificação"""
        with self.lock:
            if self._timer is not None:
                self._timer.cancel()
            
            # Se foi erro, retry mais rápido
            delay = 0.1 if error_retry else self.debounce_seconds
            self._timer = Timer(delay, self._process_modification)
            self._timer.start()

    def on_modified(self, event):
        """Chamado quando o arquivo é modificado"""
        if not event.is_directory and os.path.abspath(event.src_path) == self.file_path:
            # Emite o som imediatamente ao detectar alteração
            if self._should_play_sound():
                try:
                    import winsound
                    winsound.Beep(1000, 100)  # Frequência: 1000Hz, Duração: 100ms
                except Exception:
                    pass  # Se não conseguir tocar o som, apenas ignora
            
            # Agenda o processamento
            self._schedule_next_check()

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