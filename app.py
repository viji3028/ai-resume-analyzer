
import streamlit as st
import plotly.express as px

from matcher import extract_resume_text, compare_resume, load_jobs
from reportlab.pdfgen import canvas
from io import BytesIO

def create_pdf_report(job_title, result):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)

    pdf.setTitle("AI Resume Analysis Report")

    y = 800
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, y, "AI Resume Analysis Report")

    y -= 35
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, y, f"Target Job: {job_title}")

    y -= 30
    pdf.drawString(
        50, y,
        f"Overall Demo Score: {result['overall_score']}%"
    )

    y -= 22
    pdf.drawString(
        50, y,
        f"Skill Match Score: {result['skill_score']}%"
    )

    y -= 22
    pdf.drawString(
        50, y,
        f"Text Similarity: {result['text_similarity']}%"
    )

    y -= 35
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(50, y, "Matching Skills")

    y -= 22
    pdf.setFont("Helvetica", 11)

    matched = result["matched_skills"] or ["None"]
    for skill in matched:
        if y < 60:
            pdf.showPage()
            y = 800
            pdf.setFont("Helvetica", 11)
        pdf.drawString(60, y, f"- {skill}")
        y -= 18

    y -= 15
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(50, y, "Skills to Develop")

    y -= 22
    pdf.setFont("Helvetica", 11)

    missing = result["missing_skills"] or ["None"]
    for skill in missing:
        if y < 60:
            pdf.showPage()
            y = 800
            pdf.setFont("Helvetica", 11)
        pdf.drawString(60, y, f"- {skill}")
        y -= 18

    y -= 25
    if y < 60:
        pdf.showPage()
        y = 800

    pdf.setFont("Helvetica-Oblique", 9)
    pdf.drawString(
        50, y,
        "This report supports career preparation; it does not "
        "predict hiring outcomes."
    )

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()


st.set_page_config(
    page_title="AI Resume Matcher",
    page_icon="🎯",
    layout="wide"
)

st.markdown("""
<style>
/* Force a colourful page background */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(
        135deg,
        #e0e7ff 0%,
        #f3e8ff 50%,
        #cffafe 100%
    ) !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

/* Main content */
[data-testid="stMainBlockContainer"] {
    padding-top: 2rem;
}

/* Headings */
h1, h2, h3 {
    color: #312e81 !important;
    font-weight: 800 !important;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #ffffff, #dbeafe) !important;
    border: 1px solid #a5b4fc !important;
    border-radius: 16px !important;
    padding: 20px !important;
    box-shadow: 0 5px 15px rgba(79, 70, 229, 0.12) !important;
}

/* Expandable skill cards */
[data-testid="stExpander"] {
    background: #ffffff !important;
    border: 2px solid #c4b5fd !important;
    border-radius: 14px !important;
}

/* Primary buttons */
.stButton > button {
    background: linear-gradient(90deg, #4f46e5, #9333ea) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: bold !important;
}

/* Download report button */
.stDownloadButton > button {
    background: linear-gradient(90deg, #059669, #0d9488) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: bold !important;
}

/* Alert boxes */
[data-testid="stAlert"] {
    border-radius: 12px !important;
}

/* Text readability */
[data-testid="stMarkdownContainer"] p {
    color: #334155;
}
</style>
""", unsafe_allow_html=True)


st.title("🎯 AI Resume Analyzer & Smart Job Matcher")
st.write(
    "Upload a resume and discover how its listed skills "
    "compare with a selected job description."
)

jobs = load_jobs()

uploaded_file = st.file_uploader(
    "Upload your resume (PDF)",
    type=["pdf"]
)

job_title = st.selectbox(
    "Choose a target job",
    jobs["job_title"].tolist()
)

