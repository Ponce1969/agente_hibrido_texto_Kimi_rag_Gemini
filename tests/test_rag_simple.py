import asyncio
import sys
sys.path.insert(0, '/app')

async def test():
    from src.adapters.dependencies import get_chat_service_dependency
    
    try:
        svc = get_chat_service_dependency()
        
        print("🧪 Testing RAG with file_id=2...")
        reply = await svc.handle_message(
            session_id="0",  # Crea nueva sesión automáticamente
            user_message="Resume este documento en 2 líneas",
            agent_mode="architect",
            file_id=2,  # <--- ID del archivo a testear
        )
        print(f"✅ RAG reply: {reply}")
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        pass

asyncio.run(test())
