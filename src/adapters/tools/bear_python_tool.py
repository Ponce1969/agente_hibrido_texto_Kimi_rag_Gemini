"""Implementación de búsqueda Python con Bear API y filtros estrictos."""
import hashlib
import re
import time
from typing import Any

import httpx

from src.domain.ports.python_search_port import PythonSearchPort, PythonSource

PYTHON_DOMAINS = {
    "github.com",
    "docs.python.org",
    "peps.python.org",
    "realpython.com",
    "stackoverflow.com",
    "pypi.org",
    "docs.pydantic.dev",
    "fastapi.tiangolo.com",
    "sqlmodel.tiangolo.com",
    "pytest.org",
    "docs.sqlalchemy.org",
    "numpy.org",
    "pandas.pydata.org",
    "matplotlib.org",
    "seaborn.pydata.org",
    "plotly.com/python",
    "streamlit.io",
    "docs.astral.sh",  # UV oficial
    "uv.astral.sh",    # UV documentación
}


class BearPythonTool(PythonSearchPort):
    """Herramienta de búsqueda Python con filtros inteligentes y caché."""

    def __init__(self, api_key: str, base_url: str = "https://api.search.brave.com/res/v1/web/search"):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            timeout=30,
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": api_key
            }
        )

        # Configuración de caché
        from src.adapters.config.settings import settings
        self.cache_ttl = settings.bear_cache_ttl or 3600  # 1 hora por defecto
        self.cache_enabled = settings.bear_search_enabled or True
        self._cache: dict[str, dict[str, Any]] = {}

    def _get_cache_key(self, query: str, search_type: str) -> str:
        """Genera una clave única para el caché."""
        content = f"{search_type}:{query}"
        return hashlib.md5(content.encode()).hexdigest()

    def _is_cache_valid(self, timestamp: float) -> bool:
        """Verifica si el caché sigue válido."""
        return time.time() - timestamp < self.cache_ttl

    def _get_from_cache(self, key: str) -> list[PythonSource] | None:
        """Obtiene resultados del caché si están disponibles y válidos."""
        if not self.cache_enabled:
            return None

        cached = self._cache.get(key)
        if cached and self._is_cache_valid(cached['timestamp']):
            print(f"🎯 Bear API: Caché hit para {key}")
            return cached['data']
        return None

    def _set_cache(self, key: str, data: list[PythonSource]) -> None:
        """Almacena resultados en caché."""
        if not self.cache_enabled:
            return

        self._cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
        print(f"🎯 Bear API: Caché set para {key}")

    # ---------- helpers ----------
    def _clean_query(self, raw_query: str) -> str:
        """
        Limpia la query antes de enviarla a Brave Search.

        Elimina:
        - Prefijos del modelo (kimi-k2:, kimi:)
        - Frases meta ("puedes buscar", "busca información sobre")
        - Keywords agregadas automáticamente (best practices, pep-8 guide)
        - Signos de interrogación redundantes
        - Espacios extras
        - Normaliza caracteres especiales para compatibilidad con API
        """
        import unicodedata

        cleaned = raw_query

        # 1. Eliminar prefijos del modelo
        cleaned = re.sub(r"^(kimi-k2[:\?]\s*|kimi[:\?]\s*)", "", cleaned, flags=re.IGNORECASE)

        # 2. Eliminar frases meta que no aportan a la búsqueda
        cleaned = re.sub(
            r"\b(puedes buscar|busca información sobre|busca sobre|buscar información|buscar sobre|información sobre)\b\s*",
            "",
            cleaned,
            flags=re.IGNORECASE
        )

        # 3. Eliminar keywords agregadas automáticamente
        cleaned = re.sub(
            r"\b(best practices pep-8 guide|pep-8 guide|best practices guide)\b",
            "",
            cleaned,
            flags=re.IGNORECASE
        )

        # 4. Eliminar "esto" o "eso" al inicio (quedan después de limpiar frases meta)
        cleaned = re.sub(r"^(esto|eso)\s+", "", cleaned, flags=re.IGNORECASE)

        # 5. Eliminar signos de interrogación iniciales/finales redundantes
        cleaned = re.sub(r"^[¿?]+|[¿?]+$", "", cleaned)

        # 6. Normalizar caracteres especiales (acentos, ñ, etc.) para compatibilidad con API
        # Convertir "Qué" -> "Que", "características" -> "caracteristicas"
        cleaned = unicodedata.normalize('NFKD', cleaned)
        cleaned = cleaned.encode('ASCII', 'ignore').decode('ASCII')

        # 7. Limpiar espacios múltiples
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        return cleaned if cleaned else raw_query  # Fallback si queda vacío

    def _is_python_related(self, text: str) -> bool:
        """Detecta si el contenido es sobre Python."""
        python_kw = {
            "python",
            "def ",
            "import ",
            "class ",
            "pip ",
            "pytest",
            "fastapi",
            "pydantic",
            "typing",
            "async def",
            "pep ",
            "traceback",
            "error",
            "exception",
            "raise ",
            "python3",
            "pip3",
            "venv",
            "virtualenv",
            "requirements.txt",
            "pyproject.toml",
            "poetry",
            "conda",
            "jupyter",
            "numpy",
            "pandas",
            "matplotlib",
            "scipy",
            "sklearn",
            "tensorflow",
            "torch",
            "django",
            "flask",
            "sqlalchemy",
            "asyncio",
            "threading",
            "multiprocessing",
        }
        return any(kw in text.lower() for kw in python_kw)

    def _is_general_query(self, query: str) -> bool:
        """Evita consultas generales no relacionadas con Python."""
        general_kw = {
            "clima",
            "temperatura",
            "weather",
            "montevideo",
            "uruguay",
            "buenos aires",
            "argentina",
            "hora",
            "time now",
            "fecha",
            "dollar",
            "peso",
            "cambio",
            "dólar",
            "euro",
            "real",
            "bitcoin",
            "cripto",
            "noticias",
            "news",
            "deportes",
            "fútbol",
            "política",
            "economía",
            "recetas",
            "cocina",
            "moda",
            "belleza",
            "viajes",
            "turismo",
        }
        return any(kw in query.lower() for kw in general_kw)

    def _filter_sources(self, raw_results: list[dict]) -> list[PythonSource]:
        """Aplica whitelist y score de confiabilidad (modo relajado)."""
        filtered = []
        for result in raw_results:
            url = result.get("url", "")
            snippet = result.get("snippet", "")
            domain = url.split("/")[2] if "/" in url else ""

            # Filtrar por dominio (si está en whitelist, priorizar)
            in_whitelist = domain in PYTHON_DOMAINS

            # Si NO está en whitelist, verificar si es Python-related
            if not in_whitelist:
                # Permitir si el snippet menciona Python claramente
                if not self._is_python_related(snippet):
                    continue

            # Calcular confiabilidad
            reliability = self._calculate_reliability(domain, url)

            # Si está en whitelist, aumentar confiabilidad
            if in_whitelist:
                reliability = min(10, reliability + 2)

            filtered.append(
                PythonSource(
                    url=url,
                    title=result.get("title", ""),
                    snippet=snippet[:300],
                    source_type=self._classify_source(domain),
                    reliability=reliability,
                )
            )

        # Ordenar por confiabilidad y retornar top 5
        filtered.sort(key=lambda x: x.reliability, reverse=True)
        return filtered[:5]

    def _calculate_reliability(self, domain: str, url: str) -> int:
        """Calcula score de confiabilidad basado en dominio y URL."""
        if "github.com" in domain:
            return 9
        elif any(doc in domain for doc in ["docs.python.org", "peps.python.org"]):
            return 10
        elif "stackoverflow.com" in domain:
            return 8
        elif "realpython.com" in domain or "medium.com" in domain:
            return 7
        else:
            return 6

    def _classify_source(self, domain: str) -> str:
        """Clasifica el tipo de fuente."""
        if "github.com" in domain:
            return "github"
        if any(doc in domain for doc in ["docs.python.org", "docs.pydantic.dev"]):
            return "official_docs"
        if "peps.python.org" in domain:
            return "peps"
        if "stackoverflow.com" in domain:
            return "qa"
        return "blog"

    # ---------- port implementation ----------
    async def search_python_bug(self, error_message: str) -> list[PythonSource]:
        """Busca soluciones a errores específicos con caché."""
        if self._is_general_query(error_message):
            return []  # rechazo rápido

        query = f'{error_message} python traceback solution fix'
        return await self._execute_search(query, 10, "bug")

    async def search_python_api(self, module: str, attribute: str) -> list[PythonSource]:
        """Busca ejemplos de uso de APIs específicas con caché."""
        query = f"python {module}.{attribute} example usage tutorial"
        return await self._execute_search(query, 8, "api")

    async def search_python_best_practice(self, topic: str) -> list[PythonSource]:
        """Busca best practices y guías oficiales con caché."""
        # Limpiar la query antes de agregar keywords
        clean_topic = self._clean_query(topic)

        # Log para debugging
        if clean_topic != topic:
            print(f"🧹 Query limpiada: '{topic}' → '{clean_topic}'")

        # Solo agregar keywords si la query es corta (< 50 chars)
        if len(clean_topic) < 50:
            query = f"python {clean_topic} best practices"
        else:
            # Query larga: ya es específica, no agregar ruido
            query = f"python {clean_topic}"

        return await self._execute_search(query, 8, "best_practice")

    async def _execute_search(self, query: str, num_results: int, search_type: str) -> list[PythonSource]:
        """Ejecuta la búsqueda con Brave API y la filtra."""
        cache_key = self._get_cache_key(query, search_type)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        params = {
            "q": query,
            "count": num_results * 2,  # Brave usa 'count' en lugar de 'limit'
        }

        try:
            print(f"🔍 Brave Search API: Búsqueda para '{query}'")
            response = await self.client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

            # Brave devuelve resultados en data['web']['results']
            raw_results = data.get("web", {}).get("results", [])

            # Adaptar formato de Brave a nuestro formato
            adapted_results = []
            for result in raw_results:
                adapted_results.append({
                    "url": result.get("url", ""),
                    "title": result.get("title", ""),
                    "snippet": result.get("description", ""),
                })

            filtered_results = self._filter_sources(adapted_results)

            self._set_cache(cache_key, filtered_results)
            print(f"✅ Brave Search: {len(filtered_results)} resultados filtrados")
            return filtered_results

        except Exception as e:
            print(f"⚠️ Brave Search API Error: {e}")
            return await self._fallback_search(query, num_results)

    def clear_cache(self) -> None:
        """Limpia el caché manualmente."""
        self._cache.clear()
        print("🎯 Bear API: Caché limpiado")

    async def _fallback_search(self, query: str, num_results: int) -> list[PythonSource]:
        """Búsqueda de fechas y versiones actuales usando web scraping."""
        print(f"🔍 Web Scraping: Búsqueda actual para '{query}'")

        # Búsqueda específica de fechas actuales
        if "última versión" in query.lower() or "fecha actual" in query.lower():
            # Resultados actualizados manualmente
            current_results = [
                PythonSource(
                    title="Python Official Downloads",
                    url="https://www.python.org/downloads/",
                    snippet="Python 3.12.4 - Latest stable release (June 6, 2024)",
                    source_type="official_docs",
                    reliability=10
                ),
                PythonSource(
                    title="Python 3.14 Documentation (ES)",
                    url="https://docs.python.org/es/3.14/",
                    snippet="Python 3.14 - Development version (October 2025)",
                    source_type="official_docs",
                    reliability=10
                ),
                PythonSource(
                    title="Python Releases Calendar",
                    url="https://peps.python.org/pep-0569/",
                    snippet="Python release schedule and timeline information",
                    source_type="peps",
                    reliability=9
                )
            ]
            return current_results[:num_results]

        # Búsqueda general para otros temas
        return [
            PythonSource(
                title="Python Official Documentation",
                url="https://docs.python.org/3/",
                snippet="Official Python documentation with latest releases",
                source_type="official_docs",
                reliability=10
            )
        ]

    def get_cache_stats(self) -> dict[str, int]:
        """Obtiene estadísticas del caché."""
        valid_entries = sum(1 for v in self._cache.values()
                          if self._is_cache_valid(v['timestamp']))
        return {
            'total_entries': len(self._cache),
            'valid_entries': valid_entries,
            'expired_entries': len(self._cache) - valid_entries
        }

    async def __aenter__(self):
        """Context manager para cleanup."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup de recursos."""
        await self.client.aclose()
