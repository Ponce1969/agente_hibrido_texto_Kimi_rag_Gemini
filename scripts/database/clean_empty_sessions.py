#!/usr/bin/env python3
"""
Script para limpiar sesiones vacías después de la migración.

Este script elimina las sesiones sin mensajes que quedaron
antes de implementar el filtro automático.
"""

import asyncio
from src.adapters.dependencies import get_chat_service
from src.adapters.db.database import get_session

async def main():
    """Limpia las sesiones vacías existentes."""
    print("🧹 Limpiando sesiones vacías...")
    
    try:
        # Crear servicio con dependencias
        session = next(get_session())
        service = get_chat_service(session)
        
        # Contar sesiones antes de limpiar
        all_sessions = service.repo.list_sessions(limit=100)
        print(f"📊 Sesiones totales antes: {len(all_sessions)}")
        
        # Limpiar sesiones vacías
        deleted_count = service.repo.delete_empty_sessions()
        print(f"🗑️ Sesiones vacías eliminadas: {deleted_count}")
        
        # Verificar resultado
        clean_sessions = service.repo.list_sessions(limit=100)
        print(f"✅ Sesiones con mensajes: {len(clean_sessions)}")
        
        # Mostrar sesiones restantes
        print("\n📋 Sesiones activas:")
        for session in clean_sessions[:5]:  # Mostrar primeras 5
            msg_count = service.repo.count_session_messages(str(session.id))
            print(f"   Sesión {session.id} - {msg_count} mensajes")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    print("🎉 Limpieza completada!")
    return 0

if __name__ == "__main__":
    asyncio.run(main())
