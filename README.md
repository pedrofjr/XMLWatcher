# XMLWatcher

XMLWatcher é uma aplicação Python que monitora alterações em arquivos XML em tempo real, exibindo os valores em uma interface gráfica no formato de grid (tabela) e destacando mudanças nos valores com a cor verde, inspirado no versionamento do Git.

## Características

- **Monitoramento em Tempo Real**: 
  - Detecta alterações em arquivos XML instantaneamente
  - Usa a biblioteca watchdog para monitoramento eficiente
  - Implementa debounce para evitar processamento excessivo

- **Interface Gráfica Intuitiva**: 
  - Grid simples e claro mostrando elementos XML
  - Colunas organizadas para tag, atributos e valores
  - Destaque visual de alterações em verde
  - Log de alterações com timestamp

- **Recursos Avançados**:
  - Comparação com estado inicial do arquivo
  - Detecção de alterações em valores e atributos
  - Suporte a namespaces XML básicos
  - Pausar/retomar monitoramento

## Requisitos

- Python 3.7 ou superior
- tkinter (geralmente incluído na instalação padrão do Python)
- lxml para parsing XML
- watchdog para monitoramento de arquivos

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/XMLWatcher.git
cd XMLWatcher
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Uso

1. Execute a aplicação:
```bash
python src/main.py
```

2. Na interface gráfica:
   - Clique em "Selecionar XML" para escolher um arquivo
   - O grid mostrará os elementos do XML
   - Alterações serão destacadas em verde automaticamente
   - Use o botão "Pausar/Retomar" para controlar o monitoramento
   - Acompanhe as mudanças na área de log

## Estrutura do Projeto

```
XMLWatcher/
├── src/
│   ├── gui/              # Interface gráfica
│   │   ├── __init__.py
│   │   └── grid_view.py  # Implementação do grid
│   ├── utils/            # Utilitários
│   │   ├── __init__.py
│   │   └── xml_parser.py # Parser XML
│   ├── watcher/          # Monitoramento
│   │   ├── __init__.py
│   │   └── xml_monitor.py# Monitor de arquivos
│   └── main.py          # Ponto de entrada
├── tests/               # Testes unitários
└── requirements.txt    # Dependências
```

## Limitações Conhecidas

- **Arquivo Único**: Suporta monitoramento de um arquivo por vez
- **Tamanho de Arquivo**: Otimizado para XMLs até 50 MB
- **Namespaces**: Suporte limitado para namespaces complexos
- **Parsing**: Assume XMLs bem formados

## Desenvolvimento

Para executar os testes:
```bash
python -m unittest discover tests
```

### Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature
3. Faça suas alterações
4. Execute os testes
5. Envie um Pull Request

## Licença

Este projeto é licenciado sob a Licença MIT - veja o arquivo LICENSE para detalhes.