from pydantic import BaseModel, Field
from typing import List, Optional

class InterviewQuestionPayload(BaseModel):
    """Data contract for individual generated interview questions."""
    question_id: int = Field(description="Sequential identifier tracking the question turn (1-indexed).")
    question_text: str = Field(description="The question string payload calibrated for a junior/entry-level candidate.")
    targeted_evaluation_node: str = Field(description="The specific skill or concept evaluated (e.g., 'Python OOP Mechanics', 'Database Indexing', 'STAR Conflict Resolution').")

class QuestionGenerationMatrix(BaseModel):
    """Container holding the dynamic array of generated interview questions."""
    round_type: str = Field(description="'Technical' or 'Behavioral'.")
    target_role: Optional[str] = Field(default=None, description="The job role being targeted, if specified.")
    questions: List[InterviewQuestionPayload] = Field(description="List of generated questions matching the requested question count.")

class ComponentMetrics(BaseModel):
    """Sub-metrics mapping discrete scoring categories out of 10."""
    technical_accuracy_or_situation: int = Field(description="Score (1-10) for technical precision or STAR Situation/Task setup.")
    communication_clarity: int = Field(description="Score (1-10) for verbal clarity and articulation.")
    foundational_depth_or_action: int = Field(description="Score (1-10) for core language/CS understanding or STAR individual Action/Result demonstration.")

class ATSAlignmentReport(BaseModel):
    """Audit metrics comparing the candidate's resume against the target role/job description."""
    ats_match_percentage: int = Field(description="Estimated match percentage (0-100) based on skills and keywords.")
    matched_skills: List[str] = Field(description="Skills and competencies from the resume that align with the target role.")
    missing_critical_skills: List[str] = Field(description="Important skills or keywords mentioned in the JD that are absent from the resume.")
    resume_optimization_tips: List[str] = Field(description="Specific suggestions to optimize the resume for applicant tracking systems.")

class DiagnosticReportSchema(BaseModel):
    """Comprehensive post-interview evaluation report."""
    overall_performance_critique: str = Field(description="Detailed engineering feedback analyzing the candidate's responses across all turns.")
    composite_score_out_of_10: int = Field(description="Unified overall score out of 10 summarizing performance.")
    metric_breakdown: ComponentMetrics = Field(description="Categorical score breakdown.")
    reconstructive_feedback: List[str] = Field(description="Step-by-step actionable advice on how the candidate can improve their answers.")
    ats_alignment: Optional[ATSAlignmentReport] = Field(default=None, description="ATS alignment assessment, populated if target role or JD was provided.")