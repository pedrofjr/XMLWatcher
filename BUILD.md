# Instruções de Build - XMLWatcher

Este documento descreve o processo de compilação do XMLWatcher para gerar o executável Windows.

## Pré-requisitos

- Windows 7 ou superior
- Python 3.7 ou superior
- Git (opcional, para clonar o repositório)

## Preparação do Ambiente

1. Clone ou baixe o repositório:
```bash
git clone https://github.com/seu-usuario/XMLWatcher.git
cd XMLWatcher
```

Ou baixe e extraia o arquivo ZIP do projeto.

## Build Automático

A maneira mais simples de compilar o projeto é usando o script `build.bat`:

1. Abra o Explorador de Arquivos na pasta do projeto
2. Dê dois cliques no arquivo `build.bat`
3. Aguarde o processo de build completar
4. O executável será gerado na pasta `dist`

O script automaticamente:
- Cria um ambiente virtual Python
- Instala todas as dependências necessárias
- Compila o projeto usando PyInstaller
- Limpa arquivos temporários

## Build Manual

Se preferir fazer o processo manualmente:

1. Crie um ambiente virtual:
```bash
python -m venv venv
```

2. Ative o ambiente virtual:
```bash
venv\Scripts\activate
```

3. Atualize o pip:
```bash
python -m pip install --upgrade pip
```

4. Instale as dependências:
```bash
pip install -r requirements.txt
pip install pyinstaller
```

5. Execute o PyInstaller:
```bash
pyinstaller build.spec --clean
```

## Estrutura do Build

O processo de build usa os seguintes arquivos:

- `build.bat`: Script de automação do build
- `build.spec`: Configuração do PyInstaller
- `requirements.txt`: Lista de dependências Python

### Arquivos Gerados

Após a compilação, você encontrará:

```
dist/
└── XMLWatcher/
    ├── XMLWatcher.exe     # Executável principal
    ├── python3X.dll       # DLLs do Python
    ├── resources/         # Recursos (ícones, etc)
    └── ... outros arquivos
```

## Configurações do Build

O arquivo `build.spec` contém configurações importantes:

- Ícone da aplicação
- Arquivos de recursos incluídos
- Dependências Python
- Configurações de empacotamento

## Troubleshooting

### Erros Comuns

1. **Python não encontrado**
   - Verifique se o Python está instalado
   - Adicione o Python ao PATH do sistema

2. **Dependências faltando**
   - Execute o pip install manualmente
   - Verifique se o ambiente virtual está ativo

3. **Erro de permissão**
   - Execute como administrador
   - Verifique permissões da pasta

4. **Antivírus bloqueando**
   - Adicione exceção para a pasta do projeto
   - Desative temporariamente o antivírus

### Verificação do Build

Para verificar se o build foi bem sucedido:

1. Navegue até a pasta `dist`
2. Execute `XMLWatcher.exe`
3. Verifique se:
   - O ícone aparece corretamente
   - A aplicação inicia sem erros
   - As configurações podem ser salvas
   - Todas as funcionalidades funcionam

## Distribuição

Para distribuir o aplicativo:

1. Copie a pasta `dist/XMLWatcher`
2. Crie um arquivo ZIP
3. Distribua o ZIP para os usuários

Os usuários precisam apenas:
1. Extrair o ZIP
2. Executar `XMLWatcher.exe`

## Suporte

Se encontrar problemas durante o build:

1. Verifique os logs de erro
2. Consulte a documentação do PyInstaller
3. Abra uma issue no GitHub
4. Entre em contato com a equipe de desenvolvimento 