"""
Tests para el sistema de seguridad.

Verifica el funcionamiento de hashing de contraseñas, tokens JWT y autenticación.
"""
import pytest
from src.adapters.security.argon2_hasher import Argon2PasswordHasher
from src.adapters.security.jwt_token_service import JWTTokenService


class TestArgon2Hasher:
    """Tests para el hasher de contraseñas con Argon2."""
    
    def test_hash_password(self):
        """Verifica que se pueda hashear una contraseña."""
        hasher = Argon2PasswordHasher()
        password = "mi_contraseña_segura_123"
        
        hashed = hasher.hash_password(password)
        
        assert hashed is not None
        assert hashed.startswith("$argon2id$")
        assert len(hashed) > 50
    
    def test_verify_password_correct(self):
        """Verifica que una contraseña correcta sea validada."""
        hasher = Argon2PasswordHasher()
        password = "test_password_123"
        
        hashed = hasher.hash_password(password)
        result = hasher.verify_password(password, hashed)
        
        assert result is True
    
    def test_verify_password_incorrect(self):
        """Verifica que una contraseña incorrecta sea rechazada."""
        hasher = Argon2PasswordHasher()
        password = "correct_password"
        wrong_password = "wrong_password"
        
        hashed = hasher.hash_password(password)
        result = hasher.verify_password(wrong_password, hashed)
        
        assert result is False
    
    def test_different_hashes_for_same_password(self):
        """Verifica que el mismo password genere hashes diferentes (por el salt)."""
        hasher = Argon2PasswordHasher()
        password = "same_password"
        
        hash1 = hasher.hash_password(password)
        hash2 = hasher.hash_password(password)
        
        assert hash1 != hash2
        assert hasher.verify_password(password, hash1)
        assert hasher.verify_password(password, hash2)


class TestJWTTokenService:
    """Tests para el servicio de tokens JWT."""
    
    def test_create_token(self):
        """Verifica que se pueda crear un token JWT."""
        service = JWTTokenService(secret_key="test_secret_key_123")
        
        token = service.create_access_token(user_id="123", email="test@example.com")
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50
    
    def test_verify_valid_token(self):
        """Verifica que un token válido sea decodificado correctamente."""
        service = JWTTokenService(secret_key="test_secret_key_123")
        user_id = "456"
        email = "user@example.com"
        
        token = service.create_access_token(user_id=user_id, email=email)
        decoded = service.verify_token(token)
        
        assert decoded is not None
        assert decoded["user_id"] == user_id
        assert decoded["email"] == email
    
    def test_verify_invalid_token(self):
        """Verifica que un token inválido sea rechazado."""
        service = JWTTokenService(secret_key="test_secret_key_123")
        
        invalid_token = "invalid.token.here"
        decoded = service.verify_token(invalid_token)
        
        assert decoded is None
    
    def test_verify_token_wrong_secret(self):
        """Verifica que un token firmado con otra clave sea rechazado."""
        service1 = JWTTokenService(secret_key="secret_key_1")
        service2 = JWTTokenService(secret_key="secret_key_2")
        
        token = service1.create_access_token(user_id="789", email="test@example.com")
        decoded = service2.verify_token(token)
        
        assert decoded is None


@pytest.mark.asyncio
class TestAuthenticationFlow:
    """Tests de integración para el flujo de autenticación."""
    
    def test_complete_auth_flow(self):
        """Verifica el flujo completo: hash password -> create token -> verify token."""
        hasher = Argon2PasswordHasher()
        token_service = JWTTokenService(secret_key="integration_test_secret")
        
        # 1. Usuario registra con contraseña
        password = "user_password_123"
        hashed_password = hasher.hash_password(password)
        
        # 2. Verificar contraseña en login
        assert hasher.verify_password(password, hashed_password)
        
        # 3. Generar token tras login exitoso
        user_id = "user_123"
        email = "user@test.com"
        token = token_service.create_access_token(user_id=user_id, email=email)
        
        # 4. Verificar token en requests subsecuentes
        decoded = token_service.verify_token(token)
        assert decoded is not None
        assert decoded["user_id"] == user_id
        assert decoded["email"] == email


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
