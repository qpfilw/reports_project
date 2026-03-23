from __future__ import annotations
from typing import Any
from app.ml.features.header_features import calculate_header_similarity
from app.ml.utils.preprocessing import normalize_text
from app.models.ml_template import MlTemplate

_DEFAULT_AUTO_APPLY_THRESHOLD = 0.88

def _template_fields(template: MlTemplate) -> list[dict[str, Any]]:
    config = dict(template.config_json or {})
    fields = config.get("fields")
    if isinstance(fields, list):
        normalized_fields: list[dict[str, Any]] = []
        for item in fields:
            if isinstance(item, dict):
                name = str(item.get("name") or item.get("target_field") or "").strip()
                if not name:
                    continue
                aliases_raw = item.get("aliases") or []
                aliases = [str(alias).strip() for alias in aliases_raw if str(alias).strip()]
                normalized_fields.append({"name": name, "aliases": aliases})
            else:
                name = str(item).strip()
                if name:
                    normalized_fields.append({"name": name, "aliases": []})
        if normalized_fields:
            return normalized_fields

    target_fields_raw = config.get("target_fields") or config.get("expected_fields") or []
    field_aliases = config.get("field_aliases") or {}
    normalized_fields = []
    for raw_field in target_fields_raw:
        name = str(raw_field).strip()
        if not name:
            continue
        aliases_raw = field_aliases.get(name, []) if isinstance(field_aliases, dict) else []
        aliases = [str(alias).strip() for alias in aliases_raw if str(alias).strip()]
        normalized_fields.append({"name": name, "aliases": aliases})
    return normalized_fields

def _field_expected_headers(field: dict[str, Any]) -> list[str]:
    expected = [field["name"]]
    expected.extend(field.get("aliases") or [])
    return [value for value in expected if normalize_text(value)]

def score_template_for_headers(headers: list[str], template: MlTemplate) -> dict[str, Any]:
    normalized_headers = [header for header in headers if normalize_text(header)]
    fields = _template_fields(template)

    if not normalized_headers:
        return {
            "template": template,
            "confidence": 0.0,
            "coverage": 0.0,
            "matched_fields": [],
            "unmatched_fields": [field["name"] for field in fields],
            "headers": headers,
        }

    if not fields:
        confidence = 0.55 if template.is_default else 0.45
        return {
            "template": template,
            "confidence": round(confidence, 4),
            "coverage": 0.0,
            "matched_fields": [],
            "unmatched_fields": [],
            "headers": headers,
        }

    matched_fields: list[dict[str, Any]] = []
    unmatched_fields: list[str] = []
    total_score = 0.0

    for field in fields:
        candidates = _field_expected_headers(field)
        best_score = 0.0
        best_header: str | None = None
        best_alias: str | None = None
        for header in normalized_headers:
            for candidate in candidates:
                score = calculate_header_similarity(header, candidate)
                if score > best_score:
                    best_score = score
                    best_header = header
                    best_alias = candidate
        if best_score >= 0.55 and best_header is not None:
            matched_fields.append(
                {
                    "field": field["name"],
                    "header": best_header,
                    "matched_by": best_alias,
                    "score": round(best_score, 4),
                }
            )
            total_score += best_score
        else:
            unmatched_fields.append(field["name"])

    coverage = len(matched_fields) / len(fields) if fields else 0.0
    avg_match_score = total_score / len(fields) if fields else 0.0

    confidence = (coverage * 0.65) + (avg_match_score * 0.3)
    if template.is_default:
        confidence += 0.03
    if normalized_headers and fields:
        header_ratio = min(len(normalized_headers), len(fields)) / max(len(normalized_headers), len(fields))
        confidence += header_ratio * 0.05

    confidence = max(0.0, min(0.99, confidence))
    return {
        "template": template,
        "confidence": round(confidence, 4),
        "coverage": round(coverage, 4),
        "matched_fields": matched_fields,
        "unmatched_fields": unmatched_fields,
        "headers": headers,
    }

def build_template_prediction(headers: list[str], templates: list[MlTemplate]) -> dict[str, Any]:
    scored = [score_template_for_headers(headers, template) for template in templates]
    scored.sort(key=lambda item: (item["confidence"], item["coverage"], item["template"].is_default), reverse=True)
    best = scored[0] if scored else None

    return {
        "best": best,
        "candidates": scored,
        "auto_apply_threshold": _DEFAULT_AUTO_APPLY_THRESHOLD,
    }
