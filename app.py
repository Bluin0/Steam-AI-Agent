import streamlit as st
import os
import requests
import time
import re

# ==========================================
# CONFIGURACIÓN GENERAL
# ==========================================
st.set_page_config(page_title="Steam AI Assistant", page_icon="🎮", layout="centered")

RUTA_TXT = "juegos_filtrados.txt"

# ==========================================
# FUNCIONES DE IA Y RED
# ==========================================
def obtener_modelo_activo():
    """Pregunta a LM Studio qué modelo tiene cargado actualmente."""
    try:
        res = requests.get("http://localhost:2901/v1/models", timeout=2)
        if res.status_code == 200:
            datos = res.json()
            if "data" in datos and len(datos["data"]) > 0:
                return datos["data"][0]["id"]
    except:
        return None
    return None

# ==========================================
# FUNCIONES DEL MOTOR DE ESCANEO (MASIVO)
# ==========================================
def escanear_carpetas_appid(ruta_carpetas):
    if not os.path.exists(ruta_carpetas):
        return False, f"La ruta '{ruta_carpetas}' no existe en tu PC."

    st.info("🔍 Buscando carpetas numéricas (AppIDs)...")
    
    appids_encontrados = []
    for nombre in os.listdir(ruta_carpetas):
        ruta_completa = os.path.join(ruta_carpetas, nombre)
        if os.path.isdir(ruta_completa) and nombre.isdigit():
            appids_encontrados.append(nombre)
            
    if not appids_encontrados:
        return False, "No se han encontrado carpetas de Steam (números) en esa ruta."

    st.info(f"📂 Encontradas {len(appids_encontrados)} carpetas. Consultando a Steam pacientemente...")
    
    juegos_reales = 0
    barra = st.progress(0)
    texto = st.empty()
    
    open(RUTA_TXT, 'w', encoding='utf-8').close()

    for idx, appid in enumerate(appids_encontrados):
        url_steam = f"https://store.steampowered.com/api/appdetails?appids={appid}"
        
        try:
            res = requests.get(url_steam, timeout=5)
            if res.status_code == 200:
                datos = res.json()
                if datos and str(appid) in datos and datos[str(appid)]['success']:
                    info = datos[str(appid)]['data']
                    
                    if info.get('type') == 'game':
                        nombre_juego = info.get('name', 'Desconocido')
                        with open(RUTA_TXT, "a", encoding="utf-8") as f:
                            f.write(f"{appid} == ({nombre_juego})\n")
                        juegos_reales += 1
        except:
            pass 
            
        barra.progress((idx + 1) / len(appids_encontrados))
        texto.text(f"Procesando carpeta: {idx+1}/{len(appids_encontrados)} | Juegos filtrados: {juegos_reales}")
        
        time.sleep(1.5)
        
    return True, f"¡Proceso completado! Se han guardado {juegos_reales} juegos reales."

# ==========================================
# FUNCIÓN: RESET DE FÁBRICA
# ==========================================
def hard_reset():
    """Borra el archivo de texto y limpia la memoria de la sesión para volver al tutorial."""
    if os.path.exists(RUTA_TXT):
        os.remove(RUTA_TXT)
    st.session_state.clear()
    st.rerun()

# ==========================================
# PANTALLA 1: ONBOARDING
# ==========================================
def pantalla_onboarding():
    st.title("👋 ¡Bienvenido a Steam AI Assistant!")
    st.markdown("Configura tu Asistente Personal en 3 pasos.")
    
    with st.expander("1. Instalar LM Studio", expanded=True):
        st.write("Descarga e instala [LM Studio](https://lmstudio.ai/) para procesar la IA de forma local y privada.")
    
    with st.expander("2. Descargar un Modelo", expanded=True):
        st.write("Descarga uno de estos modelos en LM Studio según tu RAM:")
        st.info("**🟢 8GB RAM:** `Llama-3.2-3B-Instruct` o `Qwen2.5-Coder-1.5B`")
        st.warning("**🟡 16GB RAM:** `Llama-3.1-8B-Instruct` o `Qwen2.5-7B`")
        
    with st.expander("3. Encender el Servidor", expanded=True):
        st.markdown("En LM Studio, ve a **Local Server**, carga el modelo y pulsa **Start Server** (Puerto 2901).")

    st.divider()
    st.subheader("Paso Final: Sincronizar Biblioteca (Escaneo Masivo)")
    
    st.caption("Asegúrate de poner la ruta de la carpeta que contiene las subcarpetas con los números (AppIDs).")
    ruta_usuario = st.text_input(
        "Ruta a escanear:", 
        value=r"C:\Program Files (x86)\Steam\appcache\librarycache"
    )
    
    if st.button("🚀 Iniciar Escaneo Paciente (Puede tardar)", type="primary", use_container_width=True):
        with st.spinner("Analizando miles de carpetas pacientemente..."):
            exito, msg = escanear_carpetas_appid(ruta_usuario)
            if exito:
                st.success(msg)
                time.sleep(2)
                st.rerun()
            else:
                st.error(msg)

