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

If user says "finalizar":

📊 Evaluación final:
- Fluidez: %
- Gramática: %
- Vocabulario: %
- Puntuación general: %
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
st.info("Habla con Lucy usando el botón 🎤 después de cada respuesta")

for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

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

            # 🔊 AUDIO RESPUESTA
            audio_response = client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="alloy",
                input=reply
            )

            st.audio(audio_response.content, format="audio/mp3")

            # 👉 BOTÓN DINÁMICO PARA HABLAR
            if st.button("🎤 Responder hablando", key=f"btn_{len(st.session_state.messages)}"):
                st.session_state.hablar_activo = True
                st.rerun()

            st.session_state.messages.append({"role": "assistant", "content": reply})

# ---------------- BOTONES EXTRA ----------------
col1, col2 = st.columns(2)

with col1:
    if st.button("🇪🇸 Traducir último"):
        if st.session_state.messages:
            texto = st.session_state.messages[-1]["content"]
            traducido = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"Traduce al español: {texto}"}]
            )
            st.session_state.messages.append({
                "role": "assistant",
                "content": traducido.choices[0].message.content
            })
            st.rerun()

with col2:
    if st.button("🧹 Limpiar"):
        st.session_state.messages = []
        st.rerun()
