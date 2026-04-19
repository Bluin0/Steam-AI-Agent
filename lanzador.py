import sys
import os
from streamlit.web import cli

if __name__ == '__main__':
    # Forzamos a Streamlit a arrancar nuestro app.py de forma invisible
    sys.argv = ["streamlit", "run", "app.py", "--global.developmentMode=false"]
    sys.exit(cli.main())