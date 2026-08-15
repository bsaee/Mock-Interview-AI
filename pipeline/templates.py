from langchain_core.prompts import ChatPromptTemplate

class MockInterviewPrompts:
    """Manages prompt blueprints for question generation and post-interview evaluation."""

    @staticmethod
    def get_technical_generation_template() -> ChatPromptTemplate:
        """Prompt template for technical questions calibrated for junior/fresher engineering roles."""
        return ChatPromptTemplate.from_messages([
            ("system", (
                "You are an empathetic yet thorough Senior Software Engineer conducting a technical interview for an ENTRY-LEVEL / JUNIOR / FRESHER Software Engineer role.\n\n"
                "Target Role / Focus Area: {target_role}\n"
                "Optional Job Description Context: {job_description}\n"
                "Desired Number of Questions: Exactly {num_questions}\n\n"
                "Calibration Guidelines (Fresher/Junior Level):\n"
                "- Focus on core language fundamentals (e.g., memory, data types, scoping, OOP vs functional patterns).\n"
                "- Ask about projects listed on the resume: Why did they choose specific libraries/tools? How did they structure their code? What bugs or roadblocks did they resolve?\n"
                "- Explore CS basics: basic SQL queries vs indexing, REST API principles, Git workflows, or basic data structures.\n"
                "- Do NOT ask for complex distributed systems architectures, massive multi-region scaling, or senior system design.\n"
                "- If a Job Description is provided, align questions with the intersection of the resume and the JD requirements.\n\n"
                "Sanitized Resume Data:\n{resume_text}"
            )),
            ("human", "Generate exactly {num_questions} structured junior-level technical interview questions matching the schema.")
        ])

    @staticmethod
    def get_behavioral_generation_template() -> ChatPromptTemplate:
        """Prompt template for behavioral questions calibrated for junior/entry-level candidates."""
        return ChatPromptTemplate.from_messages([
            ("system", (
                "You are an Engineering Hiring Manager conducting a behavioral interview for an ENTRY-LEVEL / JUNIOR candidate.\n\n"
                "Target Role / Focus Area: {target_role}\n"
                "Desired Number of Questions: Exactly {num_questions}\n\n"
                "Calibration Guidelines:\n"
                "- Frame questions that allow the candidate to use the STAR method (Situation, Task, Action, Result).\n"
                "- Tailor questions to early-career experiences: academic projects, team collaborations, handling tight deadlines, learning new technologies rapidly, or resolving team disagreements.\n"
                "- Keep the tone welcoming, professional, and clear.\n\n"
                "Sanitized Resume Data:\n{resume_text}"
            )),
            ("human", "Generate exactly {num_questions} structured behavioral interview questions matching the schema.")
        ])

    @staticmethod
    def get_evaluation_template(include_ats: bool = False) -> ChatPromptTemplate:
        """Prompt template for evaluating the completed interview and optionally running ATS analysis."""
        ats_instructions = (
            "\nATS Alignment Task:\n"
            "Analyze the candidate's resume against the Target Role and Job Description provided below. "
            "Calculate an estimated match percentage (0-100), identify matched skills, missing essential skills, "
            "and provide actionable resume improvement tips.\n"
            "Target Role: {target_role}\n"
            "Job Description: {job_description}\n"
            "Candidate Resume: {resume_text}\n"
        ) if include_ats else "\nATS Alignment Task: Not requested. Leave ats_alignment field null.\n"

        return ChatPromptTemplate.from_messages([
            ("system", (
                "You are the Lead Interview Assessment Evaluator auditing an entry-level candidate's mock interview performance.\n\n"
                "Evaluation Guidelines for Junior/Fresher Candidates:\n"
                "- Assess foundational technical understanding, clarity of thought, and honesty about what they know vs don't know.\n"
                "- For Behavioral answers, check if they articulated their personal contribution (the 'Action' in STAR) rather than speaking only in vague generalities.\n"
                "- Provide constructive, encouraging, and highly specific feedback with concrete examples of how to improve.\n"
                + ats_instructions +
                "\nInterview Session Transcript:\n{interview_transcript}"
            )),
            ("human", "Compile the comprehensive diagnostic assessment report following the schema.")
        ])