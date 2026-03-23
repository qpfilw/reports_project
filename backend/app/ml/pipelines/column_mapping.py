from __future__ import annotations
from typing import Any
from app.ml.features.header_features import calculate_header_similarity
from app.ml.pipelines.template_selection import _template_fields
from app.models.ml_template import MlTemplate

def build_column_mapping(headers: list[str], template: MlTemplate | None) -> dict[str, Any]:
    if template is None:
        return {
            "matches": [],
            "unmatched_headers": headers,
            "requires_confirmation": True,
            "template_fields": [],
        }

    fields = _template_fields(template)
    if not fields:
        fallback_matches = [
            {
                "source_column": header,
                "target_field": header,
                "confidence": 0.55,
                "rule": "fallback_same_name",
            }
            for header in headers
        ]
        return {
            "matches": fallback_matches,
            "unmatched_headers": [],
            "requires_confirmation": True,
            "template_fields": [],
        }

    template_fields = [field["name"] for field in fields]
    matches: list[dict[str, Any]] = []
    used_target_fields: set[str] = set()
    unmatched_headers: list[str] = []

    for header in headers:
        best_score = 0.0
        best_field_name: str | None = None
        best_alias: str | None = None

        for field in fields:
            if field["name"] in used_target_fields:
                continue
            candidates = [field["name"], *(field.get("aliases") or [])]
            for candidate in candidates:
                score = calculate_header_similarity(header, candidate)
                if score > best_score:
                    best_score = score
                    best_field_name = field["name"]
                    best_alias = candidate

        if best_field_name is None or best_score < 0.5:
            unmatched_headers.append(header)
            continue

        used_target_fields.add(best_field_name)
        matches.append(
            {
                "source_column": header,
                "target_field": best_field_name,
                "confidence": round(best_score, 4),
                "rule": f"similarity:{best_alias}",
            }
        )

    requires_confirmation = bool(unmatched_headers) or any(match["confidence"] < 0.82 for match in matches)
    return {
        "matches": matches,
        "unmatched_headers": unmatched_headers,
        "requires_confirmation": requires_confirmation,
        "template_fields": template_fields,
    }
