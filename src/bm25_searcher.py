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
    
    def __init__(self, k1: float = 1.5, b: float = 0.75, use_ngrams: bool = True):
        """
        Initialize BM25 searcher
        
        Args:
            k1: Term frequency saturation parameter (default: 1.5)
            b: Length normalization parameter (default: 0.75)
            use_ngrams: Use bigrams and trigrams for multi-word terms (default: True)
        """
        self.k1 = k1
        self.b = b
        self.use_ngrams = use_ngrams
        self.documents = []
        self.doc_lengths = []
        self.avg_doc_length = 0
        self.doc_freqs = defaultdict(int)
        self.idf_cache = {}
        self.total_docs = 0
        
        # MEP technical terms dictionary (Turkish-English mappings)
        self.mep_terms = {
            'kablo tavası': 'cable_tray',
            'yangın dedektörü': 'fire_detector',
            'duman dedektörü': 'smoke_detector',
            'ısı dedektörü': 'heat_detector',
            'acil aydınlatma': 'emergency_lighting',
            'paratoner sistemi': 'lightning_protection',
            'topraklama sistemi': 'grounding_system',
            'güç kaynağı': 'power_supply',
            'sigorta kutusu': 'fuse_box',
            'elektrik panosu': 'electrical_panel',
            'koruma rölesi': 'protection_relay',
            'devre kesici': 'circuit_breaker',
            'kaçak akım': 'leakage_current',
            'kısa devre': 'short_circuit',
            'toprak kaçağı': 'earth_fault',
            'faz dengesizliği': 'phase_imbalance'
        }
        
        logger.info(f"✅ BM25 Searcher initialized (k1={k1}, b={b}, ngrams={use_ngrams})")
        logger.info(f"   📚 MEP terms dictionary: {len(self.mep_terms)} technical terms")
    
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
        Advanced tokenization with n-grams and MEP term preservation
        
        Args:
            text: Input text
            
        Returns:
            List of tokens including unigrams, bigrams, and technical terms
        """
        import re
        
        # Lowercase
        text_lower = text.lower()
        
        # First, extract and replace MEP technical terms with single tokens
        protected_terms = {}
        term_counter = 0
        
        for term, token in self.mep_terms.items():
            if term in text_lower:
                # Replace multi-word term with single token
                placeholder = f"__{token}__"
                text_lower = text_lower.replace(term, placeholder)
                protected_terms[placeholder] = token
                term_counter += 1
        
        # Basic tokenization: split on whitespace and punctuation
        unigrams = re.findall(r'[a-z0-9çğıöşüâîû_]+', text_lower)
        
        # Restore protected terms as single tokens
        final_tokens = []
        for token in unigrams:
            if token in protected_terms:
                final_tokens.append(protected_terms[token])
            else:
                final_tokens.append(token)
        
        # Add bigrams and trigrams if enabled
        if self.use_ngrams and len(final_tokens) > 1:
            # Add bigrams (2-word phrases)
            for i in range(len(final_tokens) - 1):
                bigram = f"{final_tokens[i]}_{final_tokens[i+1]}"
                final_tokens.append(bigram)
            
            # Add trigrams (3-word phrases) for better phrase matching
            if len(final_tokens) > 2:
                for i in range(len(final_tokens) - 2):
                    # Avoid adding n-grams of already protected terms
                    if not any(t.startswith('__') for t in [final_tokens[i], final_tokens[i+1], final_tokens[i+2]]):
                        trigram = f"{final_tokens[i]}_{final_tokens[i+1]}_{final_tokens[i+2]}"
                        final_tokens.append(trigram)
        
        return final_tokens
    
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
