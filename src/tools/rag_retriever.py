
"""Curriculum ingestion and retrieval for the Sprints learner advisor."""
from pathlib import Path
import time
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import tiktoken
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from src.config import get_embeddings

class CurriculumRAG:
    """Index curriculum files into Chroma and retrieve traceable passages.

    The configured splitter uses a tokenizer-backed 500-token target and 50-token overlap.
    """
    def __init__(self, docs_dir="data/curriculum_docs", persist_dir="data/chroma"):
        self.docs_dir, self.persist_dir = Path(docs_dir), persist_dir
        self.embeddings = get_embeddings()        
        self.vectorstore = None

    def ingest(self):
        """Load supported text/Markdown files, split them, and persist the index."""
        docs = []
        for ext in ("*.txt", "*.md"):
            for path in self.docs_dir.rglob(ext):
                docs.extend(TextLoader(str(path), encoding="utf-8").load())
        if not docs:
            raise FileNotFoundError(
                f"No .txt/.md curriculum files found in {self.docs_dir}. "
                "Add the client curriculum before claiming source-grounded answers."
            )
        # Token-aware chunking: 500 tokens with 50-token overlap.
        splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            encoding_name="cl100k_base", chunk_size=500, chunk_overlap=50,
            add_start_index=True
        )
        chunks = splitter.split_documents(docs)
        for i, d in enumerate(chunks):
            d.metadata.update({"chunk_id": i, "source_file": d.metadata.get("source")})
        self.vectorstore = Chroma.from_documents(
            chunks, self.embeddings, persist_directory=self.persist_dir,
            collection_name="sprints_curriculum"
        )
        return len(chunks)

    def retrieve(self, query, k=4):
        """Return relevant passages and elapsed retrieval time in milliseconds."""
        if self.vectorstore is None:
            self.vectorstore = Chroma(
                collection_name="sprints_curriculum",
                persist_directory=self.persist_dir, embedding_function=self.embeddings
            )
        start = time.perf_counter()
        docs = self.vectorstore.similarity_search(query, k=k)
        elapsed_ms = (time.perf_counter() - start) * 1000
        return docs, elapsed_ms
