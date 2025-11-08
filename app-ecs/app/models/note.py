"""
Modelos Pydantic para validación de notas
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime


class NoteCreate(BaseModel):
    """Modelo para crear una nota"""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=10000)
    tags: Optional[List[str]] = Field(default_factory=list, max_items=10)

    @validator('tags')
    def validate_tags(cls, v):
        if v:
            # Cada tag máximo 50 caracteres
            for tag in v:
                if len(tag) > 50:
                    raise ValueError('Tag demasiado largo (máx 50 caracteres)')
            # Sin duplicados
            if len(v) != len(set(v)):
                raise ValueError('No se permiten tags duplicados')
        return v


class NoteUpdate(BaseModel):
    """Modelo para actualizar una nota"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    tags: Optional[List[str]] = Field(None, max_items=10)

    @validator('tags')
    def validate_tags(cls, v):
        if v is not None:
            for tag in v:
                if len(tag) > 50:
                    raise ValueError('Tag demasiado largo (máx 50 caracteres)')
            if len(v) != len(set(v)):
                raise ValueError('No se permiten tags duplicados')
        return v


class NoteResponse(BaseModel):
    """Modelo de respuesta de una nota"""
    note_id: str
    title: str
    content: str
    tags: List[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True