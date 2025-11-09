"""
Utilidades compartidas para las funciones Lambda
"""
import json
from typing import Dict, Any


def create_response(status_code: int, body: Any, headers: Dict = None) -> Dict:
    """
    Crear respuesta HTTP para Lambda Proxy Integration
    """
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,X-Api-Key'
    }
    
    if headers:
        default_headers.update(headers)
    
    response = {
        'statusCode': status_code,
        'headers': default_headers
    }
    
    if body is not None:
        if isinstance(body, str):
            response['body'] = body
        else:
            response['body'] = json.dumps(body)
    else:
        response['body'] = ''
    
    return response


def parse_json_body(event: Dict) -> Dict:
    """
    Parsear body JSON del evento Lambda
    """
    body = event.get('body', '{}')
    if isinstance(body, str):
        return json.loads(body)
    return body