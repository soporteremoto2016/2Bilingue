import streamlit as st
from openai import OpenAI
import json
import re

# ---------------- CONFIG ----------------
st.set_page_config(page_title="2Bilingue Pro", page_icon="🌍", layout="centered")

# ---------------- CONSTANTES ----------------
PASSWORD_REQUERIDA = "Seguridad2026*+"

# ---------------- BASE DE DATOS ----------------
def load_data():
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f)

data = load_data()

# --- FUNCIÓN PARA LIMPIAR SESIÓN AL CAMBIAR DE USUARIO ---
def clear_session_data():
    st.session_state.messages = []
    st.session_state.topic = ""
    st.session_state.last_audio_id = None

# ---------------- LOGIN ----------------
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("🔐 Acceso 2Bilingue Pro")
    st.info(f"Nota: Se requiere la contraseña de acceso autorizada.")
    
    user = st.text_input("Nombre de Usuario")
    password = st.text_input("Contraseña de Seguridad", type="password")

    if st.button("Ingresar"):
        user = user.strip()
        
        # VALIDACIÓN DE CONTRASEÑA MAESTRA
        if password != PASSWORD_REQUERIDA:
            st.error("Contraseña de seguridad incorrecta. Acceso denegado.")
        elif not user:
            st.warning("Por favor, ingresa un nombre de usuario.")
        else:
            # Si el usuario ya existe, entramos. Si no, lo creamos con esa contraseña.
            if user not in data:
                data[user] = {
                    "password": PASSWORD_REQUERIDA,
                    "stats": {"conversaciones": 0, "promedio": 0, "nivel": "A1"},
                    "errores": []
                }
                save_data(data)
                st.success(f"Usuario '{user}' registrado exitosamente.")
            
            # Limpiar rastro de sesiones anteriores y loguear
            clear_session_data()
            st.session_state.user = user
            st.rerun()
    st.stop()

# ---------------- VALIDACIÓN DE SEGURIDAD ----------------
if st.session_state.user not in data:
    st.session_state.user = None
    st.rerun()

user_data = data[st.session_state.user]
stats = user_data["stats"]

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header(f"👤 {st.session_state.user}")
    st.subheader("📊 Mi Progreso")
    st.metric("Conversaciones", stats["conversaciones"])
    st.metric("Nivel Actual", stats["nivel"])
    st.metric("Promedio", f'{stats["promedio"]}%')

    if st.button("Cerrar sesión"):
        clear_session_data()
        st.session_state.user = None
        st.rerun()

    st.divider()
    modo_continuo = st.toggle("🎧 Modo conversación continua", value=True)

# ---------------- API KEY ----------------
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

with st.sidebar:
    st.subheader("🔑 Configuración API")
    if st.session_state.api_key:
        st.success("Conexión activa")
        if st.button("Cambiar API Key"):
            st.session_state.api_key = ""
            st.rerun()
    else:
        api_input = st.text_input("OpenAI API Key", type="password")
        if st.button("Validar y Guardar"):
            st.session_state.api_key = api_input.strip()
            st.rerun()

if not st.session_state.api_key:
    st.warning("Ingresa tu API Key para activar a Paty.")
    st.stop()

client = OpenAI(api_key=st.session_state.api_key)

# ---------------- SYSTEM PROMPT (PATY) ----------------
SYSTEM_PROMPT = """
You are Paty, a professional English teacher for Spanish speakers.
Eres una profesora de (Ingles - Español) especializada en educar a personas desde el nivel A1 hasta C2.
- Siempre habla en inglés para la conversación.
- Si detectas errores, detente y corrígelos en ESPAÑOL de forma amable.
- Empieza preguntando el nivel de inglés (A1-C2) para ajustar tu vocabulario.
- Al final de la sesión (si dicen 'finalizar'), entrega un reporte detallado.

Format for corrections:
Corrección:
- Error:
- Corrección:
- Explicación:
"""

# ---------------- TEMA DE PRÁCTICA ----------------
if "topic" not in st.session_state:
    st.session_state.topic = ""

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.topic:
    st.title("🌍 2Bilingue Pro")
    tema = st.text_input("🎯 ¿Qué tema te gustaría practicar hoy con Paty?")
    if st.button("Comenzar Clase"):
        st.session_state.topic = tema
        st.session_state.messages = [
            {"role": "assistant", "content": f"Hello! I'm Paty. I'm excited to practice '{tema}' with you. To start, what is your current English level?"}
        ]
        st.rerun()
    st.stop()

# ---------------- INTERFAZ DE CHAT ----------------
st.title("👩‍🏫 Clase con Paty")
st.caption(f"Tema actual: {st.session_state.topic}")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ---------------- ENTRADA (AUDIO O TEXTO) ----------------
user_input = None
audio = st.audio_input("🎤 Presiona para hablar")

if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

if audio:
    if id(audio) != st.session_state.last_audio_id:
        st.session_state.last_audio_id = id(audio)
        try:
            with st.spinner("Paty te está escuchando..."):
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio)
                user_input = transcript.text
        except Exception as e:
            st.error(f"Error procesando audio: {e}")

if not modo_continuo:
    text_input = st.chat_input("Escribe tu mensaje aquí...")
    if text_input:
        user_input = text_input

# ---------------- LÓGICA DE RESPUESTA ----------------
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.
