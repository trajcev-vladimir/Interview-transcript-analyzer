import os
import logging
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.llms.litellm import LiteLLM


logger = logging.getLogger("rag_module")
logging.basicConfig(level=logging.INFO)

class RAGModule:
    def __init__(self, config: dict):

        self.data_dir = config.get("data_dir")
        self.storage_dir = config.get("storage_dir")
        self.embed_model = config.get("embed_model")
        self.llm_model = config.get("llm_model")
        self.rebuild_index = config.get("rebuild_index")
        self.temperature = config.get("temperature", 0.5)


        # Initialize models
        api_key = os.getenv("OPENAI_API_KEY_HTEC")

        Settings.embed_model = HuggingFaceEmbedding(model_name=self.embed_model)
        Settings.llm = LiteLLM(
            model=f"openai/{self.llm_model}",
            api_key=api_key,
            api_base="https://litellm.ai.paas.htec.rs",
            temperature=self.temperature,
        )

        if self.rebuild_index or not os.path.exists(self.storage_dir):
            logger.info("Building new RAG index from transcripts...")
            self._build_index()
        else:
            logger.info("Loading existing RAG index from storage...")
            self._load_index()

    def _build_index(self):
        """
        Reads all transcripts from data_dir and builds a vector index.
        """
        documents = SimpleDirectoryReader(input_dir=self.data_dir).load_data()
        index = VectorStoreIndex.from_documents(documents)

        # Persist index
        index.storage_context.persist(persist_dir=self.storage_dir)
        self.index = index
        logger.info(f"RAG index built with {len(documents)} documents.")

    def _load_index(self):
        storage_context = StorageContext.from_defaults(persist_dir=self.storage_dir)
        self.index = load_index_from_storage(storage_context)
        logger.info("RAG index loaded successfully.")

    def query_similar_cases(self, text: str, top_k: int = 2, similarity_threshold: float = 0.7):
        """
        Query the vector index for similar interview transcripts.
        """
        retriever = self.index.as_retriever(similarity_top_k=top_k)
        query_engine = RetrieverQueryEngine(retriever=retriever)

        response = query_engine.query(text)
        if not response or not response.response:
            logger.warning("No relevant similar cases found.")
            return []

        results = []
        for node in response.source_nodes:
            sim = node.score if hasattr(node, "score") else 0.0
            if sim >= similarity_threshold:
                results.append({
                    "text": node.node.text[:500],  # partial snippet
                    "similarity": round(sim, 3)
                })

        return results

    def summarize_similar_cases(self, query: str):
        """
        Retrieve and summarize context from similar cases.
        """
        results = self.query_similar_cases(query)
        print(f"Results from RAG before summarize {results}")
        if not results:
            logger.info("No sufficiently similar cases found. Using LLM output as is.")
            return "No similar past cases available."

        summaries = []
        for r in results:
            summaries.append(f"Similarity: {r['similarity']}\nExcerpt: {r['text']}")
        context_summary = "\n---\n".join(summaries)

        return f"Retrieved similar cases:\n{context_summary}"

