import streamlit as st
from openai import OpenAI

# ---------------- CONFIG ----------------
st.set_page_config(page_title="2Bilingue Pro", page_icon="🌍")

# ---------------- ESTADOS ----------------
if "user" not in st.session_state:
    st.session_state.user = None

if "api_key" not in st.session_state:
    st.session_state.api_key = ""

if "messages" not in st.session_state:
    st.session_state.messages = []

if "topic" not in st.session_state:
    st.session_state.topic = ""

if "hablar_activo" not in st.session_state:
    st.session_state.hablar_activo = False

if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

# ---------------- CSS BOTÓN FLOTANTE ----------------
st.markdown("""
<style>
.floating-btn {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background-color: #ff4b4b;
    color: white;
    border-radius: 50%;
    width: 70px;
    height: 70px;
    font-size: 30px;
    text-align: center;
    line-height: 70px;
    cursor: pointer;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
    z-index: 999;
}
</style>
""", unsafe_allow_html=True)

# ---------------- LOGIN ----------------
if not st.session_state.user:
    st.title("🔐 2Bilingue Pro")

    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if user and password:
            st.session_state.user = user
            st.rerun()

    st.stop()

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header(f"👤 {st.session_state.user}")

    if st.button("Cerrar sesión"):
        st.session_state.user = None
        st.rerun()

    st.divider()

    st.subheader("🔑 API Key")

    if st.session_state.api_key:
        st.success("API conectada")
    else:
        api_input = st.text_input("API Key", type="password")
        if st.button("Guardar API Key"):
            st.session_state.api_key = api_input.strip()
            st.rerun()

# ---------------- VALIDACIÓN API ----------------
if not st.session_state.api_key:
    st.warning("Ingresa tu API Key")
    st.stop()

if not st.session_state.api_key.startswith("sk-"):
    st.error("API Key inválida")
    st.stop()

client = OpenAI(api_key=st.session_state.api_key)

# ---------------- SYSTEM PROMPT ----------------
SYSTEM_PROMPT = """
You are Lucy, a professional English teacher.

- Speak ONLY in English
- Correct mistakes in Spanish
"""

# ---------------- TEMA ----------------
if not st.session_state.topic:
    st.title("🌍 2Bilingue Pro")
    tema = st.text_input("🎯 Tema para practicar")

    if st.button("Comenzar"):
        st.session_state.topic = tema
        st.session_state.messages = [
            {"role": "assistant", "content": f"Great! Let's talk about {tema} 😊"}
        ]
        st.rerun()

    st.stop()

# ---------------- CHAT ----------------
st.title("🎧 Lucy - Conversación hablada")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ---------------- BOTÓN FLOTANTE ----------------
clicked = st.button("🎤", key="floating_btn")

if clicked:
    st.session_state.hablar_activo = True

# ---------------- AUDIO ----------------
user_input = None

if st.session_state.hablar_activo:
    st.warning("🎧 Habla ahora...")

    audio = st.audio_input("Grabar voz")

    if audio:
        current_id = str(audio)

        if current_id != st.session_state.last_audio_id:
            st.session_state.last_audio_id = current_id

            with st.spinner("Transcribiendo..."):
                transcript = client.audio.transcriptions.create(
                    model="gpt-4o-mini-transcribe",
                    file=audio
                )

            user_input = transcript.text
            st.session_state.hablar_activo = False

# ---------------- TEXTO ----------------
text_input = st.chat_input("O escribe aquí...")
if text_input:
    user_input = text_input

# ---------------- PROCESAR ----------------
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("Lucy responde..."):

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "system", "content": f"Topic: {st.session_state.topic}"}
            ] + st.session_state.messages

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )

            reply = response.choices[0].message.content
            st.write(reply)

            audio_response = client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="alloy",
                input=reply
            )

            st.audio(audio_response.content, format="audio/mp3")

            st.session_state.messages.append({"role": "assistant", "content": reply})

# ---------------- LIMPIAR ----------------
if st.button("🧹 Limpiar conversación"):
    st.session_state.messages = []
    st.rerun()
