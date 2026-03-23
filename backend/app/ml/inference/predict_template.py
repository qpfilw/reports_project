from __future__ import annotations
from app.ml.pipelines.template_selection import build_template_prediction
from app.models.ml_template import MlTemplate

def predict_template(headers: list[str], templates: list[MlTemplate]) -> dict[str, object]:
    return build_template_prediction(headers=headers, templates=templates)
