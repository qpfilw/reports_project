from __future__ import annotations
from typing import Any
from pydantic import Field
from .common import BaseSchema
from .template import MlTemplateShortRead

class ColumnMatchSuggestion(BaseSchema):
    source_column: str
    target_field: str
    confidence: float = Field(..., ge=0, le=1)
    rule: str | None = None

class TemplatePrediction(BaseSchema):
    template_id: int | None = None
    template_code: str | None = None
    confidence: float = Field(..., ge=0, le=1)

class TemplatePredictionResult(BaseSchema):
    best_match: TemplatePrediction | None = None
    candidates: list[TemplatePrediction] = Field(default_factory=list)

class AnomalyItem(BaseSchema):
    row_number: int | None = Field(None, ge=1)
    field_path: str | None = None
    anomaly_type: str
    severity: str
    message: str
    source_value: str | None = None
    confidence: float | None = Field(None, ge=0, le=1)

class MLPipelineResult(BaseSchema):
    selected_template: MlTemplateShortRead | None = None
    template_prediction: TemplatePredictionResult | None = None
    column_matches: list[ColumnMatchSuggestion] = Field(default_factory=list)
    anomalies: list[AnomalyItem] = Field(default_factory=list)
    quality_score: float | None = Field(None, ge=0, le=1)
    mapping_confirmation_required: bool = False
    diagnostics: dict[str, Any] = Field(default_factory=dict)

class ColumnMappingConfirmRequest(BaseSchema):
    mappings: list[ColumnMatchSuggestion] = Field(default_factory=list)