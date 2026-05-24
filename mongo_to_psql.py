from pymongo import MongoClient
from dotenv import load_dotenv
import os
import logging
import psycopg2
from lib import MongoToPostgresLoader

logger = logging.getLogger(__name__)

load_dotenv()

mongo_uri = os.getenv('MONGO_URI')
mongo_db = os.getenv('MONGO_DB_NAME')
psql_dbname = os.getenv('PSQL_DB_NAME')
psql_username = os.getenv('PSQL_DB_USER_NAME')
psql_password = os.getenv('PSQL_DB_USER_PASSWORD')
psql_host = os.getenv('PSQL_DB_HOST')
psql_port = os.getenv('PSQL_DB_PORT')
psql_schema = os.getenv('PSQL_SCHEMA_NAME')

loader = MongoToPostgresLoader(
    mongo_uri=mongo_uri,
    mongo_db=mongo_db,
    pg_host=psql_host,
    pg_port=psql_port,
    pg_db=psql_dbname,
    pg_user=psql_username,
    pg_password=psql_password,
    pg_schema=psql_schema,
    batch_size=1000
)

try:
    load_info = loader.get_last_load_info()
    
    print(f"Последняя загрузка: {load_info['last_load_ts']}")
    print(f"Загружено таблиц: {load_info['summary']['loaded_tables']}")
    
    for table, info in load_info['tables'].items():
        print(f"  {table}: {info['row_count']} строк, обновлена {info['last_update']}")
    
    last_ts = loader.get_last_load_timestamp()
    
    if last_ts:
        print(f"\nМожно делать инкрементальную загрузку с {last_ts}")
        
        results = loader.load_all_collections(last_loaded_ts=last_ts)
    else:
        print("\nБаза пуста, нужна полная загрузка")
        results = loader.load_all_collections(force_full_load=True)
    
    loader.print_load_status()
        
finally:
    loader.close()
