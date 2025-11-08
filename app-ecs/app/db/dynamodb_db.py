"""
Implementación de DynamoDB para el almacenamiento de notas
"""
import boto3
from boto3.dynamodb.conditions import Key
from typing import List, Optional, Dict
from datetime import datetime
import uuid
import os
from .db import Database


class DynamoDBDatabase(Database):
    """Implementación de DynamoDB"""

    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        self.table_name = os.getenv('DB_DYNAMONAME', 'Notes')
        self.table = self.dynamodb.Table(self.table_name)

    def create_note(self, note_data: Dict) -> Dict:
        """Crear una nueva nota"""
        note_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + 'Z'

        item = {
            'note_id': note_id,
            'title': note_data['title'],
            'content': note_data['content'],
            'tags': note_data.get('tags', []),
            'created_at': timestamp,
            'updated_at': timestamp
        }

        self.table.put_item(Item=item)
        return item

    def get_note(self, note_id: str) -> Optional[Dict]:
        """Obtener una nota por ID"""
        response = self.table.get_item(Key={'note_id': note_id})
        return response.get('Item')

    def list_notes(self) -> List[Dict]:
        """Listar todas las notas"""
        response = self.table.scan()
        return response.get('Items', [])

    def update_note(self, note_id: str, note_data: Dict) -> Optional[Dict]:
        """Actualizar una nota existente"""
        # Verificar que la nota existe
        existing = self.get_note(note_id)
        if not existing:
            return None

        timestamp = datetime.utcnow().isoformat() + 'Z'

        # Construir expresión de actualización
        update_expression = "SET updated_at = :updated_at"
        expression_values = {':updated_at': timestamp}

        if 'title' in note_data:
            update_expression += ", title = :title"
            expression_values[':title'] = note_data['title']

        if 'content' in note_data:
            update_expression += ", content = :content"
            expression_values[':content'] = note_data['content']

        if 'tags' in note_data:
            update_expression += ", tags = :tags"
            expression_values[':tags'] = note_data['tags']

        # Actualizar
        response = self.table.update_item(
            Key={'note_id': note_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ReturnValues='ALL_NEW'
        )

        return response.get('Attributes')

    def delete_note(self, note_id: str) -> bool:
        """Eliminar una nota"""
        # Verificar que existe
        existing = self.get_note(note_id)
        if not existing:
            return False

        self.table.delete_item(Key={'note_id': note_id})
        return True

    def health_check(self) -> bool:
        """Verificar estado de la conexión"""
        try:
            self.table.table_status
            return True
        except Exception:
            return False