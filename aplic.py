import streamlit as st
from openai import OpenAI
import json
import re

# ---------------- 1. CONFIGURACIÓN DE PÁGINA ----------------
st.set_page_config(page_title="2Bilingue", page_icon="🌍", layout="centered")

# ---------------- 2. ESTILOS CSS (Fondo azul y Recuadro) ----------------
st.markdown("""
    <style>
    /* Fondo azul cálido para toda la app */
    .stApp {
        background-color: #0D47A1; 
    }
    
    /* Contenedor blanco para el Login (Recuadro) */
    .login-container {
        background-color: white;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0px 8px 16px rgba(0, 0, 0, 0.1);
        margin-top: 20px;
    }
    
    /* Estilo para el título del login */
    .login-header {
        color: #1565C0;
        text-align: center;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------- 3. CONSTANTES Y BASE DE DATOS ----------------
PASSWORD_REQUERIDA = "Seguridad2026*+"

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

def clear_session_data():
    st.session_state.messages = []
    st.session_state.topic = ""
    st.session_state.last_audio_id = None

# ---------------- 4. LÓGICA DE LOGIN ----------------
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    # Centrar el recuadro usando columnas
    col1, col2, col3 = st.columns([0.5, 2, 0.5])
    
    with col2:
        # Inicio del recuadro blanco
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<h1 class="login-header">🔐 Acceso 2Bilingue</h1>', unsafe_allow_html=True)
        
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
        
        # Cierre del recuadro blanco
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ---------------- 5. VALIDACIÓN Y SIDEBAR ----------------
if st.session_state.user not in data:
    st.session_state.user = None
    st.rerun()

user_data = data[st.session_state.user]
stats = user_data["stats"]

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

# ---------------- 6. CONFIGURACIÓN API OPENAI ----------------
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

with st.sidebar:
    st.subheader("🔑 API Key")
    if st.session_state.api_key:
        st.success("Conectada")
        if st.button("Cambiar API Key"):
            st.session_state.api_key = ""
            st.rerun()
    else:
        api_input = st.text_input("Ingresa OpenAI API Key", type="password")
        if st.button("Guardar"):
            st.session_state.api_key = api_input.strip()
            st.rerun()

if not st.session_state.api_key:
    st.warning("Por favor, ingresa una API Key para continuar.")
    st.stop()

client = OpenAI(api_key=st.session_state.api_key)

# ---------------- 7. PROMPT Y TEMA ----------------
SYSTEM_PROMPT = """You are Paty, a professional English teacher. 
Speak English, correct in Spanish. 
Provide a summary with 'Evaluación final' and 'Puntuación general: [0-100]' when finished."""

if "topic" not in st.session_state:
    st.session_state.topic = ""
if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.topic:
    st.title("🌍 2Bilingue Pro")
    tema = st.text_input("🎯 ¿Sobre qué practicamos hoy?")
    if st.button("Comenzar Clase"):
        st.session_state.topic = tema
        st.session_state.messages = [{"role": "assistant", "content": f"Hello! Let's talk about {tema}. What is your level?"}]
        st.rerun()
    st.stop()

# ---------------- 8. CHAT Y PROCESAMIENTO ----------------
st.title("👩‍🏫 Clase con Paty")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = None
audio = st.audio_input("🎤 Habla con Paty")
if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

if audio and id(audio) != st.session_state.last_audio_id:
    st.session_state.last_audio_id = id(audio)
    try:
        with st.spinner("Escuchando..."):
            transcript = client.audio.transcriptions.create(model="whisper-1", file=audio)
            user_input = transcript.text
    except Exception as e:
        st.error(f"Error de audio: {e}")

if not modo_continuo:
    text_input = st.chat_input("Escribe tu mensaje...")
    if text_input: user_input = text_input

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Pensando..."):
                messages = [{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages
                response = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
                reply = response.choices[0].message.content
                st.write(reply)
                
                audio_res = client.audio.speech.create(model="tts-1", voice="nova", input=reply[:4096])
                st.audio(audio_res.content, format="audio/mp3")
                st.session_state.messages.append({"role": "assistant", "content": reply})

                # Actualizar estadísticas si hay evaluación
                if "Evaluación final" in reply:
                    stats["conversaciones"] += 1
                    match = re.search(r'Puntuación general: (\d+)', reply)
                    if match:
                        score = int(match.group(1))
                        n = stats["conversaciones"]
                        stats["promedio"] = int((stats["promedio"] * (n - 1) + score) / n)
                    
                data[st.session_state.user] = user_data
                save_data(data)
        except Exception as e:
            st.error(f"Error: {e}")

# ---------------- 9. BOTONES DE CONTROL ----------------
st.divider()
c1, c2 = st.columns(2)
with c1:
    if st.button("🇪🇸 Traducir última"):
        if st.session_state.messages:
            last = [m for m in st.session_state.messages if m["role"] == "assistant"][-1]["content"]
            res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": f"Traduce: {last}"}])
            st.info(res.choices[0].message.content)
with c2:
    if st.button("🧹 Nuevo Tema"):
        clear_session_data()
        st.rerun()
