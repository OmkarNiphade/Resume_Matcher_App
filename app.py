import streamlit as st
import pdfplumber
import spacy
import re
from datetime import datetime
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import csv
import os

from email_utils import send_email
from job_database import create_job_table, add_job, get_all_jobs
from fpdf import FPDF  # <-- Added import for PDF generation

import spacy
import subprocess
import importlib.util

# Check and download the spaCy model if not found
if importlib.util.find_spec("en_core_web_sm") is None:
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])

nlp = spacy.load("en_core_web_sm")

# ---- Constants ----
INTERVIEW_QUESTIONS = {
    "python": [
        "Explain Python’s memory management.",
        "What are Python decorators?",
        "How does Python handle multithreading?"
    ],
    "machine learning": [
        "What is overfitting and how can you prevent it?",
        "Explain the difference between supervised and unsupervised learning."
    ],
    "communication": [
        "Tell me about a time you resolved a conflict at work.",
        "How do you handle difficult stakeholders?"
    ],
}

APPLICATIONS_FILE = "applications.csv"
PORTFOLIO_FILE = "portfolio.csv"

# ---- Page Config ----
st.set_page_config(page_title="Resume & Job Match Analyzer", layout="wide")

# ---- Load NLP Model ----
nlp = spacy.load("en_core_web_sm")

# ---- Sidebar Navigation ----
st.sidebar.title("🔍 Navigation")
selected_page = st.sidebar.radio("Go to", ["🏠 Home", "📝 Apply Now", "📋 Application Status"])

with st.sidebar.expander("📈 Stats"):
    app_count = len(open(APPLICATIONS_FILE).readlines()) - 1 if os.path.exists(APPLICATIONS_FILE) else 0
    st.markdown(f"**Total Applications:** {app_count}")

# ---- Utility Functions ----

