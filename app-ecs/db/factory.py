"""
Factory para seleccionar la implementación de base de datos
"""
import os
from .db import Database
from .dynamodb_db import DynamoDBDatabase


def get_database() -> Database:
    """
    Retorna una instancia de la base de datos según la configuración
    """
    db_type = os.getenv('DB_TYPE', 'dynamodb').lower()

    if db_type == 'dynamodb':
        return DynamoDBDatabase()
    else:
        raise ValueError(f"Tipo de base de datos no soportado: {db_type}")