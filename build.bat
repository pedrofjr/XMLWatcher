@echo off
echo Iniciando processo de build do XMLWatcher...

REM Verifica se Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python nao encontrado! Por favor, instale o Python 3.7 ou superior.
    pause
    exit /b 1
)

REM Verifica se venv existe, se não, cria
if not exist "venv" (
    echo Criando ambiente virtual...
    python -m venv venv
)

REM Ativa o ambiente virtual
call venv\Scripts\activate.bat

REM Atualiza pip
python -m pip install --upgrade pip

REM Instala dependências
echo Instalando dependencias...
pip install -r requirements.txt
pip install pyinstaller

REM Limpa diretório dist se existir
if exist "dist" (
    echo Limpando builds anteriores...
    rmdir /s /q "dist"
)

REM Executa o PyInstaller
echo Compilando o projeto...
pyinstaller build.spec --clean

REM Verifica se a compilação foi bem sucedida
if %errorlevel% neq 0 (
    echo Erro durante a compilacao!
    pause
    exit /b 1
)

echo Build concluido com sucesso!
echo O executavel esta na pasta 'dist'

REM Desativa o ambiente virtual
deactivate

pause 