if uploaded_file and st.button("Analyze Resume"):
    try:
        resume_text = extract_resume_text(
            uploaded_file.getvalue()
        )

        if not resume_text.strip():
            st.error(
                "No selectable text found. Try a text-based PDF."
            )
            st.stop()

        job = jobs.loc[
            jobs["job_title"] == job_title
        ].iloc[0]

        result = compare_resume(resume_text, job)

        st.subheader("Analysis Results")
        
        st.markdown("### 🎯 Skill Match Overview")

        total_skills = (
            len(result["matched_skills"])
            + len(result["missing_skills"])
        )

        if total_skills > 0:
            match_percentage = (
            len(result["matched_skills"]) / total_skills
        )
            st.progress(
                match_percentage,
                text=f"Required Skills Matched: {match_percentage:.0%}"
            )
        else:
            st.info("No required skills available to compare.")


        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Combined Demo Score",
            f'{result["overall_score"]}%'
        )

        col2.metric(
            "Required Skills Matched",
            len(result["matched_skills"])
        )

        col3.metric(
            "Skills to Develop",
            len(result["missing_skills"])
        )

        st.caption(
            "Similarity score is not a probability of getting hired."
        )

        left, right = st.columns(2)

        with left:
            st.markdown("### Matching skills")
            if result["matched_skills"]:
                st.success(
                    ", ".join(result["matched_skills"])
                )
            else:
                st.info("No listed skills matched.")

        with right:
            st.markdown("### Skills to develop")
            if result["missing_skills"]:
                st.warning(
                    ", ".join(result["missing_skills"])
                )
            else:
                st.success("All listed job skills matched.")

        chart_data = {
            "Category": [
                "Skill Match",
                "Text Similarity"
            ],
            "Score": [
                result["skill_score"],
                result["text_similarity"]
            ]
        }

        fig = px.bar(
            chart_data,
            x="Category",
            y="Score",
            range_y=[0, 100],
            title="Resume-to-Job Comparison"
        )

        st.plotly_chart(fig, use_container_width=True)
        
        pdf_bytes = create_pdf_report(job_title, result)

        st.download_button(
            label="📄 Download Analysis Report (PDF)",
            data=pdf_bytes,
            file_name="resume_analysis_report.pdf",
            mime="application/pdf"
        )


        
        if result["missing_skills"]:
            st.markdown("### 🚀 Personalized Skill Improvement Plan")

            learning_resources = {
                "python": {
                    "topic": "Python fundamentals, functions, and projects",
                    "task": "Write a small Python program and build a mini project."
                },
                "sql": {
                    "topic": "SQL queries, joins, and aggregation",
                    "task": "Practise SELECT, WHERE, GROUP BY, and JOIN queries."
                },
                "excel": {
                    "topic": "Excel formulas, sorting, filtering, and pivot tables",
                    "task": "Create a spreadsheet and summarize sample data."
                },
                "power bi": {
                    "topic": "Data visualization and dashboard creation",
                    "task": "Build a dashboard using a sample dataset."
                },
                "machine learning": {
                    "topic": "Supervised learning and model evaluation",
                    "task": "Train and evaluate a simple classification model."
                },
                "c": {
                    "topic": "C fundamentals, arrays, and functions",
                    "task": "Solve beginner programming problems in C."
                }
            }

            st.write(
                "Focus on the missing skills below. "
                "Complete the suggested practice before listing "
                "a skill as a proficiency on your resume."
            )

            for skill in result["missing_skills"]:
                details = learning_resources.get(
                    skill.lower(),
                    {
                        "topic": f"{skill} fundamentals and practical applications",
                        "task": f"Complete a small practice project using {skill}."
                    }
                )

                with st.expander(f"📚 Improve: {skill}"):
                    st.write(f"**What to learn:** {details['topic']}")
                    st.write(f"**Practice task:** {details['task']}")
                    st.checkbox(
                        f"I have practised {skill}",
                        key=f"practice_{skill}"
                    )

        else:
            st.success(
                "🎉 All the listed required skills matched! "
                "Continue building projects and practical experience."
            )


        st.info(
            "This tool supports career preparation. "
            "It does not make hiring decisions."
        )

    except Exception as error:
        st.error(f"Could not analyze the resume: {error}")
