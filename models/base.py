"""
Base models and shared data types for the Kryptopedia application.
Pydantic v2 compatible version.
"""
from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional, Annotated
import json

class PyObjectId(ObjectId):
    """
    Custom type for handling MongoDB ObjectIDs with Pydantic v2
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
    def __get_pydantic_json_schema__(cls, _schema_generator):
        """
        Replacement for __modify_schema__ in Pydantic v2
        """
        return {"type": "string"}

class DBModel(BaseModel):
    """
    Base model for all database models.
    Includes common fields and configuration for MongoDB documents.
    """
    id: Annotated[PyObjectId, Field(default_factory=PyObjectId, alias="_id")]
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

    def model_dump_json(self, **kwargs):
        """
        Override model_dump_json to handle ObjectId serialization
        """
        def _custom_encoder(obj):
            if isinstance(obj, ObjectId):
                return str(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        return json.dumps(self.model_dump(**kwargs), default=_custom_encoder)

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
