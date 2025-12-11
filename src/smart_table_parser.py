"""
Smart Table Processing Module

Converts markdown tables into structured JSON with:
- Row/column relationships preserved
- Header context for each cell
- Semantic descriptions of table content

This dramatically improves retrieval accuracy for tabular data.
"""

import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from loguru import logger


@dataclass
class TableCell:
    """Represents a single cell in a table"""
    value: str
    row_index: int
    col_index: int
    header: str = ""
    row_context: str = ""  # First cell of the row (often describes the row)
    data_type: str = "text"  # text, number, range, unit_value
    numeric_value: Optional[float] = None
    unit: Optional[str] = None


@dataclass
class TableRow:
    """Represents a row in a table"""
    index: int
    cells: List[TableCell] = field(default_factory=list)
    row_header: str = ""  # First cell often serves as row header
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert row to dictionary with header:value pairs"""
        result = {}
        for cell in self.cells:
            if cell.header:
                result[cell.header] = cell.value
        return result


@dataclass
class ParsedTable:
    """Represents a fully parsed table"""
    headers: List[str]
    rows: List[TableRow]
    caption: str = ""
    table_type: str = ""  # specification, comparison, reference, data
    summary: str = ""
    
    def to_json(self) -> str:
        """Convert table to JSON representation"""
        data = {
            "caption": self.caption,
            "type": self.table_type,
            "summary": self.summary,
            "headers": self.headers,
            "data": [row.to_dict() for row in self.rows]
        }
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def to_natural_language(self) -> str:
        """Convert table to natural language description"""
        lines = []
        
        if self.caption:
            lines.append(f"Table: {self.caption}")
        
        if self.summary:
            lines.append(f"Summary: {self.summary}")
        
        # Describe each row
        for row in self.rows:
            row_desc = []
            for cell in row.cells:
                if cell.header and cell.value:
                    row_desc.append(f"{cell.header}: {cell.value}")
            if row_desc:
                if row.row_header:
                    lines.append(f"For {row.row_header}: " + ", ".join(row_desc[1:]))
                else:
                    lines.append(" | ".join(row_desc))
        
        return "\n".join(lines)


class SmartTableParser:
    """
    Parse markdown tables into structured data
    
    Features:
    - Detects table type (specification, comparison, etc.)
    - Extracts numeric values and units
    - Generates natural language descriptions
    - Preserves row/column relationships
    """
    
    def __init__(self):
        # Unit patterns for value extraction
        self.unit_patterns = [
            (r'(\d+(?:\.\d+)?)\s*(mm²|mm2|sq\.?\s*mm)', 'area'),
            (r'(\d+(?:\.\d+)?)\s*(kV|V|mV|volt)', 'voltage'),
            (r'(\d+(?:\.\d+)?)\s*(kA|A|mA|amp)', 'current'),
            (r'(\d+(?:\.\d+)?)\s*(kW|W|MW|watt)', 'power'),
            (r'(\d+(?:\.\d+)?)\s*(Ω|ohm|ohms)', 'resistance'),
            (r'(\d+(?:\.\d+)?)\s*(°C|°F|K|degree)', 'temperature'),
            (r'(\d+(?:\.\d+)?)\s*(m|mm|cm|km|meter)', 'length'),
            (r'(\d+(?:\.\d+)?)\s*(Hz|kHz|MHz)', 'frequency'),
            (r'(\d+(?:\.\d+)?)\s*(%|percent)', 'percentage'),
            (r'(\d+(?:\.\d+)?)\s*(kg|g|lb|ton)', 'weight'),
        ]
        
        # Table type indicators
        self.type_indicators = {
            'specification': ['rating', 'spec', 'parameter', 'value', 'unit', 'range', 'limit'],
            'comparison': ['vs', 'compare', 'difference', 'option', 'choice', 'type'],
            'reference': ['standard', 'code', 'clause', 'section', 'reference', 'norm'],
            'data': ['measurement', 'result', 'test', 'sample', 'reading'],
            'requirement': ['requirement', 'mandatory', 'optional', 'condition', 'criteria'],
        }
        
        logger.info("✅ Smart Table Parser initialized")
    
    def parse_markdown_table(self, text: str) -> Optional[ParsedTable]:
        """
        Parse a markdown table from text
        
        Args:
            text: Text containing markdown table
            
        Returns:
            ParsedTable or None if no valid table found
        """
        lines = text.strip().split('\n')
        table_lines = []
        caption = ""
        
        # Find table lines
        in_table = False
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Check for table caption (line before table)
            if not in_table and line and not line.startswith('|'):
                if re.match(r'^(Table|Tablo|Tab\.?)\s*\d*[.:]*', line, re.IGNORECASE):
                    caption = line
            
            # Table row detection
            if line.startswith('|') and '|' in line[1:]:
                in_table = True
                # Skip separator row
                if not re.match(r'^\|[-:\s|]+\|$', line):
                    table_lines.append(line)
            elif in_table and not line.startswith('|'):
                break
        
        if len(table_lines) < 2:  # Need at least header + 1 data row
            return None
        
        # Parse header row
        headers = self._parse_row(table_lines[0])
        
        # Parse data rows
        rows = []
        for idx, line in enumerate(table_lines[1:]):
            cells = self._parse_row(line)
            
            if len(cells) != len(headers):
                # Pad or trim to match headers
                while len(cells) < len(headers):
                    cells.append("")
                cells = cells[:len(headers)]
            
            # Create row with cells
            row = TableRow(index=idx, row_header=cells[0] if cells else "")
            
            for col_idx, (header, value) in enumerate(zip(headers, cells)):
                cell = self._create_cell(value, idx, col_idx, header, cells[0] if cells else "")
                row.cells.append(cell)
            
            rows.append(row)
        
        # Determine table type
        table_type = self._detect_table_type(headers, rows)
        
        # Generate summary
        summary = self._generate_summary(headers, rows, table_type)
        
        return ParsedTable(
            headers=headers,
            rows=rows,
            caption=caption,
            table_type=table_type,
            summary=summary
        )
    
    def _parse_row(self, line: str) -> List[str]:
        """Parse a table row into cell values"""
        # Remove leading/trailing pipes and split
        line = line.strip()
        if line.startswith('|'):
            line = line[1:]
        if line.endswith('|'):
            line = line[:-1]
        
        cells = [cell.strip() for cell in line.split('|')]
        return cells
    
    def _create_cell(self, value: str, row_idx: int, col_idx: int, 
                     header: str, row_context: str) -> TableCell:
        """Create a TableCell with parsed attributes"""
        cell = TableCell(
            value=value,
            row_index=row_idx,
            col_index=col_idx,
            header=header,
            row_context=row_context
        )
        
        # Try to extract numeric value and unit
        for pattern, unit_type in self.unit_patterns:
            match = re.search(pattern, value, re.IGNORECASE)
            if match:
                try:
                    cell.numeric_value = float(match.group(1))
                    cell.unit = match.group(2)
                    cell.data_type = 'unit_value'
                    return cell
                except (ValueError, IndexError):
                    pass
        
        # Check for plain number
        if re.match(r'^-?\d+(?:\.\d+)?$', value.strip()):
            try:
                cell.numeric_value = float(value)
                cell.data_type = 'number'
            except ValueError:
                pass
        
        # Check for range (e.g., "10-20" or "10 to 20")
        range_match = re.match(r'^(\d+(?:\.\d+)?)\s*[-–to]\s*(\d+(?:\.\d+)?)(.*)$', value, re.IGNORECASE)
        if range_match:
            cell.data_type = 'range'
            cell.unit = range_match.group(3).strip() if range_match.group(3) else None
        
        return cell
    
    def _detect_table_type(self, headers: List[str], rows: List[TableRow]) -> str:
        """Detect the type of table based on headers and content"""
        header_text = ' '.join(headers).lower()
        
        for table_type, indicators in self.type_indicators.items():
            for indicator in indicators:
                if indicator in header_text:
                    return table_type
        
        # Check row content
        all_values = []
        for row in rows:
            for cell in row.cells:
                all_values.append(cell.value.lower())
        
        all_text = ' '.join(all_values)
        
        for table_type, indicators in self.type_indicators.items():
            for indicator in indicators:
                if indicator in all_text:
                    return table_type
        
        return 'data'  # Default
    
    def _generate_summary(self, headers: List[str], rows: List[TableRow], 
                          table_type: str) -> str:
        """Generate a natural language summary of the table"""
        parts = []
        
        # Basic info
        parts.append(f"A {table_type} table with {len(headers)} columns and {len(rows)} rows.")
        
        # Column info
        parts.append(f"Columns: {', '.join(headers)}")
        
        # Value range info for numeric columns
        numeric_columns = {}
        for row in rows:
            for cell in row.cells:
                if cell.numeric_value is not None:
                    if cell.header not in numeric_columns:
                        numeric_columns[cell.header] = []
                    numeric_columns[cell.header].append(cell.numeric_value)
        
        if numeric_columns:
            range_info = []
            for col, values in numeric_columns.items():
                if values:
                    min_val = min(values)
                    max_val = max(values)
                    if min_val != max_val:
                        range_info.append(f"{col}: {min_val}-{max_val}")
                    else:
                        range_info.append(f"{col}: {min_val}")
            
            if range_info:
                parts.append(f"Value ranges: {', '.join(range_info)}")
        
        return ' '.join(parts)
    
    def convert_to_enriched_text(self, table: ParsedTable) -> str:
        """
        Convert parsed table to enriched text suitable for embedding
        
        Creates multiple representations:
        1. Natural language description
        2. Key-value pairs for each row
        3. Column-based summary
        """
        sections = []
        
        # Table header
        if table.caption:
            sections.append(f"# {table.caption}")
        
        # Summary
        sections.append(f"## Summary\n{table.summary}")
        
        # Natural language description
        sections.append(f"## Content Description\n{table.to_natural_language()}")
        
        # Structured data representation
        sections.append("## Structured Data")
        for row in table.rows:
            row_desc = []
            for cell in row.cells:
                if cell.header and cell.value:
                    if cell.unit:
                        row_desc.append(f"- {cell.header}: {cell.value}")
                    else:
                        row_desc.append(f"- {cell.header}: {cell.value}")
            
            if row_desc:
                if row.row_header:
                    sections.append(f"\n### {row.row_header}")
                sections.extend(row_desc)
        
        return '\n'.join(sections)


class TableEnhancedChunker:
    """
    Enhance document chunks with smart table processing
    
    - Detects tables in chunks
    - Converts to structured JSON
    - Adds enriched text for better embedding
    """
    
    def __init__(self):
        self.parser = SmartTableParser()
        logger.info("✅ Table Enhanced Chunker initialized")
    
    def has_table(self, text: str) -> bool:
        """Check if text contains a markdown table"""
        # Look for table pattern: | header | header |
        return bool(re.search(r'\|[^|]+\|[^|]+\|', text))
    
    def process_chunk(self, text: str) -> Dict[str, Any]:
        """
        Process a text chunk and extract/enhance tables
        
        Returns:
            {
                'original_text': str,
                'has_table': bool,
                'tables': List[ParsedTable],
                'enriched_text': str,  # Text with table descriptions
                'table_json': List[str],  # JSON representations
                'table_metadata': Dict  # Metadata for filtering
            }
        """
        result = {
            'original_text': text,
            'has_table': False,
            'tables': [],
            'enriched_text': text,
            'table_json': [],
            'table_metadata': {}
        }
        
        if not self.has_table(text):
            return result
        
        result['has_table'] = True
        
        # Extract and parse tables
        tables = self._extract_tables(text)
        
        if not tables:
            return result
        
        result['tables'] = tables
        
        # Generate enriched text
        enriched_parts = [text]  # Keep original
        
        for table in tables:
            # Add natural language description
            enriched_parts.append("\n\n--- Table Analysis ---")
            enriched_parts.append(self.parser.convert_to_enriched_text(table))
            
            # Add JSON representation
            result['table_json'].append(table.to_json())
        
        result['enriched_text'] = '\n'.join(enriched_parts)
        
        # Aggregate table metadata
        all_headers = []
        all_types = []
        has_numeric = False
        
        for table in tables:
            all_headers.extend(table.headers)
            all_types.append(table.table_type)
            for row in table.rows:
                for cell in row.cells:
                    if cell.numeric_value is not None:
                        has_numeric = True
                        break
        
        result['table_metadata'] = {
            'table_count': len(tables),
            'table_headers': list(set(all_headers)),
            'table_types': list(set(all_types)),
            'has_numeric_data': has_numeric,
            'total_rows': sum(len(t.rows) for t in tables)
        }
        
        return result
    
    def _extract_tables(self, text: str) -> List[ParsedTable]:
        """Extract all tables from text"""
        tables = []
        
        # Split text into potential table sections
        lines = text.split('\n')
        current_table_lines = []
        in_table = False
        caption = ""
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Check for caption before table
            if not in_table and stripped and not stripped.startswith('|'):
                if re.match(r'^(Table|Tablo|Tab\.?)\s*\d*[.:]*', stripped, re.IGNORECASE):
                    caption = stripped
            
            # Table detection
            if stripped.startswith('|') and '|' in stripped[1:]:
                in_table = True
                current_table_lines.append(line)
            elif in_table:
                if stripped.startswith('|'):
                    current_table_lines.append(line)
                else:
                    # End of table
                    if current_table_lines:
                        table_text = '\n'.join(current_table_lines)
                        if caption:
                            table_text = caption + '\n' + table_text
                        
                        parsed = self.parser.parse_markdown_table(table_text)
                        if parsed:
                            tables.append(parsed)
                    
                    current_table_lines = []
                    caption = ""
                    in_table = False
        
        # Handle last table
        if current_table_lines:
            table_text = '\n'.join(current_table_lines)
            if caption:
                table_text = caption + '\n' + table_text
            
            parsed = self.parser.parse_markdown_table(table_text)
            if parsed:
                tables.append(parsed)
        
        return tables


# Singleton instance
_table_chunker: Optional[TableEnhancedChunker] = None


def get_table_chunker() -> TableEnhancedChunker:
    """Get or create table chunker singleton"""
    global _table_chunker
    if _table_chunker is None:
        _table_chunker = TableEnhancedChunker()
    return _table_chunker


if __name__ == "__main__":
    # Test the module
    logger.info("Testing Smart Table Parser...")
    
    test_text = """
