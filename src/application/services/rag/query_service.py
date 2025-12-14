"""
Servicio especializado para queries RAG.

Responsabilidades:
1. Búsqueda semántica con filtros
2. Construcción de prompt RAG
3. Integración con embeddings_repository
"""
from datetime import UTC, datetime
from typing import Any

from src.adapters.agents.gemini_adapter import GeminiAdapter
from src.adapters.db.embeddings_repository import EmbeddingsRepository
from src.domain.models import ChatMessage, MessageRole


class RagQueryService:
    def __init__(self, embeddings_repository: EmbeddingsRepository, gemini_adapter: GeminiAdapter) -> None:
        self.embeddings_repo = embeddings_repository
        self.gemini = gemini_adapter

    async def query_rag(
        self,
        query: str,
        file_id: int | None = None,
        session_id: str | None = None
    ) -> str:
        """Ejecuta query RAG con opción de filtro por file_id"""
        # 1. Obtener embedding de la query
        query_embedding = await self._get_query_embedding(query)

        # 2. Buscar chunks similares (¡CON FILTRO si hay file_id!)
        chunks = self.embeddings_repo.search_top_k(
            query_embedding=query_embedding,
            file_id=file_id,
            top_k=self._calculate_top_k(query)
        )

        if not chunks:
            return "No encontré información relevante en los documentos."

        # 3. Construir contexto RAG con optimización de tokens
        rag_context = self._build_rag_context_optimized(chunks, file_id, max_context_tokens=6000)

        # 4. Construir prompt
        prompt = self._build_rag_prompt(query, rag_context)

        # 5. Llamar a Gemini con más tokens para respuestas completas
        user_message = ChatMessage(
            session_id=0,
            role=MessageRole.USER,
            content=prompt,
            timestamp=datetime.now(UTC),
            message_index=0
        )
        response, _ = await self.gemini.get_chat_completion(
            system_prompt=self._get_system_prompt(),
            messages=[user_message],
            max_tokens=4096,  # Aumentado para respuestas más completas
            temperature=0.3
        )

        return response

    async def _get_query_embedding(self, query: str) -> list[float]:
        """Obtiene el embedding de la query usando el servicio de embeddings"""
        import httpx

        from src.adapters.agents.gemini_embeddings_adapter import (
            GeminiEmbeddingsAdapter,
        )

        async with httpx.AsyncClient() as client:
            embeddings_adapter = GeminiEmbeddingsAdapter(client)
            embedding_vector = await embeddings_adapter.generate_embedding(query)
            result: list[float] = embedding_vector.tolist()
            return result

    def _build_rag_context(self, chunks: list[Any], file_id: int | None) -> str:
        """Construye el contexto RAG a partir de los chunks con metadata"""
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            # Incluir metadata si está disponible
            metadata_info = ""
            if hasattr(chunk, 'metadata') and chunk.metadata:
                # Extraer información de sección/capítulo si existe
                section = chunk.metadata.get('section', '')
                page = chunk.metadata.get('page_number', '')
                if section:
                    metadata_info = f" (Sección: {section})"
                elif page:
                    metadata_info = f" (Página: {page})"

            context_parts.append(
                f"[Fragmento {i}{metadata_info}]\n{chunk.content}\n"
            )
        return "\n".join(context_parts)

    def _build_rag_context_optimized(self, chunks: list[Any], file_id: int | None, max_context_tokens: int = 6000) -> str:
        """Construye el contexto RAG optimizado para no exceder límite de tokens"""
        context_parts = []
        estimated_tokens = 0

        for i, chunk in enumerate(chunks, 1):
            # Estimar tokens (aproximadamente 4 caracteres por token)
            chunk_tokens = len(chunk.content) // 4

            # Si agregar este chunk excede el límite, detener
            if estimated_tokens + chunk_tokens > max_context_tokens:
                break

            # Incluir metadata si está disponible
            metadata_info = ""
            if hasattr(chunk, 'metadata') and chunk.metadata:
                section = chunk.metadata.get('section', '')
                page = chunk.metadata.get('page_number', '')
                if section:
                    metadata_info = f" (Sección: {section})"
                elif page:
                    metadata_info = f" (Página: {page})"

            context_parts.append(
                f"[Fragmento {i}{metadata_info}]\n{chunk.content}\n"
            )
            estimated_tokens += chunk_tokens

        return "\n".join(context_parts)

    def _build_rag_prompt(self, query: str, rag_context: str) -> str:
        """Construye el prompt final con contexto RAG y estructura mejorada"""
        return f"""Contexto de documentos:
{rag_context}

Pregunta del usuario: {query}

INSTRUCCIONES IMPORTANTES:
1. Si encuentras la información en los fragmentos, estructura tu respuesta así:
   - **Definición/Concepto**: Explica qué es
   - **Detalles**: Profundiza con información del documento
   - **Referencias**: Menciona secciones, capítulos o "Trucos" específicos si aparecen
   - **Citas**: Incluye citas textuales relevantes entre comillas

2. Si la información NO está en los fragmentos:
   - Sé honesto: "El documento no proporciona información específica sobre..."
   - Si puedes inferir algo del contexto, indícalo claramente: "Basándome en el contexto..."
   - NO inventes información

3. Cuando menciones secciones o capítulos, usa el formato: "En la sección X, titulada 'Y'..."

4. Mantén un tono profesional pero accesible.

Responde basándote únicamente en el contexto proporcionado."""

    def _get_system_prompt(self) -> str:
        """System prompt mejorado para respuestas estructuradas"""
        return """Eres un asistente especializado en análisis de documentos PDF.

Tus fortalezas:
- Extraer información precisa de documentos
- Citar referencias específicas (secciones, capítulos, páginas)
- Estructurar respuestas de forma clara y profesional
- Admitir cuando la información no está disponible

Tus principios:
- NUNCA inventes información que no esté en el documento
- SIEMPRE cita secciones/capítulos cuando los menciones
- ESTRUCTURA tus respuestas con bullets y secciones claras
- SÉ HONESTO si la información no está en los fragmentos proporcionados"""

    def _calculate_top_k(self, query: str) -> int:
        """Calcula top_k basado en complejidad de la query"""
        query_lower = query.lower()

        # Preguntas simples o específicas
        if len(query) < 20:
            return 5

        # Preguntas que requieren contexto amplio (reducido para evitar overflow)
        if any(word in query_lower for word in ["explica", "cómo funciona", "diferencia", "compara", "principales", "cuáles son"]):
            return 12  # Reducido de 15 a 12

        # Preguntas sobre conceptos específicos
        if any(word in query_lower for word in ["qué es", "define", "significa"]):
            return 8

        # Default
        return 10
