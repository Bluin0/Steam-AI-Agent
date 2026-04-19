import streamlit as st
import os
import sys
import requests
import time
import re
import json

# ==========================================
# CONFIGURACIÓN GENERAL Y RUTAS SEGURAS
# ==========================================
st.set_page_config(page_title="Steam AI Assistant", page_icon="🎮", layout="centered")

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Carpeta secreta en AppData (Escritorio limpio)
APPDATA_DIR = os.path.join(os.getenv('APPDATA'), "SteamAIAssistant")
os.makedirs(APPDATA_DIR, exist_ok=True)
DB_PATH = os.path.join(APPDATA_DIR, "biblioteca.json")

# ==========================================
# DICCIONARIO MULTI-IDIOMA
# ==========================================
TEXTOS = {
    "English": {
        "title1": "Welcome to Steam AI Assistant",
        "title2": "🧠 Connect LM Studio",
        "title3": "📂 Smart Library Sync",
        "title4": "🤖 Your Personal Sommelier",
        "next": "Next >",
        "back": "< Back",
        "instrucciones_ia": "1. Open **LM Studio**.\n2. Load **Llama 3.2 3B Instruct**.\n3. In **Local Server**, set port **2901** and click START.",
        "ai_on": "🟢 Online: ",
        "ai_off": "🔴 Offline (Check port 2901)",
        "scan_new": "Scan New Games",
        "scan_full": "Force Full Rescan",
        "go_chat": "Go to Chat",
    },
    "Español": {
        "title1": "Bienvenido a Steam AI Assistant",
        "title2": "🧠 Conectar LM Studio",
        "title3": "📂 Sincronización Inteligente",
        "title4": "🤖 Tu Sumiller Personal",
        "next": "Siguiente >",
        "back": "< Atrás",
        "instrucciones_ia": "1. Abre **LM Studio**.\n2. Carga **Llama 3.2 3B Instruct**.\n3. En **Local Server**, pon puerto **2901** y pulsa START.",
        "ai_on": "🟢 Conectado: ",
        "ai_off": "🔴 Desconectado (Revisa puerto 2901)",
        "scan_new": "Buscar Juegos Nuevos",
        "scan_full": "Forzar Escaneo Completo",
        "go_chat": "Ir al Chat directamente",
    }
}

# ==========================================
# GESTIÓN DE ESTADOS
# ==========================================
if "paso" not in st.session_state: st.session_state.paso = 1
if "idioma" not in st.session_state: st.session_state.idioma = "English"

def avanzar(): st.session_state.paso += 1
def retroceder(): st.session_state.paso -= 1
def actualizar_idioma(): st.session_state.idioma = st.session_state.selector

T = TEXTOS[st.session_state.idioma]

# ==========================================
# FUNCIONES NÚCLEO (BBDD Y STEAM API)
# ==========================================
def check_lm_studio():
    try:
        res = requests.get("http://localhost:2901/v1/models", timeout=1)
        return res.json()["data"][0]["id"] if res.status_code == 200 else None
    except: return None

def cargar_db():
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "r", encoding="utf-8") as f: return json.load(f)
    return {}

def guardar_db(datos):
    with open(DB_PATH, "w", encoding="utf-8") as f: json.dump(datos, f, ensure_ascii=False, indent=4)

