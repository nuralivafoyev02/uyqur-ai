from __future__ import annotations

import re
from dataclasses import asdict
from typing import Any

from app.models.domain import KBMatch
from app.repositories.kb_repository import KBRepository
from app.utils.text import best_similarity, keyword_hit_score, normalize_text, token_overlap_score


class KnowledgeService:
    def __init__(self, repository: KBRepository, fallback_text: str):
        self.repository = repository
        self.fallback_text = fallback_text

    @staticmethod
    def _collect_terms(entry: dict, term_type: str) -> list[str]:
        return [
            term["term_value"]
            for term in entry.get("kb_terms", [])
            if term.get("term_type") == term_type
        ]

    @staticmethod
    def _render_template(template: str, variables: dict[str, Any] | None = None) -> str:
        rendered = template
        for key, value in (variables or {}).items():
            rendered = rendered.replace(f"{{{key}}}", str(value))
        return rendered

    @staticmethod
    def _pattern_score(text: str, patterns: list[str]) -> tuple[float, list[str]]:
        reasons: list[str] = []
        normalized = normalize_text(text)
        best = 0.0
        for pattern in patterns:
            norm_pattern = normalize_text(pattern)
            if not norm_pattern:
                continue
            if norm_pattern in normalized:
                reasons.append(f"phrase:{pattern}")
                best = max(best, 1.0)
                continue
            try:
                if re.search(pattern, text, flags=re.IGNORECASE):
                    reasons.append(f"regex:{pattern}")
                    best = max(best, 0.9)
            except re.error:
                continue
        return best, reasons

    async def list_entries(self, only_active: bool = False) -> list[dict]:
        rows = await self.repository.list_entries(only_active=only_active)
        for row in rows:
            row["keywords"] = self._collect_terms(row, "keyword")
            row["synonyms"] = self._collect_terms(row, "synonym")
            row["patterns"] = self._collect_terms(row, "pattern")
        return rows

    async def create_entry(self, payload: dict) -> dict:
        terms = {
            "keyword": payload.pop("keywords", []),
            "synonym": payload.pop("synonyms", []),
            "pattern": payload.pop("patterns", []),
        }
        entry = await self.repository.create_entry(payload)
        await self._replace_terms(entry["id"], terms)
        return await self.repository.get_entry(entry["id"])

    async def update_entry(self, entry_id: str, payload: dict) -> dict:
        terms = {
            "keyword": payload.pop("keywords", []),
            "synonym": payload.pop("synonyms", []),
            "pattern": payload.pop("patterns", []),
        }
        await self.repository.update_entry(entry_id, payload)
        await self._replace_terms(entry_id, terms)
        return await self.repository.get_entry(entry_id)

    async def delete_entry(self, entry_id: str) -> None:
        await self.repository.delete_entry(entry_id)

    async def _replace_terms(self, entry_id: str, terms: dict[str, list[str]]) -> None:
        payload: list[dict] = []
        for term_type, values in terms.items():
            for value in values:
                cleaned = normalize_text(value)
                if not cleaned:
                    continue
                payload.append(
                    {
                        "kb_entry_id": entry_id,
                        "term_type": term_type,
                        "term_value": value.strip(),
                    }
                )
        await self.repository.replace_terms(entry_id, payload)

    async def match_message(
        self,
        text: str,
        *,
        language: str = "uz",
        default_threshold: float = 0.62,
        variables: dict[str, Any] | None = None,
    ) -> KBMatch:
        entries = await self.list_entries(only_active=True)
        normalized = normalize_text(text)
        best: KBMatch | None = None
        best_priority = -1
        for entry in entries:
            if entry.get("language") not in {language, "any"}:
                continue
            keywords = entry.get("keywords", [])
            synonyms = entry.get("synonyms", [])
            patterns = entry.get("patterns", [])
            all_terms = [*keywords, *synonyms, *patterns]
            pattern_score, pattern_reasons = self._pattern_score(text, patterns)
            keyword_score = keyword_hit_score(text, keywords)
            synonym_score = keyword_hit_score(text, synonyms)
            overlap = token_overlap_score(text, all_terms)
            similarity = best_similarity(text, all_terms)
            exact_bonus = 0.0
            reasons = list(pattern_reasons)
            if normalized and normalized in {normalize_text(term) for term in all_terms}:
                exact_bonus = 0.35
                reasons.append("exact_match")
            if keyword_score > 0:
                reasons.append(f"keyword:{keyword_score:.2f}")
            if synonym_score > 0:
                reasons.append(f"synonym:{synonym_score:.2f}")
            if overlap > 0:
                reasons.append(f"token_overlap:{overlap:.2f}")
            if similarity > 0:
                reasons.append(f"similarity:{similarity:.2f}")
            confidence = min(
                1.0,
                (keyword_score * 0.35)
                + (synonym_score * 0.2)
                + (pattern_score * 0.2)
                + (overlap * 0.15)
                + (similarity * 0.1)
                + exact_bonus
                + (min(int(entry.get("priority", 0)), 20) / 20.0 * 0.05),
            )
            threshold = entry.get("confidence_threshold_override") or default_threshold
            candidate = KBMatch(
                entry_id=entry["id"],
                title=entry["title"],
                answer_text=self._render_template(entry["answer_template"], variables),
                confidence=round(confidence, 4),
                match_reasons=reasons,
                requires_escalation=confidence < threshold,
            )
            if (
                best is None
                or candidate.confidence > best.confidence
                or (
                    candidate.confidence == best.confidence
                    and int(entry.get("priority", 0)) > best_priority
                )
            ):
                best = candidate
                best_priority = int(entry.get("priority", 0))
        if best is None:
            return KBMatch(
                entry_id=None,
                title=None,
                answer_text=self.fallback_text,
                confidence=0.0,
                match_reasons=["no_match"],
                requires_escalation=True,
            )
        if best.requires_escalation:
            return KBMatch(
                entry_id=best.entry_id,
                title=best.title,
                answer_text=self.fallback_text,
                confidence=best.confidence,
                match_reasons=best.match_reasons,
                requires_escalation=True,
            )
        return best

    async def preview_match(self, text: str, language: str = "uz", default_threshold: float = 0.62) -> dict:
        match = await self.match_message(
            text,
            language=language,
            default_threshold=default_threshold,
        )
        payload = asdict(match)
        payload["normalized_text"] = normalize_text(text)
        return payload
