"""
Test new Neo4j connection directly
"""
from src.utils import get_settings
from neo4j import GraphDatabase
from loguru import logger

# Get settings
settings = get_settings()

print("=" * 60)
print("NEO4J CONNECTION TEST")
print("=" * 60)
print(f"URI: {settings.neo4j_uri}")
print(f"Username: {settings.neo4j_username}")
print(f"Database: {settings.neo4j_database}")
print(f"Password: {'*' * 20}...")
print()

# Try to connect
try:
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password)
    )
    
    # Test connection
    with driver.session(database=settings.neo4j_database) as session:
        result = session.run("RETURN 'Connection successful!' AS message, datetime() AS time")
        record = result.single()
        print(f"✅ {record['message']}")
        print(f"🕐 Server time: {record['time']}")
    
    # Check existing nodes
    with driver.session(database=settings.neo4j_database) as session:
        result = session.run("MATCH (n) RETURN count(n) AS total")
        total = result.single()['total']
        print(f"📊 Total nodes in database: {total}")
        
        if total > 0:
            print("\n⚠️ Database is not empty! Contains existing data.")
        else:
            print("\n✅ Database is empty and ready for new data.")
    
    driver.close()
    print("\n✅ Connection test successful!")
    
except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    print(f"\nPlease check:")
    print(f"  1. Neo4j instance is running")
    print(f"  2. URI is correct: {settings.neo4j_uri}")
    print(f"  3. Credentials are correct")
    print(f"  4. Network/firewall allows connection")
