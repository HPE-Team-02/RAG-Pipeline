import os
import json
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

def load_rules_md(filepath):
    loader = TextLoader(filepath, encoding='utf-8')
    return loader.load()

def load_failure_json(filepath):
    with open(filepath, "r") as f:
        data = json.load(f)["firmware_update_logs"]
    docs = []

    for failure in data["failures"]:
        content = f"Failure Type: {failure['failure_type']}\n"
        content += f"UUID: {failure.get('server_uuid', 'N/A')}\n"
        content += f"Component: {failure.get('component', 'N/A')}\n"
        content += f"Error Details: {json.dumps(failure.get('error_details', {}), indent=2)}\n"
        docs.append(Document(page_content=content, metadata={"type": "failure"}))

    for success in data["successes"]:
        content = f"Success Type: {success['success_type']}\n"
        content += f"UUID: {success.get('server_uuid', 'N/A')}\n"
        content += f"Update Type: {success.get('update_type', 'N/A')}\n"
        content += f"Executors: {', '.join(success.get('executors', []))}\n"
        content += f"Final State: {success.get('final_state', 'N/A')}"
        docs.append(Document(page_content=content, metadata={"type": "success"}))

    return docs

def load_all_documents():
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = []

    rules_path = os.path.join("corpus", "rules_and_guides.md")
    json_path = os.path.join("corpus", "Failures_success.json")

    docs.extend(load_rules_md(rules_path))
    docs.extend(load_failure_json(json_path))

    return splitter.split_documents(docs)
