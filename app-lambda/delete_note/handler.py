"""
Lambda function: Delete Note
DELETE /notes/{id}
"""
import os
import boto3
import sys

from shared.utils import create_response, parse_json_body

# Cliente DynamoDB
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('REGION', 'us-east-1'))
table_name = os.environ.get('TABLE_NAME', 'Notes')
table = dynamodb.Table(table_name)


def lambda_handler(event, context):
    """
    Handler para eliminar una nota
    """
    try:
        # Extraer note_id
        note_id = event.get('pathParameters', {}).get('id')
        
        if not note_id:
            return create_response(400, {
                'error': 'ID de nota requerido'
            })
        
        # Verificar que existe
        response = table.get_item(Key={'note_id': note_id})
        if 'Item' not in response:
            return create_response(404, {
                'error': 'Nota no encontrada'
            })
        
        # Eliminar de DynamoDB
        table.delete_item(Key={'note_id': note_id})
        
        # Retornar 204 No Content
        return create_response(204, None)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return create_response(500, {
            'error': 'Error interno del servidor',
            'message': str(e)
        })