import pymongo
import random
from datetime import date, timedelta
from bson import ObjectId
from dotenv import load_dotenv
import os

mongo_uri = os.getenv('MONGO_URI')
mongo_db_name = os.getenv('MONGO_DB_NAME')
# Подключение
client = pymongo.MongoClient(mongo_uri)
db = client[mongo_db_name]


# Очистка всех коллекций
for coll_name in db.list_collection_names():
    db[coll_name].drop()

print("Коллекции очищены. Начинаем заполнение...")

# =============================================================================
# 1. ОРГАНИЗАЦИИ
# =============================================================================
orgs = [
    {"_id": ObjectId(), "name": 'ООО "Электрон-Маркет"', "inn": "7701234567", "is_our_org": True},
    {"_id": ObjectId(), "name": 'ООО "Цифровая Техника"', "inn": "7712345678", "is_our_org": False},
    {"_id": ObjectId(), "name": 'АО "ТехноТорг"', "inn": "7723456789", "is_our_org": False},
    {"_id": ObjectId(), "name": 'ООО "Элит Гаджет"', "inn": "7734567890", "is_our_org": False},
]
db.organizations.insert_many(orgs)
org_our = orgs[0]["_id"]

# =============================================================================
# 2. СКЛАДЫ
# =============================================================================
whs = [
    {"_id": ObjectId(), "name": "Основной склад", "address": "Москва, ул. Складская, 12"},
    {"_id": ObjectId(), "name": "Склад Ozon", "address": "Москва, ул. Логистическая, 7"},
    {"_id": ObjectId(), "name": "Склад Wildberries", "address": "Москва, ул. Маркетплейсная, 3"},
    {"_id": ObjectId(), "name": "Пункт выдачи заказов", "address": "Москва, ул. Тверская, 25"},
]
db.warehouses.insert_many(whs)
wh_main = whs[0]["_id"]
wh_ozon = whs[1]["_id"]
wh_wb = whs[2]["_id"]
wh_pvz = whs[3]["_id"]
wh_ids = [wh_main, wh_ozon, wh_wb]

# =============================================================================
# 3. КАТЕГОРИИ ТОВАРОВ
# =============================================================================
cat_data = [
    (1, "Электроника", None),
    (2, "Смартфоны", 1),
    (3, "Ноутбуки", 1),
    (4, "Планшеты", 1),
    (5, "Наушники и аудио", 1),
    (6, "Умные часы и браслеты", 1),
    (7, "Телевизоры", 1),
    (8, "Игровые консоли", 1),
    (9, "Компьютеры и комплектующие", None),
    (10, "Мониторы", 9),
    (11, "Клавиатуры и мыши", 9),
    (12, "Бытовая техника", None),
    (13, "Кухонная техника", 12),
    (14, "Климатическая техника", 12),
    (15, "Аксессуары", None),
]

cat_ids = {}
cat_docs = []
for cid, cname, pid in cat_data:
    doc = {"_id": ObjectId(), "name": cname, "parent_id": None}
    cat_ids[cid] = doc["_id"]
    cat_docs.append(doc)

for (cid, cname, pid), doc in zip(cat_data, cat_docs):
    if pid is not None:
        doc["parent_id"] = cat_ids[pid]

db.product_categories.insert_many(cat_docs)

# Создаём обратный маппинг: ObjectId категории -> числовой ID
cat_oid_to_num = {doc["_id"]: cid for (cid, cname, pid), doc in zip(cat_data, cat_docs)}

