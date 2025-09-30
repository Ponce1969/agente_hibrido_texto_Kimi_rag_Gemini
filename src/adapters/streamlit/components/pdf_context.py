"""
Componente para gestión de contexto PDF.
Maneja la subida, selección y configuración de PDFs como contexto.
"""
import streamlit as st
from typing import Optional, Tuple
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.file_service import FileService
from models.file_models import FileUploadInfo, ProcessingPhase


class PDFContextManager:
    """Componente para gestión de contexto PDF."""
    
    def __init__(self, file_service: FileService):
        self.file_service = file_service
    
    def render_pdf_upload(self) -> Optional[int]:
        """
        Renderiza la sección de subida de PDFs.
        Returns: file_id si se subió un archivo, None en caso contrario.
        """
        st.subheader("📄 Carga de Archivos")
        
        uploaded_file = st.file_uploader(
            "Sube un archivo para dar contexto a la IA",
            type=["txt", "md", "py", "pdf"],
            help="Formatos soportados: PDF, TXT, MD, PY. Máximo 200MB por archivo."
        )
        
        if uploaded_file is not None:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Archivo:** {uploaded_file.name}")
                st.write(f"**Tamaño:** {uploaded_file.size / 1024:.1f} KB")
                st.write(f"**Tipo:** {uploaded_file.type}")
            
            with col2:
                # Botón de indexar con un click
                if st.button("🚀 Indexar con un click", use_container_width=True, type="primary"):
                    with st.spinner("Subiendo y procesando archivo..."):
                        success, message, file_id = self.file_service.upload_pdf(uploaded_file, auto_index=True)
                    
                    if success:
                        st.success(message)
                        st.balloons()  # Efecto visual de éxito
                        st.session_state._show_progress = True
                        return file_id
                    else:
                        st.error(message)
        
        return None
    
    def render_existing_pdf_selector(self) -> Optional[int]:
        """
        Renderiza el selector de PDFs existentes con UX mejorada.
        Returns: file_id seleccionado o None
        """
        st.subheader("📂 PDFs Disponibles")
        
        files = self.file_service.get_file_list(limit=30)
        
        if not files:
            st.info("📭 No hay PDFs indexados aún. Sube uno en la pestaña 'Subir Nuevo'.")
            return None
        
        # Mostrar contador
        st.success(f"✅ {len(files)} PDF(s) disponible(s)")
        
        if files:
            st.write(f"**{len(files)} archivos disponibles:**")
            
            # Mostrar archivos en una tabla más visual
            for file in files:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        # Icono según el estado
                        if file.status == "ready":
                            icon = "✅"
                        elif file.status == "processing":
                            icon = "⏳"
                        else:
                            icon = "❌"
                        
                        st.write(f"{icon} **{file.filename}**")
                        
                        # Información adicional
                        info_parts = [f"ID: {file.id}", f"Estado: {file.status}"]
                        if hasattr(file, 'size_bytes') and file.size_bytes:
                            info_parts.append(f"Tamaño: {file.size_bytes / 1024:.1f} KB")
                        if hasattr(file, 'pages_processed') and file.pages_processed:
                            info_parts.append(f"Páginas: {file.pages_processed}")
                        
                        st.caption(" | ".join(info_parts))
                    
                    with col2:
                        # Mostrar estado simple basado en el status del archivo
                        if file.status == "ready":
                            st.success("Listo", icon="✅")
                        elif file.status == "processing":
                            st.warning("Procesando", icon="⏳")
                        else:
                            st.error("Error", icon="❌")
                    
                    with col3:
                        # Verificar si este PDF está seleccionado
                        current_id = st.session_state.get("pdf_file_id")
                        is_selected = (current_id == file.id)
                        
                        if is_selected:
                            st.success("✓ Activo", icon="✅")
                        else:
                            # Botón para seleccionar
                            if st.button(f"📌 Seleccionar", key=f"select_{file.id}", use_container_width=True, type="primary"):
                                st.session_state.pdf_file_id = file.id
                                st.rerun()
                    
                    st.divider()
        else:
            st.info("📂 No hay PDFs cargados aún. Sube uno arriba para comenzar.")
        
        return st.session_state.get("pdf_file_id")
    
    def render_pdf_status(self, file_id: int) -> None:
        """Renderiza el estado del PDF seleccionado."""
        if not file_id:
            return
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🔍 Ver estado de preparación (PDF)", use_container_width=True):
                try:
                    progress = self.file_service.get_file_progress(file_id)
                    if progress:
                        # Manejar tanto enums como strings
                        phase_str = progress.phase.value if hasattr(progress.phase, 'value') else str(progress.phase)
                        status_str = progress.status.value if hasattr(progress.status, 'value') else str(progress.status)
                        
                        st.write(f"**Fase:** {phase_str}")
                        st.write(f"**Estado:** {status_str}")
                        st.write(f"**Páginas:** {progress.pages_processed}/{progress.total_pages}")
                        
                        if progress.detail:
                            chunks = progress.detail.get("chunks_indexed", 0)
                            st.write(f"**Chunks indexados:** {chunks}")
                    else:
                        st.error("No se pudo obtener el estado del archivo")
                except Exception as e:
                    st.error(f"❌ Error verificando estado del archivo: {str(e)}")
        
        with col2:
            # Badge de estado siempre visible
            try:
                is_ready, status = self.file_service.is_file_ready_for_context(file_id)
                badge = "✅ listo" if is_ready else "⏳ preparando"
                st.caption(f"file_id actual: {file_id} ({badge})")
                st.caption(status)
            except Exception:
                st.caption(f"file_id actual: {file_id}")
    
    def render_context_toggle(self) -> bool:
        """
        Renderiza el toggle para usar PDF como contexto con UX mejorada.
        Returns: True si está activado.
        """
        st.divider()
        st.subheader("🔍 Modo de Búsqueda")
        
        # Inicializar estado si no existe
        if "usar_pdf_contexto" not in st.session_state:
            st.session_state.usar_pdf_contexto = False
        
        # Toggle más visible con explicación (sin value hardcodeado)
        use_rag = st.toggle(
            "**Activar Búsqueda Inteligente en PDF**", 
            key="usar_pdf_contexto",
            help="Cuando está activado, el asistente buscará información en el PDF seleccionado usando IA (Gemini 2.5)"
        )
        
        # Mostrar estado claramente
        if use_rag:
            st.success("✅ **Modo RAG Activo** - El asistente consultará el PDF con Gemini 2.5", icon="🔍")
        else:
            st.info("💬 **Modo Chat Normal** - Conversación general con Kimi-K2", icon="💭")
        
        return use_rag
    
    def render_pdf_section(self) -> Tuple[Optional[int], bool]:
        """
        Renderiza la sección completa de gestión de PDFs.
        Returns: (file_id, use_context)
        """
        st.header("📚 Herramientas del Agente")
        
        # Tabs para organizar mejor
        tab1, tab2 = st.tabs(["📤 Subir Nuevo", "📂 Usar Existente"])
        
        uploaded_file_id = None
        selected_file_id = None
        
        with tab1:
            # Uploader único con indexación automática
            st.write("**📤 Subir e Indexar PDF**")
            st.caption("Sube un archivo PDF y se indexará automáticamente")
            
            uploaded_file = st.file_uploader(
                "Selecciona un archivo PDF",
                type=["pdf"],
                key="pdf_upload",
                help="El archivo se procesará e indexará automáticamente"
            )
            
            if uploaded_file is not None:
                if st.button("🚀 Subir e Indexar", use_container_width=True, type="primary", key="upload_index"):
                    with st.spinner("🔄 Subiendo e indexando archivo..."):
                        success, message, file_id = self.file_service.upload_pdf(uploaded_file, auto_index=True)
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.balloons()
                        st.session_state.pdf_file_id = file_id
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        
        with tab2:
            # Selector de archivos existentes
            selected_file_id = self.render_existing_pdf_selector()
            
            # Botón para reindexar PDFs existentes
            st.divider()
            if st.button("🔄 Reindexar PDFs existentes", use_container_width=True, type="secondary"):
                with st.spinner("Reindexando archivos..."):
                    files = self.file_service.get_file_list(limit=30)
                    if files:
                        for file in files:
                            try:
                                self.file_service.trigger_indexing(file.id)
                            except Exception:
                                pass
                        st.success(f"✅ Reindexación iniciada para {len(files)} archivos")
                    else:
                        st.info("No hay archivos para reindexar")
        
        # Determinar file_id actual
        current_file_id = st.session_state.get("pdf_file_id")
        
        # Mostrar información si hay archivos disponibles pero no seleccionados
        if not current_file_id:
            files = self.file_service.get_file_list(limit=1)
            if files and len(files) > 0:
                st.info(f"💡 Hay {len(files)} PDF(s) disponible(s). Ve a la pestaña 'Usar Existente' para seleccionar uno.")
        
        # Toggle de contexto (PRIMERO, más visible)
        use_context = self.render_context_toggle()
        
        # Mostrar PDF seleccionado si hay uno
        if current_file_id:
            st.divider()
            st.caption(f"📄 PDF seleccionado: ID {current_file_id}")
        
        return current_file_id, use_context
