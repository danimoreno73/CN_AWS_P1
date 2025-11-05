"""
Aplicación Flask para gestión de notas
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import ValidationError
import os

from .models.note import NoteCreate, NoteUpdate, NoteResponse
from .db.factory import get_database

# Crear aplicación Flask
app = Flask(__name__)

# Configurar CORS
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "X-Api-Key"]
    }
})

# Inicializar base de datos
db = get_database()


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    db_status = db.health_check()
    return jsonify({
        'status': 'healthy' if db_status else 'unhealthy',
        'database': 'connected' if db_status else 'disconnected'
    }), 200 if db_status else 503


@app.route('/notes', methods=['POST'])
def create_note():
    """Crear una nueva nota"""
    try:
        # Validar datos de entrada
        note_data = NoteCreate(**request.json)

        # Crear nota en la base de datos
        created_note = db.create_note(note_data.model_dump())

        # Retornar respuesta
        return jsonify(created_note), 201

    except ValidationError as e:
        return jsonify({'error': 'Datos inválidos', 'details': e.errors()}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/notes', methods=['GET'])
def list_notes():
    """Listar todas las notas"""
    try:
        notes = db.list_notes()
        return jsonify(notes), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/notes/<note_id>', methods=['GET'])
def get_note(note_id):
    """Obtener una nota por ID"""
    try:
        note = db.get_note(note_id)

        if not note:
            return jsonify({'error': 'Nota no encontrada'}), 404

        return jsonify(note), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/notes/<note_id>', methods=['PUT'])
def update_note(note_id):
    """Actualizar una nota existente"""
    try:
        # Validar datos de entrada
        note_data = NoteUpdate(**request.json)

        # Actualizar en la base de datos
        updated_note = db.update_note(note_id, note_data.model_dump(exclude_none=True))

        if not updated_note:
            return jsonify({'error': 'Nota no encontrada'}), 404

        return jsonify(updated_note), 200

    except ValidationError as e:
        return jsonify({'error': 'Datos inválidos', 'details': e.errors()}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/notes/<note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Eliminar una nota"""
    try:
        deleted = db.delete_note(note_id)

        if not deleted:
            return jsonify({'error': 'Nota no encontrada'}), 404

        return '', 204

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)