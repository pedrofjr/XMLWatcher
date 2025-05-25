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
            
            # Abordagem 1: Tenta usar lxml diretamente com várias codificações
            encodings_to_try = ['utf-8', 'utf-16le', 'utf-16be', 'latin1', 'cp1252']
            root = None
            last_error = None
            
            # Verifica o BOM primeiro para determinar a codificação
            try:
                with open(file_path, 'rb') as f:
                    header = f.read(4)
                    if header.startswith(b'\xff\xfe'):
                        encodings_to_try.insert(0, 'utf-16le')
                    elif header.startswith(b'\xfe\xff'):
                        encodings_to_try.insert(0, 'utf-16be')
                    elif header.startswith(b'\xef\xbb\xbf'):
                        encodings_to_try.insert(0, 'utf-8-sig')
            except Exception as e:
                print(f"Aviso: Erro ao ler cabeçalho do arquivo: {e}")
            
            # Tenta cada codificação
            for encoding in encodings_to_try:
                try:
                    parser = etree.XMLParser(encoding=encoding, recover=True)
                    tree = etree.parse(file_path, parser=parser)
                    root = tree.getroot()
                    if root is not None:
                        break
                except Exception as e:
                    last_error = e
                    continue
            
            # Abordagem 2: Se ainda não conseguiu, tenta ler o arquivo e analisá-lo manualmente
            if root is None:
                try:
                    # Para UTF-16LE especificamente
                    content = None
                    
                    # Tenta UTF-16LE explicitamente
                    try:
                        with open(file_path, 'r', encoding='utf-16le') as f:
                            content = f.read()
                    except Exception:
                        # Outras tentativas
                        for enc in ['utf-16', 'utf-8', 'latin1']:
                            try:
                                with open(file_path, 'r', encoding=enc) as f:
                                    content = f.read()
                                break
                            except Exception:
                                continue
                    
                    if content:
                        # Remove a declaração XML para evitar problemas de codificação
                        if '<?xml' in content and '?>' in content:
                            content = content[content.find('?>') + 2:]
                        
                        # Força a análise do conteúdo como uma string
                        try:
                            root = etree.fromstring(content.encode('utf-8'), parser=etree.XMLParser(recover=True))
                        except Exception as e:
                            print(f"Erro ao analisar conteúdo como string: {e}")
                except Exception as e:
                    last_error = e
            
            # Se ainda não temos uma raiz, algo está realmente errado
            if root is None:
                error_msg = str(last_error) if last_error else "Motivo desconhecido"
                raise Exception(f"Não foi possível parsear o XML: {error_msg}")
            
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
            
            # Abordagem 1: Tenta usar lxml diretamente com várias codificações
            encodings_to_try = ['utf-8', 'utf-16le', 'utf-16be', 'latin1', 'cp1252']
            root = None
            last_error = None
            
            # Verifica o BOM primeiro para determinar a codificação
            try:
                with open(file_path, 'rb') as f:
                    header = f.read(4)
                    if header.startswith(b'\xff\xfe'):
                        encodings_to_try.insert(0, 'utf-16le')
                    elif header.startswith(b'\xfe\xff'):
                        encodings_to_try.insert(0, 'utf-16be')
                    elif header.startswith(b'\xef\xbb\xbf'):
                        encodings_to_try.insert(0, 'utf-8-sig')
            except Exception as e:
                print(f"Aviso: Erro ao ler cabeçalho do arquivo: {e}")
            
            # Tenta cada codificação
            for encoding in encodings_to_try:
                try:
                    parser = etree.XMLParser(encoding=encoding, recover=True)
                    tree = etree.parse(file_path, parser=parser)
                    root = tree.getroot()
                    if root is not None:
                        break
                except Exception as e:
                    last_error = e
                    continue
            
            # Abordagem 2: Se ainda não conseguiu, tenta ler o arquivo e analisá-lo manualmente
            if root is None:
                try:
                    # Para UTF-16LE especificamente
                    content = None
                    
                    # Tenta UTF-16LE explicitamente
                    try:
                        with open(file_path, 'r', encoding='utf-16le') as f:
                            content = f.read()
                    except Exception:
                        # Outras tentativas
                        for enc in ['utf-16', 'utf-8', 'latin1']:
                            try:
                                with open(file_path, 'r', encoding=enc) as f:
                                    content = f.read()
                                break
                            except Exception:
                                continue
                    
                    if content:
                        # Remove a declaração XML para evitar problemas de codificação
                        if '<?xml' in content and '?>' in content:
                            content = content[content.find('?>') + 2:]
                        
                        # Força a análise do conteúdo como uma string
                        try:
                            root = etree.fromstring(content.encode('utf-8'), parser=etree.XMLParser(recover=True))
                        except Exception as e:
                            print(f"Erro ao analisar conteúdo como string: {e}")
                except Exception as e:
                    last_error = e
            
            # Se ainda não temos uma raiz, algo está realmente errado
            if root is None:
                error_msg = str(last_error) if last_error else "Motivo desconhecido"
                raise Exception(f"Não foi possível parsear o XML: {error_msg}")
            
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
        Extrai elementos do XML seguindo a lógica correta de numeração
        
        Regras:
        1. Elementos começam com linha 1
        2. Apenas elementos repetidos no MESMO NÍVEL incrementam
        3. Elementos filhos herdam a numeração do pai até serem repetidos
        """
        elements = []
        
        def clean_tag(tag_with_ns):
            """Remove namespace da tag"""
            if '}' in tag_with_ns:
                return tag_with_ns.split('}')[-1]
            return tag_with_ns
        
        def process_level(parent_element, parent_path="", parent_line=1):
            """
            Processa um nível de elementos, contando repetições apenas neste nível
            """
            # Conta quantas vezes cada tag aparece neste nível
            tag_counts = {}
            children = list(parent_element)
            
            for child in children:
                clean_child_tag = clean_tag(child.tag)
                tag_counts[clean_child_tag] = tag_counts.get(clean_child_tag, 0) + 1
            
            # Processa cada filho
            tag_counters = {}
            for child in children:
                clean_child_tag = clean_tag(child.tag)
                
                # Determina o número da linha
                if tag_counts[clean_child_tag] > 1:
                    # Tag repetida neste nível - incrementa contador
                    tag_counters[clean_child_tag] = tag_counters.get(clean_child_tag, 0) + 1
                    line_number = tag_counters[clean_child_tag]
                else:
                    # Tag única neste nível - usa 1 ou herda do pai
                    line_number = 1 if parent_path == "" else parent_line
                
                # Cria o xpath usando getpath para consistência
                try:
                    current_xpath = root.getroottree().getpath(child)
                except Exception:
                    # Fallback se getpath falhar
                    current_xpath = f"{parent_path}/{clean_child_tag}" if parent_path else f"/{clean_child_tag}"
                
                # Adiciona o elemento
                element_data = {
                    'tag': clean_child_tag,
                    'value': child.text.strip() if child.text else '',
                    'xpath': current_xpath,
                    'namespace': self._namespace_map.get(clean_child_tag, ''),
                    'parent_number': line_number
                }
                elements.append(element_data)
                
                # Processa atributos com a mesma numeração
                for attr_name, attr_value in child.attrib.items():
                    clean_attr = clean_tag(attr_name)
                    attr_data = {
                        'tag': f"{clean_child_tag}@{clean_attr}",
                        'value': str(attr_value),
                        'xpath': f"{current_xpath}/@{clean_attr}",
                        'namespace': self._namespace_map.get(clean_child_tag, ''),
                        'parent_number': line_number
                    }
                    elements.append(attr_data)
                
                # Processa filhos recursivamente
                if len(child) > 0:
                    process_level(child, current_xpath, line_number)
        
        # Inicia o processamento
        if root is not None:
            # Processa o elemento raiz
            root_tag = clean_tag(root.tag)
            root_xpath = f"/{root_tag}"
            
            root_data = {
                'tag': root_tag,
                'value': root.text.strip() if root.text else '',
                'xpath': root_xpath,
                'namespace': self._namespace_map.get(root_tag, ''),
                'parent_number': 1
            }
            elements.append(root_data)
            
            # Processa atributos da raiz
            for attr_name, attr_value in root.attrib.items():
                clean_attr = clean_tag(attr_name)
                attr_data = {
                    'tag': f"{root_tag}@{clean_attr}",
                    'value': str(attr_value),
                    'xpath': f"{root_xpath}/@{clean_attr}",
                    'namespace': self._namespace_map.get(root_tag, ''),
                    'parent_number': 1
                }
                elements.append(attr_data)
            
            # Processa filhos da raiz
            process_level(root, root_xpath, 1)
        
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
