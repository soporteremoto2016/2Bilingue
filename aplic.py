import streamlit as st
from openai import OpenAI
import os
import speech_recognition as sr
from gtts import gTTS
import tempfile

st.set_page_config(page_title="Chat Pro", page_icon="💬")

# 🔒 API KEY oculta
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 🤖 Personalidad fija (NO visible)
SYSTEM_PROMPT = "Eres un asistente útil, claro y amigable. Respondes en español."

st.title("💬 Chat Inteligente Pro")

# Estado
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar historial
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 🎤 Función voz → texto
def speech_to_text():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Habla ahora...")
        audio = r.listen(source)

    try:
        text = r.recognize_google(audio, language="es-ES")
        return text
    except:
        return "No entendí el audio"

# 🔊 Función texto → voz
def text_to_speech(text):
    tts = gTTS(text=text, lang="es")
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(tmp_file.name)
    return tmp_file.name

# 🌍 Traducción
def traducir(texto, idioma):
    prompt = f"Traduce el siguiente texto al {idioma}: {texto}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

# Botones extra
col1, col2 = st.columns(2)

with col1:
    if st.button("🎤 Hablar"):
        voz = speech_to_text()
        st.session_state.messages.append({"role": "user", "content": voz})
        st.rerun()

with col2:
    if st.button("🌍 Traducir último mensaje"):
        if st.session_state.messages:
            ultimo = st.session_state.messages[-1]["content"]
            traducido = traducir(ultimo, "inglés")
            st.session_state.messages.append({"role": "assistant", "content": traducido})
            st.rerun()

# Input texto
if prompt := st.chat_input("Escribe o usa el micrófono..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                )
                reply = response.choices[0].message.content

                st.write(reply)

                # 🔊 Reproducir voz
                audio_file = text_to_speech(reply)
                st.audio(audio_file)

                st.session_state.messages.append({"role": "assistant", "content": reply})

            except Exception as e:
                st.error(f"Error: {e}")

# Limpiar chat
if st.session_state.messages:
    if st.button("🗑️ Limpiar"):
        st.session_state.messages = []
        st.rerun()
