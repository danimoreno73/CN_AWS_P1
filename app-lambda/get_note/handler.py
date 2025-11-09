"""
Lambda function: Get Note
GET /notes/{id}
"""
import os
import boto3
from decimal import Decimal
import sys

from shared.models import NoteCreate
from shared.utils import create_response, parse_json_body

# Cliente DynamoDB
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('REGION', 'us-east-1'))
table_name = os.environ.get('TABLE_NAME', 'Notes')
table = dynamodb.Table(table_name)


def decimal_to_float(obj):
    """Convertir Decimal a float para JSON"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def lambda_handler(event, context):
    """
    Handler para obtener una nota por ID
    """
    try:
        # Extraer note_id de pathParameters
        note_id = event.get('pathParameters', {}).get('id')
        
        if not note_id:
            return create_response(400, {
                'error': 'ID de nota requerido'
            })
        
        # Obtener de DynamoDB
        response = table.get_item(Key={'note_id': note_id})
        
        if 'Item' not in response:
            return create_response(404, {
                'error': 'Nota no encontrada'
            })
        
        # Retornar nota
        return create_response(200, response['Item'])
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return create_response(500, {
            'error': 'Error interno del servidor',
            'message': str(e)
        })