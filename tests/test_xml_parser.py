import unittest
from pathlib import Path
import tempfile
import sys
import os
import time
import threading
from unittest.mock import MagicMock, patch
import tkinter as tk

# Adiciona o diretório raiz do projeto ao PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.utils.xml_parser import XMLParser
from src.gui.grid_view import XMLGridView
from src.watcher.xml_monitor import XMLFileMonitor

class TestXMLParser(unittest.TestCase):
    def setUp(self):
        self.parser = XMLParser()
        self.test_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <root>
            <item>
                <name>Test Item</name>
                <price>100.00</price>
            </item>
            <item>
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

    def test_large_file(self):
        """Testa o parser com um arquivo XML grande"""
        # Cria um XML grande com 1000 elementos
        large_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<root>\n'
        for i in range(1000):
            large_xml += f'<item><name>Item {i}</name><value>{i}</value></item>\n'
        large_xml += '</root>'
        
        file_path = self.create_temp_xml(large_xml)
        
        try:
            start_time = time.time()
            data, _ = self.parser.parse_file_and_get_changes(file_path)
            end_time = time.time()
            
            # Verifica se o parsing foi rápido o suficiente (menos de 1 segundo)
            self.assertLess(end_time - start_time, 1.0)
            # Verifica se todos os elementos foram parseados
            self.assertEqual(len([x for x in data if x['tag'] == 'item']), 1000)
            
        finally:
            Path(file_path).unlink()

    def test_malformed_xml(self):
        """Testa a recuperação de erros com XML malformado"""
        malformed_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <root>
            <item>
                <name>Test Item</name>
                <price>100.00
            </item>
        </root>
        """
        
        file_path = self.create_temp_xml(malformed_xml)
        
        try:
            # Deve lançar uma exceção ou retornar dados parciais
            data, _ = self.parser.parse_file_and_get_changes(file_path)
            # Verifica se pelo menos alguns dados foram extraídos
            self.assertTrue(len(data) > 0)
        finally:
            Path(file_path).unlink()

    def test_special_characters(self):
        """Testa o parsing de caracteres especiais"""
        special_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <root>
            <item>
                <name>Teste áéíóú</name>
                <description>Símbolos: &lt; &gt; &amp; © ®</description>
            </item>
        </root>
        """
        
        file_path = self.create_temp_xml(special_xml)
        
        try:
            data, _ = self.parser.parse_file_and_get_changes(file_path)
            # Verifica se os caracteres especiais foram preservados
            name_elem = next(elem for elem in data if elem['tag'] == 'name')
            self.assertEqual(name_elem['value'], 'Teste áéíóú')
        finally:
            Path(file_path).unlink()

class TestXMLMonitor(unittest.TestCase):
    def setUp(self):
        self.monitor = XMLFileMonitor()
        self.callback_called = False
        self.callback_data = None
        
    def callback(self, data, info=None):
        self.callback_called = True
        self.callback_data = data
        
    def test_file_monitoring(self):
        """Testa o monitoramento de arquivos"""
        # Cria um arquivo temporário
        temp = tempfile.NamedTemporaryFile(delete=False, suffix='.xml')
        temp.write(b'<?xml version="1.0"?><root><test>1</test></root>')
        temp.close()
        
        try:
            # Inicia o monitoramento
            self.monitor.start_monitoring(temp.name, self.callback)
            
            # Modifica o arquivo
            time.sleep(0.1)  # Pequena pausa para garantir que o monitor está pronto
            with open(temp.name, 'w') as f:
                f.write('<?xml version="1.0"?><root><test>2</test></root>')
            
            # Aguarda a detecção da mudança
            time.sleep(0.5)
            
            # Verifica se o callback foi chamado
            self.assertTrue(self.callback_called)
            
        finally:
            self.monitor.stop_monitoring()
            Path(temp.name).unlink()

class TestGridView(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.parser = XMLParser()
        self.monitor = XMLFileMonitor()
        self.grid = XMLGridView(self.root, self.parser, self.monitor)
        
    def tearDown(self):
        self.root.destroy()
        
    def test_grid_creation(self):
        """Testa a criação da interface gráfica"""
        # Verifica se os componentes principais foram criados
        self.assertIsNotNone(self.grid.tree)
        self.assertIsNotNone(self.grid.log_area)
        
    def test_log_message(self):
        """Testa o sistema de log"""
        test_message = "Teste de mensagem"
        self.grid.log_message(test_message)
        
        # Habilita a área de log para leitura
        self.grid.log_area.configure(state='normal')
        log_content = self.grid.log_area.get("1.0", tk.END)
        self.grid.log_area.configure(state='disabled')
        
        # Verifica se a mensagem foi registrada
        self.assertIn(test_message, log_content)
        
    @patch('tkinter.filedialog.askopenfilename')
    def test_file_selection(self, mock_filedialog):
        """Testa a seleção de arquivo"""
        # Simula a seleção de um arquivo
        mock_filedialog.return_value = "test.xml"
        
        # Tenta selecionar um arquivo
        self.grid.select_file()
        
        # Verifica se o label foi atualizado
        self.assertEqual(self.grid.file_label.cget("text"), "test.xml")

if __name__ == '__main__':
    unittest.main()