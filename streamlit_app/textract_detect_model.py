from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    Pages: int


class BoundingBox(BaseModel):
    Width: float
    Height: float
    Left: float
    Top: float


class PolygonItem(BaseModel):
    X: float
    Y: float


class Geometry(BaseModel):
    BoundingBox: BoundingBox
    Polygon: List[PolygonItem]


class Relationship(BaseModel):
    Type: str
    Ids: List[str]


class Block(BaseModel):
    BlockType: str
    Geometry: Geometry
    Id: str
    Relationships: Optional[List[Relationship]] = None
    Confidence: Optional[float] = None
    Text: Optional[str] = None
    TextType: Optional[str] = None


class HTTPHeaders(BaseModel):
    x_amzn_requestid: str = Field(..., alias='x-amzn-requestid')
    content_type: str = Field(..., alias='content-type')
    content_length: str = Field(..., alias='content-length')
    date: str


class ResponseMetadata(BaseModel):
    RequestId: str
    HTTPStatusCode: int
    HTTPHeaders: HTTPHeaders
    RetryAttempts: int


class TextractDetectModel(BaseModel):
    DocumentMetadata: DocumentMetadata
    Blocks: List[Block]
    DetectDocumentTextModelVersion: str
    ResponseMetadata: ResponseMetadata
