
from src.graph_manager import get_graph_manager
from loguru import logger
import sys

def main():
    logger.info("Initializing Graph Manager...")
    gm = get_graph_manager()
    if gm:
        logger.info("Clearing Neo4j Graph...")
        gm.clear_graph()
        gm.close()
        logger.success("Neo4j graph has been completely reset.")
    else:
        logger.error("Could not initialize GraphManager. Check your .env.neo4j configuration.")

if __name__ == "__main__":
    main()
