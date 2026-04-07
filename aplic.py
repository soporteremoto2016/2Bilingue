import streamlit as st
from openai import OpenAI

# Configuración
st.set_page_config(page_title="2Bilingue Pro", page_icon="🌍")

st.title("🌍 2Bilingue Pro")

# 🔑 API KEY (usuario)
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

with st.sidebar:
    st.header("🔐 Configuración")

    if st.session_state.api_key:
        st.success("✅ API Key cargada")
    else:
        api_input = st.text_input("API Key de OpenAI", type="password")

        if st.button("Guardar API Key"):
            st.session_state.api_key = api_input
            st.rerun()

# Validación
if not st.session_state.api_key:
    st.warning("⚠️ Ingresa tu API Key para usar la app")
    st.stop()

# Cliente OpenAI
client = OpenAI(api_key=st.session_state.api_key)

# 🤖 Personalidad fija
SYSTEM_PROMPT = "Eres un asistente bilingüe experto en inglés y español. Ayudas a traducir, conversar y explicar claramente."

# Estado chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar historial
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 🌍 Función traducción
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
        return f"Error: {e}"

# 🎤 Entrada por voz
audio = st.audio_input("🎤 Habla aquí")

if audio:
    try:
        with st.spinner("Transcribiendo..."):
            transcript = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio
            )
            texto = transcript.text

            st.session_state.messages.append({"role": "user", "content": texto})
            st.rerun()
    except Exception as e:
        st.error(f"Error de audio: {e}")

# 🌍 Botones de traducción
col1, col2 = st.columns(2)

with col1:
    if st.button("🇪🇸 Traducir a Español"):
        if st.session_state.messages:
            texto = st.session_state.messages[-1]["content"]
            resultado = traducir(texto, "español")
            st.session_state.messages.append({"role": "assistant", "content": resultado})
            st.rerun()

with col2:
    if st.button("🇺🇸 Translate to English"):
        if st.session_state.messages:
            texto = st.session_state.messages[-1]["content"]
            resultado = traducir(texto, "inglés")
            st.session_state.messages.append({"role": "assistant", "content": resultado})
            st.rerun()

# 💬 Input de texto
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

                # 🔊 Audio con OpenAI
                audio_response = client.audio.speech.create(
                    model="gpt-4o-mini-tts",
                    voice="alloy",
                    input=reply
                )

                st.audio(audio_response.content, format="audio/mp3")

                st.session_state.messages.append({"role": "assistant", "content": reply})

            except Exception as e:
                st.error(f"Error: {e}")

# 🧼 Limpiar conversación
if st.session_state.messages:
    if st.button("🗑️ Limpiar conversación"):
        st.session_state.messages = []
        st.rerun()
