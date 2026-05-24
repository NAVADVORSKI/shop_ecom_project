import pymongo
from dotenv import load_dotenv
import os

mongo_uri = os.getenv('MONGO_URI')
mongo_db_name = os.getenv('MONGO_DB_NAME')
# Подключение
client = pymongo.MongoClient(mongo_uri)
db = client[mongo_db_name]

# Очистка всех коллекций
collections = [
    "organizations",
    "warehouses", 
    "product_categories",
    "nomenclature",
    "price_types",
    "prices",
    "counterparties",
    "customer_orders",
    "sales",
    "purchases",
    "transfers",
    "inventory_balances",
    "sales_turnover"
]

for collection_name in collections:
    if collection_name in db.list_collection_names():
        db[collection_name].drop()
        print(f"Коллекция {collection_name} удалена")

print("База данных очищена!")