def escaneo_inteligente(ruta, escaneo_completo=False):
    if not os.path.exists(ruta): return False, "Carpeta no encontrada."
    
    db_actual = cargar_db() if not escaneo_completo else {}
    appids_carpeta = set()
    
    # 1. Leer AppIDs físicos
    for item in os.listdir(ruta):
        match = re.search(r'^(\d+)', item)
        if match: appids_carpeta.add(match.group(1))
            
    # 2. Filtrar solo los nuevos (Diferencial)
    appids_nuevos = [aid for aid in appids_carpeta if aid not in db_actual]
    
    if not appids_nuevos:
        return True, "Tu biblioteca ya está 100% actualizada."

    # 3. Consultar a Steam (Con Anti-Baneo)
    contenedor_ui = st.empty()
    barra = st.progress(0)
    
    nuevos_guardados = 0
    for i, aid in enumerate(appids_nuevos):
        exito = False
        intentos = 0
        while not exito and intentos < 3:
            try:
                res = requests.get(f"https://store.steampowered.com/api/appdetails?appids={aid}", timeout=5)
                if res.status_code == 429:
                    contenedor_ui.warning(f"Steam pide una pausa. Esperando 10 segundos... ({i}/{len(appids_nuevos)})")
                    time.sleep(10)
                    intentos += 1
                    continue
                
                datos_api = res.json()
                if datos_api and datos_api[str(aid)]["success"]:
                    datos_juego = datos_api[str(aid)]["data"]
                    if datos_juego.get("type") == "game":
                        generos = [g["description"] for g in datos_juego.get("genres", [])][:5]
                        db_actual[aid] = {
                            "name": datos_juego["name"],
                            "genres": generos
                        }
                        nuevos_guardados += 1
                exito = True
            except: exito = True
            
        barra.progress((i + 1) / len(appids_nuevos))
        contenedor_ui.info(f"Analizando nuevos: {i+1}/{len(appids_nuevos)} | Guardados: {nuevos_guardados}")
        time.sleep(0.5)

    guardar_db(db_actual)
    contenedor_ui.empty()
    barra.empty()
    return True, f"¡Actualizado! Se han añadido {nuevos_guardados} juegos nuevos."

# ==========================================
# INTERFAZ WIZARD
# ==========================================

if st.session_state.paso == 1:
    st.title(T["title1"])
    opciones = ["English", "Español"]
    idx = opciones.index(st.session_state.idioma)
    st.selectbox("Language / Idioma", opciones, index=idx, key="selector", on_change=actualizar_idioma)
    st.write("---")

elif st.session_state.paso == 2:
    st.title(T["title2"])
    c1, c2 = st.columns([1, 1.5])
    with c1:
        st.markdown(T["instrucciones_ia"])
        modelo = check_lm_studio()
        if modelo: st.success(f"{T['ai_on']} **{modelo}**")
        else:
            st.error(T["ai_off"])
            if st.button("🔄 Refresh"): st.rerun()
    with c2: st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ") 
    st.write("---")

elif st.session_state.paso == 3:
    st.title(T["title3"])
    ruta_input = st.text_input("Ruta / Path:", value=r"C:\Program Files (x86)\Steam\appcache\librarycache")
    db = cargar_db()
    
    if db:
        st.success(f"✅ Se han detectado **{len(db)} juegos** en tu base de datos.")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button(T["go_chat"], type="primary", use_container_width=True): avanzar()
        with c2:
            if st.button(T["scan_new"], use_container_width=True):
                exito, msj = escaneo_inteligente(ruta_input)
                if exito: st.success(msj)
        with c3:
            if st.button(T["scan_full"], use_container_width=True):
                exito, msj = escaneo_inteligente(ruta_input, escaneo_completo=True)
                if exito: st.success(msj)
    else:
        st.info("No hay base de datos. Necesitamos hacer un escaneo inicial.")
        if st.button("Escanear Biblioteca (Puede tardar)", type="primary"):
            exito, msj = escaneo_inteligente(ruta_input)
            if exito: st.success(msj)
    st.write("---")

