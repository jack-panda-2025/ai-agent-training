from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = "./chroma_db"
DATA_PATH = "./data"


def ingest():
    # Load all txt files from data/
    docs = []
    for filename in os.listdir(DATA_PATH):
        if filename.endswith(".txt"):
            loader = TextLoader(os.path.join(DATA_PATH, filename))
            docs.extend(loader.load())
            print(f"Loaded: {filename}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    print(f"Created {len(chunks)} chunks from {len(docs)} documents")

    # Store in Chroma
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma.from_documents(
        documents=chunks, embedding=embeddings, persist_directory=CHROMA_PATH
    )
    print(f"Stored {len(chunks)} chunks in Chroma at {CHROMA_PATH}")
    return vectorstore


if __name__ == "__main__":
    ingest()
