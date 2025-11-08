"""
Modelos de datos (Pydantic schemas).
"""
from .note import NoteCreate, NoteUpdate, NoteResponse

__all__ = ['NoteCreate', 'NoteUpdate', 'NoteResponse']