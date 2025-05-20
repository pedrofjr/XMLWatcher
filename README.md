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
  - Busca rápida com Ctrl+F
  - Navegação entre alterações com setas do teclado

- **Recursos Avançados**:
  - Comparação com estado inicial do arquivo
  - Detecção de alterações em valores e atributos
  - Suporte a namespaces XML básicos
  - Pausar/retomar monitoramento
  - Configurações de som personalizáveis
  - Busca e navegação entre elementos
  - Salvamento automático de configurações

## Requisitos

- Windows 7 ou superior
- Python 3.7 ou superior (para desenvolvimento)

## Instalação

### Usuários
1. Baixe a última versão do executável na seção [Releases](https://github.com/seu-usuario/XMLWatcher/releases)
2. Execute o arquivo `XMLWatcher.exe`

### Desenvolvedores
1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/XMLWatcher.git
cd XMLWatcher
```

2. Execute o script de build:
```bash
build.bat
```

Para mais detalhes sobre o processo de build, consulte [BUILD.md](BUILD.md).

## Uso

1. Execute a aplicação (XMLWatcher.exe ou via código fonte)
2. Na interface gráfica:
   - Clique em "Selecionar XML" para escolher um arquivo
   - O grid mostrará os elementos do XML
   - Alterações serão destacadas em verde automaticamente
   - Use o botão "Pausar/Retomar" para controlar o monitoramento
   - Use Ctrl+F para buscar elementos
   - Use as setas ↑/↓ para navegar entre alterações
   - Configure sons de notificação no menu Configurações
   - Acompanhe as mudanças na área de log

## Estrutura do Projeto

```
XMLWatcher/
├── src/
│   ├── gui/              # Interface gráfica
│   │   ├── __init__.py
│   │   ├── grid_view.py  # Implementação do grid
│   │   └── settings_dialog.py # Diálogo de configurações
│   ├── resources/        # Recursos
│   │   └── icone.ico    # Ícone da aplicação
│   ├── utils/           # Utilitários
│   │   ├── __init__.py
│   │   ├── xml_parser.py # Parser XML
│   │   └── resource_manager.py # Gerenciador de recursos
│   ├── watcher/         # Monitoramento
│   │   ├── __init__.py
│   │   └── xml_monitor.py # Monitor de arquivos
│   └── main.py         # Ponto de entrada
├── tests/              # Testes unitários
├── build.spec         # Configuração do PyInstaller
├── build.bat         # Script de build
└── requirements.txt  # Dependências
```

## Funcionalidades

### Monitoramento
- Detecção instantânea de alterações
- Debounce inteligente para evitar processamento excessivo
- Suporte a arquivos grandes
- Recuperação automática de erros

### Interface
- Grid organizado e responsivo
- Destaque visual de alterações
- Busca rápida com Ctrl+F
- Navegação com setas do teclado
- Log detalhado com timestamps
- Configurações persistentes

### Som
- Notificações sonoras configuráveis
- Suporte a arquivos WAV personalizados
- Controle de frequência e duração
- Opção para desativar sons

## Limitações Conhecidas

- **Arquivo Único**: Suporta monitoramento de um arquivo por vez
- **Tamanho de Arquivo**: Otimizado para XMLs até 50 MB
- **Namespaces**: Suporte limitado para namespaces complexos
- **Parsing**: Assume XMLs bem formados
- **Sistema**: Otimizado para Windows

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