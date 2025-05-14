import unittest
from pathlib import Path
import tempfile
import sys
import os

# Adiciona o diretório raiz do projeto ao PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.utils.xml_parser import XMLParser

class TestXMLParser(unittest.TestCase):
    def setUp(self):
        self.parser = XMLParser()
        self.test_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <root>
            <item id="1">
                <name>Test Item</name>
                <price>100.00</price>
            </item>
            <item id="2">
                <name>Another Item</name>
                <price>200.00</price>
            </item>
        </root>
        """
        
    def create_temp_xml(self, content):
        temp = tempfile.NamedTemporaryFile(delete=False, suffix='.xml')
        temp.write(content.encode('utf-8'))
        temp.close()
        return temp.name
        
    def test_parse_file(self):
        """Testa o parsing básico de um arquivo XML"""
        file_path = self.create_temp_xml(self.test_xml)
        
        try:
            data, changes = self.parser.parse_file_and_get_changes(file_path)
            
            # Primeira leitura não deve ter mudanças
            self.assertEqual(len(changes), 0)
            
            # Verifica se todos os elementos foram extraídos
            self.assertTrue(any(elem['tag'] == 'name' for elem in data))
            self.assertTrue(any(elem['tag'] == 'price' for elem in data))
            
        finally:
            Path(file_path).unlink()
            
    def test_detect_changes(self):
        """Testa a detecção de mudanças no XML"""
        file_path = self.create_temp_xml(self.test_xml)
        
        try:
            # Primeira leitura
            self.parser.parse_file_and_get_changes(file_path)
            
            # Modifica o XML
            modified_xml = self.test_xml.replace('100.00', '150.00')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_xml)
            
            # Segunda leitura
            data, changes = self.parser.parse_file_and_get_changes(file_path)
            
            # Verifica se a mudança foi detectada
            self.assertTrue(len(changes) > 0)
            self.assertTrue(any(
                change.get('type') == 'modified' and 
                change.get('new_value') == '150.00'
                for change in changes
            ))
            
        finally:
            Path(file_path).unlink()
            
    def test_attribute_changes(self):
        """Testa a detecção de mudanças em atributos"""
        file_path = self.create_temp_xml(self.test_xml)
        
        try:
            # Primeira leitura
            self.parser.parse_file_and_get_changes(file_path)
            
            # Modifica um atributo
            modified_xml = self.test_xml.replace('id="1"', 'id="3"')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_xml)
            
            # Segunda leitura
            data, changes = self.parser.parse_file_and_get_changes(file_path)
            
            # Verifica se a mudança foi detectada
            self.assertTrue(any(
                change.get('type') == 'attributes_changed'
                for change in changes
            ))
            
        finally:
            Path(file_path).unlink()

if __name__ == '__main__':
    unittest.main()