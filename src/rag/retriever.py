"""
Simple RAG (Retrieval-Augmented Generation) retriever.

Lightweight vector similarity search for agent context augmentation.
Uses numpy for cosine similarity to minimize dependencies.
"""

import json
import hashlib
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class Document:
    """A retrievable document chunk."""
    id: str
    content: str
    source: str  # File or origin
    doc_type: str  # 'bible', 'character', 'fact', 'chapter', etc.
    metadata: Dict = None
    embedding: Optional[np.ndarray] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SearchResult:
    """Result of a similarity search."""
    document: Document
    score: float
    rank: int


class SimpleEmbedding:
    """
    Simple embedding using TF-IDF or word frequency.
    
    Lightweight alternative to sentence-transformers.
    Good for keyword matching and basic semantic similarity.
    """
    
    def __init__(self, vocab_size: int = 5000):
        self.vocab_size = vocab_size
        self.vocab: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self._doc_count = 0
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for Japanese/English."""
        # Simple character-based tokenization for Japanese
        # In production, use MeCab or similar
        chars = []
        for char in text.lower():
            if char.isalnum() or '\u4e00' <= char <= '\u9fff':
                chars.append(char)
        return chars
    
    def _build_vocab(self, documents: List[str]):
        """Build vocabulary from documents."""
        word_freq: Dict[str, int] = {}
        doc_freq: Dict[str, int] = {}
        
        for doc in documents:
            tokens = self._tokenize(doc)
            unique_tokens = set(tokens)
            
            for token in tokens:
                word_freq[token] = word_freq.get(token, 0) + 1
            
            for token in unique_tokens:
                doc_freq[token] = doc_freq.get(token, 0) + 1
        
        # Select top vocab_size words
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        self.vocab = {word: idx for idx, (word, _) in enumerate(sorted_words[:self.vocab_size])}
        
        # Calculate IDF
        for word, df in doc_freq.items():
            if word in self.vocab:
                self.idf[word] = np.log(self._doc_count / (df + 1)) + 1
    
    def embed(self, text: str) -> np.ndarray:
        """Convert text to vector."""
        tokens = self._tokenize(text)
        vector = np.zeros(len(self.vocab))
        
        for token in tokens:
            if token in self.vocab:
                idx = self.vocab[token]
                vector[idx] += self.idf.get(token, 1.0)
        
        # L2 normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector
    
    def fit(self, documents: List[str]):
        """Fit on corpus."""
        self._doc_count = len(documents)
        self._build_vocab(documents)


class SimpleRetriever:
    """
    Simple vector retriever for RAG.
    
    Stores documents with embeddings and retrieves by similarity.
    Persists to JSON for easy git tracking.
    """
    
    def __init__(self, project_path: Path, index_name: str = "default"):
        self.project_path = project_path
        self.index_name = index_name
        self.index_dir = project_path / ".index"
        self.index_file = self.index_dir / f"{index_name}_rag.json"
        
        self.documents: Dict[str, Document] = {}
        self.embedder = SimpleEmbedding()
        self._fitted = False
        
        # Load existing index
        self._load()
    
    def _doc_to_dict(self, doc: Document) -> Dict:
        """Convert document to dict for serialization."""
        d = asdict(doc)
        if doc.embedding is not None:
            d['embedding'] = doc.embedding.tolist()
        return d
    
    def _doc_from_dict(self, data: Dict) -> Document:
        """Create document from dict."""
        if 'embedding' in data and data['embedding']:
            data['embedding'] = np.array(data['embedding'])
        return Document(**data)
    
    def _save(self):
        """Save index to disk."""
        self.index_dir.mkdir(exist_ok=True)
        
        data = {
            'vocab': self.embedder.vocab,
            'idf': self.embedder.idf,
            'documents': [self._doc_to_dict(d) for d in self.documents.values()]
        }
        
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load(self):
        """Load index from disk."""
        if not self.index_file.exists():
            return
        
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.embedder.vocab = data.get('vocab', {})
            self.embedder.idf = data.get('idf', {})
            self._fitted = True
            
            for doc_data in data.get('documents', []):
                doc = self._doc_from_dict(doc_data)
                self.documents[doc.id] = doc
        
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Failed to load RAG index: {e}")
    
    def add_document(self, content: str, source: str, doc_type: str, 
                     metadata: Dict = None, doc_id: Optional[str] = None) -> str:
        """
        Add document to index.
        
        Args:
            content: Document text
            source: Source file/location
            doc_type: Type of document
            metadata: Optional metadata
            doc_id: Optional ID (generated if not provided)
        
        Returns:
            Document ID
        """
        if doc_id is None:
            # Generate ID from content hash
            doc_id = hashlib.md5(content.encode()).hexdigest()[:12]
        
        doc = Document(
            id=doc_id,
            content=content,
            source=source,
            doc_type=doc_type,
            metadata=metadata or {}
        )
        
        self.documents[doc_id] = doc
        self._fitted = False  # Need to refit
        
        return doc_id
    
    def index_project(self):
        """Index all project documents."""
        # Index bible
        bible_path = self.project_path / "bible.md"
        if bible_path.exists():
            content = bible_path.read_text(encoding='utf-8')
            # Split into sections
            sections = content.split('##')
            for i, section in enumerate(sections[1:], 1):  # Skip first (title)
                section = section.strip()
                if section:
                    title = section.split('\n')[0][:50]
                    self.add_document(
                        content=section,
                        source="bible.md",
                        doc_type="bible",
                        doc_id=f"bible_{i}",
                        metadata={"section": title}
                    )
        
        # Index characters
        chars_dir = self.project_path / "characters"
        if chars_dir.exists():
            for char_file in chars_dir.glob("*.json"):
                content = char_file.read_text(encoding='utf-8')
                self.add_document(
                    content=content,
                    source=f"characters/{char_file.name}",
                    doc_type="character",
                    doc_id=f"char_{char_file.stem}",
                    metadata={"name": char_file.stem}
                )
        
        # Index facts
        facts_file = self.project_path / "memory" / "facts.json"
        if facts_file.exists():
            import json
            data = json.loads(facts_file.read_text(encoding='utf-8'))
            for fact in data.get('facts', []):
                self.add_document(
                    content=fact['content'],
                    source=f"memory/facts.json",
                    doc_type="fact",
                    doc_id=f"fact_{fact['id']}",
                    metadata={"fact_id": fact['id']}
                )
        
        # Index chapters
        chapters_dir = self.project_path / "chapters"
        if chapters_dir.exists():
            for ch_file in chapters_dir.glob("*.md"):
                content = ch_file.read_text(encoding='utf-8')
                # Split into chunks (paragraphs)
                chunks = content.split('\n\n')
                for i, chunk in enumerate(chunks):
                    if len(chunk) > 50:  # Only meaningful chunks
                        self.add_document(
                            content=chunk,
                            source=f"chapters/{ch_file.name}",
                            doc_type="chapter",
                            doc_id=f"ch_{ch_file.stem}_{i}",
                            metadata={"chapter": ch_file.stem, "chunk": i}
                        )
        
        # Build index
        self.build()
    
    def build(self):
        """Build embeddings for all documents."""
        if not self.documents:
            return
        
        # Fit embedder
        contents = [d.content for d in self.documents.values()]
        self.embedder.fit(contents)
        
        # Generate embeddings
        for doc in self.documents.values():
            doc.embedding = self.embedder.embed(doc.content)
        
        self._fitted = True
        self._save()
    
    def search(self, query: str, top_k: int = 5, 
               doc_type: Optional[str] = None) -> List[SearchResult]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            top_k: Number of results
            doc_type: Filter by document type
        
        Returns:
            List of SearchResult
        """
        if not self._fitted or not self.documents:
            return []
        
        # Embed query
        query_vec = self.embedder.embed(query)
        
        # Calculate similarities
        results = []
        for doc in self.documents.values():
            # Filter by type if specified
            if doc_type and doc.doc_type != doc_type:
                continue
            
            if doc.embedding is not None:
                similarity = np.dot(query_vec, doc.embedding)
                results.append((doc, float(similarity)))
        
        # Sort by score
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k
        return [
            SearchResult(document=doc, score=score, rank=i+1)
            for i, (doc, score) in enumerate(results[:top_k])
        ]
    
    def search_for_agent(self, query: str, agent_type: str, 
                         context: Dict = None) -> List[SearchResult]:
        """
        Agent-specific search with context awareness.
        
        Args:
            query: Agent's query
            agent_type: Type of agent (director, writer, etc.)
            context: Additional context (current chapter, characters, etc.)
        
        Returns:
            Relevant documents for the agent
        """
        # Different agents need different document types
        type_priority = {
            'director': ['bible', 'fact', 'foreshadowing', 'chapter'],
            'writer': ['bible', 'character', 'fact', 'chapter'],
            'checker': ['fact', 'character', 'bible'],
        }
        
        priority = type_priority.get(agent_type, ['bible', 'character', 'fact'])
        
        all_results = []
        for doc_type in priority:
            results = self.search(query, top_k=3, doc_type=doc_type)
            all_results.extend(results)
        
        # Re-rank by combined score
        all_results.sort(key=lambda x: x.score, reverse=True)
        
        return all_results[:5]


class RAGContextBuilder:
    """Builds RAG-augmented context for agents."""
    
    def __init__(self, retriever: SimpleRetriever):
        self.retriever = retriever
    
    def build_context(self, query: str, agent_type: str) -> str:
        """
        Build context string from retrieved documents.
        
        Args:
            query: Search query
            agent_type: Agent type
        
        Returns:
            Formatted context string
        """
        results = self.retriever.search_for_agent(query, agent_type)
        
        if not results:
            return ""
        
        lines = ["## Retrieved Context", ""]
        
        # Group by type
        by_type: Dict[str, List[SearchResult]] = {}
        for r in results:
            by_type.setdefault(r.document.doc_type, []).append(r)
        
        for doc_type, docs in by_type.items():
            lines.append(f"### {doc_type.title()} References")
            for r in docs:
                content = r.document.content[:500]  # Truncate long content
                lines.append(f"- [{r.document.source}] {content[:200]}...")
            lines.append("")
        
        return '\n'.join(lines)
