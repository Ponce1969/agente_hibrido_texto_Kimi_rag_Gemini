"""
Implementación del puerto PasswordHasherPort usando Argon2.

Adaptador que implementa el hashing de contraseñas con Argon2id,
el estándar recomendado por OWASP.
"""
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

from src.domain.ports.auth_port import PasswordHasherPort


class Argon2PasswordHasher(PasswordHasherPort):
    """
    Implementación de PasswordHasherPort usando Argon2id.
    
    Argon2id es el algoritmo ganador del Password Hashing Competition
    y proporciona resistencia contra ataques GPU/ASIC.
    """
    
    def __init__(
        self,
        time_cost: int = 3,
        memory_cost: int = 65536,
        parallelism: int = 4,
        hash_len: int = 32,
        salt_len: int = 16
    ) -> None:
        """
        Inicializa el hasher con parámetros configurables.
        
        Args:
            time_cost: Número de iteraciones (default: 3)
            memory_cost: Memoria en KB (default: 64 MB)
            parallelism: Número de threads (default: 4)
            hash_len: Longitud del hash en bytes (default: 32)
            salt_len: Longitud del salt en bytes (default: 16)
        """
        self.ph = PasswordHasher(
            time_cost=time_cost,
            memory_cost=memory_cost,
            parallelism=parallelism,
            hash_len=hash_len,
            salt_len=salt_len
        )
    
    def hash_password(self, password: str) -> str:
        """
        Genera un hash seguro usando Argon2id.
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            Hash en formato Argon2id (incluye salt y parámetros)
        """
        return self.ph.hash(password)
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verifica si una contraseña coincide con su hash.
        
        Args:
            password: Contraseña en texto plano
            hashed: Hash almacenado
            
        Returns:
            True si la contraseña es correcta, False en caso contrario
        """
        try:
            self.ph.verify(hashed, password)
            return True
        except (VerifyMismatchError, InvalidHashError):
            return False
    
    def needs_rehash(self, hashed: str) -> bool:
        """
        Verifica si un hash necesita ser regenerado.
        
        Útil cuando se actualizan los parámetros de seguridad.
        
        Args:
            hashed: Hash a verificar
            
        Returns:
            True si el hash debe regenerarse, False en caso contrario
        """
        return self.ph.check_needs_rehash(hashed)
