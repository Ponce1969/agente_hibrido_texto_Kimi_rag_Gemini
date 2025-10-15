#!/usr/bin/env python3
"""
Script para generar una clave secreta segura para JWT.

Uso:
    python scripts/generate_secret_key.py
"""
import secrets


def generate_secret_key(length: int = 32) -> str:
    """
    Genera una clave secreta criptográficamente segura.
    
    Args:
        length: Longitud en bytes (default: 32 = 256 bits)
        
    Returns:
        Clave secreta en formato URL-safe base64
    """
    return secrets.token_urlsafe(length)


def main():
    """Genera y muestra una clave secreta."""
    print("🔐 Generando clave secreta para JWT...\n")
    
    secret_key = generate_secret_key()
    
    print("✅ Clave generada exitosamente:")
    print(f"\n{secret_key}\n")
    print("📋 Agrega esta línea a tu archivo .env:")
    print(f"\nJWT_SECRET_KEY={secret_key}\n")
    print("⚠️  IMPORTANTE:")
    print("   - NO compartas esta clave")
    print("   - Usa claves diferentes para dev/staging/prod")
    print("   - Guárdala de forma segura (variables de entorno, secrets manager)")
    print("   - Si la clave se compromete, genera una nueva inmediatamente\n")


if __name__ == "__main__":
    main()
