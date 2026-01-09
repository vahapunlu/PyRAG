
import os
import re
import json
import fitz  # PyMuPDF
from typing import List, Dict, Any
from loguru import logger

class RuleMiner:
    """
    Extracts mandatory engineering rules from standard documents
    based on strong modal verbs (shall, must, required).
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.rules_file = os.path.join(data_dir, "golden_rules.json")
        self._load_existing_rules()

    def _load_existing_rules(self):
        if os.path.exists(self.rules_file):
            try:
                with open(self.rules_file, 'r', encoding='utf-8') as f:
                    self.existing_rules = json.load(f)
            except:
                self.existing_rules = []
        else:
            self.existing_rules = []

    def get_processed_documents(self) -> List[str]:
        """Returns list of documents that have already contributed to golden rules"""
        return sorted(list({rule.get('source_doc') for rule in self.existing_rules if rule.get('source_doc')}))

    def get_document_path(self, doc_name: str) -> str:
        # Simple lookup in data dir
        # In a real app, this might query the index metadata for full path
        possible_path = os.path.join(self.data_dir, doc_name)
        if os.path.exists(possible_path):
            return possible_path
        return ""

    def mine_rules(self, doc_name: str) -> List[Dict[str, Any]]:
        """
        Scans a document for mandatory rules and numeric technical specifications.
        """
        file_path = self.get_document_path(doc_name)
        if not file_path:
            raise FileNotFoundError(f"Document {doc_name} not found in {self.data_dir}")

        candidates = []
        
        # Regex for mandatory language
        mandatory_pattern = re.compile(r'\b(shall|must|required to|strictly)\b', re.IGNORECASE)
        
        # Numeric Specification Pattern (Unit-aware)
        # Matches: Number + Space(opt) + Unit
        self.numeric_pattern = re.compile(
            r'\b\d+(?:[\.,]\d+)?\s*(?:mm2|mm|m|cm|km|V|kV|mV|A|kA|mA|W|kW|MW|Hz|kHz|lux|lm\/W|lm|cd|K|°C|C|Pa|kPa|bar|m3\/h|l\/s|kg|g|dB|dB\(A\)|%)\b',
            re.IGNORECASE
        )
        
        # Open PDF and iterate blocks to preserve context
        try:
            doc = fitz.open(file_path)
            
            current_context = "General"
            buffer_text = ""
            
            for page in doc:
                blocks = page.get_text("blocks")
                for b in blocks:
                    # b structure: (x0, y0, x1, y1, "text", block_no, block_type)
                    text = b[4].strip()
                    if not text: continue
                    
                    if self._is_header(text):
                        # Flush existing buffer with previous context
                        if buffer_text:
                            self._extract_from_buffer(buffer_text, current_context, candidates, mandatory_pattern)
                            buffer_text = ""
                        # Update context
                        current_context = self._clean_header(text)
                    else:
                        buffer_text += " " + text
            
            # Final flush
            if buffer_text:
                self._extract_from_buffer(buffer_text, current_context, candidates, mandatory_pattern)
                
            # Post-process: Add document name source to all candidates
            for c in candidates:
                c['source_doc'] = doc_name
                
        except Exception as e:
            logger.error(f"Error extracting with context: {e}")
            # Fallback to simple extraction if something fails
            return self._mine_rules_fallback(file_path)

        return candidates

    def _is_header(self, text: str) -> bool:
        """Heuristic to check if a block is a header"""
        # 1. Starts with numbering (e.g., "1.0", "2.1.3")
        if re.match(r'^\d+(\.\d+)*\.?', text):
            return True
        # 2. Short and Uppercase (e.g., "SECTION 5")
        if len(text) < 60 and text.isupper():
            return True
        # 3. Specific patterns
        if text.lower().startswith(("part ", "section ", "chapter ")):
            return True
        return False

    def _clean_header(self, text: str) -> str:
        """Clean up header text"""
        return text.replace('\n', ' ').strip()
        
    def _extract_from_buffer(self, text: str, context: str, candidates: List[Dict], pattern: re.Pattern):
        """Split buffer into sentences and find rules"""
        # Normalize
        text = re.sub(r'\s+', ' ', text)
        # Split sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        for sent in sentences:
            sent_clean = sent.strip()
            if 20 <= len(sent_clean) <= 800:
                is_mandatory = bool(pattern.search(sent_clean))
                numeric_matches = self.numeric_pattern.findall(sent_clean)
                
                # Rule is valid if it is mandatory OR contains numeric spec (Numeric Hunter)
                if is_mandatory or (numeric_matches and len(numeric_matches) > 0 and len(sent_clean) < 300):
                    # Detect topics
                    topics = self._detect_topics(sent_clean, context)
                    
                    candidates.append({
                        "id": str(hash(sent_clean)), # Simple ID
                        "source_doc": "", # Filled later
                        "rule_text": sent_clean,
                        "keywords": pattern.findall(sent_clean) if is_mandatory else ["numeric_spec"],
                        "numeric_values": numeric_matches, # New field
                        "context": context,
                        "topics": topics
                    })

    def _detect_topics(self, text: str, context: str) -> List[str]:
        """Tag content with engineering topics"""
        combined = (text + " " + context).lower()
        topics = set()
        
        keywords = {
            "Fire Safety": ["fire", "smoke", "alarm", "detection", "extinguish", "evacuation"],
            "Electrical": ["voltage", "current", "wiring", "cable", "circuit", "earthing", "power", "switchgear"],
            "Mechanical/HVAC": ["ventilation", "heating", "cooling", "pump", "valve", "pipe", "duct", "hvac"],
            "Access Control": ["access", "security", "door", "reader", "card", "intercom", "cctv"],
            "Lighting": ["lux", "luminaire", "lighting", "lamp", "dimaming", "led"],
            "BMS": ["bms", "building management", "control", "sensor", "setpoint"],
            "Plumbing": ["water", "drainage", "sewage", "sanitary", "foul", "waste"],
            "Lifts": ["lift", "elevator", "hoist"],
            "Sustainability": ["energy", "solar", "pv", "thermal", "leed", "breeam", "sustainability"]
        }
        
        for topic, keys in keywords.items():
            for k in keys:
                # Use regex for whole word match to avoid noise (e.g. 'duct' in 'introduction')
                if re.search(r'\b' + re.escape(k) + r'\b', combined):
                    topics.add(topic)
                    break
                
        return sorted(list(topics))

    def _mine_rules_fallback(self, file_path: str) -> List[Dict[str, Any]]:
        # This is the old logic, kept just in case
        return []

    def _extract_text(self, file_path: str) -> str:
        """Reads PDF text"""
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            return text
        except Exception as e:
            logger.error(f"Error reading PDF: {e}")
            return ""

    def save_rules(self, rules: List[Dict[str, Any]]):
        """
        Save selected rules to the knowledge base.
        """
        # Load fresh (in case of concurrent writes)
        self._load_existing_rules()
        
        # Append new rules
        # Check duplicates based on text
        existing_texts = {r['rule_text'] for r in self.existing_rules}
        
        added_count = 0
        for rule in rules:
            if rule['rule_text'] not in existing_texts:
                self.existing_rules.append(rule)
                added_count += 1
        
        # Save
        with open(self.rules_file, 'w', encoding='utf-8') as f:
            json.dump(self.existing_rules, f, indent=2, ensure_ascii=False)
            
        logger.success(f"Saved {added_count} new golden rules to {self.rules_file}")
        return added_count
