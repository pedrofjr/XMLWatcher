from lxml import etree
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
import time
import threading
from queue import Queue

class XMLParser:
    def __init__(self):
        self.initial_state = None
        self.intermediate_state = None
        self._namespace_map = {}
        self._element_cache = {}  # Mudando para um dicionário normal
        self._cache_lock = threading.Lock()
        self._parse_queue = Queue(maxsize=100)
        self._last_parse_time = 0
        self._parse_interval = 0.1  # 100ms
        self._lock = threading.Lock()
        
    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parseia um arquivo XML usando iterparse para melhor performance
        
        Args:
            file_path (str): Caminho do arquivo XML
            
        Returns:
            List[Dict]: Lista de elementos XML com suas propriedades
        """
        try:
            current_time = time.time()
            if current_time - self._last_parse_time < self._parse_interval:
                # Usa cache se disponível
                with self._cache_lock:
                    if file_path in self._element_cache:
                        return self._element_cache[file_path].copy()
            
            # Configura o parser para recuperar de erros
            tree = etree.parse(file_path, parser=etree.XMLParser(recover=True))
            root = tree.getroot()
            
            # Se não tiver estado inicial, salva o estado atual
            if self.initial_state is None:
                with self._lock:
                    self.initial_state = self._extract_elements(root)
                    with self._cache_lock:
                        self._element_cache[file_path] = self.initial_state.copy()
                    self._last_parse_time = time.time()
                    return self.initial_state
            
            # Extrai o estado atual e compara com o inicial
            current_state = self._extract_elements(root)
            result = self._compare_states(self.initial_state, current_state)
            
            # Atualiza cache
            with self._cache_lock:
                self._element_cache[file_path] = result.copy()
            self._last_parse_time = time.time()
            return result
            
        except Exception as e:
            raise Exception(f"Erro ao parsear XML: {str(e)}")

    def parse_file_and_get_changes(self, file_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Parseia o arquivo XML e retorna os dados atualizados e as mudanças de forma otimizada
        
        Args:
            file_path (str): Caminho do arquivo XML
            
        Returns:
            tuple: (dados_xml, lista_de_mudancas)
        """
        try:
            current_time = time.time()
            if current_time - self._last_parse_time < self._parse_interval:
                with self._cache_lock:
                    if file_path in self._element_cache:
                        cached_data = self._element_cache[file_path].copy()
                        changes = [elem for elem in cached_data if elem.get('modified', False)]
                        return cached_data, changes
            
            # Configura o parser para recuperar de erros
            tree = etree.parse(file_path, parser=etree.XMLParser(recover=True))
            root = tree.getroot()
            
            current_state = self._extract_elements(root)
            
            if self.initial_state is None:
                with self._lock:
                    self.initial_state = current_state
                    self.intermediate_state = None
                    with self._cache_lock:
                        self._element_cache[file_path] = current_state.copy()
                    self._last_parse_time = time.time()
                    return current_state, []
            
            last_changes = []
            if self.intermediate_state:
                last_changes = self._compare_states(self.intermediate_state, current_state)
                last_changes = [elem for elem in last_changes if elem.get('modified', False)]
            self.intermediate_state = current_state

            result_data = self._compare_states(self.initial_state, current_state)
            
            changes = [elem for elem in result_data if elem.get('modified', False)]
            
            # Atualiza cache
            with self._cache_lock:
                self._element_cache[file_path] = result_data.copy()
            self._last_parse_time = time.time()
            
            return result_data, changes, last_changes
            
        except Exception as e:
            raise Exception(f"Erro ao parsear XML: {str(e)}")

    def _extract_elements(self, root: etree.Element) -> List[Dict[str, Any]]:
        """
        Extrai elementos do XML com otimização de namespace e cache
        
        Args:
            root (Element): Elemento raiz do XML
            
        Returns:
            List[Dict]: Lista de elementos com suas propriedades
        """
        elements = []
        current_parent_number = 0
        
        # Cache de namespaces para este processamento
        local_ns_cache = {}
        
        # Encontra todos os elementos filhos diretos do root (produtos/itens)
        for parent in root.findall('./*'):
            current_parent_number += 1
            
            # Para cada filho do elemento pai
            for child in parent:
                # Extrai namespace com cache
                if '}' in child.tag:
                    ns_key = child.tag.split('}')[0] + '}'
                    if ns_key in local_ns_cache:
                        clean_tag = local_ns_cache[ns_key]
                    else:
                        ns = child.tag[1:].split('}')[0]
                        clean_tag = child.tag.split('}')[-1]
                        self._namespace_map[clean_tag] = ns
                        local_ns_cache[ns_key] = clean_tag
                else:
                    clean_tag = child.tag
                
                element_data = {
                    'tag': clean_tag,
                    'value': child.text.strip() if child.text else '',
                    'xpath': root.getroottree().getpath(child),
                    'namespace': self._namespace_map.get(clean_tag, ''),
                    'parent_number': current_parent_number
                }
                elements.append(element_data)
            
        return elements
        
    def _compare_states(
        self,
        initial_state: List[Dict[str, Any]],
        current_state: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Compara estados inicial e atual do XML, retornando lista com elementos atualizados
        
        Args:
            initial_state (List[Dict]): Estado inicial dos elementos
            current_state (List[Dict]): Estado atual dos elementos
            
        Returns:
            List[Dict]: Lista de elementos com informações de mudança
        """
        result = []
        changes = []
        
        # Mapeia elementos por xpath
        initial_map = {elem['xpath']: elem for elem in initial_state}
        current_map = {elem['xpath']: elem for elem in current_state}
        
        # Identifica elementos modificados, adicionados e removidos
        current_xpaths = set(current_map.keys())
        initial_xpaths = set(initial_map.keys())
        
        potentially_modified = current_xpaths.intersection(initial_xpaths)
        added_xpaths = current_xpaths - initial_xpaths
        removed_xpaths = initial_xpaths - current_xpaths
        
        # Processa elementos modificados
        for xpath in potentially_modified:
            current_elem = current_map[xpath]
            initial_elem = initial_map[xpath]
            elem_data = current_elem.copy()
            
            # Verifica mudanças em valores
            if initial_elem['value'] != current_elem['value']:
                elem_data.update({
                    'initial_value': initial_elem['value'],
                    'modified': True,
                    'change_type': 'modified',
                    'old_value': initial_elem['value'],
                    'new_value': current_elem['value'],
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                })
                changes.append(elem_data)
            
            result.append(elem_data)
        
        # Processa elementos adicionados
        for xpath in added_xpaths:
            elem_data = current_map[xpath].copy()
            elem_data.update({
                'modified': True,
                'change_type': 'added',
                'timestamp': datetime.now().strftime("%H:%M:%S")
            })
            changes.append(elem_data)
            result.append(elem_data)
        
        # Processa elementos removidos
        for xpath in removed_xpaths:
            elem_data = initial_map[xpath].copy()
            elem_data.update({
                'modified': True,
                'change_type': 'removed',
                'timestamp': datetime.now().strftime("%H:%M:%S")
            })
            changes.append(elem_data)
            result.append(elem_data)
        
        return result

    def format_change_message(self, change: Dict[str, Any]) -> str:
        """Formata mensagem de log com cache de strings frequentes"""
        tag = change['tag']
        change_type = change.get('change_type') or change.get('type')
        
        if change_type == 'modified':
            return f"Elemento <{tag}> alterado de '{change['old_value']}' para '{change['new_value']}'"
        elif change_type == 'added':
            return f"Novo elemento <{tag}> adicionado com valor '{change['value']}'"
        elif change_type == 'removed':
            return f"Elemento <{tag}> removido (valor anterior: '{change['value']}')"
        else:
            return f"Alteração não reconhecida em <{tag}>"