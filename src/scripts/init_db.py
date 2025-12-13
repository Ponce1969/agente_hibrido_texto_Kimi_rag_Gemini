#!/usr/bin/env python3
import os
import sys

# Agregar el directorio raíz al path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

# Imports del proyecto después de configurar el path
from src.adapters.db.database import create_db_and_tables  # noqa: E402

if __name__ == "__main__":
    print("🚀 Inicializando base de datos...")
    create_db_and_tables()
    print("✅ Base de datos inicializada correctamente")