# =============================================================================
# 4. НОМЕНКЛАТУРА
# =============================================================================
nomenclature_list = [
    ("SM-001", "Apple iPhone 15 Pro Max 256GB", 2),
    ("SM-002", "Samsung Galaxy S24 Ultra 512GB", 2),
    ("SM-003", "Xiaomi 13T Pro 256GB", 2),
    ("SM-004", "Google Pixel 8 128GB", 2),
    ("SM-005", "OnePlus 11 5G 128GB", 2),
    ("SM-006", "Nothing Phone (2) 256GB", 2),
    ("SM-007", "Huawei P60 Pro 256GB", 2),
    ("SM-008", "Sony Xperia 1 V 256GB", 2),
    ("NB-001", 'Apple MacBook Pro 14" M3 Pro', 3),
    ("NB-002", "Lenovo ThinkPad X1 Carbon Gen 11", 3),
    ("NB-003", "ASUS ROG Zephyrus G14 2024", 3),
    ("NB-004", 'HP Spectre x360 14" 2024', 3),
    ("NB-005", "Dell XPS 15 9530", 3),
    ("NB-006", "Acer Swift Go 14", 3),
    ("NB-007", "Microsoft Surface Laptop 6", 3),
    ("TB-001", 'Apple iPad Pro 12.9" M2', 4),
    ("TB-002", "Samsung Galaxy Tab S9+", 4),
    ("TB-003", "Xiaomi Pad 6 Pro", 4),
    ("TB-004", "Lenovo Tab P12 Pro", 4),
    ("AU-001", "Apple AirPods Pro 2nd gen", 5),
    ("AU-002", "Sony WH-1000XM5", 5),
    ("AU-003", "Samsung Galaxy Buds2 Pro", 5),
    ("AU-004", "JBL Tour One M2", 5),
    ("AU-005", "Marshall Major IV", 5),
    ("WEAR-001", "Apple Watch Series 9 45mm", 6),
    ("WEAR-002", "Samsung Galaxy Watch6 Classic 47mm", 6),
    ("WEAR-003", "Huawei Watch GT 4", 6),
    ("WEAR-004", "Amazfit GTR 4", 6),
    ("TV-001", 'Samsung QE75Q70C 75" QLED 4K', 7),
    ("TV-002", 'LG OLED77C3 77" 4K', 7),
    ("TV-003", 'Sony XR-65A95L 65" OLED', 7),
    ("TV-004", 'Xiaomi TV A Pro 65" 4K', 7),
    ("GAME-001", "PlayStation 5 Slim Digital", 8),
    ("GAME-002", "Xbox Series X 1TB", 8),
    ("GAME-003", "Nintendo Switch OLED", 8),
    ("GAME-004", "Steam Deck 512GB", 8),
    ("MON-001", 'Dell UltraSharp U2723QE 27" 4K', 10),
    ("MON-002", 'Samsung Odyssey G7 28" 4K 144Hz', 10),
    ("MON-003", 'LG 27GP950-B 27" 4K 160Hz', 10),
    ("MON-004", 'ASUS ProArt PA279CRV 27" 4K', 10),
    ("PC-001", "Apple Mac mini M2 Pro", 9),
    ("PC-002", "Intel NUC 13 Pro Kit", 9),
    ("KM-001", "Logitech MX Keys S Combo", 11),
    ("KM-002", "Keychron Q6 Pro", 11),
    ("KM-003", "Razer BlackWidow V4 Pro", 11),
    ("KM-004", "Logitech G Pro X Superlight 2", 11),
    ("KT-001", "Philips Airfryer XXL HD9650", 13),
    ("KT-002", "DeLonghi Magnifica S ECAM 22.110.B", 13),
    ("KT-003", "Bosch MUM5XW10 кухонный комбайн", 13),
    ("KT-004", "Xiaomi Smart Air Fryer Pro", 13),
    ("KT-005", "Redmond RMC-M90 мультиварка", 13),
    ("KT-006", "KitchenAid Artisan 5KSM175", 13),
    ("CLIM-001", "Xiaomi Mi Air Purifier 4 Pro", 14),
    ("CLIM-002", "Dyson Purifier Hot+Cool Formaldehyde", 14),
    ("CLIM-003", "Electrolux EHU-5010D увлажнитель", 14),
    ("ACC-001", "Apple MagSafe Charger", 15),
    ("ACC-002", "Samsung 65W Super Fast Charger", 15),
    ("ACC-003", "Anker PowerCore 26800mAh", 15),
    ("ACC-004", "UGREEN USB-C Hub 7-in-1", 15),
]

