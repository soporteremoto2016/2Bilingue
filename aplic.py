import streamlit as st
from openai import OpenAI
import os

# Config
st.set_page_config(page_title="2Bilingue Pro", page_icon="🌍")

# Cliente OpenAI
client = OpenAI(api_key=os.getenv("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"))

# Personalidad fija
SYSTEM_PROMPT = "Eres un asistente bilingüe experto en inglés y español. Ayudas a traducir, conversar y explicar claramente."

st.title("🌍 2Bilingue Pro")

# Estado
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar historial
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 🌍 Traducción
def traducir(texto, idioma):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un traductor experto."},
                {"role": "user", "content": f"Traduce al {idioma}: {texto}"}
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error en traducción: {e}"

# 🎤 Voz (Streamlit compatible)
audio = st.audio_input("🎤 Habla aquí")

if audio:
    try:
        with st.spinner("Transcribiendo..."):
            transcript = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio
            )
            prompt = transcript.text

            st.session_state.messages.append({"role": "user", "content": prompt})
            st.rerun()
    except Exception as e:
        st.error(f"Error de audio: {e}")

# 🌍 Botones traducción
col1, col2 = st.columns(2)

with col1:
    if st.button("🇪🇸 Español"):
        if st.session_state.messages:
            texto = st.session_state.messages[-1]["content"]
            resultado = traducir(texto, "español")
            st.session_state.messages.append({"role": "assistant", "content": resultado})
            st.rerun()

with col2:
    if st.button("🇺🇸 English"):
        if st.session_state.messages:
            texto = st.session_state.messages[-1]["content"]
            resultado = traducir(texto, "inglés")
            st.session_state.messages.append({"role": "assistant", "content": resultado})
            st.rerun()

# 💬 Input texto
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

                # 🔊 AUDIO REAL con OpenAI
                audio_response = client.audio.speech.create(
                    model="gpt-4o-mini-tts",
                    voice="alloy",
                    input=reply
                )

                st.audio(audio_response.content, format="audio/mp3")

                st.session_state.messages.append({"role": "assistant", "content": reply})

            except Exception as e:
                st.error(f"Error: {e}")

# 🧼 Limpiar
if st.session_state.messages:
    if st.button("🗑️ Limpiar conversación"):
        st.session_state.messages = []
        st.rerun()
