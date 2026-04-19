import streamlit as st
import os
import sys
import requests
import time
import re

# ==========================================
# CONFIGURACIÓN GENERAL
# ==========================================
st.set_page_config(page_title="Steam AI Assistant", page_icon="🎮", layout="centered")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

RUTA_TXT = "juegos_filtrados.txt"
RUTA_TEMP = "temp_appids.txt"

# ==========================================
# DICCIONARIO MULTI-IDIOMA (INGLÉS BASE)
# ==========================================
TEXTOS = {
    "English": {
        "title1": "Welcome to Steam AI Assistant",
        "title2": "🧠 Connect LM Studio",
        "title3": "📂 Scan your Library",
        "title4": "🤖 Your Personal Sommelier",
        "next": "Next >",
        "back": "< Back",
        "instrucciones_ia": """
        1. Open **LM Studio**.
        2. Load model (**Llama 3.2 3B Instruct**).
        3. Go to **Local Server** tab.
        4. Set port to **2901** and click **START**.
        """,
        "path_label": "Steam Cache Path:",
        "scan_btn": "Extract & Translate Games",
        "ai_on": "🟢 Online: ",
        "ai_off": "🔴 Offline (Check port 2901)",
    },
    "Español": {
        "title1": "Bienvenido a Steam AI Assistant",
        "title2": "🧠 Conectar LM Studio",
        "title3": "📂 Escanear Biblioteca",
        "title4": "🤖 Tu Sumiller Personal",
        "next": "Siguiente >",
        "back": "< Atrás",
        "instrucciones_ia": """
        1. Abre **LM Studio**.
        2. Carga el modelo (**Llama 3.2 3B Instruct**).
        3. Ve a la pestaña **Local Server**.
        4. Pon el puerto **2901** y pulsa **START**.
        """,
        "path_label": "Ruta de la caché de Steam:",
        "scan_btn": "Extraer y Traducir Juegos",
        "ai_on": "🟢 Conectado: ",
        "ai_off": "🔴 Desconectado (Revisa puerto 2901)",
    }
}

# ==========================================
# GESTIÓN DE ESTADOS Y CALLBACKS
# ==========================================
if "paso" not in st.session_state: st.session_state.paso = 1
if "idioma" not in st.session_state: st.session_state.idioma = "English"

def avanzar(): st.session_state.paso += 1
def retroceder(): st.session_state.paso -= 1
def actualizar_idioma(): st.session_state.idioma = st.session_state.selector

T = TEXTOS[st.session_state.idioma]

# ==========================================
# FUNCIONES PRINCIPALES (LÓGICA ESTRICTA)
# ==========================================
def check_lm_studio():
    try:
        res = requests.get("http://localhost:2901/v1/models", timeout=1)
        return res.json()["data"][0]["id"] if res.status_code == 200 else None
    except: return None

def procesar_biblioteca(ruta):
    if not os.path.exists(ruta):
        return False, "Error: Folder not found."
    
    # PASO 1: Extraer números (AppIDs) de los nombres y guardar en TXT temporal
    st.info("Paso 1/2: Extrayendo AppIDs de las carpetas...")
    appids_encontrados = set()
    elementos = os.listdir(ruta)
    
    for item in elementos:
        # Busca cualquier número al principio del nombre de la carpeta/archivo
        match = re.search(r'^(\d+)', item)
        if match:
            appids_encontrados.add(match.group(1))
            
    if not appids_encontrados:
        return False, "Error: No AppIDs found in the folder."

    # Guardamos en el temporal
    with open(RUTA_TEMP, "w", encoding="utf-8") as temp_file:
        for aid in appids_encontrados:
            temp_file.write(f"{aid}\n")

    # PASO 2: Leer el temporal y traducir ESTRICTAMENTE a juegos
    st.info("Paso 2/2: Traduciendo AppIDs y filtrando solo juegos...")
    
    with open(RUTA_TEMP, "r", encoding="utf-8") as temp_file:
        lista_ids = [line.strip() for line in temp_file.readlines()]

    juegos_puros = []
    total = len(lista_ids)
    
    barra = st.progress(0)
    texto_progreso = st.empty()

    for i, aid in enumerate(lista_ids):
        try:
            # Consulta a Steam
            url = f"https://store.steampowered.com/api/appdetails?appids={aid}"
            res = requests.get(url, timeout=3).json()
            
            # Filtro Ultra Estricto
            if res and res[str(aid)]["success"]:
                datos = res[str(aid)]["data"]
                # Si no dice exactamente "game", lo ignoramos completamente
                if datos.get("type") == "game":
                    juegos_puros.append(datos["name"])
        except:
            pass # Si la API falla, seguimos
            
        # UI
        barra.progress((i + 1) / total)
        texto_progreso.text(f"Analizados: {i+1}/{total} | Juegos reales encontrados: {len(juegos_puros)}")
        time.sleep(0.4) # Retraso para no saturar la API
        
    # PASO 3: Guardar resultado final
    if juegos_puros:
        with open(RUTA_TXT, "w", encoding="utf-8") as f:
            for juego in sorted(juegos_puros):
                f.write(f"{juego}\n")
        
        # Limpieza del archivo temporal
        if os.path.exists(RUTA_TEMP):
            os.remove(RUTA_TEMP)
            
        return True, f"¡Éxito! {len(juegos_puros)} juegos guardados en tu lista."
    else:
        return False, "No se encontraron juegos válidos tras el filtro."

