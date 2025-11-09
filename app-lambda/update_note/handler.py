"""
Lambda function: Update Note
PUT /notes/{id}
"""
import os
from datetime import datetime
import boto3
from pydantic import ValidationError
import sys

# Añadir shared al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from models import NoteUpdate
from utils import create_response, parse_json_body

# Cliente DynamoDB
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('REGION', 'us-east-1'))
table_name = os.environ.get('TABLE_NAME', 'Notes')
table = dynamodb.Table(table_name)


def lambda_handler(event, context):
    """
    Handler para actualizar una nota existente
    """
    try:
        # Extraer note_id
        note_id = event.get('pathParameters', {}).get('id')
        
        if not note_id:
            return create_response(400, {
                'error': 'ID de nota requerido'
            })
        
        # Verificar que la nota existe
        response = table.get_item(Key={'note_id': note_id})
        if 'Item' not in response:
            return create_response(404, {
                'error': 'Nota no encontrada'
            })
        
        # Parsear y validar body
        body = parse_json_body(event)
        note_data = NoteUpdate(**body)
        
        # Construir expresión de actualización
        timestamp = datetime.utcnow().isoformat() + 'Z'
        update_dict = note_data.dict(exclude_unset=True)  # Solo campos enviados
        
        update_expression = "SET updated_at = :updated_at"
        expression_values = {':updated_at': timestamp}
        
        if 'title' in update_dict:
            update_expression += ", title = :title"
            expression_values[':title'] = update_dict['title']
        
        if 'content' in update_dict:
            update_expression += ", content = :content"
            expression_values[':content'] = update_dict['content']
        
        if 'tags' in update_dict:
            update_expression += ", tags = :tags"
            expression_values[':tags'] = update_dict['tags']
        
        # Actualizar en DynamoDB
        response = table.update_item(
            Key={'note_id': note_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ReturnValues='ALL_NEW'
        )
        
        return create_response(200, response['Attributes'])
        
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