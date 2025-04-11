"""
Base models and shared data types for the Kryptopedia application.
"""
from bson import ObjectId
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional

class PyObjectId(ObjectId):
    """
    Custom type for handling MongoDB ObjectIDs with Pydantic
    """
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class DBModel(BaseModel):
    """
    Base model for all database models.
    Includes common fields and configuration for MongoDB documents.
    """
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

class DateTimeModelMixin(BaseModel):
    """
    Mixin for models that include created/updated timestamps
    """
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None

class StatusModelMixin(BaseModel):
    """
    Mixin for models that include a status field
    """
    status: str = "active"

class MetadataModelMixin(BaseModel):
    """
    Mixin for models that include a metadata dictionary
    """
    metadata: Dict[str, Any] = Field(default_factory=dict)
