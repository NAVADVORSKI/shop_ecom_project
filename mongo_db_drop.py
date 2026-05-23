import pymongo

# Подключение
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["electronics_db"]

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