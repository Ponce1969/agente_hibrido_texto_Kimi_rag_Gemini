import asyncio
import sys
sys.path.insert(0, '/app')

async def test():
    from src.adapters.dependencies import get_session, get_chat_service
    
    session = next(get_session())
    try:
        svc = get_chat_service(session)
        
        print("🧪 Testing RAG with file_id=2...")
        reply = await svc.handle_message(
            session_id="0",  # Crea nueva sesión automáticamente
            user_message="Resume este documento en 2 líneas",
            agent_mode="architect",
            file_id=2
        )
        
        print("\n📩 RESPUESTA DEL LLM:")
        print("=" * 80)
        print(reply)
        print("=" * 80)
    finally:
        session.close()

asyncio.run(test())