nomenclature_docs = []
nomenclature_ids = []
nomenclature_cat_num = {}  # маппинг: ObjectId номенклатуры -> числовой ID категории
for art, name, cat_num in nomenclature_list:
    doc = {
        "_id": ObjectId(),
        "article": art,
        "name": name,
        "category_id": cat_ids[cat_num],
        "base_unit": "шт",
        "vat_rate": 20.00
    }
    nomenclature_docs.append(doc)
    nomenclature_ids.append(doc["_id"])
    nomenclature_cat_num[doc["_id"]] = cat_num

db.nomenclature.insert_many(nomenclature_docs)

# =============================================================================
# 5. ТИПЫ ЦЕН
# =============================================================================
pt_docs = [
    {"_id": ObjectId(), "name": "Закупочная", "currency": "RUB"},
    {"_id": ObjectId(), "name": "Розничная", "currency": "RUB"},
    {"_id": ObjectId(), "name": "Оптовая", "currency": "RUB"},
]
db.price_types.insert_many(pt_docs)
pt_purchase = pt_docs[0]["_id"]
pt_retail = pt_docs[1]["_id"]
pt_wholesale = pt_docs[2]["_id"]

# =============================================================================
# 6. ЦЕНЫ
# =============================================================================
def generate_price(price_type, cat_num):
    """Генерация цены по логике SQL-скрипта"""
    if price_type == "Закупочная":
        if cat_num == 2:
            return 45000 + random.randint(0, 35000)
        elif cat_num == 3:
            return 50000 + random.randint(0, 60000)
        elif cat_num == 4:
            return 20000 + random.randint(0, 30000)
        elif cat_num == 5:
            return 3000 + random.randint(0, 15000)
        elif cat_num == 6:
            return 8000 + random.randint(0, 20000)
        elif cat_num == 7:
            return 30000 + random.randint(0, 70000)
        elif cat_num == 8:
            return 18000 + random.randint(0, 30000)
        elif cat_num == 9:
            return 35000 + random.randint(0, 40000)
        elif cat_num == 10:
            return 12000 + random.randint(0, 25000)
        elif cat_num == 11:
            return 1500 + random.randint(0, 5000)
        elif cat_num == 13:
            return 4000 + random.randint(0, 15000)
        elif cat_num == 14:
            return 5000 + random.randint(0, 20000)
        else:
            return 1000 + random.randint(0, 3000)
    elif price_type == "Розничная":
        if cat_num == 2:
            return 70000 + random.randint(0, 60000)
        elif cat_num == 3:
            return 80000 + random.randint(0, 90000)
        elif cat_num == 4:
            return 35000 + random.randint(0, 50000)
        elif cat_num == 5:
            return 6000 + random.randint(0, 25000)
        elif cat_num == 6:
            return 12000 + random.randint(0, 35000)
        elif cat_num == 7:
            return 50000 + random.randint(0, 100000)
        elif cat_num == 8:
            return 25000 + random.randint(0, 40000)
        elif cat_num == 9:
            return 60000 + random.randint(0, 70000)
        elif cat_num == 10:
            return 20000 + random.randint(0, 40000)
        elif cat_num == 11:
            return 3000 + random.randint(0, 8000)
        elif cat_num == 13:
            return 7000 + random.randint(0, 25000)
        elif cat_num == 14:
            return 8000 + random.randint(0, 30000)
        else:
            return 2000 + random.randint(0, 5000)
    else:  # Оптовая
        if cat_num == 2:
            return 60000 + random.randint(0, 50000)
        elif cat_num == 3:
            return 70000 + random.randint(0, 80000)
        elif cat_num == 4:
            return 28000 + random.randint(0, 40000)
        elif cat_num == 5:
            return 5000 + random.randint(0, 20000)
        elif cat_num == 6:
            return 10000 + random.randint(0, 30000)
        elif cat_num == 7:
            return 40000 + random.randint(0, 80000)
        elif cat_num == 8:
            return 20000 + random.randint(0, 35000)
        elif cat_num == 9:
            return 50000 + random.randint(0, 60000)
        elif cat_num == 10:
            return 15000 + random.randint(0, 35000)
        elif cat_num == 11:
            return 2500 + random.randint(0, 6000)
        elif cat_num == 13:
            return 6000 + random.randint(0, 20000)
        elif cat_num == 14:
            return 7000 + random.randint(0, 25000)
        else:
            return 1500 + random.randint(0, 4000)