def extract_text_from_pdf(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        return " ".join([page.extract_text() for page in pdf.pages if page.extract_text()])

def calculate_similarity(text1, text2):
    tfidf = TfidfVectorizer().fit_transform([text1, text2])
    score = cosine_similarity(tfidf[0:1], tfidf[1:2])
    return round(float(score[0][0]) * 100, 2)

def split_resume_sections(resume_text):
    sections = {}
    current_section = "Summary"
    sections[current_section] = []

    section_headers = ["summary", "objective", "experience", "work history", "skills", "education", "certifications", "projects"]

    lines = resume_text.split("\n")
    for line in lines:
        line_lower = line.strip().lower()
        if any(header in line_lower for header in section_headers):
            for header in section_headers:
                if header in line_lower:
                    current_section = header.title()
                    sections[current_section] = []
                    break
        else:
            sections[current_section].append(line.strip())

    for key in sections:
        sections[key] = " ".join(sections[key]).strip()

    return sections

def calculate_section_scores(sections, job_desc_text):
    scores = {}
    for section, text in sections.items():
        scores[section] = calculate_similarity(text, job_desc_text) if text else 0.0
    return scores

def get_suggestions(resume_text, job_desc_text):
    resume_doc = nlp(resume_text.lower())
    job_doc = nlp(job_desc_text.lower())

    def clean_tokens(doc):
        return [token.lemma_ for token in doc if token.is_alpha and not token.is_stop]

    resume_tokens = set(clean_tokens(resume_doc))
    job_tokens = clean_tokens(job_doc)
    job_token_freq = Counter(job_tokens)

    missing_keywords = [(kw, freq) for kw, freq in job_token_freq.items() if kw not in resume_tokens]
    missing_keywords.sort(key=lambda x: x[1], reverse=True)

    suggestions = "### 🔍 Ranked Missing Keywords (Most Important First):\n\n"
    if missing_keywords:
        for kw, freq in missing_keywords[:20]:
            suggestions += f"- **{kw}** (mentioned {freq} times)\n"
        suggestions += "\n📌 Try incorporating the above keywords to better align your resume."
    else:
        suggestions += "Your resume already includes most of the important keywords from the job description!"

    return suggestions

def keyword_matching(resume_text, job_desc_text):
    resume_doc = nlp(resume_text.lower())
    job_doc = nlp(job_desc_text.lower())

    resume_tokens = set(token.lemma_ for token in resume_doc if token.is_alpha and not token.is_stop)
    job_tokens = set(token.lemma_ for token in job_doc if token.is_alpha and not token.is_stop)

    matched = job_tokens.intersection(resume_tokens)
    missing = job_tokens - resume_tokens

    def highlight_keywords(words, color):
        return ", ".join([f"<span style='color:{color}'>{w}</span>" for w in sorted(words)])

    matched_str = highlight_keywords(matched, "green")
    missing_str = highlight_keywords(missing, "red")

    return matched_str, missing_str

def extract_basic_info(text):
    email = re.findall(r'[\w\.-]+@[\w\.-]+', text)
    phone = re.findall(r'\+?\d[\d\s-]{8,}\d', text)
    name = text.split('\n')[0] if text else ""
    return {
        "name": name,
        "email": email[0] if email else "",
        "phone": phone[0] if phone else ""
    }

def save_application(data):
    file_exists = os.path.isfile(APPLICATIONS_FILE)
    with open(APPLICATIONS_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

def load_applications():
    if not os.path.isfile(APPLICATIONS_FILE):
        return []
    with open(APPLICATIONS_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

# ---- PDF Save Function (Unicode font) ----
def save_text_as_pdf(text, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    # Use your uploaded DejaVu font file (update path if needed)
    pdf.add_font('DejaVu', '', '/mnt/data/00ae9d37-0ff1-4cb4-b7f8-2d3bf033f85b.ttf', uni=True)
    pdf.set_font("DejaVu", size=12)
    for line in text.split('\n'):
        pdf.multi_cell(0, 10, line)
    pdf.output(filename)

# ---- Pages ----

def application_form(prefill_data=None, job_info=None):
    if "submitted" not in st.session_state:
        st.session_state["submitted"] = False

    message_container = st.empty()

    with st.form("job_application_form"):
        st.header("📝 Job Application Form")

        name = st.text_input("Full Name", value=prefill_data.get("name", "") if prefill_data else "")
        email = st.text_input("Email", value=prefill_data.get("email", "") if prefill_data else "")
        phone = st.text_input("Phone Number", value=prefill_data.get("phone", "") if prefill_data else "")
        education = st.text_area("Education Details", placeholder="Enter your education background...")
        experience = st.text_area("Work Experience", placeholder="Enter your work experience...")

        # Job info inputs - prefilled if job_info passed
        job_title = st.text_input("Job Title", value=job_info.get("title", "") if job_info else "")
        job_company = st.text_input("Company Name", value=job_info.get("company", "") if job_info else "")
        job_location = st.text_input("Job Location", value=job_info.get("location", "") if job_info else "")

        submit = st.form_submit_button("Submit Application")

        if submit:
            if not education.strip():
                message_container.warning("⚠️ Please fill in the education section.")
                st.session_state["submitted"] = False
            else:
                data = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "education": education,
                    "experience": experience,
                    "job_title": job_title,
                    "job_company": job_company,
                    "job_location": job_location
                }
                save_application(data)
                st.session_state["submitted"] = True

                email_body = f"""Hi {name},

Thank you for applying to the position of {job_title} at {job_company} located in {job_location}.
We have received your application with the following details:

📞 Phone: {phone}
🎓 Education: {education}
💼 Experience: {experience}

We will get back to you shortly.

Best regards,  
{job_company}
"""

                try:
                    send_email(
                        to=email,
                        subject="Your Application Has Been Received",
                        body=email_body
                    )
                except Exception as e:
                    st.error(f"❌ Failed to send email: {e}")

    if st.session_state["submitted"]:
        message_container.success("✅ Application submitted! Please also visit the official job page to complete your application.")

def application_status_page():
    st.title("📋 Submitted Applications Status")
    applications = load_applications()
    if not applications:
        st.info("No applications submitted yet.")
    else:
        st.dataframe(applications)

def main_page():
    st.title("📄 Resume & Job Match Analyzer")
    resume_file = st.file_uploader("Upload your Resume (PDF)", type="pdf")
    job_desc = st.text_area("Paste Job Description Here")

    if resume_file and job_desc:
        with st.spinner("Extracting text from resume..."):
            resume_text = extract_text_from_pdf(resume_file)

        sections = split_resume_sections(resume_text)
        section_scores = calculate_section_scores(sections, job_desc)

        st.subheader("📊 Section-wise Match Scores")
        for section, score in section_scores.items():
            st.write(f"**{section}:** {score}%")

        st.subheader("✅ Overall Match Score")
        score = calculate_similarity(resume_text, job_desc)
        st.metric(label="Match Score", value=f"{score}%")

        if score < 70:
            st.warning("The match is below 70%. Consider improving your resume.")

        if st.button("💡 Get Suggestions to Improve Resume"):
            with st.spinner("Analyzing..."):
                suggestions = get_suggestions(resume_text, job_desc)
            st.subheader("🔍 AI Suggestions")
            st.write(suggestions)

        st.subheader("🔍 Keyword Matching")
        matched_str, missing_str = keyword_matching(resume_text, job_desc)
        st.markdown(f"✅ Matched Keywords:\n\n{matched_str}", unsafe_allow_html=True)
        st.markdown(f"❌ Missing Keywords:\n\n{missing_str}", unsafe_allow_html=True)

        # === Added Save PDF button here ===
        if st.button("💾 Save Resume as PDF"):
            save_folder = "saved_resumes"
            os.makedirs(save_folder, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(save_folder, f"resume_{timestamp}.pdf")
            save_text_as_pdf(resume_text, filename)
            st.success(f"Resume saved as PDF: {filename}")

            with open(filename, "rb") as f:
                st.download_button(
                    label="⬇️ Download Resume PDF",
                    data=f,
                    file_name=os.path.basename(filename),
                    mime="application/pdf"
                )

        if st.button("Apply for this Job"):
            basic_info = extract_basic_info(resume_text)
            job_info = {
                "title": "N/A",
                "company": "N/A",
                "location": "N/A"
            }
            # For demo, you might want to extract job title/company/location from job_desc or input separately.
            st.session_state["application_info"] = (basic_info, job_info)
            st.experimental_rerun()

if selected_page == "🏠 Home":
    main_page()
elif selected_page == "📝 Apply Now":
    if "application_info" in st.session_state:
        prefill, job_info = st.session_state["application_info"]
        application_form(prefill, job_info)
    else:
        st.info("Please analyze your resume and job description first on the Home page, then click 'Apply for this Job'.")
elif selected_page == "📋 Application Status":
    application_status_page()
