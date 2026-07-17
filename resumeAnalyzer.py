import re
import tempfile
import streamlit as st

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaLLM


st.set_page_config(page_title="Resume ATS Analyzer", layout="centered")

st.title("📄 Resume ATS Analyzer + RAG Bot")

resume_file = st.file_uploader("Upload Resume PDF", type=["pdf"])
job_description = st.text_area("Paste Job Description", height=200)


def clean_words(text):
    text = text.lower()
    text = re.sub(r"[^a-zA-Z0-9+#. ]", " ", text)
    words = text.split()
    return set(words)


def calculate_ats_score(resume_text, jd_text):
    resume_words = clean_words(resume_text)
    jd_words = clean_words(jd_text)

    matched_words = resume_words.intersection(jd_words)
    missing_words = jd_words - resume_words

    score = (len(matched_words) / max(len(jd_words), 1)) * 100

    return round(score, 2), sorted(matched_words), sorted(missing_words)


if st.button("Analyze Resume"):

    if resume_file is None:
        st.error("Please upload resume PDF")
        st.stop()

    if job_description.strip() == "":
        st.error("Please enter job description")
        st.stop()

    with st.spinner("Analyzing resume..."):

        # Save uploaded PDF temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(resume_file.read())
            pdf_path = temp_file.name

        # Load PDF
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()

        resume_text = "\n".join([doc.page_content for doc in documents])

        # Split resume into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )

        docs = splitter.split_documents(documents)

        # Embeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # FAISS Vector DB
        vectorstore = FAISS.from_documents(docs, embeddings)

        # Retrieve relevant resume chunks based on JD
        relevant_docs = vectorstore.similarity_search(job_description, k=4)

        context = "\n\n".join([doc.page_content for doc in relevant_docs])

        # ATS Score
        ats_score, matched_words, missing_words = calculate_ats_score(
            resume_text,
            job_description
        )

        # LLM
        llm = OllamaLLM(model="llama3")

        prompt = f"""
You are an expert ATS Resume Analyzer.

Analyze the resume according to the job description.

Relevant Resume Content:
{context}

Job Description:
{job_description}

Calculated ATS Score:
{ats_score}%

Matched Keywords:
{matched_words[:30]}

Missing Keywords:
{missing_words[:30]}

Give output in this format:

1. ATS Score Explanation
2. Matching Skills
3. Missing Skills
4. Resume Strengths
5. Resume Weaknesses
6. Suggestions to Improve Resume
7. Interview Readiness Score out of 100
"""

        response = llm.invoke(prompt)

    st.subheader("✅ ATS Score")
    st.progress(min(int(ats_score), 100))
    st.success(f"ATS Score: {ats_score}%")

    st.subheader("✅ Matched Keywords")
    st.write(matched_words[:30])

    st.subheader("❌ Missing Keywords")
    st.write(missing_words[:30])

    st.subheader("🤖 AI Resume Analysis")
    st.write(response)