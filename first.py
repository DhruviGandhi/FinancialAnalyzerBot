from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM

# Load PDF
loader = PyPDFLoader("clg.pdf")
documents = loader.load()

# Split text into chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

docs = splitter.split_documents(documents)

# Create embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Store in vector database
vectorstore = FAISS.from_documents(docs, embeddings)

# Load Llama3
llm = OllamaLLM(model="llama3")

print("RAG Bot Ready")
print("Type 'exit' to stop")

while True:

    question = input("\nAsk Question: ")

    if question.lower() == "exit":
        break

    results = vectorstore.similarity_search(question, k=2)

    context = "\n".join(
        [doc.page_content for doc in results]
    )

    prompt = f"""
    Answer only from the provided context.

    Context:
    {context}

    Question:
    {question}
    """

    response = llm.invoke(prompt)

    print("\nAnswer:")
    print(response)