# ==========================================
# PANTALLA 2: EL CHATBOT
# ==========================================
def pantalla_chatbot():
    st.title("🤖 Asistente de Steam")
    
    modelo_actual = obtener_modelo_activo()
    
    # --- PANEL LATERAL ---
    with st.sidebar:
        if modelo_actual:
            st.success(f"🟢 Conectado a LM Studio\n\nModelo: `{modelo_actual}`")
        else:
            st.error("🔴 LM Studio Desconectado\n\nAbre la app y arranca el Local Server (Puerto 2901).")
            
        st.divider()
        
        # 1. VISOR DE JUEGOS
        st.subheader("Tu Biblioteca")
        if os.path.exists(RUTA_TXT):
            with open(RUTA_TXT, "r", encoding="utf-8") as f:
                lineas = f.readlines()
            if lineas:
                with st.expander(f"Ver los {len(lineas)} juegos"):
                    for linea in lineas:
                        st.text(linea.strip())
            else:
                st.info("Lista vacía.")
                
        st.divider()
        
        # 2. BOTÓN DE RESET PELIGROSO
        st.subheader("Opciones de Sistema")
        st.caption("Si quieres volver a escanear otra carpeta o empezar desde cero, usa este botón.")
        if st.button("🚨 Reset de Fábrica", use_container_width=True):
            hard_reset()

    # --- CHAT PRINCIPAL ---
    with open(RUTA_TXT, "r", encoding="utf-8") as f:
        biblioteca = f.read()

    prompt_sistema = f"""Eres un sumiller de videojuegos experto.
    [BIBLIOTECA DEL USUARIO]
    {biblioteca}
    [FIN]
    Reglas: 
    1. Si pide juego al azar, elige uno de la lista.
    2. Si pide recomendación, busca en la lista. Si no hay, dilo.
    3. PROHIBIDO inventar juegos que no estén en la lista.
    4. Usa los géneros reales de los videojuegos."""

    if "mensajes" not in st.session_state:
        st.session_state.mensajes = [{"role": "system", "content": prompt_sistema}]

    for msg in st.session_state.mensajes:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    pregunta = st.chat_input("Pídele un juego al azar o una recomendación...", disabled=not modelo_actual)

    if pregunta and modelo_actual:
        with st.chat_message("user"): st.markdown(pregunta)
        st.session_state.mensajes.append({"role": "user", "content": pregunta})

        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("Pensando...")
            
            try:
                res = requests.post("http://localhost:2901/v1/chat/completions", json={
                    "model": modelo_actual,
                    "messages": st.session_state.mensajes,
                    "temperature": 0.4,
                    "max_tokens": 800
                })
                if res.status_code == 200:
                    respuesta = res.json()['choices'][0]['message']['content'].strip()
                    placeholder.markdown(respuesta)
                    st.session_state.mensajes.append({"role": "assistant", "content": respuesta})
                else:
                    placeholder.error(f"Error de LM Studio. Código {res.status_code}")
            except:
                placeholder.error("Error de conexión. ¿Se ha apagado LM Studio?")

# ==========================================
# ENRUTADOR DE PANTALLAS
# ==========================================
if not os.path.exists(RUTA_TXT):
    pantalla_onboarding()
else:
    pantalla_chatbot()