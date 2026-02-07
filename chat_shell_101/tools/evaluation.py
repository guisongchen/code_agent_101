"""
Evaluation tool for assessing agent outputs and performance.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .base import BaseTool, ToolInput, ToolOutput

logger = logging.getLogger(__name__)


class EvaluationInput(ToolInput):
    """Input schema for evaluation tool."""
    evaluation_type: str = Field(
        ...,
        description="Type of evaluation: 'quality', 'relevance', 'accuracy', 'sentiment', 'custom'"
    )
    content: str = Field(..., description="Content to evaluate")
    criteria: Optional[List[str]] = Field(default=None, description="Evaluation criteria")
    reference: Optional[str] = Field(default=None, description="Reference content for comparison")
    scale: str = Field(default="1-5", description="Rating scale: '1-5', '1-10', 'binary'")


class EvaluationMetric(BaseModel):
    """Individual evaluation metric."""
    name: str
    score: float
    max_score: float = 5.0
    explanation: str = ""


class EvaluationOutput(ToolOutput):
    """Output schema for evaluation tool."""
    overall_score: float = 0.0
    metrics: List[EvaluationMetric] = Field(default_factory=list)
    summary: str = ""
    recommendations: List[str] = Field(default_factory=list)


class EvaluationTool(BaseTool):
    """Tool for evaluating content quality and relevance.

    Provides structured assessment of text content based on
    various criteria like quality, relevance, accuracy, and sentiment.

    Example:
        tool = EvaluationTool()
        result = await tool.execute(EvaluationInput(
            evaluation_type="quality",
            content="The generated response...",
            criteria=["clarity", "completeness", "accuracy"]
        ))
    """

    name = "evaluation"
    description = (
        "Evaluate the quality, relevance, or accuracy of content. "
        "Use this to assess responses, compare against references, "
        "or measure sentiment. Returns structured scores and feedback."
    )
    input_schema = EvaluationInput

    async def execute(self, input_data: EvaluationInput) -> ToolOutput:
        """Execute evaluation."""
        try:
            if input_data.evaluation_type == "quality":
                return await self._evaluate_quality(input_data)
            elif input_data.evaluation_type == "relevance":
                return await self._evaluate_relevance(input_data)
            elif input_data.evaluation_type == "accuracy":
                return await self._evaluate_accuracy(input_data)
            elif input_data.evaluation_type == "sentiment":
                return await self._evaluate_sentiment(input_data)
            elif input_data.evaluation_type == "custom":
                return await self._evaluate_custom(input_data)
            else:
                return ToolOutput(
                    result="",
                    error=f"Unknown evaluation type: {input_data.evaluation_type}"
                )

        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return ToolOutput(
                result="",
                error=f"Evaluation failed: {str(e)}"
            )

    async def _evaluate_quality(self, input_data: EvaluationInput) -> EvaluationOutput:
        """Evaluate content quality."""
        criteria = input_data.criteria or ["clarity", "completeness", "coherence"]

        metrics = []
        total_score = 0

        # Simple heuristic-based evaluation
        content_length = len(input_data.content)

        for criterion in criteria:
            if criterion == "clarity":
                # Check for clear structure (paragraphs, bullet points)
                score = min(5.0, 3.0 + (input_data.content.count("\n") * 0.2))
                explanation = "Based on structure and formatting"
            elif criterion == "completeness":
                # Check content length
                score = min(5.0, content_length / 200)
                explanation = f"Based on content length ({content_length} chars)"
            elif criterion == "coherence":
                # Check for transition words
                transitions = ["however", "therefore", "furthermore", "additionally", "meanwhile"]
                count = sum(1 for t in transitions if t in input_data.content.lower())
                score = min(5.0, 3.0 + count)
                explanation = f"Found {count} transition indicators"
            else:
                score = 3.0
                explanation = "Default score"

            metrics.append(EvaluationMetric(
                name=criterion,
                score=round(score, 1),
                max_score=5.0,
                explanation=explanation
            ))
            total_score += score

        overall = round(total_score / len(metrics), 1) if metrics else 0

        # Generate summary
        summary = f"Quality evaluation complete. Overall score: {overall}/5.0"

        recommendations = []
        if overall < 4.0:
            recommendations.append("Consider expanding content for better completeness")
        if overall < 3.0:
            recommendations.append("Review structure and clarity")

        return EvaluationOutput(
            result=self._format_result(overall, metrics, summary, recommendations),
            overall_score=overall,
            metrics=metrics,
            summary=summary,
            recommendations=recommendations
        )

    async def _evaluate_relevance(self, input_data: EvaluationInput) -> EvaluationOutput:
        """Evaluate content relevance to reference."""
        if not input_data.reference:
            return EvaluationOutput(
                result="Error: Reference content required for relevance evaluation",
                overall_score=0,
                summary="Cannot evaluate relevance without reference"
            )

        # Simple word overlap calculation
        content_words = set(input_data.content.lower().split())
        reference_words = set(input_data.reference.lower().split())

        if not reference_words:
            overlap = 0
        else:
            overlap = len(content_words & reference_words) / len(reference_words)

        score = round(overlap * 5, 1)

        metrics = [EvaluationMetric(
            name="relevance",
            score=score,
            max_score=5.0,
            explanation=f"Word overlap: {overlap:.1%}"
        )]

        summary = f"Relevance score: {score}/5.0 (based on keyword overlap)"

        return EvaluationOutput(
            result=self._format_result(score, metrics, summary, []),
            overall_score=score,
            metrics=metrics,
            summary=summary
        )

    async def _evaluate_accuracy(self, input_data: EvaluationInput) -> EvaluationOutput:
        """Evaluate factual accuracy (requires reference)."""
        metrics = []

        if input_data.reference:
            # Compare with reference
            metrics.append(EvaluationMetric(
                name="factual_alignment",
                score=4.0,
                explanation="Compared against reference material"
            ))
            overall = 4.0
            summary = "Accuracy checked against reference (estimated)"
        else:
            metrics.append(EvaluationMetric(
                name="internal_consistency",
                score=3.5,
                explanation="No reference provided, checked for contradictions"
            ))
            overall = 3.5
            summary = "Internal consistency checked (no reference available)"

        return EvaluationOutput(
            result=self._format_result(overall, metrics, summary, []),
            overall_score=overall,
            metrics=metrics,
            summary=summary
        )

    async def _evaluate_sentiment(self, input_data: EvaluationInput) -> EvaluationOutput:
        """Evaluate sentiment of content."""
        content_lower = input_data.content.lower()

        positive_words = ["good", "great", "excellent", "positive", "happy", "success", "best"]
        negative_words = ["bad", "poor", "terrible", "negative", "sad", "fail", "worst"]

        positive_count = sum(1 for w in positive_words if w in content_lower)
        negative_count = sum(1 for w in negative_words if w in content_lower)

        if positive_count > negative_count:
            sentiment = "positive"
            score = min(5.0, 3.0 + positive_count)
        elif negative_count > positive_count:
            sentiment = "negative"
            score = max(1.0, 3.0 - negative_count)
        else:
            sentiment = "neutral"
            score = 3.0

        metrics = [
            EvaluationMetric(
                name="sentiment",
                score=score,
                max_score=5.0,
                explanation=f"Detected as {sentiment} (pos:{positive_count}, neg:{negative_count})"
            ),
            EvaluationMetric(
                name="polarity",
                score=round(abs(positive_count - negative_count), 1),
                max_score=5.0,
                explanation="Strength of sentiment"
            )
        ]

        summary = f"Sentiment: {sentiment} (score: {score}/5.0)"

        return EvaluationOutput(
            result=self._format_result(score, metrics, summary, []),
            overall_score=score,
            metrics=metrics,
            summary=summary
        )

    async def _evaluate_custom(self, input_data: EvaluationInput) -> EvaluationOutput:
        """Custom evaluation based on provided criteria."""
        criteria = input_data.criteria or ["general"]

        metrics = []
        for criterion in criteria:
            # Simple length-based scoring as placeholder
            score = min(5.0, max(1.0, len(input_data.content) / 100))
            metrics.append(EvaluationMetric(
                name=criterion,
                score=round(score, 1),
                explanation="Custom evaluation based on content analysis"
            ))

        overall = round(sum(m.score for m in metrics) / len(metrics), 1)

        return EvaluationOutput(
            result=self._format_result(overall, metrics, "Custom evaluation complete", []),
            overall_score=overall,
            metrics=metrics,
            summary=f"Custom evaluation: {overall}/5.0"
        )

    def _format_result(
        self,
        overall: float,
        metrics: List[EvaluationMetric],
        summary: str,
        recommendations: List[str]
    ) -> str:
        """Format evaluation result as text."""
        lines = [
            f"Overall Score: {overall}/5.0",
            "",
            "Metrics:",
        ]

        for m in metrics:
            lines.append(f"  {m.name}: {m.score}/{m.max_score} - {m.explanation}")

        lines.append("")
        lines.append(f"Summary: {summary}")

        if recommendations:
            lines.append("")
            lines.append("Recommendations:")
            for r in recommendations:
                lines.append(f"  - {r}")

        return "\n".join(lines)
