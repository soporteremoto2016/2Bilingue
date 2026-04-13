import streamlit as st
from openai import OpenAI
import json
import re

# ---------------- CONFIG ----------------
st.set_page_config(page_title="2Bilingue Pro", page_icon="🌍")

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

# ---------------- LOGIN ----------------
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("🔐 2Bilingue Pro")

    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if user in data:
            if data[user]["password"] == password:
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
        else:
            data[user] = {
                "password": password,
                "stats": {"conversaciones": 0, "promedio": 0, "nivel": "A1"},
                "errores": []
            }
            save_data(data)
            st.success("Usuario creado")
            st.session_state.user = user
            st.rerun()

    st.stop()

# ---------------- USUARIO ----------------
user_data = data[st.session_state.user]
stats = user_data["stats"]

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header(f"👤 {st.session_state.user}")

    st.subheader("📊 Progreso")
    st.metric("Conversaciones", stats["conversaciones"])
    st.metric("Nivel", stats["nivel"])
    st.metric("Promedio", f'{stats["promedio"]}%')

    if st.button("Cerrar sesión"):
        st.session_state.user = None
        st.rerun()

    st.divider()
    modo_continuo = st.toggle("🎧 Modo conversación continua", value=True)

# ---------------- API KEY ----------------
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

with st.sidebar:
    st.subheader("🔑 API Key")

    if st.session_state.api_key:
        st.success("API conectada")
        if st.button("Cambiar API Key"):
            st.session_state.api_key = ""
            st.rerun()
    else:
        api_input = st.text_input("API Key", type="password")
        if st.button("Guardar API Key"):
            st.session_state.api_key = api_input.strip()
            st.rerun()

if not st.session_state.api_key:
    st.warning("Ingresa tu API Key para continuar")
    st.stop()

# Inicialización segura del cliente
client = OpenAI(api_key=st.session_state.api_key)

# ---------------- SYSTEM PROMPT ----------------
SYSTEM_PROMPT = """
You are Lucy, a professional English teacher for Spanish speakers.
- Always speak in English.
- Correct errors in Spanish.

Format:
Corrección:
- Error:
- Corrección:
- Explicación:

If user says "finalizar":
📊 Evaluación final:
- Fluidez: %
- Gramática: %
- Vocabulario: %
- Puntuación general: %
🧠 Nivel estimado:
📈 Recomendaciones:
"""

# ---------------- TEMA ----------------
if "topic" not in st.session_state:
    st.session_state.topic = ""

if not st.session_state.topic:
    st.title("🌍 2Bilingue Pro")
    tema = st.text_input("🎯 Tema para practicar")

    if st.button("Comenzar"):
        st.session_state.topic = tema
        st.session_state.messages = [
            {"role": "assistant", "content": f"Great! Let's talk about {tema}. 😊"}
        ]
        st.rerun()
    st.stop()

# ---------------- CHAT INTERFACE ----------------
st.title("🌍 2Bilingue Pro - Lucy 👩‍🏫")
st.info(f"Tema actual: **{st.session_state.topic}**")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ---------------- INPUT LOGIC ----------------
user_input = None

# 🎤 AUDIO
audio = st.audio_input("🎤 Habla")

if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

if audio:
    current_audio_id = id(audio) # Usamos id para detectar cambio de archivo
    if current_audio_id != st.session_state.last_audio_id:
        st.session_state.last_audio_id = current_audio_id
        try:
            with st.spinner("🎧 Transcribiendo..."):
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio
                )
                user_input = transcript.text
        except Exception as e:
            st.error(f"Error en transcripción: {e}")

# 💬 TEXTO
if not modo_continuo:
    text_input = st.chat_input("Escribe en inglés...")
    if text_input:
        user_input = text_input

# ---------------- PROCESAR ----------------
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Lucy responde..."):
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "system", "content": f"Topic: {st.session_state.topic}"}
                ] + st.session_state.messages

                # Chat Completion
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages
                )
                reply = response.choices[0].message.content
                st.write(reply)

                # Text-to-Speech
                audio_response = client.audio.speech.create(
                    model="tts-1",
                    voice="alloy",
                    input=reply
                )
                st.audio(audio_response.content, format="audio/mp3")

                st.session_state.messages.append({"role": "assistant", "content": reply})

                # Lógica de guardado y stats
                if "Corrección:" in reply:
                    user_data["errores"].append(reply)

                if "Evaluación final" in reply:
                    stats["conversaciones"] += 1
                    match = re.search(r'Puntuación general: (\d+)', reply)
                    if match:
                        score = int(match.group(1))
                        prev = stats["promedio"]
                        n = stats["conversaciones"]
                        stats["promedio"] = int((prev * (n - 1) + score) / n)
                        
                        # Actualizar nivel
                        if score < 40: stats["nivel"] = "A1"
                        elif score < 60: stats["nivel"] = "A2"
                        elif score < 75: stats["nivel"] = "B1"
                        elif score < 90: stats["nivel"] = "B2"
                        else: stats["nivel"] = "C1"

                data[st.session_state.user] = user_data
                save_data(data)
                
        except Exception as e:
            st.error(f"Hubo un problema con la API: {e}")

# ---------------- BOTONES ----------------
st.divider()
col1, col2 = st.columns(2)

with col1:
    if st.button("🇪🇸 Traducir última respuesta"):
        if st.session_state.messages:
            last_msg = [m for m in st.session_state.messages if m["role"] == "assistant"][-1]["content"]
            try:
                traducido = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": f"Traduce al español: {last_msg}"}]
                )
                st.info(traducido.choices[0].message.content)
            except:
                st.error("No se pudo traducir.")

with col2:
    if st.button("🧹 Limpiar Chat"):
        st.session_state.messages = []
        st.rerun()