## 6.5.1 Cable Current Ratings

Table 6.1: Maximum current ratings for copper conductors

| Conductor Size | Single Phase | Three Phase | Installation |
|----------------|--------------|-------------|--------------|
| 1.5 mm²        | 15 A         | 13 A        | Conduit      |
| 2.5 mm²        | 20 A         | 18 A        | Conduit      |
| 4 mm²          | 27 A         | 24 A        | Tray         |
| 6 mm²          | 35 A         | 30 A        | Tray         |
| 10 mm²         | 48 A         | 42 A        | Direct       |

Notes: Values are for 30°C ambient temperature.
"""
    
    chunker = get_table_chunker()
    result = chunker.process_chunk(test_text)
    
    print("\n📋 Table Processing Result:")
    print(f"   Has table: {result['has_table']}")
    print(f"   Tables found: {len(result['tables'])}")
    
    if result['tables']:
        table = result['tables'][0]
        print(f"\n   Caption: {table.caption}")
        print(f"   Type: {table.table_type}")
        print(f"   Headers: {table.headers}")
        print(f"   Rows: {len(table.rows)}")
        print(f"\n   Summary: {table.summary}")
        
        print("\n📊 JSON Representation:")
        print(result['table_json'][0][:500])
        
        print("\n📝 Natural Language:")
        print(table.to_natural_language())