prices_docs = []
price_map = {}  # Кэш цен: (nomenclature_id, price_type_id) -> price

for n_doc in nomenclature_docs:
    nid = n_doc["_id"]
    cat_num = nomenclature_cat_num[nid]
    
    for pt_name, pt_id in [("Закупочная", pt_purchase), ("Розничная", pt_retail), ("Оптовая", pt_wholesale)]:
        price_value = float(generate_price(pt_name, cat_num))
        price_map[(nid, pt_id)] = price_value
        prices_docs.append({
            "nomenclature_id": nid,
            "price_type_id": pt_id,
            "price": price_value,
            "valid_from": "2022-01-01"
        })

db.prices.insert_many(prices_docs)

# =============================================================================
# 7. КОНТРАГЕНТЫ
# =============================================================================
counterparties = [
    {"_id": ObjectId(), "name": "Иванов Иван", "type": "client", "phone": "+79031110001", "email": "ivanov@mail.ru"},
    {"_id": ObjectId(), "name": "Петрова Анна", "type": "client", "phone": "+79051110002", "email": "petrova@mail.ru"},
    {"_id": ObjectId(), "name": "Сидоров Олег", "type": "client", "phone": "+79062220003", "email": "sidorov@yandex.ru"},
    {"_id": ObjectId(), "name": "Козлова Елена", "type": "client", "phone": "+79083330004", "email": "kozlova@gmail.com"},
    {"_id": ObjectId(), "name": "Морозов Дмитрий", "type": "client", "phone": "+79104440005", "email": "morozov@outlook.com"},
    {"_id": ObjectId(), "name": "Волкова Светлана", "type": "client", "phone": "+79115550006", "email": "volkova@rambler.ru"},
    {"_id": ObjectId(), "name": "Новиков Артем", "type": "client", "phone": "+79126660007", "email": "novikov@mail.com"},
    {"_id": ObjectId(), "name": "Федорова Мария", "type": "client", "phone": "+79137770008", "email": "fedorova@yandex.com"},
    {"_id": ObjectId(), "name": "Григорьев Павел", "type": "client", "phone": "+79148880009", "email": "grigoriev@mail.ru"},
    {"_id": ObjectId(), "name": "Алексеева Юлия", "type": "client", "phone": "+79159990010", "email": "alekseeva@gmail.com"},
    {"_id": ObjectId(), "name": "Зайцев Роман", "type": "client", "phone": "+79160001111", "email": "zaytsev@yandex.ru"},
    {"_id": ObjectId(), "name": "Соловьева Виктория", "type": "client", "phone": "+79171112222", "email": "solovieva@mail.ru"},
    {"_id": ObjectId(), "name": "Кузьмин Никита", "type": "client", "phone": "+79182223333", "email": "kuzmin@outlook.com"},
    {"_id": ObjectId(), "name": "Игнатова Полина", "type": "client", "phone": "+79193334444", "email": "ignatova@mail.ru"},
    {"_id": ObjectId(), "name": "Баранов Андрей", "type": "client", "phone": "+79204445555", "email": "baranov@yandex.ru"},
    {"_id": ObjectId(), "name": 'ООО "Цифровой Мир"', "type": "supplier", "phone": "+74950000001", "email": "supply@digitalmir.ru"},
    {"_id": ObjectId(), "name": 'АО "ТехноПро"', "type": "supplier", "phone": "+74950000002", "email": "info@technopro.ru"},
    {"_id": ObjectId(), "name": 'ООО "Электро-Торг"', "type": "supplier", "phone": "+74950000003", "email": "sale@electrotorg.ru"},
    {"_id": ObjectId(), "name": 'ИП "Гаджет Опт"', "type": "both", "phone": "+74950000004", "email": "opt@gadget-opt.ru"},
    {"_id": ObjectId(), "name": 'ООО "Смарт-Поставка"', "type": "supplier", "phone": "+74950000005", "email": "supply@smart-post.ru"},
]
db.counterparties.insert_many(counterparties)

