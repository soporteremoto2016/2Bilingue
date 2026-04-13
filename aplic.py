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

# ---------------- USUARIO Y SIDEBAR ----------------
user_data = data[st.session_state.user]
stats = user_data["stats"]

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

# ---------------- API KEY (CORRECCIÓN DE PERMISOS) ----------------
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
    st.warning("Por favor, ingresa una API Key con permisos 'Full Access'.")
    st.stop()

# Inicialización del cliente
client = OpenAI(api_key=st.session_state.api_key)

# ---------------- PROMPT DE LUCY ----------------
SYSTEM_PROMPT = """
You are Paty, a professional English teacher for Spanish speakers.
Eres una profesora de (Ingles - Español)especializada en educar a personas desde el nivel A1 hasta C2, si te hablan en otro idioma, debes responder que "Solo eres profesora de Ingles-Español), además si no te seleccionan el nivel de ingle debes responder que tu proceso es solo para practicar el idioma ingles,  cuando el usuario seleccione el tema para practicar debe ser claro en el tema , debes siempre  hablar en Ingles, siempre debe tener una conversación clara y fluida sobre el tema que te propone el usuario,  debes empezar siempre saludando y preguntando al usuario que tipo de Nivel de Inglés van a practicar hoy y que le permita seleccionar una de las siguientes opciones : 
A1 - Principiante (Acceso): Comunicación básica, frases cotidianas, presentarse y pedir información personal simple.
A2 - Básico (Plataforma): Entiende frases de uso frecuente (compras, familia, trabajo) y describe aspectos del pasado.
B1 - Intermedio (Umbral): Capacidad para desenvolverse en situaciones cotidianas, viajar y describir experiencias, deseos y opiniones de forma sencilla.
B2 - Intermedio Alto (Avanzado): Entiende ideas principales de textos complejos, interactúa con fluidez y naturalidad sin esfuerzo.
C1 - Avanzado (Dominio Operativo Eficaz): Comprende una amplia variedad de textos largos y exigentes, expresándose de forma fluida y espontánea para fines sociales o profesionales.
C2 - Maestría (Maestría): Dominio total, comprende con facilidad prácticamente todo lo que lee o escucha, expresándose con matices precisos.
Una vez el cliente selecciona la opción, todo el proceso de conversación debe ser dirigido y contextualizado según la opción escogida, tus respuestas deben ser siempre en ingles, pero si el usuario comete un error debes decirlo y escribirlo en español explicándole cual fue su error y como debes ser la mejor propuesta en el dialogo.
En el proceso de conversación debes ir entregado unas estadísticas del nivel de conversación en % Fluidez en la conversación buena si estas hablando con el  o de % Escritura buena si estas chateando con él  y en ambos casos también debe mostrar el  % de errores en la conversación
- Always speak in English.
- Correct errors in Spanish.

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

# ---------------- SELECCIÓN DE TEMA ----------------
if "topic" not in st.session_state:
    st.session_state.topic = ""

if not st.session_state.topic:
    st.title("🌍 2Bilingue Pro")
    tema = st.text_input("🎯 ¿Sobre qué te gustaría practicar hoy?")
    if st.button("Comenzar"):
        st.session_state.topic = tema
        st.session_state.messages = [
            {"role": "assistant", "content": f"Great choice! Let's talk about {tema}. How are you feeling today?"}
        ]
        st.rerun()
    st.stop()

# ---------------- CHAT ----------------
st.title("🌍 2Bilingue Pro - Lucy 👩‍🏫")
st.caption(f"Practicando sobre: {st.session_state.topic}")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ---------------- ENTRADA DE AUDIO / TEXTO ----------------
user_input = None
audio = st.audio_input("🎤 Habla con Lucy")

if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

if audio:
    if id(audio) != st.session_state.last_audio_id:
        st.session_state.last_audio_id = id(audio)
        try:
            with st.spinner("Escuchando..."):
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio
                )
                user_input = transcript.text
        except Exception as e:
            st.error(f"Error en transcripción (401/Scopes): {e}")
            st.info("💡 Consejo: Revisa que tu API Key tenga permisos 'Full Access' en el panel de OpenAI.")

if not modo_continuo:
    text_input = st.chat_input("Escribe tu mensaje...")
    if text_input:
        user_input = text_input

# ---------------- PROCESAMIENTO ----------------
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Lucy está pensando..."):
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "system", "content": f"Current Topic: {st.session_state.topic}"}
                ] + st.session_state.messages

                # Respuesta de Chat
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages
                )
                reply = response.choices[0].message.content
                st.write(reply)

                # Respuesta de Voz
                audio_res = client.audio.speech.create(
                    model="tts-1",
                    voice="alloy",
                    input=reply
                )
                st.audio(audio_res.content, format="audio/mp3")

                st.session_state.messages.append({"role": "assistant", "content": reply})

                # Lógica de Estadísticas
                if "Corrección:" in reply:
                    user_data["errores"].append(reply)

                if "Evaluación final" in reply:
                    stats["conversaciones"] += 1
                    match = re.search(r'Puntuación general: (\d+)', reply)
                    if match:
                        score = int(match.group(1))
                        n = stats["conversaciones"]
                        stats["promedio"] = int((stats["promedio"] * (n - 1) + score) / n)
                        
                        if score < 40: stats["nivel"] = "A1"
                        elif score < 60: stats["nivel"] = "A2"
                        elif score < 75: stats["nivel"] = "B1"
                        elif score < 90: stats["nivel"] = "B2"
                        else: stats["nivel"] = "C1"

                data[st.session_state.user] = user_data
                save_data(data)
                
        except Exception as e:
            st.error(f"Error de API: {e}")

# ---------------- HERRAMIENTAS ----------------
st.divider()
col1, col2 = st.columns(2)
with col1:
    if st.button("🇪🇸 Traducir última frase"):
        if st.session_state.messages:
            last_text = [m for m in st.session_state.messages if m["role"] == "assistant"][-1]["content"]
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"Traduce al español de forma natural: {last_text}"}]
            )
            st.info(res.choices[0].message.content)

with col2:
    if st.button("🧹 Nuevo Chat"):
        st.session_state.messages = []
        st.session_state.topic = ""
        st.rerun()
