"""
Frontend de la aplicación de chat con Streamlit.
"""
import streamlit as st
import httpx
import io

import os

from src.adapters.agents.prompts import AgentMode

# --- Configuración de la Página ---
st.set_page_config(page_title="Asistente de Aprendizaje de Python", layout="wide")

# --- Constantes y Configuración del Backend ---
# La URL del backend se obtiene de una variable de entorno, con un valor por defecto para desarrollo local
BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000/api/v1")
USER_ID = "streamlit_user"  # ID de usuario fijo para este prototipo

# --- Funciones de Comunicación con el Backend ---

def create_new_session() -> int:
    """Crea una nueva sesión en el backend y devuelve el ID de la sesión."""
    try:
        response = httpx.post(f"{BACKEND_URL}/sessions", json={"user_id": USER_ID})
        response.raise_for_status()
        return response.json()["session_id"]
    except httpx.RequestError as e:
        st.error(f"Error de conexión al crear sesión: {e}")
        return 0

def post_chat_message(session_id: int, message: str, mode: AgentMode, file_id: int | None = None) -> str:
    """Envía un mensaje al backend y devuelve la respuesta de la IA."""
    try:
        payload = {"session_id": session_id, "message": message, "mode": mode.value}
        if file_id is not None:
            payload["file_id"] = file_id
        response = httpx.post(
            f"{BACKEND_URL}/chat",
            json=payload,
            timeout=120,  # Timeout de 2 minutos para respuestas largas de la IA
        )
        response.raise_for_status()
        return response.json()["reply"]
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            # Mensaje claro de rate limit alcanzado (TPD)
            detail = e.response.text
            wait_hint = ""
            try:
                import re
                m = re.search(r"try again in ([0-9]+m[0-9.]*s)", detail, re.IGNORECASE)
                if not m:
                    m = re.search(r'Try again in ([^."]+)', detail)
                if m:
                    wait_hint = f" Intenta nuevamente en {m.group(1)}."
            except Exception:
                pass
            st.warning(
                "Se alcanzó el límite diario de tokens del proveedor (429)."
                + wait_hint
                + " Para evitar esto: reduce el contexto o activa el fallback a Gemini si está disponible."
            )
        else:
            st.error(f"Error en la API: {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        st.error(f"Error de conexión al enviar mensaje: {e}")
    return ""


def api_upload_pdf(file_name: str, file_bytes: bytes, mime: str) -> dict:
    files = {
        "file": (file_name, file_bytes, mime or "application/pdf"),
    }
    r = httpx.post(f"{BACKEND_URL}/files/upload", files=files, timeout=120)
    r.raise_for_status()
    return r.json()


def api_start_process(file_id: int) -> dict:
    r = httpx.post(f"{BACKEND_URL}/files/process/{file_id}", timeout=10)
    r.raise_for_status()
    return r.json()


def api_get_status(file_id: int) -> dict:
    r = httpx.get(f"{BACKEND_URL}/files/status/{file_id}", timeout=10)
    r.raise_for_status()
    return r.json()


def api_list_sections(file_id: int) -> list[dict]:
    r = httpx.get(f"{BACKEND_URL}/files/{file_id}/sections", timeout=30)
    r.raise_for_status()
    return r.json()


def api_get_section_text(file_id: int, section_id: int) -> str:
    r = httpx.get(f"{BACKEND_URL}/files/{file_id}/sections/{section_id}/text", timeout=60)
    r.raise_for_status()
    data = r.json()
    return data.get("text", "")

# --- Inicialización del Estado de la Sesión ---

if "session_id" not in st.session_state:
    st.session_state.session_id = create_new_session()

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Barra Lateral (Sidebar) ---

with st.sidebar:
    st.title("Herramientas del Agente")
    
    st.header("Selector de Agente")
    agent_mode = st.selectbox(
        "Elige el rol del agente:",
        options=[mode.value for mode in AgentMode],
        key="agent_mode_selector"
    )

    st.header("Carga de Archivos")
    advanced_pdf_mode = st.toggle("Procesamiento avanzado de PDFs grandes", value=False, help="Usa segmentación por secciones y procesamiento en segundo plano")
    uploaded_file = st.file_uploader(
        "Sube un archivo para dar contexto a la IA",
        type=["txt", "md", "py", "pdf"] # Se pueden añadir más tipos
    )

    # Estado para pipeline avanzado
    if "pdf_file_id" not in st.session_state:
        st.session_state.pdf_file_id = None
    if "pdf_sections" not in st.session_state:
        st.session_state.pdf_sections = []
    if "selected_section_ids" not in st.session_state:
        st.session_state.selected_section_ids = []
    if "pdf_status" not in st.session_state:
        st.session_state.pdf_status = None

    if advanced_pdf_mode and uploaded_file is not None and (uploaded_file.name.lower().endswith(".pdf")):
        # Flujo: upload -> process -> status -> sections
        with st.expander("Procesamiento de PDF", expanded=True):
            col1, col2 = st.columns([1,1])
            with col1:
                if st.button("1) Subir PDF", use_container_width=True):
                    try:
                        meta = api_upload_pdf(uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/pdf")
                        st.session_state.pdf_file_id = meta["file_id"]
                        st.success(f"Subido OK. file_id={meta['file_id']}")
                    except Exception as e:
                        st.error(f"Error al subir PDF: {e}")
            with col2:
                if st.button("2) Procesar en servidor", use_container_width=True, disabled=st.session_state.pdf_file_id is None):
                    try:
                        api_start_process(st.session_state.pdf_file_id)
                        st.info("Procesamiento iniciado.")
                    except Exception as e:
                        st.error(f"No se pudo iniciar el procesamiento: {e}")

            # Polling de estado
            if st.session_state.pdf_file_id is not None:
                with st.status("Procesando…", expanded=True) as status_box:
                    try:
                        # Poll corto (hasta ~10 iteraciones)
                        ready = False
                        for _ in range(10):
                            s = api_get_status(st.session_state.pdf_file_id)
                            st.write(f"Páginas {s.get('pages_processed', 0)}/{s.get('total_pages', 0)} - estado: {s.get('status')}")
                            if s.get("status") == "ready":
                                ready = True
                                break
                            if s.get("status") == "error":
                                st.error(f"Error de procesamiento: {s.get('error_message')}")
                                break
                            st.sleep(1.0)
                        if ready:
                            status_box.update(label="¡Listo! Secciones disponibles", state="complete")
                            try:
                                st.session_state.pdf_sections = api_list_sections(st.session_state.pdf_file_id)
                            except Exception as e:
                                st.error(f"No se pudieron listar secciones: {e}")
                        else:
                            status_box.update(label="Procesamiento en curso. Vuelve a intentar listar secciones en unos segundos.", state="running")
                    except Exception as e:
                        st.error(f"Fallo al consultar estado: {e}")

            if st.session_state.pdf_sections:
                st.caption("Selecciona las secciones a incluir como contexto")
                options = {f"Pág. {s['start_page']+1}-{s['end_page']+1} (≈{s['char_count']} chars)": s["id"] for s in st.session_state.pdf_sections}
                selected = st.multiselect("Secciones", options=list(options.keys()))
                st.session_state.selected_section_ids = [options[k] for k in selected]
                # Mostrar suma de caracteres aproximada
                approx_chars = sum(next((s["char_count"] for s in st.session_state.pdf_sections if s["id"]==sid), 0) for sid in st.session_state.selected_section_ids)
                st.caption(f"Contexto seleccionado (aprox.): {approx_chars} caracteres")

    st.header("Descarga de Chat")
    st.button("Descargar como Markdown", key="download_md", disabled=True)
    st.button("Descargar como PDF", key="download_pdf", disabled=True)
    st.info("La funcionalidad de descarga se implementará próximamente.")

# --- Interfaz Principal del Chat ---

st.title("🤖 Asistente de Aprendizaje de Python")

# Mostrar mensajes del historial
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input del usuario
if prompt := st.chat_input("Escribe tu consulta aquí..."):
    # Añadir y mostrar el mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Procesar y mostrar la respuesta de la IA
    with st.chat_message("assistant"):
        with st.spinner("El agente está pensando..."):
            full_prompt = prompt
            if uploaded_file is not None and not (advanced_pdf_mode and uploaded_file.name.lower().endswith(".pdf")):
                try:
                    # Enviar el archivo al backend para extraer texto (soporta PDF y truncado)
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type or "application/octet-stream",
                        )
                    }
                    resp = httpx.post(
                        f"{BACKEND_URL}/files/extract-text",
                        files=files,
                        timeout=httpx.Timeout(connect=10.0, read=180.0, write=180.0, pool=10.0),
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    file_content = data.get("text", "")
                    truncated = data.get("truncated", False)
                    if truncated:
                        st.warning("El contenido del archivo fue truncado por longitud máxima configurada.")
                    full_prompt = f"""Basado en el siguiente contexto de archivo:
--- INICIO DEL ARCHIVO ({uploaded_file.name}) ---
{file_content}
--- FIN DEL ARCHIVO ---

Mi pregunta es: {prompt}"""
                    st.info(f"Contexto del archivo `{uploaded_file.name}` incluido desde el backend.")
                except httpx.TimeoutException:
                    st.error("No se pudo comunicar con el backend para extraer el archivo: timeout. Considera subir un archivo más pequeño o intentar nuevamente.")
                except httpx.HTTPStatusError as e:
                    st.error(f"Error del backend al extraer el archivo: {e.response.status_code} - {e.response.text}")
                except httpx.HTTPError as e:
                    st.error(f"No se pudo comunicar con el backend para extraer el archivo: {e}")
                except Exception as e:
                    st.error(f"No se pudo procesar el archivo: {e}")

            # Modo avanzado: NO incrustar el texto de secciones para evitar exceso de tokens.
            # El backend usará tool-calling (list_sections/get_section_text) con file_id para traer sólo lo necesario.
            if advanced_pdf_mode and st.session_state.selected_section_ids:
                st.info("Usando modo agentic: el backend recuperará automáticamente las secciones relevantes del PDF.")
                full_prompt = prompt

            # Enviar al backend
            file_id_to_send = None
            if advanced_pdf_mode and st.session_state.get("pdf_file_id"):
                file_id_to_send = st.session_state.pdf_file_id

            ai_response = post_chat_message(
                session_id=st.session_state.session_id,
                message=full_prompt,
                mode=AgentMode(agent_mode),
                file_id=file_id_to_send,
            )
            
            if ai_response:
                st.markdown(ai_response)
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
            else:
                st.error("No se recibió respuesta del agente.")