elif st.session_state.paso == 4:
    st.title(T["title4"])
    db = cargar_db()
    
    with st.sidebar:
        if st.button("⚙️ Reset Completo"):
            if os.path.exists(DB_PATH): os.remove(DB_PATH)
            st.session_state.clear()
            st.rerun()
        st.divider()
        st.header(f"🎮 {len(db)} Juegos")
        with st.expander("Ver Base de Datos"):
            for aid, data in db.items(): 
                st.markdown(f"- **{data['name']}** *( {', '.join(data['genres'])} )*")

    # Botones de Ánimo Rápidos
    cols_animo = st.columns(4)
    if cols_animo[0].button("🔥 Acción rápida"): st.session_state.anim_prompt = "Quiero un juego de pura acción y adrenalina."
    if cols_animo[1].button("😌 Relax absoluto"): st.session_state.anim_prompt = "Quiero algo tranquilo para relajarme hoy."
    if cols_animo[2].button("🧠 Pensar y gestionar"): st.session_state.anim_prompt = "Me apetece un juego de estrategia o gestión."
    if cols_animo[3].button("📖 Buena historia"): st.session_state.anim_prompt = "Recomiéndame un juego con una narrativa increíble."

    if "mensajes" not in st.session_state:
        st.session_state.mensajes = [{"role": "assistant", "content": "¡Hola! Dime cómo te sientes hoy o usa los botones de arriba para que busque la mejor opción en tu biblioteca."}]

    for m in st.session_state.mensajes:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    prompt = st.chat_input("Escribe aquí a qué te apetece jugar...")
    if "anim_prompt" in st.session_state:
        prompt = st.session_state.anim_prompt
        del st.session_state.anim_prompt

    if prompt:
        st.session_state.mensajes.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            modelo_activo = check_lm_studio()
            if not modelo_activo: st.error("Sin conexión a LM Studio. Revisa el puerto 2901.")
            else:
                catalogo_texto = "\n".join([f"ID: {aid} | Nombre: {d['name']} | Géneros: {', '.join(d['genres'])}" for aid, d in db.items()])
                
                sys_prompt = f"""Eres un carismático, amigable y experto sommelier de videojuegos. Tu idioma principal es {st.session_state.idioma}.
                Esta es la biblioteca de juegos del usuario, con sus géneros:
                {catalogo_texto}
                
                INSTRUCCIONES VITALES:
                1. Recomienda SOLO UN JUEGO de la lista que encaje con lo que pide el usuario.
                2. ¡HÁBLALE AL USUARIO! Escribe un párrafo entusiasta explicando detalladamente por qué ese juego es perfecto para su estado de ánimo hoy, basándote en los géneros del juego.
                3. OBLIGATORIO: Tu mensaje debe terminar SIEMPRE con el ID del juego entre corchetes.
                
                EJEMPLO DE CÓMO DEBES RESPONDER SIEMPRE:
                "¡Tengo la opción perfecta para ti! Sabiendo que buscas algo relajante, te recomiendo encarecidamente **Stardew Valley**. Es un juego de simulación donde podrás gestionar tu granja a tu propio ritmo, plantar cultivos y olvidarte del estrés. ¡Justo lo que necesitas hoy!"
                [413150]
                """
                
                try:
                    res = requests.post("http://localhost:2901/v1/chat/completions", json={
                        "model": modelo_activo,
                        "messages": [{"role": "system", "content": sys_prompt}] + st.session_state.mensajes,
                        "temperature": 0.7
                    })
                    respuesta = res.json()['choices'][0]['message']['content']
                    
                    match = re.search(r'\[(\d+)\]', respuesta)
                    texto_limpio = re.sub(r'\[\d+\]', '', respuesta).strip()
                    
                    if not texto_limpio and match:
                        texto_limpio = "¡Aquí tienes mi recomendación perfecta para lo que buscas hoy! Espero que lo disfrutes."
                    
                    st.markdown(texto_limpio)
                    if match:
                        appid = match.group(1)
                        st.image(f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/header.jpg", use_container_width=True)
                    
                    st.session_state.mensajes.append({"role": "assistant", "content": texto_limpio})
                except Exception as e: st.error("Error al comunicar con la IA.")

# ==========================================
# FOOTER DE NAVEGACIÓN
# ==========================================
if st.session_state.paso < 4:
    c_izq, c_esp, c_der = st.columns([1, 3, 1])
    with c_izq:
        if st.session_state.paso > 1: st.button(T["back"], on_click=retroceder, use_container_width=True)
    with c_der:
        bloqueado = False
        if st.session_state.paso == 2 and not check_lm_studio(): bloqueado = True
        if st.session_state.paso == 3 and not cargar_db(): bloqueado = True
        st.button(T["next"], on_click=avanzar, disabled=bloqueado, type="primary", use_container_width=True)