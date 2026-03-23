from __future__ import annotations
from app.ml.pipelines.column_mapping import build_column_mapping
from app.models.ml_template import MlTemplate

def map_columns(headers: list[str], template: MlTemplate | None) -> dict[str, object]:
    return build_column_mapping(headers=headers, template=template)
