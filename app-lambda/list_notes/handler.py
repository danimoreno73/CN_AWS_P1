"""
Lambda function: List Notes
GET /notes
"""
import os
import boto3
from decimal import Decimal
import json
import sys

# Añadir shared al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from utils import create_response

# Cliente DynamoDB
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
table_name = os.environ.get('TABLE_NAME', 'Notes')
table = dynamodb.Table(table_name)


class DecimalEncoder(json.JSONEncoder):
    """Encoder personalizado para Decimal"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    """
    Handler para listar todas las notas
    """
    try:
        # Hacer scan de la tabla
        response = table.scan()
        items = response.get('Items', [])
        
        # Manejar paginación si hay más items
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))
        
        # Convertir a JSON con encoder personalizado
        body = json.dumps(items, cls=DecimalEncoder)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,X-Api-Key'
            },
            'body': body
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return create_response(500, {
            'error': 'Error interno del servidor',
            'message': str(e)
        })