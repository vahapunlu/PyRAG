"""LLM-based Index Extraction Module"""

import json
import re
from pathlib import Path
from typing import Dict, List
from loguru import logger
import fitz

from src.utils import get_settings


class IndexExtractor:
    def __init__(self):
        self.settings = get_settings()
        self.cache_dir = Path("cache_db/index_structures")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def extract_document_structure(self, pdf_path: str, force_refresh: bool = False) -> Dict:
        pdf_path = Path(pdf_path)
        doc_name = pdf_path.stem
        
        cache_file = self.cache_dir / f"{doc_name}.json"
        if cache_file.exists() and not force_refresh:
            logger.info(f"Loading cached structure for {doc_name}")
            return json.loads(cache_file.read_text(encoding='''utf-8'''))
        
        logger.info(f"Extracting index from {doc_name}")
        
        index_pages = self._find_index_pages(pdf_path)
        if not index_pages:
            logger.warning(f"No index pages found")
            return self._create_empty_structure(doc_name)
        
        logger.info(f"Found index pages: {index_pages}")
        
        index_text = self._extract_index_text(pdf_path, index_pages)
        if not index_text.strip():
            return self._create_empty_structure(doc_name)
        
        structure = self._parse_index_with_llm(doc_name, index_text)
        
        cache_file.write_text(json.dumps(structure, indent=2, ensure_ascii=False), encoding='''utf-8''')
        logger.success(f"Extracted {len(structure.get('''elements''', []))} elements")
        
        return structure
    
    def _find_index_pages(self, pdf_path: Path) -> List[int]:
        try:
            doc = fitz.open(pdf_path)
            index_pages = []
            
            search_range = min(20, len(doc))
            
            for page_num in range(search_range):
                page = doc[page_num]
                text = page.get_text().lower()
                
                keywords = ['''contents''', '''table of contents''', '''index''', '''içindekiler''']
                
                if any(kw in text[:500] for kw in keywords):
                    index_pages.append(page_num)
                    continue
                
                lines = text.split('''\n''')
                numbered_lines = sum(1 for line in lines if re.match(r'''^\s*\d+[\.\d]*\s+\w''', line))
                
                if numbered_lines > 10:
                    index_pages.append(page_num)
            
            doc.close()
            
            if len(index_pages) > 5:
                index_pages = index_pages[:5]
            
            return index_pages
            
        except Exception as e:
            logger.error(f"Error finding index pages: {e}")
            return []
    
    def _extract_index_text(self, pdf_path: Path, page_numbers: List[int]) -> str:
        try:
            doc = fitz.open(pdf_path)
            text_parts = []
            
            for page_num in page_numbers:
                if page_num < len(doc):
                    page = doc[page_num]
                    text = page.get_text()
                    text_parts.append(f"=== PAGE {page_num + 1} ===\n{text}")
            
            doc.close()
            return "\n\n".join(text_parts)
            
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""
    
    def _parse_index_with_llm(self, doc_name: str, index_text: str) -> Dict:
        from openai import OpenAI
        
        client = OpenAI(api_key=self.settings.openai_api_key)
        
        prompt = self._create_extraction_prompt(index_text)
        
        try:
            logger.info("Sending to LLM...")
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Extract document structure. Return JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            result['''document_name'''] = doc_name
            
            if '''elements''' not in result:
                result['''elements'''] = []
            
            logger.success(f"LLM extracted {len(result['''elements'''])} elements")
            return result
            
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return self._create_empty_structure(doc_name)
    
    def _create_extraction_prompt(self, index_text: str) -> str:
        return f"""
Extract ALL sections, tables, figures from this index.

RULES:
1. Detect format automatically
2. Extract hierarchies
3. Get page numbers
4. Classify types: section, table, figure, annex

EXAMPLES:
- "Figure 1: Title ... 9" -> {{"type":"figure","identifier":"Figure 1","title":"Title","page_number":9}}
- "Table 16: Title ... 52" -> {{"type":"table","identifier":"Table 16","title":"Title","page_number":52}}

INDEX TEXT:
{index_text[:4000]}

Return JSON: {{"elements": [...]}}
"""
    
    def _create_empty_structure(self, doc_name: str) -> Dict:
        return {"document_name": doc_name, "elements": []}


def extract_index(pdf_path: str, force_refresh: bool = False) -> Dict:
    extractor = IndexExtractor()
    return extractor.extract_document_structure(pdf_path, force_refresh)
