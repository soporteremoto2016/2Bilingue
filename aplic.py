import streamlit as st
from openai import OpenAI

# CONFIG
st.set_page_config(
    page_title="2Bilingue Pro",
    page_icon="🌍",
    layout="centered"
)

# ESTILO (modo pro)
st.markdown("""
    <style>
        .stChatMessage {border-radius: 12px;}
        .stButton>button {width: 100%; border-radius: 10px;}
    </style>
""", unsafe_allow_html=True)

# HEADER
st.title("🌍 2Bilingue Pro")
st.caption("Chat inteligente con traducción y voz en tiempo real")

# API KEY
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

with st.sidebar:
    st.header("🔐 Configuración")

    if st.session_state.api_key:
        st.success("✅ API conectada")
    else:
        api_input = st.text_input("API Key", type="password")

        if st.button("Guardar"):
            st.session_state.api_key = api_input
            st.rerun()

# VALIDACIÓN
if not st.session_state.api_key:
    st.warning("👈 Ingresa tu API Key para comenzar")
    st.stop()

client = OpenAI(api_key=st.session_state.api_key)

# PERSONALIDAD
SYSTEM_PROMPT = "Eres un asistente bilingüe experto en inglés y español. Respondes claro, útil y amigable."

# ESTADO CHAT
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 ¡Hola! Soy tu asistente bilingüe. Puedes escribir, hablar o traducir."}
    ]

# MOSTRAR CHAT
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# FUNCION TRADUCCIÓN
def traducir(texto, idioma):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Eres un traductor profesional."},
            {"role": "user", "content": f"Traduce al {idioma}: {texto}"}
        ],
    )
    return response.choices[0].message.content

# VOZ INPUT
audio = st.audio_input("🎤 Habla (opcional)")

if audio:
    with st.spinner("🎧 Procesando audio..."):
        transcript = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=audio
        )
        texto = transcript.text
        st.session_state.messages.append({"role": "user", "content": texto})
        st.rerun()

# BOTONES
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🇪🇸 Español"):
        if st.session_state.messages:
            texto = st.session_state.messages[-1]["content"]
            st.session_state.messages.append({
                "role": "assistant",
                "content": traducir(texto, "español")
            })
            st.rerun()

with col2:
    if st.button("🇺🇸 English"):
        if st.session_state.messages:
            texto = st.session_state.messages[-1]["content"]
            st.session_state.messages.append({
                "role": "assistant",
                "content": traducir(texto, "inglés")
            })
            st.rerun()

with col3:
    if st.button("🧹 Limpiar"):
        st.session_state.messages = []
        st.rerun()

# INPUT TEXTO
if prompt := st.chat_input("💬 Escribe aquí..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("🤖 Pensando..."):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages
            )

            reply = response.choices[0].message.content
            st.write(reply)

            # AUDIO
            audio_response = client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="alloy",
                input=reply
            )

            st.audio(audio_response.content, format="audio/mp3")

            st.session_state.messages.append({"role": "assistant", "content": reply})
