from src.ingestion import DocumentIngestion
from src.utils import setup_logger
from loguru import logger

setup_logger('INFO')

logger.info(' Testing LLM-Based Ingestion with RULES OF THUMB')

ingestion = DocumentIngestion()
pdf_path = 'data/RULES OF THUMB.pdf'

logger.info(f' Processing: {pdf_path}')

result = ingestion.ingest_files(
    [pdf_path],
    categories=['HVAC', 'Design Guidelines'],
    skip_duplicates=False
)

logger.info(f' Complete! Results: {result}')

from src.graph_manager import GraphManager
graph_manager = GraphManager()

query = '''
MATCH (d:DOCUMENT {name: \"RULES OF THUMB\"})-[:HAS_SECTION]->(s:SECTION)
RETURN s.number AS section, s.title AS title, s.page_number AS page
ORDER BY s.page_number
LIMIT 30
'''

sections = graph_manager.neo4j_client.execute_query(query)

logger.info(f' Found {len(sections)} sections:')
for sec in sections:
    logger.info(f'   {sec[\"section\"]:20s} {sec[\"title\"]:50s} (page {sec[\"page\"]})')
