from lxml import etree
from typing import List, Dict, Any, Optional
from datetime import datetime

class XMLParser:
    def __init__(self):
        self.initial_state = None
        self._namespace_map = {}

    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parseia um arquivo XML e retorna uma lista de elementos
        
        Args:
            file_path (str): Caminho do arquivo XML
            
        Returns:
            List[Dict]: Lista de elementos XML com suas propriedades
        """
        try:
            # Configura o parser para recuperar de erros e ignorar codificação
            parser = etree.XMLParser(recover=True)
            
            with open(file_path, 'rb') as f:  # Abre em modo binário
                tree = etree.parse(f, parser=parser)
                root = tree.getroot()
            
            # Se não tiver estado inicial, salva o estado atual
            if self.initial_state is None:
                self.initial_state = self._extract_elements(root)
                return self.initial_state
            
            # Extrai o estado atual e compara com o inicial
            current_state = self._extract_elements(root)
            return self._compare_states(self.initial_state, current_state)
            
        except Exception as e:
            raise Exception(f"Erro ao parsear XML: {str(e)}")

    def parse_file_and_get_changes(self, file_path: str) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Parseia o arquivo XML e retorna os dados atualizados e as mudanças
        
        Args:
            file_path (str): Caminho do arquivo XML
            
        Returns:
            tuple: (dados_xml, lista_de_mudancas)
        """
        try:
            tree = etree.parse(file_path)
            root = tree.getroot()
            
            current_state = self._extract_elements(root)
            
            if self.initial_state is None:
                self.initial_state = current_state
                return current_state, []
            
            result_data = self._compare_states(self.initial_state, current_state)
            changes = [elem for elem in result_data if elem.get('modified', False)]
            
            return result_data, changes
            
        except Exception as e:
            raise Exception(f"Erro ao parsear XML: {str(e)}")

    def _extract_elements(self, root: etree.Element) -> List[Dict[str, Any]]:
        """
        Extrai todos os elementos e seus atributos do XML
        
        Args:
            root (Element): Elemento raiz do XML
            
        Returns:
            List[Dict]: Lista de elementos com suas propriedades
        """
        elements = []
        current_parent_number = 0
        
        # Encontra todos os elementos filhos diretos do root (produtos/itens)
        for parent in root.findall('./*'):
            current_parent_number += 1
            
            # Para cada filho do elemento pai (nome, preço, etc)
            for child in parent:
                # Extrai namespace se existir
                if '}' in child.tag:
                    ns = child.tag[1:].split('}')[0]
                    clean_tag = child.tag.split('}')[-1]
                    self._namespace_map[clean_tag] = ns
                else:
                    clean_tag = child.tag
                
                # Formata atributos do pai para elementos filhos
                parent_attrs = []
                for key, value in parent.attrib.items():
                    if '}' in key:
                        key = key.split('}')[-1]
                    parent_attrs.append(f"{key}='{value}'")
                
                element_data = {
                    'tag': clean_tag,
                    'value': child.text.strip() if child.text else '',
                    'attributes': " ".join(parent_attrs),  # Mostra os atributos do pai
                    'xpath': root.getroottree().getpath(child),
                    'namespace': self._namespace_map.get(clean_tag, ''),
                    'parent_number': current_parent_number  # Número do item pai
                }
                elements.append(element_data)
            
        return elements
        
    def _compare_states(
        self,
        initial_state: List[Dict[str, Any]],
        current_state: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Compara o estado inicial com o atual e marca as diferenças
        
        Args:
            initial_state (List[Dict]): Estado inicial dos elementos
            current_state (List[Dict]): Estado atual dos elementos
            
        Returns:
            List[Dict]: Lista de elementos com marcação de alterações
        """
        result = []
        changes = []
        
        # Cria um mapa de elementos por xpath para facilitar a comparação
        initial_map = {elem['xpath']: elem for elem in initial_state}
        current_map = {elem['xpath']: elem for elem in current_state}
        
        # Compara os elementos
        for xpath in current_map:
            current_elem = current_map[xpath]
            elem_data = current_elem.copy()
            
            if xpath in initial_map:
                initial_elem = initial_map[xpath]
                
                # Verifica mudanças em valores
                if initial_elem['value'] != current_elem['value']:
                    elem_data['initial_value'] = initial_elem['value']
                    elem_data['modified'] = True
                    elem_data['change_type'] = 'modified'
                    change_info = {
                        'tag': current_elem['tag'],
                        'type': 'modified',
                        'change_type': 'modified',
                        'old_value': initial_elem['value'],
                        'new_value': current_elem['value'],
                        'xpath': xpath,
                        'timestamp': datetime.now().strftime("%H:%M:%S")
                    }
                    changes.append(change_info)
                    elem_data.update(change_info)
                
                # Verifica mudanças em atributos
                if initial_elem['attributes'] != current_elem['attributes']:
                    elem_data['initial_attributes'] = initial_elem['attributes']
                    elem_data['modified'] = True
                    elem_data['attributes_changed'] = True
                    change_info = {
                        'tag': current_elem['tag'],
                        'type': 'attributes_changed',
                        'change_type': 'attributes_changed',
                        'old_attrs': initial_elem['attributes'],
                        'new_attrs': current_elem['attributes'],
                        'xpath': xpath,
                        'timestamp': datetime.now().strftime("%H:%M:%S")
                    }
                    changes.append(change_info)
                    elem_data.update(change_info)
            else:
                # Elemento novo
                elem_data['modified'] = True
                elem_data['change_type'] = 'added'
                change_info = {
                    'tag': current_elem['tag'],
                    'type': 'added',
                    'change_type': 'added',
                    'value': current_elem['value'],
                    'xpath': xpath,
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                }
                changes.append(change_info)
                elem_data.update(change_info)
            
            result.append(elem_data)
        
        # Verifica elementos removidos
        for xpath in initial_map:
            if xpath not in current_map:
                initial_elem = initial_map[xpath]
                elem_data = initial_elem.copy()
                elem_data['modified'] = True
                elem_data['change_type'] = 'removed'
                change_info = {
                    'tag': initial_elem['tag'],
                    'type': 'removed',
                    'value': initial_elem['value'],
                    'xpath': xpath,
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                }
                changes.append(change_info)
                elem_data.update(change_info)  # Garante que o elemento tem todas as informações necessárias
                result.append(elem_data)
                
        return result

    def format_change_message(self, change: Dict[str, Any]) -> str:
        """
        Formata uma mensagem de log para uma alteração
        
        Args:
            change (Dict): Informações sobre a alteração
            
        Returns:
            str: Mensagem formatada
        """
        tag = change['tag']
        change_type = change.get('change_type') or change.get('type')
        timestamp = change.get('timestamp', datetime.now().strftime("%H:%M:%S"))
        
        if change_type == 'modified':
            return f"Elemento <{tag}> alterado de '{change['old_value']}' para '{change['new_value']}'"
        elif change_type == 'attributes_changed':
            return f"Atributos do elemento <{tag}> alterados de [{change['old_attrs']}] para [{change['new_attrs']}]"
        elif change_type == 'added':
            return f"Novo elemento <{tag}> adicionado com valor '{change['value']}'"
        elif change_type == 'removed':
            return f"Elemento <{tag}> removido (valor anterior: '{change['value']}')"
        else:
            return f"Alteração não reconhecida em <{tag}>"