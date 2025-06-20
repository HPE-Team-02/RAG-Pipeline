from langchain.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os
from urllib.parse import quote_plus

load_dotenv()

def load_index():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return FAISS.load_local("embeddings/faiss_index", embeddings, allow_dangerous_deserialization=True)

def generate_query_from_metadata(json_data):
    server = json_data.get("Server", {})
    update = json_data.get("Firmware Update", {})
    component = json_data.get("Components", [{}])[0]

    lines = [
        f"The firmware update failed with status: {update.get('Install state', 'Unknown')}.",
        f"Server Gen: {server.get('Gen', 'N/A')}, OS: {server.get('OS', 'N/A')} {server.get('OsVersion', '')}.",
        f"SUT Mode: {server.get('SUT Mode', 'N/A')} | SUT State: {server.get('SUT Service State', 'N/A')}.",
        f"Component involved: {component.get('FileName', 'Unknown')} (from {component.get('Installed Version')} to {component.get('To Version')}).",
        f"The installation method was {update.get('Installation Method')} using policy {update.get('Policy')}."
    ]
    return " ".join(lines)

def connect_mongo():
    username = quote_plus(os.getenv("MONGO_USER"))
    password = quote_plus(os.getenv("MONGO_PASS"))
    uri = f"mongodb://{username}:{password}@mongodb.phazite.space"
    client = MongoClient(uri)
    input_db = client["log_analysis_db"]
    output_db = client["log_analysis_rag"]
    return input_db, output_db

def process_all_documents():
    input_db, output_db = connect_mongo()
    db = load_index()

    prompt_template = PromptTemplate(
        input_variables=["context", "question"],
        template="""You are an HPE firmware diagnostic assistant.
Use the context and the failure metadata below to generate a clear explanation of the failure reason and identify the failure type. Do not guess unrelated failures.

Context:
{context}

Failure Metadata:
{question}
""")

    llm = Ollama(model="llama2")
    chain = load_qa_chain(llm, chain_type="stuff", prompt=prompt_template)

    for collection_name in input_db.list_collection_names():
        if collection_name in ["admin", "config", "local"]: continue
        collection = input_db[collection_name]

        for doc in collection.find():
            query = generate_query_from_metadata(doc)
            retriever = db.as_retriever(search_kwargs={"k": 1})
            docs = retriever.get_relevant_documents(query)
            result = chain.run(input_documents=docs, question=query)

            # Store result
            output_db["diagnosis"].insert_one({
                "_id": doc["_id"],
                "diagnosis": result.strip()
            })

            print(f"✔ Diagnosed {str(doc['_id'])}")

if __name__ == "__main__":
    process_all_documents()