client_ids = [c["_id"] for c in counterparties if c["type"] in ("client", "both")]
supplier_ids = [c["_id"] for c in counterparties if c["type"] in ("supplier", "both")]

print("Справочники заполнены. Начинаем генерацию движений...")

# =============================================================================
# 8. НАЧАЛЬНЫЕ ОСТАТКИ (ЗАКУПКА + ТРАНСФЕРЫ)
# =============================================================================

# 8.1. Крупное оприходование на Основной склад
purch_id_initial = ObjectId()
db.purchases.insert_one({
    "_id": purch_id_initial,
    "number": "ПТ-2022-001",
    "date": "2022-01-01",
    "organization_id": org_our,
    "counterparty_id": supplier_ids[0],
    "warehouse_id": wh_main,
    "items": []
})

inv_ops = []
for nid in nomenclature_ids:
    cat_num = nomenclature_cat_num[nid]
    
    if cat_num in (2, 3, 4, 7, 8, 9, 10):
        qty = 150
    elif cat_num in (5, 6, 13, 14):
        qty = 200
    else:
        qty = 300
    
    purch_price = price_map[(nid, pt_purchase)]
    amount = qty * purch_price
    
    db.purchases.update_one(
        {"_id": purch_id_initial},
        {"$push": {"items": {
            "nomenclature_id": nid,
            "quantity": qty,
            "price": purch_price,
            "amount": amount
        }}}
    )
    
    inv_ops.append(
        pymongo.UpdateOne(
            {"warehouse_id": wh_main, "nomenclature_id": nid},
            {"$inc": {"quantity": qty, "total_cost": amount}},
            upsert=True
        )
    )

db.inventory_balances.bulk_write(inv_ops)

# 8.2. Трансфер на Склад Ozon (40 шт.)
transfer1_id = ObjectId()
db.transfers.insert_one({
    "_id": transfer1_id,
    "number": "ТР-2022-001",
    "date": "2022-01-02",
    "from_warehouse_id": wh_main,
    "to_warehouse_id": wh_ozon,
    "items": []
})

transfer_items_ozon = []
for nid in nomenclature_ids:
    cat_num = nomenclature_cat_num[nid]
    if cat_num in (2, 3, 4, 5, 6, 7, 8, 9, 10):
        qty = 40
        
        db.transfers.update_one(
            {"_id": transfer1_id},
            {"$push": {"items": {
                "nomenclature_id": nid,
                "quantity": qty
            }}}
        )
        
        # Получаем себестоимость с основного склада
        inv_main = db.inventory_balances.find_one({"warehouse_id": wh_main, "nomenclature_id": nid})
        if inv_main and inv_main["quantity"] > 0:
            avg_cost = inv_main["total_cost"] / inv_main["quantity"]
            cost_amount = qty * avg_cost
            
            # Списываем с основного склада
            db.inventory_balances.update_one(
                {"warehouse_id": wh_main, "nomenclature_id": nid},
                {"$inc": {"quantity": -qty, "total_cost": -cost_amount}}
            )
            
            # Зачисляем на Ozon
            transfer_items_ozon.append(
                pymongo.UpdateOne(
                    {"warehouse_id": wh_ozon, "nomenclature_id": nid},
                    {"$inc": {"quantity": qty, "total_cost": cost_amount}},
                    upsert=True
                )
            )

if transfer_items_ozon:
    db.inventory_balances.bulk_write(transfer_items_ozon)

# 8.3. Трансфер на Склад Wildberries (30 шт.)
transfer2_id = ObjectId()
db.transfers.insert_one({
    "_id": transfer2_id,
    "number": "ТР-2022-002",
    "date": "2022-01-02",
    "from_warehouse_id": wh_main,
    "to_warehouse_id": wh_wb,
    "items": []
})

