"""
Middleware de seguridad con Guardian.
Intercepta requests al chat y valida mensajes.
"""
import logging
from collections.abc import Callable

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.application.services.guardian_service import GuardianService
from src.domain.exceptions.guardian_exceptions import MessageBlockedException

logger = logging.getLogger(__name__)


class GuardianMiddleware(BaseHTTPMiddleware):
    """
    Middleware que valida mensajes usando el Guardian antes de procesarlos.
    Solo se activa en endpoints de chat.
    """

    # Endpoints que requieren validación
    PROTECTED_PATHS = [
        "/api/v1/chat",
        "/api/v1/chat/stream",
    ]

    def __init__(
        self,
        app,
        guardian_service: GuardianService,
        enabled: bool = True
    ):
        super().__init__(app)
        self.guardian_service = guardian_service
        self.enabled = enabled

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Intercepta requests y valida mensajes si es necesario.
        """
        # Si el Guardian está desactivado, pasar sin validar
        if not self.enabled:
            return await call_next(request)

        # Solo validar endpoints protegidos
        if not any(request.url.path.startswith(path) for path in self.PROTECTED_PATHS):
            return await call_next(request)

        # Solo validar POST requests
        if request.method != "POST":
            return await call_next(request)

        try:
            # Leer el body del request
            body = await request.body()

            # Parsear JSON
            import json
            data = json.loads(body.decode())

            # Extraer el mensaje del usuario
            message = data.get("message", "")
            user_id = data.get("user_id", "unknown")

            if not message:
                # Si no hay mensaje, continuar
                return await call_next(request)

            # Validar con Guardian
            logger.info(f"🛡️ Guardian validating message from user {user_id}")
            result = await self.guardian_service.check_message(
                text=message,
                user_id=user_id
            )

            # Si el mensaje no es seguro, bloquear
            if not result.is_safe:
                logger.warning(
                    f"🚫 Guardian blocked message from user {user_id}: "
                    f"{result.reason} (threat: {result.threat_level.value})"
                )

                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "error": "message_blocked",
                        "message": "Tu mensaje ha sido bloqueado por razones de seguridad.",
                        "reason": result.reason,
                        "threat_level": result.threat_level.value,
                        "categories": result.categories or [],
                    }
                )

            # Mensaje seguro, continuar
            logger.info(f"✅ Guardian approved message from user {user_id}")

            # IMPORTANTE: Recrear el request con el body original
            # porque ya lo consumimos al leerlo
            async def receive():
                return {"type": "http.request", "body": body}

            request._receive = receive

            return await call_next(request)

        except json.JSONDecodeError:
            # Si no se puede parsear el JSON, continuar sin validar
            logger.warning("Guardian: Could not parse request body as JSON")
            return await call_next(request)

        except MessageBlockedException as e:
            # Mensaje bloqueado por el Guardian
            logger.warning(f"🚫 Guardian blocked: {e.reason}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "message_blocked",
                    "message": str(e),
                    "threat_level": e.threat_level,
                }
            )

        except Exception as e:
            # Si hay un error, permitir el mensaje (fail-open)
            logger.error(f"Guardian error: {e}", exc_info=True)
            return await call_next(request)
