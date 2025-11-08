"""
Interfaz abstracta para operaciones de base de datos
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict


class Database(ABC):
    """Interfaz abstracta para la base de datos"""

    @abstractmethod
    def create_note(self, note_data: Dict) -> Dict:
        """Crear una nueva nota"""
        pass

    @abstractmethod
    def get_note(self, note_id: str) -> Optional[Dict]:
        """Obtener una nota por ID"""
        pass

    @abstractmethod
    def list_notes(self) -> List[Dict]:
        """Listar todas las notas"""
        pass

    @abstractmethod
    def update_note(self, note_id: str, note_data: Dict) -> Optional[Dict]:
        """Actualizar una nota existente"""
        pass

    @abstractmethod
    def delete_note(self, note_id: str) -> bool:
        """Eliminar una nota"""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verificar estado de la conexión"""
        pass