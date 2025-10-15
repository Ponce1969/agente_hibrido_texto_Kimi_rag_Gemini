"""
Servicio de hashing y verificación de contraseñas usando Argon2.

Argon2id es el estándar recomendado por OWASP y ganador del Password Hashing Competition.
Proporciona resistencia contra ataques GPU/ASIC gracias a su naturaleza memory-hard.
"""
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError


class PasswordService:
    """
    Servicio para gestionar el hashing y verificación de contraseñas.
    
    Utiliza Argon2id con configuración optimizada para seguridad y rendimiento.
    """
    
    def __init__(self) -> None:
        """
        Inicializa el hasher con parámetros seguros.
        
        Configuración:
        - time_cost=3: Número de iteraciones (balance seguridad/rendimiento)
        - memory_cost=65536: 64 MB de memoria (dificulta ataques GPU)
        - parallelism=4: Número de threads paralelos
        - hash_len=32: Longitud del hash en bytes
        - salt_len=16: Longitud del salt en bytes
        """
        self.ph = PasswordHasher(
            time_cost=3,        # Iteraciones
            memory_cost=65536,  # 64 MB
            parallelism=4,      # Threads
            hash_len=32,        # Longitud del hash
            salt_len=16         # Longitud del salt
        )
    
    def hash_password(self, password: str) -> str:
        """
        Genera un hash seguro de la contraseña.
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            Hash en formato Argon2id (incluye salt y parámetros)
            
        Example:
            >>> service = PasswordService()
            >>> hashed = service.hash_password("mi_contraseña_segura")
            >>> print(hashed)
            $argon2id$v=19$m=65536,t=3,p=4$...
        """
        return self.ph.hash(password)
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verifica si una contraseña coincide con su hash.
        
        Args:
            password: Contraseña en texto plano a verificar
            hashed: Hash almacenado previamente
            
        Returns:
            True si la contraseña es correcta, False en caso contrario
            
        Example:
            >>> service = PasswordService()
            >>> hashed = service.hash_password("mi_contraseña")
            >>> service.verify_password("mi_contraseña", hashed)
            True
            >>> service.verify_password("contraseña_incorrecta", hashed)
            False
        """
        try:
            self.ph.verify(hashed, password)
            return True
        except (VerifyMismatchError, InvalidHashError):
            return False
    
    def needs_rehash(self, hashed: str) -> bool:
        """
        Verifica si un hash necesita ser regenerado con parámetros actualizados.
        
        Útil cuando se actualizan los parámetros de seguridad del hasher.
        
        Args:
            hashed: Hash a verificar
            
        Returns:
            True si el hash debe regenerarse, False en caso contrario
        """
        return self.ph.check_needs_rehash(hashed)
