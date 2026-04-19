import streamlit.web.cli as stcli
import sys
import os

def main():
    # Detectar si estamos corriendo desde el .exe compilado o desde Python normal
    if getattr(sys, 'frozen', False):
        # Modo .exe: buscar app.py en la carpeta temporal de PyInstaller
        app_path = os.path.join(sys._MEIPASS, 'app.py')
    else:
        # Modo desarrollo normal
        app_path = os.path.abspath('app.py')

    # Configurar los argumentos como si lo escribiéramos en la terminal
    sys.argv = [
        "streamlit", 
        "run", 
        app_path, 
        "--global.developmentMode=false",
        "--server.headless=false" # Para que abra el navegador automáticamente
    ]
    
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()