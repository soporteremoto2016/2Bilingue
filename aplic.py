# 🔑 API KEY desde usuario
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

with st.sidebar:
    st.header("🔐 Configuración")

    api_input = st.text_input(
        "API Key de OpenAI",
        type="password",
        placeholder="sk-...",
    )

    if st.button("Guardar API Key"):
        st.session_state.api_key = api_input
        st.success("API Key guardada")

# Validación
if not st.session_state.api_key:
    st.warning("⚠️ Ingresa tu API Key para usar la aplicación")
    st.stop()

# Cliente
client = OpenAI(api_key=st.session_state.api_key)
