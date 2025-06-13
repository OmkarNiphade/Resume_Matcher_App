🤖 AI Resume Matcher & Job Analyzer
    A smart AI-powered web application that analyzes resumes and job descriptions to provide a match score, skill gap analysis, and recommendations. 
    Built using Python, Flask, NLP (spaCy & NLTK), and FPDF, this tool helps candidates tailor their resumes and helps recruiters screen resumes faster.

💡 Key Features
📊 Match Score between candidate resume and job description

🧠 NLP-powered keyword extraction (skills, roles, responsibilities)

📌 Highlight missing keywords or skills in resumes

📄 Generate downloadable PDF report

🔍 Analyze both text and PDF input

🎯 Simple web interface built with Flask

🛠️ Tech Stack
    Python 3

    Flask

    spaCy

    NLTK

    FPDF

collections, dateutil, os, re (for processing and parsing)

Folder Structure->

/ai-resume-matcher
├── app.py                 # Main Flask application
├── templates/             # HTML templates for UI
├── static/                # CSS, JS, assets
├── resume_samples/        # Example resumes
├── job_descriptions/      # Example job descriptions
├── generated_reports/     # Output PDF reports
├── requirements.txt       # Project dependencies
