"""
Lambda function: Create Note
POST /notes
"""
import json
import os
import uuid
from datetime import datetime
import boto3
from pydantic import ValidationError
import sys

# Añadir shared al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from models import NoteCreate
from utils import create_response, parse_json_body

# Cliente DynamoDB
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('REGION', 'us-east-1'))
table_name = os.environ.get('TABLE_NAME', 'Notes')
table = dynamodb.Table(table_name)


def lambda_handler(event, context):
    """
    Handler para crear una nueva nota
    """
    try:
        # Parsear body
        body = parse_json_body(event)
        
        # Validar con Pydantic
        note_data = NoteCreate(**body)
        
        # Generar ID y timestamps
        note_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Crear item
        note_dict = note_data.dict()
        item = {
            'note_id': note_id,
            'title': note_dict['title'],
            'content': note_dict['content'],
            'tags': note_dict['tags'],
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        # Guardar en DynamoDB
        table.put_item(Item=item)
        
        # Retornar respuesta
        return create_response(201, item)
        
    except ValidationError as e:
        return create_response(400, {
            'error': 'Datos inválidos',
            'details': e.errors()
        })
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return create_response(500, {
            'error': 'Error interno del servidor',
            'message': str(e)
        })