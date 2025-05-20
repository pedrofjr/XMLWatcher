import weakref
import os
import time
from queue import Queue, Empty
import threading
import configparser
from typing import Any, Dict, Optional

class ResourceManager:
    def __init__(self):
        self._resources = {}  # Mudando para um dicionário normal
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutos
        self._lock = threading.Lock()
        
    def get_resource(self, key: str) -> Any:
        current_time = time.time()
        with self._lock:
            if current_time - self._last_cleanup > self._cleanup_interval:
                self._cleanup()
            
            if key in self._resources:
                return self._resources[key]
            resource = self._create_resource(key)
            self._resources[key] = resource
            return resource
    
    def _cleanup(self) -> None:
        """Limpa recursos não utilizados"""
        with self._lock:
            self._last_cleanup = time.time()
            # Implementação básica - pode ser estendida conforme necessidade
            self._resources.clear()

    def _create_resource(self, key: str) -> Any:
        """Cria um novo recurso - deve ser implementado por subclasses"""
        raise NotImplementedError

class ConfigManager:
    def __init__(self, config_file: str):
        self._config_cache: Dict[str, Any] = {}
        self._last_load_time = 0
        self._config_file_mtime = 0
        self._config_file = config_file
        self._lock = threading.Lock()
        self._config = configparser.ConfigParser()
        self._load_config()
    
    def _load_config(self) -> None:
        """Carrega as configurações do arquivo"""
        with self._lock:
            if os.path.exists(self._config_file):
                self._config.read(self._config_file)
                self._config_file_mtime = os.path.getmtime(self._config_file)
                self._last_load_time = time.time()
    
    def get_config(self, section: str, key: str, default: Any = None) -> Any:
        """Obtém um valor de configuração com cache"""
        current_mtime = os.path.getmtime(self._config_file)
        if current_mtime > self._config_file_mtime:
            self._load_config()
        
        cache_key = f"{section}.{key}"
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]
        
        try:
            value = self._config.get(section, key)
            self._config_cache[cache_key] = value
            return value
        except:
            return default
    
    def set_config(self, section: str, key: str, value: Any) -> None:
        """Define um valor de configuração"""
        with self._lock:
            if not self._config.has_section(section):
                self._config.add_section(section)
            self._config.set(section, key, str(value))
            cache_key = f"{section}.{key}"
            self._config_cache[cache_key] = value
            
            with open(self._config_file, 'w') as f:
                self._config.write(f)
            self._config_file_mtime = os.path.getmtime(self._config_file)

class AsyncLogger:
    def __init__(self, max_queue_size: int = 1000):
        self._log_queue = Queue(maxsize=max_queue_size)
        self._handlers = []
        self._worker = threading.Thread(target=self._process_logs, daemon=True)
        self._running = True
        self._worker.start()
    
    def add_handler(self, handler) -> None:
        """Adiciona um handler de log"""
        self._handlers.append(handler)
    
    def log(self, message: str, level: str = 'INFO') -> None:
        """Adiciona uma mensagem ao log de forma assíncrona"""
        try:
            log_entry = {
                'message': message,
                'level': level,
                'timestamp': time.time()
            }
            self._log_queue.put_nowait(log_entry)
        except Queue.Full:
            pass  # Ignora se a fila estiver cheia
    
    def _process_logs(self) -> None:
        """Processa as mensagens de log em background"""
        while self._running:
            try:
                log_entry = self._log_queue.get(timeout=1.0)
                for handler in self._handlers:
                    try:
                        handler(log_entry)
                    except Exception:
                        continue
            except Empty:
                continue
            except Exception:
                continue
    
    def shutdown(self) -> None:
        """Finaliza o logger de forma segura"""
        self._running = False
        if self._worker.is_alive():
            self._worker.join(timeout=2.0) 