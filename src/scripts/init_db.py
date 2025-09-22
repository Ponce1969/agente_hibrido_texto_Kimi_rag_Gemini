#!/usr/bin/env python3
import sys
import os

# Agregar el directorio raíz al path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.adapters.db.database import create_db_and_tables

if __name__ == "__main__":
    print("🚀 Inicializando base de datos...")
    create_db_and_tables()
    print("✅ Base de datos inicializada correctamente")