transfer_items_wb = []
for nid in nomenclature_ids:
    cat_num = nomenclature_cat_num[nid]
    if cat_num in (2, 3, 4, 7, 8, 9, 10, 13, 14):
        qty = 30
        
        db.transfers.update_one(
            {"_id": transfer2_id},
            {"$push": {"items": {
                "nomenclature_id": nid,
                "quantity": qty
            }}}
        )
        
        inv_main = db.inventory_balances.find_one({"warehouse_id": wh_main, "nomenclature_id": nid})
        if inv_main and inv_main["quantity"] > 0:
            avg_cost = inv_main["total_cost"] / inv_main["quantity"]
            cost_amount = qty * avg_cost
            
            db.inventory_balances.update_one(
                {"warehouse_id": wh_main, "nomenclature_id": nid},
                {"$inc": {"quantity": -qty, "total_cost": -cost_amount}}
            )
            
            transfer_items_wb.append(
                pymongo.UpdateOne(
                    {"warehouse_id": wh_wb, "nomenclature_id": nid},
                    {"$inc": {"quantity": qty, "total_cost": cost_amount}},
                    upsert=True
                )
            )

if transfer_items_wb:
    db.inventory_balances.bulk_write(transfer_items_wb)

# Обновляем avg_cost для всех остатков
for inv_doc in db.inventory_balances.find():
    if inv_doc["quantity"] != 0:
        avg = round(inv_doc["total_cost"] / inv_doc["quantity"], 2)
    else:
        avg = 0
    db.inventory_balances.update_one(
        {"_id": inv_doc["_id"]},
        {"$set": {"avg_cost": avg}}
    )

print("Начальные остатки созданы. Генерируем ежедневные данные...")

# =============================================================================
# 9. ЕЖЕДНЕВНАЯ ГЕНЕРАЦИЯ (2022-2024)
# =============================================================================
start_date = date(2022, 1, 1)
end_date = date(2024, 12, 31)
current_date = start_date

total_days = (end_date - start_date).days
day_counter = 0

while current_date <= end_date:
    day_counter += 1
    
    # Прогресс (раз в 3 месяца)
    if current_date.day == 1 and current_date.month in (1, 4, 7, 10):
        print(f"Обработан {current_date} (день {day_counter} из {total_days})")
    
    # ---- ЗАКУПКИ (2-5 в день) ----
    for i in range(random.randint(2, 5)):
        supplier = random.choice(supplier_ids)
        purch_id = db.purchases.insert_one({
            "number": f"ПТ-{current_date.strftime('%y%m%d')}-{i+1}",
            "date": current_date.isoformat(),
            "organization_id": org_our,
            "counterparty_id": supplier,
            "warehouse_id": wh_main,
            "items": []
        }).inserted_id
        
        items_count = random.randint(3, 7)
        inv_bulk = []
        for _ in range(items_count):
            nid = random.choice(nomenclature_ids)
            qty = random.randint(5, 19)
            purch_price = price_map[(nid, pt_purchase)]
            amount = qty * purch_price
            
            db.purchases.update_one(
                {"_id": purch_id},
                {"$push": {"items": {
                    "nomenclature_id": nid,
                    "quantity": qty,
                    "price": purch_price,
                    "amount": amount
                }}}
            )
            
            inv_bulk.append(
                pymongo.UpdateOne(
                    {"warehouse_id": wh_main, "nomenclature_id": nid},
                    {"$inc": {"quantity": qty, "total_cost": amount}},
                    upsert=True
                )
            )
        
        if inv_bulk:
            db.inventory_balances.bulk_write(inv_bulk)
    
    # ---- ПРОДАЖИ (60-120 заказов в день) ----
    num_orders = random.randint(60, 120)
    turnover_bulk = []
    
    for i in range(num_orders):
        wh = random.choice(wh_ids)
        client = random.choice(client_ids)
        
        order_id = db.customer_orders.insert_one({
            "number": f"ЗК-{current_date.strftime('%y%m%d')}-{i+1}",
            "date": current_date.isoformat(),
            "organization_id": org_our,
            "counterparty_id": client,
            "warehouse_id": wh,
            "status": "completed",
            "items": []
        }).inserted_id
        
        items_per_order = random.randint(1, 3)
        for _ in range(items_per_order):
            nid = random.choice(nomenclature_ids)
            
            inv = db.inventory_balances.find_one({"warehouse_id": wh, "nomenclature_id": nid})
            if not inv or inv["quantity"] < 1:
                continue
            
            max_qty = min(int(inv["quantity"]), 3)
            sell_qty = random.randint(1, max_qty)
            
            retail_price = price_map[(nid, pt_retail)]
            discount = random.uniform(0, 0.15)
            price = round(retail_price * (1 - discount), 2)
            
            avg_cost = inv.get("avg_cost", 0)
            cost_price = avg_cost
            
            amount = round(sell_qty * price, 2)
            cost_amount = round(sell_qty * cost_price, 2)
            
            db.customer_orders.update_one(
                {"_id": order_id},
                {"$push": {"items": {
                    "nomenclature_id": nid,
                    "quantity": sell_qty,
                    "price": price,
                    "amount": amount
                }}}
            )
            
            sale_id = db.sales.insert_one({
                "number": f"РТ-{current_date.strftime('%y%m%d')}-{i+1}",
                "date": current_date.isoformat(),
                "organization_id": org_our,
                "counterparty_id": client,
                "warehouse_id": wh,
                "order_id": order_id,
                "items": [{
                    "nomenclature_id": nid,
                    "quantity": sell_qty,
                    "price": price,
                    "cost_price": cost_price,
                    "amount": amount,
                    "cost_amount": cost_amount
                }]
            }).inserted_id
            
            db.inventory_balances.update_one(
                {"warehouse_id": wh, "nomenclature_id": nid},
                {"$inc": {"quantity": -sell_qty, "total_cost": -cost_amount}}
            )
            
            turnover_bulk.append(
                pymongo.InsertOne({
                    "date": current_date.isoformat(),
                    "nomenclature_id": nid,
                    "warehouse_id": wh,
                    "quantity": sell_qty,
                    "revenue": amount,
                    "cost_total": cost_amount
                })
            )
    
    if turnover_bulk:
        db.sales_turnover.bulk_write(turnover_bulk)
    
    # Обновляем avg_cost раз в день для затронутых товаров (опционально)
    # Для производительности можно делать раз в месяц
    
    current_date += timedelta(days=1)

