import io
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib import colors

class ReportGenerator:
    """Generates downloadable diagnostic reports in Markdown and PDF formats."""

    @staticmethod
    def generate_markdown_report(
        report_data: Any,
        transcript: List[Dict[str, Any]],
        round_type: str,
        target_role: str = ""
    ) -> str:
        """Compiles the session into a clean Markdown string."""
        md = []
        md.append("# 🎯 AI Mock Interview Diagnostic Report\n")
        md.append(f"**Evaluation Round:** {round_type}")
        if target_role:
            md.append(f"**Target Role:** {target_role}")
        md.append(f"**Composite Score:** {report_data.composite_score_out_of_10} / 10\n")
        md.append("---\n")

        # Metric Breakdown
        md.append("## 📊 Metric Breakdown")
        mb = report_data.metric_breakdown
        md.append(f"- **Technical Accuracy / Setup:** {mb.technical_accuracy_or_situation}/10")
        md.append(f"- **Communication Clarity:** {mb.communication_clarity}/10")
        md.append(f"- **Foundational Depth / Action:** {mb.foundational_depth_or_action}/10\n")

        # Performance Critique
        md.append("## 📝 Overall Performance Critique")
        md.append(f"{report_data.overall_performance_critique}\n")

        # Actionable Feedback
        md.append("## 💡 Actionable Improvement Steps")
        for idx, tip in enumerate(report_data.reconstructive_feedback, 1):
            md.append(f"{idx}. {tip}")
        md.append("")

        # ATS Report (if available)
        if report_data.ats_alignment:
            ats = report_data.ats_alignment
            md.append("## 🎯 ATS Alignment Assessment")
            md.append(f"**Match Estimation:** {ats.ats_match_percentage}%")
            md.append(f"**Matched Skills:** {', '.join(ats.matched_skills) if ats.matched_skills else 'None detected'}")
            md.append(f"**Missing Skills / Keywords:** {', '.join(ats.missing_critical_skills) if ats.missing_critical_skills else 'None'}\n")
            if ats.resume_optimization_tips:
                md.append("**Optimization Tips:**")
                for tip in ats.resume_optimization_tips:
                    md.append(f"- {tip}")
                md.append("")

        # Full Transcript
        md.append("## 📜 Full Interview Transcript")
        for idx, turn in enumerate(transcript, 1):
            md.append(f"### Question {idx} [{turn.get('targeted_node', 'N/A')}]")
            md.append(f"**Q:** {turn.get('question', '')}")
            md.append(f"**Candidate Answer:** {turn.get('answer', '')}\n")

        return "\n".join(md)

    @staticmethod
    def generate_pdf_report(
        report_data: Any,
        transcript: List[Dict[str, Any]],
        round_type: str,
        target_role: str = ""
    ) -> bytes:
        """Builds a formatted PDF document in memory and returns the raw bytes."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#1E293B')
        )
        heading_style = ParagraphStyle(
            'ReportHeading',
            parent=styles['Heading2'],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor('#0F172A'),
            spaceBefore=10,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            'ReportBody',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#334155')
        )

        story = []

        # Document Header
        story.append(Paragraph("AI Mock Interview Performance Audit", title_style))
        story.append(Spacer(1, 4))
        meta_info = f"Round: <b>{round_type}</b>"
        if target_role:
            meta_info += f" | Target Role: <b>{target_role}</b>"
        meta_info += f" | Overall Score: <b>{report_data.composite_score_out_of_10} / 10</b>"
        story.append(Paragraph(meta_info, body_style))
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=10))

        # Metrics Score Table
        mb = report_data.metric_breakdown
        score_data = [
            ["Metric Category", "Score"],
            ["Technical Accuracy / Setup", f"{mb.technical_accuracy_or_situation} / 10"],
            ["Communication Clarity", f"{mb.communication_clarity} / 10"],
            ["Foundational Depth / Action", f"{mb.foundational_depth_or_action} / 10"]
        ]
        if report_data.ats_alignment:
            score_data.append(["ATS Match Estimation", f"{report_data.ats_alignment.ats_match_percentage}%"])

        score_table = Table(score_data, colWidths=[350, 150])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#0F172A')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 12))

        # Performance Critique
        story.append(Paragraph("Overall Performance Critique", heading_style))
        story.append(Paragraph(report_data.overall_performance_critique, body_style))
        story.append(Spacer(1, 10))

        # Actionable Improvements
        story.append(Paragraph("Actionable Improvement Steps", heading_style))
        for idx, tip in enumerate(report_data.reconstructive_feedback, 1):
            story.append(Paragraph(f"<b>{idx}.</b> {tip}", body_style))
            story.append(Spacer(1, 3))
        story.append(Spacer(1, 10))

        # ATS Alignment Section (if present)
        if report_data.ats_alignment:
            ats = report_data.ats_alignment
            story.append(Paragraph("ATS Role Alignment Assessment", heading_style))
            matched_str = ", ".join(ats.matched_skills) if ats.matched_skills else "None explicitly detected"
            missing_str = ", ".join(ats.missing_critical_skills) if ats.missing_critical_skills else "None"
            story.append(Paragraph(f"<b>Matched Skills:</b> {matched_str}", body_style))
            story.append(Spacer(1, 2))
            story.append(Paragraph(f"<b>Missing Keywords:</b> {missing_str}", body_style))
            story.append(Spacer(1, 4))
            for tip in ats.resume_optimization_tips:
                story.append(Paragraph(f"• {tip}", body_style))
            story.append(Spacer(1, 10))

        # Full Transcript
        story.append(Paragraph("Interview Transcript Log", heading_style))
        for idx, turn in enumerate(transcript, 1):
            q_text = f"<b>Q{idx} [{turn.get('targeted_node', '')}]:</b> {turn.get('question', '')}"
            a_text = f"<b>Candidate Answer:</b> {turn.get('answer', '')}"
            story.append(Paragraph(q_text, body_style))
            story.append(Spacer(1, 2))
            story.append(Paragraph(a_text, body_style))
            story.append(Spacer(1, 6))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()