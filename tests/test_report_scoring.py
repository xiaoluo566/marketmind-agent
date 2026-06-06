from __future__ import annotations

from app.reporting.generator import (
    EvidenceSnippet,
    ReportGenerationInput,
    StructuredReportGenerator,
)
from app.reporting.scoring import (
    CompetitiveRiskScorer,
    ScorecardInput,
    attach_scorecard_to_report,
)


def build_evidence_snippets() -> list[EvidenceSnippet]:
    return [
        EvidenceSnippet(
            evidence_ref="chunk:chk_quality_1",
            content="The pump failed after three days and the machine started leaking.",
            similarity=0.91,
            rating=1.0,
            source_url="https://example.com/product#quality-1",
        ),
        EvidenceSnippet(
            evidence_ref="chunk:chk_quality_2",
            content="Poor quality. The pressure button broke during the first week.",
            similarity=0.82,
            rating=2.0,
            source_url="https://example.com/product#quality-2",
        ),
        EvidenceSnippet(
            evidence_ref="chunk:chk_support_1",
            content="Support ignored my return request and refund email.",
            similarity=0.86,
            rating=1.0,
            source_url="https://example.com/product#support-1",
        ),
        EvidenceSnippet(
            evidence_ref="chunk:chk_shipping_1",
            content="Shipping was slow and the delivery arrived late.",
            similarity=0.72,
            rating=2.0,
            source_url="https://example.com/product#shipping-1",
        ),
    ]


def test_scorecard_groups_evidence_by_dimension_and_binds_refs() -> None:
    scorecard = CompetitiveRiskScorer().score(
        ScorecardInput(
            task_id="tsk_score_001",
            evidence_snippets=build_evidence_snippets(),
            minimum_samples=2,
        )
    )

    quality = scorecard.get_dimension("quality")
    support = scorecard.get_dimension("support")

    assert scorecard.status == "scored"
    assert quality is not None
    assert quality.evidence_refs == ["chunk:chk_quality_1", "chunk:chk_quality_2"]
    assert quality.risk_score >= 70
    assert quality.opportunity_score >= 60
    assert "quality" in quality.explanation.lower()
    assert support is not None
    assert support.evidence_refs == ["chunk:chk_support_1"]
    assert set(scorecard.evidence_refs) == {
        "chunk:chk_quality_1",
        "chunk:chk_quality_2",
        "chunk:chk_support_1",
        "chunk:chk_shipping_1",
    }


def test_low_sample_dimensions_are_discounted_and_marked_uncertain() -> None:
    scorecard = CompetitiveRiskScorer().score(
        ScorecardInput(
            task_id="tsk_score_001",
            evidence_snippets=[
                EvidenceSnippet(
                    evidence_ref="chunk:chk_packaging_1",
                    content="The box arrived crushed and the packaging was wet.",
                    similarity=0.8,
                    rating=1.0,
                )
            ],
            minimum_samples=3,
        )
    )

    packaging = scorecard.get_dimension("packaging")

    assert packaging is not None
    assert packaging.sample_size == 1
    assert packaging.sample_warning == "LOW_SAMPLE_SIZE"
    assert packaging.confidence < 0.5
    assert packaging.risk_score < 70
    assert "样本不足" in packaging.explanation


def test_no_evidence_scorecard_does_not_fabricate_scores() -> None:
    scorecard = CompetitiveRiskScorer().score(
        ScorecardInput(task_id="tsk_score_empty", evidence_snippets=[])
    )

    assert scorecard.status == "insufficient_evidence"
    assert scorecard.overall_risk_score == 0
    assert scorecard.overall_opportunity_score == 0
    assert scorecard.dimensions == []
    assert scorecard.evidence_refs == []
    assert "证据不足" in scorecard.summary


def test_attach_scorecard_to_report_returns_new_report_and_renders_markdown() -> None:
    evidence_snippets = build_evidence_snippets()
    report = StructuredReportGenerator().generate(
        ReportGenerationInput(
            task_id="tsk_score_001",
            product_name="Portable Espresso Maker",
            evidence_snippets=evidence_snippets,
            requested_focus=["quality", "return support"],
        )
    )
    scorecard = CompetitiveRiskScorer().score(
        ScorecardInput(
            task_id="tsk_score_001",
            evidence_snippets=evidence_snippets,
            minimum_samples=2,
        )
    )

    scored_report = attach_scorecard_to_report(report, scorecard)
    markdown = scored_report.to_markdown()

    assert "analysis_scorecard" not in report.metadata
    assert scored_report.metadata["analysis_scorecard"]["status"] == "scored"
    assert "## 维度评分" in markdown
    assert "质量风险" in markdown
    assert "chunk:chk_quality_1" in markdown