# ==========================================
# INTERFAZ: WIZARD
# ==========================================

# CONTENEDORES DE PANTALLA
if st.session_state.paso == 1:
    st.title(T["title1"])
    opciones = ["English", "Español"]
    idx = opciones.index(st.session_state.idioma)
    st.selectbox("Language / Idioma", opciones, index=idx, key="selector", on_change=actualizar_idioma)
    st.write("---")

elif st.session_state.paso == 2:
    st.title(T["title2"])
    
    # Diseño compacto en dos columnas para evitar el scroll
    c1, c2 = st.columns([1, 1.5])
    
    with c1:
        st.markdown(T["instrucciones_ia"])
        modelo = check_lm_studio()
        if modelo:
            st.success(f"{T['ai_on']} **{modelo}**")
        else:
            st.error(T["ai_off"])
            if st.button("🔄 Refresh"): st.rerun()
            
    with c2:
        # El vídeo ahora es más pequeño y encaja al lado
        st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ") 
    st.write("---")

elif st.session_state.paso == 3:
    st.title(T["title3"])
    
    ruta_input = st.text_input(T["path_label"], value=r"C:\Program Files (x86)\Steam\appcache\librarycache")
    
    if st.button(T["scan_btn"], type="primary"):
        exito, msj = procesar_biblioteca(ruta_input)
        if exito:
            st.success(msj)
        else:
            st.error(msj)
    st.write("---")

elif st.session_state.paso == 4:
    st.title(T["title4"])
    
    with st.sidebar:
        if st.button("⚙️ Reset App"):
            if os.path.exists(RUTA_TXT): os.remove(RUTA_TXT)
            st.session_state.clear()
            st.rerun()
            
        st.divider()
        if os.path.exists(RUTA_TXT):
            with open(RUTA_TXT, "r", encoding="utf-8") as f:
                juegos = f.readlines()
            st.header(f"🎮 Games ({len(juegos)})")
            with st.expander("View Library"):
                for j in juegos: st.markdown(f"- {j.strip()}")

    if "mensajes" not in st.session_state:
        st.session_state.mensajes = [{"role": "assistant", "content": "Hello! Ask me what you should play today."}]

    for m in st.session_state.mensajes:
        with st.chat_message(m["role"]): st.write(m["content"])

    if prompt := st.chat_input("Type your message here..."):
        st.session_state.mensajes.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)
        
        with st.chat_message("assistant"):
            modelo_activo = check_lm_studio()
            if not modelo_activo:
                st.error("Lost connection to LM Studio.")
            else:
                with open(RUTA_TXT, "r", encoding="utf-8") as f:
                    catalogo = f.read()
                
                sys_prompt = f"""You are a helpful and expert video game sommelier. Your primary language is {st.session_state.idioma}. 
                You MUST select and recommend exactly ONE game from the following list to play today.
                Explain briefly why it's a great choice based on the user's prompt. 
                DO NOT recommend games that are not on this list.
                USER'S GAMES LIST:\n{catalogo}"""
                
                try:
                    mensajes_api = [{"role": "system", "content": sys_prompt}] + st.session_state.mensajes
                    res = requests.post("http://localhost:2901/v1/chat/completions", json={
                        "model": modelo_activo,
                        "messages": mensajes_api,
                        "temperature": 0.7
                    })
                    respuesta = res.json()['choices'][0]['message']['content']
                    st.write(respuesta)
                    st.session_state.mensajes.append({"role": "assistant", "content": respuesta})
                except Exception as e:
                    st.error(f"Error communicating with AI: {e}")

# ==========================================
# FOOTER DE NAVEGACIÓN (BOTONES FIJOS ABAJO)
# ==========================================
if st.session_state.paso < 4:
    col_izq, col_espacio, col_der = st.columns([1, 3, 1])
    
    with col_izq:
        if st.session_state.paso > 1:
            st.button(T["back"], on_click=retroceder, use_container_width=True)
            
    with col_der:
        bloqueado = False
        if st.session_state.paso == 2 and not check_lm_studio(): bloqueado = True
        if st.session_state.paso == 3 and not os.path.exists(RUTA_TXT): bloqueado = True
        
        st.button(T["next"], on_click=avanzar, disabled=bloqueado, type="primary", use_container_width=True)