@echo off
echo Activando entorno virtual...
call venv\Scripts\activate.bat

echo Verificando dependencias...
pip install -r requirements.txt

echo Iniciando servidor Django...
python manage.py runserver
pause
