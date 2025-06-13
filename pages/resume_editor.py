import streamlit as st
import pdfplumber
from fpdf import FPDF
import os
import datetime

st.title("🛠 Resume Editor")

def extract_text_from_pdf(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        return "\n".join([page.extract_text() or "" for page in pdf.pages])

def save_text_as_pdf(text, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Update this path to your absolute path for the font file
    font_path = r"C:\Users\DELL\Desktop\OJT\resume_match_app\fonts\DejaVuSans.ttf"
    if not os.path.isfile(font_path):
        st.error(f"Font file not found at {font_path}. Please add the font file.")
        return

    pdf.add_font('DejaVu', '', font_path, uni=True)
    pdf.set_font("DejaVu", size=12)

    for line in text.split('\n'):
        pdf.multi_cell(0, 10, line)
    pdf.output(filename)

uploaded_file = st.file_uploader("Upload your Resume PDF to edit", type=["pdf"])

if uploaded_file:
    resume_text = extract_text_from_pdf(uploaded_file)
    st.session_state["resume_text"] = resume_text

    edited_text = st.text_area("Edit your resume text below:", value=st.session_state.get("resume_text", ""), height=400)
    st.session_state["resume_text"] = edited_text

    if st.button("Save Edited Resume"):
        save_folder = "edited_resumes"
        os.makedirs(save_folder, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(save_folder, f"edited_resume_{timestamp}.pdf")

        save_text_as_pdf(edited_text, filename)

        if os.path.isfile(filename):
            st.success(f"Edited resume saved as PDF: {filename}")

            with open(filename, "rb") as f:
                st.download_button(
                    label="Download Edited Resume PDF",
                    data=f,
                    file_name=os.path.basename(filename),
                    mime="application/pdf"
                )
        else:
            st.error("Failed to save PDF. Please check the font file and try again.")
else:
    st.info("Please upload a PDF file to start editing.")