# Финальное обновление avg_cost
print("Обновляем среднюю себестоимость...")
for inv_doc in db.inventory_balances.find():
    if inv_doc["quantity"] != 0:
        avg = round(inv_doc["total_cost"] / inv_doc["quantity"], 2)
    else:
        avg = 0
    db.inventory_balances.update_one(
        {"_id": inv_doc["_id"]},
        {"$set": {"avg_cost": avg}}
    )

# =============================================================================
# 10. ИНДЕКСЫ
# =============================================================================
print("Создаём индексы...")
db.inventory_balances.create_index([("warehouse_id", 1), ("nomenclature_id", 1)], unique=True)
db.sales.create_index([("date", 1)])
db.sales.create_index([("order_id", 1)])
db.purchases.create_index([("date", 1)])
db.sales_turnover.create_index([("date", 1)])
db.customer_orders.create_index([("date", 1)])

# =============================================================================
# СТАТИСТИКА
# =============================================================================
print("\n" + "="*60)
print("ГЕНЕРАЦИЯ ЗАВЕРШЕНА!")
print("="*60)
print(f"Организаций: {db.organizations.count_documents({})}")
print(f"Складов: {db.warehouses.count_documents({})}")
print(f"Категорий: {db.product_categories.count_documents({})}")
print(f"Товаров: {db.nomenclature.count_documents({})}")
print(f"Типов цен: {db.price_types.count_documents({})}")
print(f"Цен: {db.prices.count_documents({})}")
print(f"Контрагентов: {db.counterparties.count_documents({})}")
print(f"Закупок: {db.purchases.count_documents({})}")
print(f"Заказов клиентов: {db.customer_orders.count_documents({})}")
print(f"Продаж: {db.sales.count_documents({})}")
print(f"Трансферов: {db.transfers.count_documents({})}")
print(f"Записей остатков: {db.inventory_balances.count_documents({})}")
print(f"Записей оборотов: {db.sales_turnover.count_documents({})}")