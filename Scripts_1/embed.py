from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from Scripts_1.loader import load_all_documents

def build_faiss_index():
    print("Loading documents...")
    docs = load_all_documents()

    print("Embedding and indexing...")
    embedder = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    db = FAISS.from_documents(docs, embedder)

    db.save_local("embeddings/faiss_index")
    print("Index built and saved to embeddings/faiss_index")

if __name__ == "__main__":
    build_faiss_index()