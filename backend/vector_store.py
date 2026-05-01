import os
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "ipractest_knowledge"


def get_vector_store() -> Chroma:
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PATH,
    )


def add_documents(texts: list[str], metadatas: list[dict] | None = None) -> int:
    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=80)
    docs = splitter.create_documents(texts, metadatas=metadatas or [{}] * len(texts))
    store = get_vector_store()
    store.add_documents(docs)
    return len(docs)


def search(query: str, k: int = 5) -> list[str]:
    store = get_vector_store()
    results = store.similarity_search(query, k=k)
    return [doc.page_content for doc in results]


def is_url_indexed(url: str) -> bool:
    store = get_vector_store()
    results = store.get(where={"source": url})
    return len(results["ids"]) > 0
