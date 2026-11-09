from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MLModelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    version: str = Field(min_length=1, max_length=50)
    description: str | None = None
    framework: str | None = Field(default=None, max_length=50)

class MLModelUpdate(BaseModel):
    description: str | None = None
    framework: str | None = Field(default=None, max_length=50)


class MLModelResponse(BaseModel):
    id: int
    name: str
    version: str
    description: str | None
    framework: str | None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PredictionRequest(BaseModel):
    features: list[float] = Field(min_length=1)