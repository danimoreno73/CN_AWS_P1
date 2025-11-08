"""
API REST de Notas con Flask - Versión todo-en-uno
"""
import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import BaseModel, Field, field_validator
import boto3
from botocore.exceptions import ClientError

# ============= MODELOS PYDANTIC =============

class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=10000)
    tags: Optional[List[str]] = Field(default_factory=list)

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        if v is None:
            return []
        if len(v) > 10:
            raise ValueError('Máximo 10 tags permitidos')
        for tag in v:
            if len(tag) > 50:
                raise ValueError('Cada tag debe tener máximo 50 caracteres')
        return v


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    tags: Optional[List[str]] = None

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        if v is None:
            return None
        if len(v) > 10:
            raise ValueError('Máximo 10 tags permitidos')
        for tag in v:
            if len(tag) > 50:
                raise ValueError('Cada tag debe tener máximo 50 caracteres')
        return v


# ============= DATABASE =============

class DynamoDBDatabase:
    def __init__(self):
        self.table_name = os.getenv('DB_DYNAMONAME', 'Notes')
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
        self.table = self.dynamodb.Table(self.table_name)

    def create_note(self, note_data: Dict) -> Dict:
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
        try:
            response = self.table.get_item(Key={'note_id': note_id})
            return response.get('Item')
        except ClientError:
            return None

    def list_notes(self) -> List[Dict]:
        try:
            response = self.table.scan()
            return response.get('Items', [])
        except ClientError:
            return []

    def update_note(self, note_id: str, updates: Dict) -> Optional[Dict]:
        note = self.get_note(note_id)
        if not note:
            return None
        
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        update_expr_parts = []
        expr_attr_values = {}
        
        for key, value in updates.items():
            update_expr_parts.append(f'#{key} = :{key}')
            expr_attr_values[f':{key}'] = value
        
        update_expr_parts.append('#updated_at = :updated_at')
        expr_attr_values[':updated_at'] = timestamp
        
        update_expression = 'SET ' + ', '.join(update_expr_parts)
        expr_attr_names = {f'#{key}': key for key in list(updates.keys()) + ['updated_at']}
        
        self.table.update_item(
            Key={'note_id': note_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values
        )
        
        return self.get_note(note_id)

    def delete_note(self, note_id: str) -> bool:
        note = self.get_note(note_id)
        if not note:
            return False
        
        self.table.delete_item(Key={'note_id': note_id})
        return True


# ============= FLASK APP =============

app = Flask(__name__)
CORS(app)

PORT = int(os.getenv('PORT', 8080))
db = DynamoDBDatabase()


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200


@app.route('/notes', methods=['GET'])
def list_notes():
    try:
        notes = db.list_notes()
        return jsonify(notes), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/notes', methods=['POST'])
def create_note():
    try:
        data = request.get_json()
        note_data = NoteCreate(**data)
        note = db.create_note(note_data.model_dump())
        return jsonify(note), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/notes/<note_id>', methods=['GET'])
def get_note(note_id):
    try:
        note = db.get_note(note_id)
        if not note:
            return jsonify({'error': 'Nota no encontrada'}), 404
        return jsonify(note), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/notes/<note_id>', methods=['PUT'])
def update_note(note_id):
    try:
        data = request.get_json()
        note_data = NoteUpdate(**data)
        note = db.update_note(note_id, note_data.model_dump(exclude_unset=True))
        if not note:
            return jsonify({'error': 'Nota no encontrada'}), 404
        return jsonify(note), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/notes/<note_id>', methods=['DELETE'])
def delete_note(note_id):
    try:
        success = db.delete_note(note_id)
        if not success:
            return jsonify({'error': 'Nota no encontrada'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print(f"Starting Flask app on port {PORT}...")
    app.run(host='0.0.0.0', port=PORT)