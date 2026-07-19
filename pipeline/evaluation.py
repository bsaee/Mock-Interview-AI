from pydantic import BaseModel, Field
from typing import List

class InterviewQuestionPayload(BaseModel):
    """Data contract for the structural generation of interview questions."""
    question_id: int = Field(description="Sequential identifier tracking the question turn (1 to 4).")
    question_text: str = Field(description="The actual question string payload to be converted to speech.")
    targeted_evaluation_node: str = Field(description="Explains what this question is testing (e.g., 'Python memory optimization', 'STAR conflict assessment').")

class QuestionGenerationMatrix(BaseModel):
    """Data contract enclosing the full array of generated questions for the round."""
    round_type: str = Field(description="Explicitly tracks if this container holds 'Technical' or 'Behavioral' questions.")
    questions: List[InterviewQuestionPayload] = Field(description="A strictly bound array containing exactly 4 generated question objects.")

class ComponentMetrics(BaseModel):
    """Sub-metrics mapping discrete scoring metrics."""
    technical_accuracy_or_situation: int = Field(description="Score out of 10 evaluating core technical accuracy or STAR situation framing.")
    communication_clarity: int = Field(description="Score out of 10 evaluating verbal clarity and coherence.")
    complexity_awareness_or_action: int = Field(description="Score out of 10 evaluating big-O architectural optimization awareness or STAR individual action delivery.")

class DiagnosticReportSchema(BaseModel):
    """The type-safe data contract mapping the final evaluation dashboard report."""
    overall_performance_critique: str = Field(description="Granular software engineering critique reviewing the candidate's total turn sequence.")
    composite_score_out_of_10: int = Field(description="The unified score summarizing total round performance.")
    metric_breakdown: ComponentMetrics = Field(description="The structured breakdowns mapping detailed analytical points.")
    reconstructive_feedback: List[str] = Field(description="Actionable, explicit steps detailing exactly how the candidate should refactor their responses.")