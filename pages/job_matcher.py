import streamlit as st
import requests
import pdfplumber
from datetime import datetime, timezone
from dateutil import parser
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
import string
from collections import Counter

# Download stopwords once
nltk.download('stopwords')

# Adzuna credentials
ADZUNA_APP_ID = "b841a9e9"
ADZUNA_APP_KEY = "a2cb932c2d2c2f9c142f75ee5a9bb7b0"

COUNTRY_CODE = "in"
DESIRED_LOCATIONS = ["Nashik", "Maharashtra", "India"]

if 'saved_jobs' not in st.session_state:
    st.session_state.saved_jobs = []

def extract_text_from_pdf(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        return " ".join([page.extract_text() for page in pdf.pages if page.extract_text()])

def calculate_similarity(resume_text, job_text):
    tfidf = TfidfVectorizer().fit_transform([resume_text, job_text])
    score = cosine_similarity(tfidf[0:1], tfidf[1:2])
    return float(score[0][0])

def format_posting_date(created_str):
    try:
        post_time = parser.parse(created_str)
        if post_time.tzinfo is None:
            post_time = post_time.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        diff = now - post_time
        days = diff.days
        if days == 0:
            return "Posted: Today"
        elif days == 1:
            return "Posted: Yesterday"
        elif days < 7:
            return f"Posted: {days} days ago"
        elif days < 30:
            weeks = days // 7
            return f"Posted: {weeks} week{'s' if weeks > 1 else ''} ago"
        else:
            months = days // 30
            return f"Posted: {months} month{'s' if months > 1 else ''} ago"
    except Exception:
        return ""

def fetch_adzuna_jobs(keyword):
    url = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY_CODE}/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": 50,
        "what": keyword,
        "content-type": "application/json"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        jobs_data = response.json().get("results", [])
        return [
            {
                "title": job.get("title", "No Title"),
                "description": job.get("description", ""),
                "redirect_url": job.get("redirect_url", ""),
                "source": "Adzuna",
                "created": job.get("created", ""),
                "location": job.get("location", {}).get("display_name", "")
            }
            for job in jobs_data
        ]
    return []

def fetch_remotive_jobs():
    response = requests.get("https://remotive.io/api/remote-jobs")
    now = datetime.now(timezone.utc)
    if response.status_code == 200:
        jobs_data = response.json().get("jobs", [])
        filtered_jobs = []
        for job in jobs_data:
            pub_date_str = job.get("publication_date")
            if pub_date_str:
                pub_date = parser.parse(pub_date_str)
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=timezone.utc)
                if (now - pub_date).days <= 14:
                    filtered_jobs.append({
                        "title": job.get("title", "No Title"),
                        "description": job.get("description", ""),
                        "redirect_url": job.get("url", ""),
                        "source": "Remotive",
                        "created": pub_date_str,
                        "location": job.get("candidate_required_location", "")
                    })
        return filtered_jobs
    return []

def extract_meaningful_keywords(text, top_n=10):
    stop_words = set(stopwords.words('english'))
    words = text.lower().split()
    cleaned_words = []
    for w in words:
        w = w.strip(string.punctuation)
        if len(w) > 3 and w not in stop_words and w.isalpha():
            cleaned_words.append(w)
    word_counts = Counter(cleaned_words)
    most_common = word_counts.most_common(top_n)
    return [word for word, count in most_common]

# --- Streamlit UI ---

st.set_page_config(page_title="Job Matcher", page_icon="🔍")
st.title("🔍 Job Matcher - Find Jobs That Align With Your Resume")

resume_file = st.file_uploader("📄 Upload your Resume (PDF)", type=["pdf"])

if resume_file:
    with st.spinner("Extracting text and matching jobs..."):
        resume_text = extract_text_from_pdf(resume_file)

        keywords = extract_meaningful_keywords(resume_text)
        st.markdown(f"📌 Auto-detected Job Keywords: {', '.join(keywords)}")

        adzuna_jobs = fetch_adzuna_jobs("developer")
        remotive_jobs = fetch_remotive_jobs()
        all_jobs = adzuna_jobs + remotive_jobs

        filtered_jobs = [
            job for job in all_jobs
            if any(loc.lower() in job.get("location", "").lower() for loc in DESIRED_LOCATIONS)
        ]

        jobs_to_match = filtered_jobs if filtered_jobs else all_jobs

        similarity_scores = []
        for job in jobs_to_match:
            score = calculate_similarity(resume_text, job["description"])
            similarity_scores.append((job, score))

        similarity_scores.sort(key=lambda x: x[1], reverse=True)

        tab1, tab2 = st.tabs(["🎯 Matching Jobs", "💾 Saved Jobs"])

        with tab1:
            threshold = 0.2
            matches = [item for item in similarity_scores if item[1] >= threshold]

            if matches:
                for idx, (job, score) in enumerate(matches):
                    title = job["title"]
                    source = job["source"]
                    post_date = format_posting_date(job.get("created", ""))
                    url = job["redirect_url"] or f"https://www.google.com/search?q={title.replace(' ', '+')}+job"

                    st.markdown(f"### ✅ {title} ({source})")
                    st.markdown(f"**Match Score:** {round(score * 100, 2)}%")
                    st.markdown(f"📍 Location: {job.get('location', 'N/A')}")
                    st.markdown(f"🗓️ {post_date}")
                    st.markdown(f"[👉 Apply Now]({url})", unsafe_allow_html=True)

                    if st.button(f"⭐ Save Job #{idx}"):
                        if job not in st.session_state.saved_jobs:
                            st.session_state.saved_jobs.append(job)
                            st.success(f"Saved job: {title}")
                    st.markdown("---")
            else:
                st.warning("❌ No highly matching jobs found. Try updating your resume.")

        with tab2:
            st.header("💾 Saved Jobs")
            if st.session_state.saved_jobs:
                for idx, job in enumerate(st.session_state.saved_jobs):
                    title = job["title"]
                    source = job["source"]
                    post_date = format_posting_date(job.get("created", ""))
                    url = job["redirect_url"] or f"https://www.google.com/search?q={title.replace(' ', '+')}+job"

                    st.markdown(f"### ✅ {title} ({source})")
                    st.markdown(f"📍 Location: {job.get('location', 'N/A')}")
                    st.markdown(f"🗓️ {post_date}")
                    st.markdown(f"[👉 Apply Now]({url})", unsafe_allow_html=True)

                    if st.button(f"❌ Remove Saved Job #{idx}"):
                        st.session_state.saved_jobs.pop(idx)
                        st.experimental_rerun()
                    st.markdown("---")
            else:
                st.info("You have no saved jobs yet.")

else:
    st.info("📥 Please upload your resume to see matching jobs.")
