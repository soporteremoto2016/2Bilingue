import streamlit as st
from openai import OpenAI
import json
import re

# ---------------- CONFIG ----------------
st.set_page_config(page_title="2Bilingue", page_icon="🌍", layout="centered")

# --- ESTILOS PERSONALIZADOS (Azul cálido y Recuadro) ---
st.markdown("""
    <style>
    /* Fondo de la aplicación */
    .stApp {
        background-color: #E3F2FD; /* Azul cálido muy claro */
    }
    
    /* Contenedor del Login */
    .login-box {
        background-color: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0px 4px 20px rgba(0, 0, 0, 0.1);
        margin-top: -50px;
    }
    
    /* Ajuste de títulos dentro del login */
    .login-title {
        color: #1E88E5;
        text-align: center;
        font-family: 'Helvetica Neue', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

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

# --- FUNCIÓN PARA LIMPIAR SESIÓN ---
def clear_session_data():
    st.session_state.messages = []
    st.session_state.topic = ""
    st.session_state.last_audio_id = None

# ---------------- LOGIN ----------------
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    # Usamos un contenedor de columnas para centrar el recuadro
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown('<h1 class="login-title">🔐 Acceso 2Bilingue</h1>', unsafe_allow_html=True)
        
        user = st.text_input("Nombre de Usuario")
        password = st.text_input("Contraseña de Seguridad", type="password")

        if st.button("Ingresar", use_container_width=True):
            user = user.strip()
            if password != PASSWORD_REQUERIDA:
                st.error("Contraseña de seguridad incorrecta.")
            elif not user:
                st.warning("Por favor, ingresa un nombre de usuario.")
            else:
                if user not in data:
                    data[user] = {
                        "password": PASSWORD_REQUERIDA,
                        "stats": {"conversaciones": 0, "promedio": 0, "nivel": "A1"},
                        "errores": []
                    }
                    save_data(data)
                
                clear_session_data()
                st.session_state.user = user
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ---------------- VALIDACIÓN DE USUARIO ----------------
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

# ---------------- SYSTEM PROMPT ----------------
SYSTEM_PROMPT = """
You are Paty, a professional English teacher for Spanish speakers.
- Speak in English for the conversation.
- If the user makes a mistake, correct it in SPANISH.
- Always ask for the English level (A1-C2) at the beginning.
- Provide fluency and error statistics.

Format for corrections:
Corrección:
- Error:
- Corrección:
- Explicación:
"""

# ---------------- TEMA ----------------
if "topic" not in st.session_state:
    st.session_state.topic = ""
if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.topic:
    st.title("🌍 2Bilingue")
    tema = st.text_input("🎯 ¿Qué tema te gustaría practicar hoy?")
    if st.button("Comenzar Clase"):
        st.session_state.topic = tema
        st.session_state.messages = [
            {"role": "assistant", "content": f"Hello! I'm Paty. Let's talk about {tema}. What is your level (A1-C2)?"}
        ]
        st.rerun()
    st.stop()

# ---------------- CHAT ----------------
st.title("👩‍🏫 Clase con Paty")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ---------------- ENTRADA ----------------
user_input = None
audio = st.audio_input("🎤 Habla con Paty")

if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

if audio:
    if id(audio) != st.session_state.last_audio_id:
        st.session_state.last_audio_id = id(audio)
        try:
            with st.spinner("Paty escucha..."):
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio)
                user_input = transcript.text
        except Exception as e:
            st.error(f"Error: {e}")

if not modo_continuo:
    text_input = st.chat_input("Escribe aquí...")
    if text_input:
        user_input = text_input

# ---------------- PROCESAR ----------------
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Respondiendo..."):
                full_messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "system", "content": f"Topic: {st.session_state.topic}"}
                ] + st.session_state.messages

                response = client.chat.completions.create(model="gpt-4o-mini", messages=full_messages)
                reply = response.choices[0].message.content
                st.write(reply)

                # Audio
                audio_res = client.audio.speech.create(model="tts-1", voice="nova", input=reply[:4096])
                st.audio(audio_res.content, format="audio/mp3")
                st.session_state.messages.append({"role": "assistant", "content": reply})

                # Stats y Guardado
                if "Corrección:" in reply:
                    user_data["errores"].append(reply)
                
                data[st.session_state.user] = user_data
                save_data(data)
        except Exception as e:
