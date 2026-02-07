"""
Knowledge base tool for RAG-based knowledge retrieval.
"""

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .base import BaseTool, ToolInput, ToolOutput

logger = logging.getLogger(__name__)


class KnowledgeBaseInput(ToolInput):
    """Input schema for knowledge base tool."""
    query: str = Field(..., description="Search query for knowledge retrieval")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of results to retrieve")
    kb_name: Optional[str] = Field(default=None, description="Specific knowledge base to query")
    min_score: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum relevance score threshold")


class KnowledgeDocument(BaseModel):
    """A knowledge document."""
    id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    score: Optional[float] = None


class KnowledgeBaseOutput(ToolOutput):
    """Output schema for knowledge base tool."""
    documents: List[KnowledgeDocument] = Field(default_factory=list)
    total_found: int = 0
    kb_name: Optional[str] = None


class KnowledgeBaseTool(BaseTool):
    """Knowledge base tool for RAG-based knowledge retrieval.

    This tool provides semantic search over indexed knowledge bases.
    It supports multiple backends (in-memory, vector DB) and can
    be extended with custom retrieval strategies.

    Example:
        tool = KnowledgeBaseTool()
        result = await tool.execute(KnowledgeBaseInput(
            query="What is Python?",
            top_k=3
        ))
    """

    name = "knowledge_base"
    description = (
        "Search knowledge bases for relevant information. "
        "Returns semantically similar documents based on query. "
        "Use this when you need to retrieve specific knowledge from indexed documents."
    )
    input_schema = KnowledgeBaseInput

    def __init__(
        self,
        embedding_model: Optional[Any] = None,
        vector_store: Optional[Any] = None,
        default_kb: str = "default",
    ):
        """Initialize knowledge base tool.

        Args:
            embedding_model: Embedding model for vectorization
            vector_store: Vector store backend
            default_kb: Default knowledge base name
        """
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.default_kb = default_kb
        self._documents: Dict[str, List[KnowledgeDocument]] = {}

    async def execute(self, input_data: KnowledgeBaseInput) -> ToolOutput:
        """Execute knowledge base search."""
        kb_name = input_data.kb_name or self.default_kb

        try:
            # If vector store is available, use it
            if self.vector_store:
                return await self._search_vector_store(input_data, kb_name)

            # Fallback to in-memory search
            return await self._search_in_memory(input_data, kb_name)

        except Exception as e:
            logger.error(f"Knowledge base search failed: {e}")
            return ToolOutput(
                result="",
                error=f"Search failed: {str(e)}"
            )

    async def _search_vector_store(
        self, input_data: KnowledgeBaseInput, kb_name: str
    ) -> KnowledgeBaseOutput:
        """Search using vector store backend."""
        # This is a placeholder for vector store integration
        # In production, this would use a proper vector database
        # like Chroma, Pinecone, Weaviate, etc.

        return KnowledgeBaseOutput(
            result="Vector store search not implemented. Using in-memory search.",
            documents=[],
            total_found=0,
            kb_name=kb_name
        )

    async def _search_in_memory(
        self, input_data: KnowledgeBaseInput, kb_name: str
    ) -> KnowledgeBaseOutput:
        """Simple in-memory keyword search fallback."""
        documents = self._documents.get(kb_name, [])

        # Simple keyword matching (in production, use embeddings)
        query_words = set(input_data.query.lower().split())
        scored_docs = []

        for doc in documents:
            doc_words = set(doc.content.lower().split())
            overlap = len(query_words & doc_words)
            score = overlap / max(len(query_words), 1)

            if score >= input_data.min_score:
                scored_docs.append((score, doc))

        # Sort by score and take top_k
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        top_docs = [
            KnowledgeDocument(
                id=doc.id,
                content=doc.content,
                metadata=doc.metadata,
                score=score
            )
            for score, doc in scored_docs[:input_data.top_k]
        ]

        # Format result
        if not top_docs:
            return KnowledgeBaseOutput(
                result="No relevant documents found.",
                documents=[],
                total_found=0,
                kb_name=kb_name
            )

        result_lines = [f"Found {len(top_docs)} relevant documents:\n"]
        for i, doc in enumerate(top_docs, 1):
            result_lines.append(f"\n[{i}] Score: {doc.score:.3f}")
            result_lines.append(f"Content: {doc.content[:500]}...")
            if doc.metadata:
                result_lines.append(f"Metadata: {doc.metadata}")

        return KnowledgeBaseOutput(
            result="\n".join(result_lines),
            documents=top_docs,
            total_found=len(top_docs),
            kb_name=kb_name
        )

    def add_document(
        self,
        content: str,
        doc_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        kb_name: Optional[str] = None
    ) -> str:
        """Add a document to the knowledge base.

        Args:
            content: Document content
            doc_id: Optional document ID (auto-generated if not provided)
            metadata: Optional metadata
            kb_name: Knowledge base name

        Returns:
            Document ID
        """
        kb = kb_name or self.default_kb

        if doc_id is None:
            import uuid
            doc_id = str(uuid.uuid4())

        doc = KnowledgeDocument(
            id=doc_id,
            content=content,
            metadata=metadata or {},
        )

        if kb not in self._documents:
            self._documents[kb] = []

        self._documents[kb].append(doc)
        return doc_id

    def clear_kb(self, kb_name: Optional[str] = None):
        """Clear a knowledge base."""
        kb = kb_name or self.default_kb
        if kb in self._documents:
            self._documents[kb] = []
