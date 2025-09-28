"""
Frontend de la aplicación de chat con Streamlit.
"""
import streamlit as st
import httpx
import io
import os
import time
from datetime import datetime
from typing import List, Dict

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


def api_get_session_messages(session_id: int) -> list[dict]:
    try:
        r = httpx.get(f"{BACKEND_URL}/sessions/{session_id}/messages", timeout=10)
        r.raise_for_status()
        data = r.json()
        # Normalizar a estructura de la UI
        return [{"role": m.get("role", "assistant"), "content": m.get("content", "")} for m in data]
    except Exception:
        return []

def api_list_files(limit: int = 20) -> list[dict]:
    try:
        r = httpx.get(f"{BACKEND_URL}/files", params={"limit": limit}, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []

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


def api_upload_pdf(file_name: str, file_bytes: bytes, mime: str, auto_index: bool = False) -> dict:
    files = {
        "file": (file_name, file_bytes, mime or "application/pdf"),
    }
    params = {"auto_index": str(auto_index).lower()} if auto_index else None
    r = httpx.post(f"{BACKEND_URL}/files/upload", files=files, params=params, timeout=120)
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


def api_get_progress(file_id: int) -> dict:
    r = httpx.get(f"{BACKEND_URL}/files/progress/{file_id}", timeout=10)
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


# --- Embeddings (pgvector) helpers ---

def api_embeddings_index(file_id: int) -> dict:
    r = httpx.post(f"{BACKEND_URL}/embeddings/index/{file_id}", timeout=600)
    r.raise_for_status()
    return r.json()


def api_embeddings_search(q: str, file_id: int | None, top_k: int = 5) -> dict:
    params = {"q": q, "top_k": top_k}
    if file_id is not None:
        params["file_id"] = file_id
    r = httpx.get(f"{BACKEND_URL}/embeddings/search", params=params, timeout=60)
    r.raise_for_status()
    return r.json()

# --- Inicialización del Estado de la Sesión ---

if "session_id" not in st.session_state:
    st.session_state.session_id = create_new_session()

if "messages" not in st.session_state:
    st.session_state.messages = []
    # Intentar cargar del backend si hay session_id válido
    if st.session_state.session_id:
        st.session_state.messages = api_get_session_messages(st.session_state.session_id)

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

    # Selector de PDF existente
    with st.expander("Seleccionar PDF existente", expanded=False):
        files = api_list_files(limit=30)
        if files:
            # Mostrar como selectbox: "file_id - filename (status)"
            options = {f"{it.get('id')} - {it.get('filename')} ({it.get('status')})": it.get('id') for it in files}
            sel = st.selectbox("Elige un PDF ya cargado", options=list(options.keys()), index=None, placeholder="— seleccionar —")
            if sel:
                st.session_state.pdf_file_id = options[sel]
                st.success(f"PDF seleccionado: file_id={st.session_state.pdf_file_id}")
        else:
            st.info("No hay PDFs cargados aún o no se pudo consultar el backend.")

    # Sesiones anteriores
    st.header("Sesiones anteriores")
    sessions = api_list_sessions(USER_ID, limit=30)
    if sessions:
        labels = [f"{s.get('id')} - {s.get('session_name') or 'sin título'} ({s.get('updated_at') or 's/fecha'})" for s in sessions]
        mapping = {labels[i]: sessions[i]["id"] for i in range(len(sessions))}
        sel_s = st.selectbox("Reabrir sesión", options=labels, index=None, placeholder="— seleccionar —")
        if sel_s:
            st.session_state.session_id = mapping[sel_s]
            st.session_state.messages = api_get_session_messages(st.session_state.session_id)
            st.success(f"Sesión cargada: {st.session_state.session_id}")

        with st.expander("Borrar sesión", expanded=False):
            del_s = st.selectbox("Elige sesión a borrar", options=labels, index=None, placeholder="— seleccionar —", key="_del_s")
            confirm = st.checkbox("Estoy seguro de borrar esta sesión", key="_del_confirm")
            if st.button("Borrar sesión seleccionada", use_container_width=True, disabled=not (del_s and confirm)):
                sid = mapping.get(del_s)
                if sid:
                    ok = api_delete_session(sid)
                    if ok:
                        st.success("Sesión borrada.")
                        # Si borraste la sesión actual, limpia el estado local
                        if st.session_state.get("session_id") == sid:
                            st.session_state.messages = []
                        # Fuerza un refresco para actualizar la lista al instante
                        st.rerun()
                    else:
                        st.error("No se pudo borrar la sesión.")
    else:
        st.caption("No hay sesiones previas para este usuario.")

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
        # Flujo simplificado: un botón que sube + procesa + indexa en background y muestra progreso unificado
        with st.expander("Usar PDF como contexto (One‑click)", expanded=True):
            if st.button("Subir y preparar contexto automáticamente", use_container_width=True):
                try:
                    meta = api_upload_pdf(
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        uploaded_file.type or "application/pdf",
                        auto_index=True,
                    )
                    st.session_state.pdf_file_id = meta["file_id"]
                    st.success(f"Subido. file_id={meta['file_id']}")
                except Exception as e:
                    st.error(f"Error al subir PDF: {e}")

            # Progreso unificado
            if st.session_state.pdf_file_id is not None:
                with st.status("Preparando contexto…", expanded=True) as status_box:
                    try:
                        ready = False
                        for i in range(20):
                            p = api_get_progress(st.session_state.pdf_file_id)
                            phase = p.get("phase")
                            detail = p.get("detail") or {}
                            if phase == "processing_sections":
                                st.write(f"Procesando páginas: {p.get('pages_processed', 0)}/{p.get('total_pages', 0)}")
                            elif phase == "indexing_embeddings":
                                st.write(f"Indexando embeddings… chunks={detail.get('chunks_indexed', 0)} (aprox.)")
                            elif phase == "ready":
                                ready = True
                                break
                            elif phase == "error":
                                st.error(f"Error: {detail.get('error')}")
                                break
                            time.sleep(1)
                        if ready:
                            status_box.update(label="¡Contexto listo!", state="complete")
                            st.info("Este PDF se usará como contexto automáticamente al chatear.")
                        else:
                            status_box.update(label="Preparación en curso. Puedes continuar chateando y volver luego.", state="running")
                    except Exception as e:
                        st.error(f"Fallo al consultar progreso: {e}")

            st.toggle("Usar como contexto en el chat", value=True, key="_use_pdf_context")
            if st.session_state.get("pdf_file_id") is not None:
                st.caption(f"file_id actual: {st.session_state.pdf_file_id}")

        # Acordeón avanzado opcional para pruebas de búsqueda
        with st.expander("Avanzado (opcional)", expanded=False):
            st.caption("Prueba de búsqueda semántica (top-k)")
            q = st.text_input("Consulta", key="_emb_q")
            top_k = st.number_input("top_k", min_value=1, max_value=50, value=5, step=1, key="_emb_k")
            if st.button("Buscar", use_container_width=True, disabled=not bool(st.session_state.get("pdf_file_id")) or not q):
                try:
                    res = api_embeddings_search(q, st.session_state.pdf_file_id, int(top_k))
                    items = res.get("results", [])
                    if not items:
                        st.info("Sin resultados aún (la indexación puede seguir en curso)")
                    for it in items:
                        with st.container(border=True):
                            st.caption(f"sec={it.get('section_id')} ch={it.get('chunk_index')} d={it.get('distance'):.3f}")
                            st.write(it.get("content", "")[:500])
                except Exception as e:
                    st.error(f"Error en búsqueda: {e}")

    st.header("Descarga de Chat")

    def _messages_to_markdown(messages: List[Dict[str, str]]) -> str:
        lines = []
        lines.append(f"# Conversación - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        for msg in messages:
            role = msg.get("role", "assistant")
            content = msg.get("content", "")
            header = "## Usuario" if role == "user" else "## Asistente"
            lines.append(header)
            lines.append("")
            lines.append(content)
            lines.append("")
            lines.append("---")
            lines.append("")
        return "\n".join(lines)

    def _messages_to_pdf_bytes(messages: List[Dict[str, str]]) -> bytes | None:
        try:
            # Importar on-demand para no romper si no está instalado en la imagen
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import cm
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
            from reportlab.lib import colors
        except Exception:
            return None

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story = []

        title = f"Conversación - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        story.append(Paragraph(f"<b>{title}</b>", styles['Title']))
        story.append(Spacer(1, 0.5*cm))

        for msg in messages:
            role = msg.get("role", "assistant")
            content = msg.get("content", "").replace("\n", "<br/>")
            header = "Usuario" if role == "user" else "Asistente"
            story.append(Paragraph(f"<b>{header}</b>", styles['Heading3']))
            story.append(Spacer(1, 0.1*cm))
            story.append(Paragraph(content, styles['BodyText']))
            story.append(Spacer(1, 0.3*cm))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    messages = st.session_state.get("messages", [])
    md_bytes = _messages_to_markdown(messages).encode("utf-8") if messages else b""
    pdf_bytes = _messages_to_pdf_bytes(messages) if messages else None

    col_md, col_pdf = st.columns(2)
    with col_md:
        st.download_button(
            label="Descargar como Markdown",
            data=md_bytes,
            file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True,
            disabled=not bool(messages),
        )
    with col_pdf:
        if messages and pdf_bytes is not None:
            st.download_button(
                label="Descargar como PDF",
                data=pdf_bytes,
                file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.button(
                "Descargar como PDF",
                disabled=True,
                use_container_width=True,
                help=(
                    "Agrega mensajes para habilitar la descarga. "
                    "Si ya hay mensajes y sigue deshabilitado, rebuild de la imagen con 'reportlab' es necesario."
                ),
            )

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

            # Enviar al backend usando el contexto del PDF si está activo el toggle
            file_id_to_send = None
            if advanced_pdf_mode and st.session_state.get("pdf_file_id") and st.session_state.get("_use_pdf_context", True):
                file_id_to_send = st.session_state.pdf_file_id
                # Avisar si el contexto aún no está listo
                try:
                    prog = api_get_progress(file_id_to_send)
                    if prog.get("phase") != "ready":
                        st.info("El PDF aún se está preparando (procesando o indexando). Puedes seguir chateando; el contexto se aplicará cuando esté listo.")
                except Exception:
                    pass

            ai_response = post_chat_message(
                session_id=st.session_state.session_id,
                message=full_prompt,
                mode=AgentMode(agent_mode),
                file_id=file_id_to_send,
            )
            
            if ai_response:
                st.markdown(ai_response)
                # Refrescar desde backend para garantizar persistencia y habilitar descargas
                st.session_state.messages = api_get_session_messages(st.session_state.session_id)
            else:
                st.error("No se recibió respuesta del agente.")
