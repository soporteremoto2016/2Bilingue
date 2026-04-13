import streamlit as st
from openai import OpenAI
import json
import re

# ---------------- CONFIG ----------------
st.set_page_config(page_title="2Bilingue Pro", page_icon="🌍", layout="centered")

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
        user = user.strip()
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

# ---------------- VALIDACIÓN DE SEGURIDAD (CORRIGE EL KEYERROR) ----------------
# Si por alguna razón el usuario no está en data, cerramos sesión
if st.session_state.user not in data:
    st.session_state.user = None
    st.rerun()

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
        api_input = st.text_input("API Key (Full Access)", type="password")
        if st.button("Guardar API Key"):
            st.session_state.api_key = api_input.strip()
            st.rerun()

if not st.session_state.api_key:
    st.warning("Por favor, ingresa una API Key válida.")
    st.stop()

client = OpenAI(api_key=st.session_state.api_key)

# ---------------- SYSTEM PROMPT ----------------
SYSTEM_PROMPT = """
You are Paty, a professional English teacher for Spanish speakers.
Eres una profesora de (Ingles - Español) especializada en educar a personas desde el nivel A1 hasta C2.
- Si te hablan en otro idioma: responde que "Solo eres profesora de Ingles-Español".
- Si no seleccionan nivel: recuerda que el proceso es para practicar inglés.
- Debes empezar saludando y preguntando qué Nivel de Inglés van a practicar hoy (A1, A2, B1, B2, C1, C2).
- Una vez seleccionado el nivel, contextualiza la charla.
- Siempre habla en inglés, pero si hay errores, corrígelos en ESPAÑOL.
- Entrega estadísticas de % Fluidez/Escritura y % de errores.

Format for corrections:
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
    tema = st.text_input("🎯 ¿Sobre qué te gustaría practicar hoy?")
    if st.button("Comenzar"):
        st.session_state.topic = tema
        st.session_state.messages = [
            {"role": "assistant", "content": f"Great choice! Let's talk about {tema}. Before we start, what English level (A1-C2) would you like to practice today?"}
        ]
        st.rerun()
    st.stop()

# ---------------- CHAT ----------------
st.title("🌍 2Bilingue Pro - Paty 👩‍🏫")
st.caption(f"Tema: {st.session_state.topic}")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ---------------- INPUT ----------------
user_input = None
audio = st.audio_input("🎤 Habla con Paty")

if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

if audio:
    if id(audio) != st.session_state.last_audio_id:
        st.session_state.last_audio_id = id(audio)
        try:
            with st.spinner("Escuchando..."):
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio)
                user_input = transcript.text
        except Exception as e:
            st.error(f"Error de audio: {e}")

if not modo_continuo:
    text_input = st.chat_input("Escribe tu mensaje...")
    if text_input:
        user_input = text_input

# ---------------- PROCESAR ----------------
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Paty está pensando..."):
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "system", "content": f"Current Topic: {st.session_state.topic}"}
                ] + st.session_state.messages

                response = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
                reply = response.choices[0].message.content
                st.write(reply)

                # Voz
                audio_res = client.audio.speech.create(model="tts-1", voice="alloy", input=reply[:4096])
                st.audio(audio_res.content, format="audio/mp3")

                st.session_state.messages.append({"role": "assistant", "content": reply})

                # Actualizar datos
                if "Corrección:" in reply:
                    user_data["errores"].append(reply)

                if "Evaluación final" in reply:
                    stats["conversaciones"] += 1
                    match = re.search(r'Puntuación general: (\d+)', reply)
                    if match:
                        score = int(match.group(1))
                        n = stats["conversaciones"]
                        stats["promedio"] = int((stats["promedio"] * (n - 1) + score) / n)
                        # Lógica de niveles...
                
                data[st.session_state.user] = user_data
                save_data(data)
                
        except Exception as e:
            st.error(f"Error: {e}")

# ---------------- BOTONES ----------------
st.divider()
col1, col2 = st.columns(2)
with col1:
    if st.button("🇪🇸 Traducir última frase"):
        if st.session_state.messages:
            last_text = [m for m in st.session_state.messages if m["role"] == "assistant"][-1]["content"]
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"Traduce al español: {last_text}"}]
            )
            st.info(res.choices[0].message.content)

with col2:
    if st.button("🧹 Nuevo Chat"):
        st.session_state.messages = []
        st.session_state.topic = ""
        st.rerun()
