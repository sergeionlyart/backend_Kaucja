from __future__ import annotations

from app.legal_memo.models import FactsPoint, MemoPoint, RiskPoint, StrategicMemo


def render_memo_markdown(memo: StrategicMemo) -> str:
    lines: list[str] = [f"# {memo.title}", ""]
    lines.extend(_render_memo_points("Краткий вывод", memo.executive_summary))
    lines.extend(_render_facts("Учитываемые факты", memo.facts_considered))
    lines.extend(_render_legal_analysis(memo))
    lines.extend(_render_plain_list("Рекомендуемые следующие шаги", memo.recommended_next_steps))
    lines.extend(_render_plain_list("Ограничения", memo.limitations))
    return "\n".join(lines).strip() + "\n"


def _render_memo_points(title: str, points: list[MemoPoint]) -> list[str]:
    lines = [f"## {title}", ""]
    if not points:
        lines.append("- Нет данных.")
        lines.append("")
        return lines
    for point in points:
        lines.append(f"- {point.text}{_render_refs(point.legal_ref_ids, point.evidence_ref_ids)}")
    lines.append("")
    return lines


def _render_facts(title: str, points: list[FactsPoint]) -> list[str]:
    lines = [f"## {title}", ""]
    if not points:
        lines.append("- Нет данных.")
        lines.append("")
        return lines
    for point in points:
        lines.append(f"- {point.text}{_render_refs([], point.evidence_ref_ids)}")
    lines.append("")
    return lines


def _render_legal_analysis(memo: StrategicMemo) -> list[str]:
    lines = ["## Правовой анализ", ""]
    if not memo.legal_analysis:
        lines.append("- Нет данных.")
        lines.append("")
        return lines
    for section in memo.legal_analysis:
        lines.append(f"### {section.issue_title} ({section.issue_code})")
        lines.append("")
        for point in section.analysis_points:
            lines.append(
                f"- {point.text}{_render_refs(point.legal_ref_ids, point.evidence_ref_ids)}"
            )
        if section.risks:
            lines.append("")
            lines.append("Риски:")
            for risk in section.risks:
                lines.append(f"- {risk.text}{_render_risk_refs(risk)}")
        lines.append("")
        lines.append(f"Практический вывод: {section.practical_takeaway}")
        lines.append("")
    return lines


def _render_plain_list(title: str, items: list[str]) -> list[str]:
    lines = [f"## {title}", ""]
    if not items:
        lines.append("- Нет данных.")
        lines.append("")
        return lines
    for item in items:
        lines.append(f"- {item}")
    lines.append("")
    return lines


def _render_refs(legal_ref_ids: list[str], evidence_ref_ids: list[str]) -> str:
    refs = [*legal_ref_ids, *evidence_ref_ids]
    return f" [{' ; '.join(refs)}]" if refs else ""


def _render_risk_refs(risk: RiskPoint) -> str:
    return f" [{' ; '.join(risk.legal_ref_ids)}]" if risk.legal_ref_ids else ""
