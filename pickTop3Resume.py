import os
import re
import streamlit as st
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader


def clean_words(text: str) -> set:
    """Normalize text and return a set of alphanumeric words.
    - Lowercase
    - Remove non‑alphanumeric characters (except +, #, .)
    - Split on whitespace
    """
    text = text.lower()
    text = re.sub(r"[^a-zA-Z0-9+#. ]", " ", text)
    words = text.split()
    return set(words)


def extract_skills_section(text: str) -> str:
    """Extract the likely "Skills" section from a resume.
    The function looks for a line containing the word "skill" (case‑insensitive)
    and returns that line plus subsequent non‑empty lines until another
    common section heading (e.g., Experience, Education, Project) or a blank line
    is encountered. If no such heading is found, an empty string is returned,
    causing the full resume to be used as a fallback.
    """
    lines = text.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if "skill" in line.lower():
            start = idx
            break
    if start is None:
        return ""
    collected = []
    for line in lines[start:]:
        stripped = line.strip()
        if not stripped:
            break
        lowered = stripped.lower()
        if any(lowered.startswith(h) for h in ("experience", "education", "project", "work", "summary", "objective", "profile")):
            break
        collected.append(stripped)
    return " ".join(collected)



def calculate_ats_score(resume_text: str, jd_text: str):
    """Calculate ATS skill match score between a resume and a job description.
    Returns:
        skill_score (float): percentage of JD skill terms found in resume.
        matched_skills (list): list of skill terms that matched.
        missing_skills (list): list of JD skill terms not found.
    """
    # Define generic stopwords to ignore
    STOP_WORDS = {"as", "with", "and", "or", "the", "a", "an", "for", "of", "in", "on", "to", "using", "skill", "skills", "strong", "basic", "knowledge", "experience", "technology", "understanding", "expertise", "etc"}
    # Use only the Skills section if detectable
    skill_section = extract_skills_section(resume_text)
    if not skill_section:
        skill_section = resume_text
    # Derive skill terms dynamically from the job description, excluding generic words
    jd_skill_terms = clean_words(jd_text) - STOP_WORDS
    resume_words = clean_words(skill_section)
    matched_skills = resume_words.intersection(jd_skill_terms)
    missing_skills = jd_skill_terms - resume_words
    skill_score = (len(matched_skills) / max(len(jd_skill_terms), 1)) * 100
    return round(skill_score, 2), sorted(matched_skills), sorted(missing_skills)



def extract_text_from_pdf(pdf_path: Path) -> str:
    """Load a PDF with PyPDFLoader and return concatenated page text."""
    loader = PyPDFLoader(str(pdf_path))
    docs = loader.load()
    return "\n".join([doc.page_content for doc in docs])


def main():
    st.title("📄 Resume ATS Analyzer + Top 3 Selector")
    job_description = st.text_area("Paste Job Description", height=200)
    cv_folder = st.text_input("CV Folder Path (relative to project)", value="CV")
    if st.button("Analyze Resumes"):
        # Validate job description
        if not job_description.strip():
            st.error("Please provide a job description.")
            return
        # Determine CV folder
        cv_path = Path(cv_folder) if cv_folder else Path("CV")
        if not cv_path.is_dir():
            st.warning(f"Folder '{cv_path}' not found. Falling back to current directory.")
            cv_path = Path('.')
        if not any(cv_path.glob('*.pdf')):
            st.error(f"No PDF resumes found in '{cv_path}'.")
            return
        # Process resumes
        results = []
        for pdf_file in cv_path.glob('*.pdf'):
            try:
                resume_text = extract_text_from_pdf(pdf_file)
                skill_score, matched, missing = calculate_ats_score(resume_text, job_description)
                overall_score = skill_score
                results.append({
                    "file": pdf_file.name,
                    "overall_score": overall_score,
                    "skill_score": skill_score,
                    "matched": matched,
                    "missing": missing
                })
            except Exception as e:
                st.warning(f"Failed to process {pdf_file.name}: {e}")
        if not results:
            st.info("No resumes processed.")
            return
        # Show top 3
        top3 = sorted(results, key=lambda x: x["overall_score"], reverse=True)[:3]
        st.subheader("Top 3 matching resumes")
        for i, entry in enumerate(top3, start=1):
            st.markdown(f"**{i}. {entry['file']}**")
            st.write(f"Overall ATS Score: {entry['overall_score']}%")
            st.write(f"Skill Match Score: {entry['skill_score']}%")
            st.write(f"Matched Keywords (sample): {', '.join(entry['matched'][:15])}")
            st.write(f"Missing Keywords (sample): {', '.join(entry['missing'][:15])}")


if __name__ == "__main__":
    main()
