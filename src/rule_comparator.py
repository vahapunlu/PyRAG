
from typing import List, Dict, Any
from loguru import logger
from llama_index.core.llms import ChatMessage
from .rule_miner import RuleMiner

class RuleComparator:
    """
    Compares two documents based on their extracted Golden Rules.
    Identifies conflicts, agreements, and unique requirements.
    """
    
    def __init__(self, query_engine):
        self.query_engine = query_engine
        self.miner = RuleMiner() # Load rules automatically on init

    def compare_documents(self, doc1_name: str, doc2_name: str) -> Dict[str, Any]:
        """
        Compare rules of two documents using LLM.
        Returns a structured dictionary with analysis results.
        """
        # 1. Fetch rules
        rules_doc1 = self._get_rules_for_doc(doc1_name)
        rules_doc2 = self._get_rules_for_doc(doc2_name)
        
        result = {
            "doc1": doc1_name,
            "doc2": doc2_name,
            "topics": [],
            "timestamp": "Now",
            "text_report": ""
        }
        
        if not rules_doc1:
            result["text_report"] = f"No golden rules found for {doc1_name}. Please use Rule Miner first."
            return result
        if not rules_doc2:
            result["text_report"] = f"No golden rules found for {doc2_name}. Please use Rule Miner first."
            return result
            
        common_topics = set(self._get_topics(rules_doc1)) & set(self._get_topics(rules_doc2))
        all_topics = sorted(list(common_topics))
        
        text_builder = f"# Rule Comparison: {doc1_name} vs {doc2_name}\n\n"
        
        # Analyze Topics
        for topic in all_topics:
            r1 = [r for r in rules_doc1 if topic in r.get('topics', [])]
            r2 = [r for r in rules_doc2 if topic in r.get('topics', [])]
            
            if r1 and r2:
                analysis_text = self._compare_chunk(doc1_name, r1, doc2_name, r2, topic=topic)
                
                result["topics"].append({
                    "name": topic,
                    "analysis": analysis_text
                })
                
                text_builder += f"## Topic: {topic}\n"
                text_builder += analysis_text
                text_builder += "\n\n"
        
        # Analyze General
        r1_gen = [r for r in rules_doc1 if not r.get('topics')]
        r2_gen = [r for r in rules_doc2 if not r.get('topics')]
        if r1_gen and r2_gen:
             analysis_text = self._compare_chunk(doc1_name, r1_gen, doc2_name, r2_gen, topic="General Requirements")
             
             result["topics"].append({
                 "name": "General Requirements",
                 "analysis": analysis_text
             })
             
             text_builder += "## Topic: General Requirements\n"
             text_builder += analysis_text
             
        result["text_report"] = text_builder
        return result


    def _compare_chunk(self, name1, rules1, name2, rules2, topic="General"):
        # Format rules for prompt
        # Include numeric values in the text for the LLM to see explicitly
        txt1 = "\n".join([f"- {r['rule_text']} (Section: {r.get('context','')}) {{Numeric: {r.get('numeric_values',[])}}}" for r in rules1])
        txt2 = "\n".join([f"- {r['rule_text']} (Section: {r.get('context','')}) {{Numeric: {r.get('numeric_values',[])}}}" for r in rules2])
        
        prompt = f"""
You are a Senior Engineering Consultant conducting a "Gap Analysis" between two technical specifications.
Topic: {topic}

Document A ({name1}) Rules:
{txt1}

Document B ({name2}) Rules:
{txt2}

TASK:
1. Identify strictly: CONTRADICTIONS, AGREEMENTS, and MISSING REQUIREMENTS.
2. **CRITICAL**: Extract and compare every numerical/technical parameter (e.g., Lux levels, Cable sizes, Ratings, percentages).

Output Format:

### 1. Analysis Summary
- **Conflict**: [Detail the conflict]
- **Alignment**: [Detail significant agreements]

### 2. Engineering Deltas (Parametric Comparison)
| Parameter | {name1} (Base) | {name2} (Comp) | Status |
|-----------|----------------|----------------|--------|
| [e.g. Min Lux] | [e.g. 500 lux] | [e.g. 300 lux] | [e.g. ⚠️ A is stricter / Conflict] |
|(If no numeric parameters found, write "No numeric parameters in this section")|

### 3. Action Items (Draft TQ)
- [If conflict exists, draft a technical query to resolve it]

Be concise and professional.
"""
        try:
            response = self.query_engine.llm.complete(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Comparison failed: {e}")
            return f"Error analyzing topic {topic}: {str(e)}"

    def _get_rules_for_doc(self, doc_name):
        return [r for r in self.miner.existing_rules if r.get('source_doc') == doc_name]

    def _get_topics(self, rules: List[Dict]) -> List[str]:
        topics = set()
        for r in rules:
            topics.update(r.get('topics', []))
        return list(topics)
