"""
BM25 Keyword Search Component

Provides TF-IDF based keyword search for exact term matching,
complementing semantic search for better hybrid retrieval.
"""

from typing import List, Dict, Any
import math
from collections import defaultdict, Counter
from loguru import logger


class BM25Searcher:
    """
    BM25 (Best Matching 25) keyword search algorithm
    
    Provides traditional keyword-based ranking that complements
    semantic search for queries requiring exact term matching.
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 searcher
        
        Args:
            k1: Term frequency saturation parameter (default: 1.5)
            b: Length normalization parameter (default: 0.75)
        """
        self.k1 = k1
        self.b = b
        self.documents = []
        self.doc_lengths = []
        self.avg_doc_length = 0
        self.doc_freqs = defaultdict(int)
        self.idf_cache = {}
        self.total_docs = 0
        
        logger.info(f"✅ BM25 Searcher initialized (k1={k1}, b={b})")
    
    def index_documents(self, documents: List[Dict[str, Any]]):
        """
        Index documents for BM25 search
        
        Args:
            documents: List of document dicts with 'text' and 'metadata'
        """
        self.documents = documents
        self.total_docs = len(documents)
        self.doc_lengths = []
        self.doc_freqs = defaultdict(int)
        self.idf_cache = {}
        
        # Calculate document lengths and document frequencies
        for doc in documents:
            text = doc.get('text', '')
            tokens = self._tokenize(text)
            self.doc_lengths.append(len(tokens))
            
            # Count unique terms in document
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freqs[token] += 1
        
        # Calculate average document length
        if self.doc_lengths:
            self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths)
        else:
            self.avg_doc_length = 0
        
        logger.info(f"   📚 Indexed {self.total_docs} documents")
        logger.info(f"   📏 Average doc length: {self.avg_doc_length:.1f} tokens")
        logger.info(f"   📖 Vocabulary size: {len(self.doc_freqs)} terms")
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Simple tokenization: lowercase + split on non-alphanumeric
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        import re
        # Lowercase and keep only alphanumeric + Turkish chars
        text = text.lower()
        # Split on whitespace and punctuation, keep Turkish characters
        tokens = re.findall(r'[a-z0-9çğıöşüâîû]+', text)
        return tokens
    
    def _calculate_idf(self, term: str) -> float:
        """
        Calculate IDF (Inverse Document Frequency) for a term
        
        IDF = log((N - df + 0.5) / (df + 0.5) + 1)
        where N = total docs, df = docs containing term
        
        Args:
            term: Query term
            
        Returns:
            IDF score
        """
        if term in self.idf_cache:
            return self.idf_cache[term]
        
        df = self.doc_freqs.get(term, 0)
        idf = math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1)
        self.idf_cache[term] = idf
        return idf
    
    def _calculate_bm25_score(self, query_tokens: List[str], doc_index: int) -> float:
        """
        Calculate BM25 score for a document given a query
        
        BM25(D,Q) = Σ IDF(qi) * (f(qi,D) * (k1 + 1)) / (f(qi,D) + k1 * (1 - b + b * |D| / avgdl))
        
        Args:
            query_tokens: Tokenized query terms
            doc_index: Document index in self.documents
            
        Returns:
            BM25 score
        """
        doc = self.documents[doc_index]
        doc_text = doc.get('text', '')
        doc_tokens = self._tokenize(doc_text)
        doc_length = self.doc_lengths[doc_index]
        
        # Count term frequencies in document
        term_freqs = Counter(doc_tokens)
        
        score = 0.0
        for term in query_tokens:
            if term not in term_freqs:
                continue
            
            # Get term frequency and IDF
            tf = term_freqs[term]
            idf = self._calculate_idf(term)
            
            # Calculate BM25 component for this term
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_length / self.avg_doc_length)
            score += idf * (numerator / denominator)
        
        return score
    
    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search documents using BM25 algorithm
        
        Args:
            query: Search query
            top_k: Number of top results to return
            
        Returns:
            List of document dicts with scores
        """
        if not self.documents:
            logger.warning("⚠️ No documents indexed for BM25 search")
            return []
        
        query_tokens = self._tokenize(query)
        if not query_tokens:
            logger.warning("⚠️ Empty query after tokenization")
            return []
        
        # Calculate BM25 scores for all documents
        scores = []
        for i in range(len(self.documents)):
            score = self._calculate_bm25_score(query_tokens, i)
            if score > 0:  # Only include docs with matches
                scores.append({
                    'doc': self.documents[i],
                    'score': score,
                    'index': i
                })
        
        # Sort by score and return top k
        scores.sort(key=lambda x: x['score'], reverse=True)
        top_results = scores[:top_k]
        
        if top_results:
            logger.info(f"   🔑 BM25 found {len(scores)} matches, top score: {top_results[0]['score']:.3f}")
        
        return top_results


# Singleton instance
_bm25_searcher = None

def get_bm25_searcher() -> BM25Searcher:
    """Get or create BM25 searcher singleton"""
    global _bm25_searcher
    if _bm25_searcher is None:
        _bm25_searcher = BM25Searcher()
    return _bm25_searcher
