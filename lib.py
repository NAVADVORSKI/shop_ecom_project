import pymongo
import psycopg2
from psycopg2.extras import execute_values
from psycopg2 import errors
from datetime import datetime
from bson import ObjectId
import json
from typing import List, Dict, Optional, Any
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MongoToPostgresLoader:
    """
    Универсальный класс для инкрементальной загрузки данных из MongoDB в PostgreSQL.
    """
    
    # Порядок загрузки коллекций (сначала справочники, потом документы)
    LOAD_ORDER = [
        # 1. Справочники (нет внешних ключей или ссылаются на справочники выше)
        "organizations",
        "warehouses",
        "product_categories",
        "nomenclature",
        "price_types",
        "counterparties",
        
        # 2. Зависимые справочники
        "prices",
        
        # 3. Документы
        "customer_orders",
        "purchases",
        "transfers",
        "sales",
        
        # 4. Регистры
        "inventory_balances",
        "sales_turnover",
    ]
    
    # Таблицы, для которых НЕ создаём внешние ключи при автосоздании
    # (потому что FK создаются отдельным скриптом инициализации)
    SKIP_FOREIGN_KEYS = True
    
    def __init__(
        self,
        mongo_uri: str,
        mongo_db: str,
        pg_host: str,
        pg_port: int,
        pg_db: str,
        pg_user: str,
        pg_password: str,
        pg_schema: str ,
        batch_size: int
    ):
        self.mongo_client = pymongo.MongoClient(mongo_uri)
        self.mongo_db = self.mongo_client[mongo_db]
        
        self.pg_conn = psycopg2.connect(
            host=pg_host,
            port=pg_port,
            dbname=pg_db,
            user=pg_user,
            password=pg_password
        )
        self.pg_conn.autocommit = False  # Явно управляем транзакциями
        self.pg_cursor = self.pg_conn.cursor()
        
        self.pg_schema = pg_schema
        self.batch_size = batch_size
        
        logger.info(f"Подключен к MongoDB: {mongo_db}")
        logger.info(f"Подключен к PostgreSQL: {pg_db}.{pg_schema}")
    
    def _get_pg_type(self, value: Any) -> str:
        """Определяет PostgreSQL тип для значения Python/MongoDB."""
        if isinstance(value, str):
            if len(value) == 10 and value.count('-') == 2:
                try:
                    datetime.strptime(value, '%Y-%m-%d')
                    return 'DATE'
                except ValueError:
                    pass
            return 'VARCHAR'
        elif isinstance(value, bool):
            return 'BOOLEAN'
        elif isinstance(value, int):
            return 'INTEGER'
        elif isinstance(value, float):
            return 'NUMERIC(12,3)'
        elif isinstance(value, datetime):
            return 'TIMESTAMP'
        elif isinstance(value, ObjectId):
            return 'VARCHAR(24)'
        elif isinstance(value, (list, dict)):
            return 'JSONB'
        elif value is None:
            return 'VARCHAR(24)'
        else:
            return 'VARCHAR'
    
    def _convert_value_for_pg(self, value: Any) -> Any:
        """Преобразует значение из MongoDB в формат для PostgreSQL."""
        if isinstance(value, ObjectId):
            return str(value)
        elif isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, (list, dict)):
            return json.dumps(self._convert_nested_objectid(value), ensure_ascii=False)
        elif isinstance(value, float):
            return round(value, 3)
        else:
            return value
    
    def _convert_nested_objectid(self, obj: Any) -> Any:
        """Рекурсивно преобразует ObjectId в строках внутри вложенных структур."""
        if isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: self._convert_nested_objectid(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_nested_objectid(item) for item in obj]
        else:
            return obj
    
    def _get_collection_columns(self, collection_name: str) -> Dict[str, str]:
        """
        Анализирует коллекцию MongoDB и возвращает словарь {имя_поля: pg_тип}.
        """
        collection = self.mongo_db[collection_name]
        sample_docs = list(collection.find().limit(100))
        
        if not sample_docs:
            logger.warning(f"Коллекция {collection_name} пуста")
            return {"_id": "VARCHAR(24)"}
        
        columns = {"_id": "VARCHAR(24)"}
        
        for doc in sample_docs:
            for key, value in doc.items():
                if key == '_id':
                    continue
                if key not in columns:
                    pg_type = self._get_pg_type(value)
                    columns[key] = pg_type
        
        return columns
    
    def create_table_from_mongo(self, collection_name: str) -> None:
        """
        Создаёт таблицу в PostgreSQL БЕЗ внешних ключей.
        Внешние ключи создаются отдельным скриптом инициализации.
        """
        columns = self._get_collection_columns(collection_name)
        
        column_defs = ["id VARCHAR(24) PRIMARY KEY"]
        
        for col_name, col_type in columns.items():
            if col_name == '_id':
                continue
            
            # Делаем все колонки NULLABLE для гибкости загрузки
            column_defs.append(f"{col_name} {col_type}")
        
        column_defs.append("update_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.pg_schema}.{collection_name} (
            {', '.join(column_defs)}
        );
        """
        
        try:
            # Создаём таблицу в отдельной транзакции
            self._execute_in_transaction(create_sql)
            logger.info(f"✅ Таблица {self.pg_schema}.{collection_name} готова")
        except Exception as e:
            logger.error(f"❌ Ошибка создания таблицы {collection_name}: {e}")
            raise
    
    def _execute_in_transaction(self, sql: str, params: tuple = None) -> None:
        """
        Выполняет SQL в отдельной транзакции.
        Если ошибка — откатывает, но НЕ ломает основное соединение.
        """
        try:
            if params:
                self.pg_cursor.execute(sql, params)
            else:
                self.pg_cursor.execute(sql)
            self.pg_conn.commit()
        except Exception as e:
            self.pg_conn.rollback()
            raise e
    
    def _prepare_document_for_insert(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Подготавливает MongoDB документ для вставки в PostgreSQL."""
        prepared = {}
        
        for key, value in doc.items():
            if key == '_id':
                prepared['id'] = str(value)
            else:
                prepared[key] = self._convert_value_for_pg(value)
        
        return prepared
    
    def load_collection(
        self,
        collection_name: str,
        last_loaded_ts: Optional[datetime] = None,
        force_full_load: bool = False
    ) -> int:
        """
        Загружает данные из MongoDB коллекции в PostgreSQL таблицу.
        Каждый пакет — в отдельной транзакции.
        """
        # Создаём таблицу, если её нет
        self.create_table_from_mongo(collection_name)
        
        # Формируем фильтр для MongoDB
        filter_query = {}
        
        if not force_full_load and last_loaded_ts:
            filter_query = {
                "_id": {"$gt": ObjectId.from_datetime(last_loaded_ts)}
            }
            logger.info(f"🔄 Инкрементальная загрузка {collection_name} с {last_loaded_ts}")
        else:
            logger.info(f"📦 Полная загрузка {collection_name}")
        
        collection = self.mongo_db[collection_name]
        total_docs = collection.count_documents(filter_query)
        
        if total_docs == 0:
            logger.info(f"  → Нет документов для загрузки")
            return 0
        
        logger.info(f"  → Найдено {total_docs} документов")
        
        loaded_count = 0
        failed_count = 0
        batch = []
        
        for doc in collection.find(filter_query).batch_size(self.batch_size):
            prepared_doc = self._prepare_document_for_insert(doc)
            batch.append(prepared_doc)
            
            if len(batch) >= self.batch_size:
                success = self._insert_batch(collection_name, batch)
                if success:
                    loaded_count += len(batch)
                else:
                    failed_count += len(batch)
                
                if loaded_count % 5000 == 0 and loaded_count > 0:
                    logger.info(f"  → Прогресс: {loaded_count}/{total_docs}")
                
                batch = []
        
        # Загружаем остаток
        if batch:
            success = self._insert_batch(collection_name, batch)
            if success:
                loaded_count += len(batch)
            else:
                failed_count += len(batch)
        
        if failed_count > 0:
            logger.warning(f"⚠️ {collection_name}: загружено {loaded_count}, ошибок в {failed_count}")
        else:
            logger.info(f"✅ {collection_name}: загружено {loaded_count}")
        
        return loaded_count
    
    def _insert_batch(self, table_name: str, batch: List[Dict[str, Any]]) -> bool:
        """
        Вставляет пакет документов в отдельной транзакции.
        Возвращает True если успешно, False если ошибка.
        """
        if not batch:
            return True
        
        columns = list(batch[0].keys())
        column_names = ', '.join(columns)
        
        # Формируем SET для ON CONFLICT
        update_set = ', '.join([
            f"{col} = EXCLUDED.{col}" 
            for col in columns 
            if col not in ['id']
        ])
        update_set += ', update_ts = CURRENT_TIMESTAMP'
        
        values = []
        for doc in batch:
            row = [doc.get(col) for col in columns]
            values.append(row)
        
        try:
            upsert_sql = f"""
            INSERT INTO {self.pg_schema}.{table_name} ({column_names})
            VALUES %s
            ON CONFLICT (id) DO UPDATE SET
                {update_set}
            """
            
            execute_values(
                self.pg_cursor,
                upsert_sql,
                values,
                template=None,
                page_size=self.batch_size
            )
            self.pg_conn.commit()
            return True
            
        except errors.ForeignKeyViolation as e:
            # Ошибка внешнего ключа — пропускаем пакет
            self.pg_conn.rollback()
            logger.warning(f"⚠️ Нарушение FK в {table_name}, пакет пропущен")
            return False
            
        except Exception as e:
            self.pg_conn.rollback()
            logger.error(f"❌ Ошибка вставки в {table_name}: {e}")
            return False
    
    def load_all_collections(
        self,
        last_loaded_ts: Optional[datetime] = None,
        force_full_load: bool = False
    ) -> Dict[str, int]:
        """
        Загружает ВСЕ коллекции в ПРАВИЛЬНОМ порядке.
        """
        # Проверяем, какие коллекции есть в MongoDB
        existing_collections = self.mongo_db.list_collection_names()
        
        results = {}
        total_collections = len(self.LOAD_ORDER)
        current = 0
        
        logger.info("=" * 60)
        logger.info("НАЧИНАЕМ ЗАГРУЗКУ ВСЕХ КОЛЛЕКЦИЙ")
        logger.info("=" * 60)
        
        for collection_name in self.LOAD_ORDER:
            current += 1
            
            if collection_name not in existing_collections:
                logger.warning(f"[{current}/{total_collections}] ⚠️ {collection_name} — нет в MongoDB, пропускаем")
                continue
            
            logger.info(f"[{current}/{total_collections}] Загружаем {collection_name}...")
            
            try:
                count = self.load_collection(
                    collection_name,
                    last_loaded_ts if not force_full_load else None,
                    force_full_load
                )
                results[collection_name] = count
            except Exception as e:
                logger.error(f"[{current}/{total_collections}] ❌ {collection_name}: {e}")
                results[collection_name] = 0
        
        # Итоги
        logger.info("=" * 60)
        logger.info("РЕЗУЛЬТАТЫ ЗАГРУЗКИ:")
        total_loaded = 0
        for coll, count in results.items():
            logger.info(f"  {coll}: {count}")
            total_loaded += count
        logger.info(f"  ВСЕГО загружено: {total_loaded}")
        logger.info("=" * 60)
        
        return results
    
    def load_only_tables(self, table_names: List[str]) -> Dict[str, int]:
        """Загружает только указанные таблицы."""
        results = {}
        for name in table_names:
            count = self.load_collection(name, force_full_load=True)
            results[name] = count
        return results
    
    def close(self):
        """Закрывает все подключения."""
        self.mongo_client.close()
        self.pg_cursor.close()
        self.pg_conn.close()
        logger.info("🔌 Подключения закрыты")

    def get_last_load_info(self) -> Dict[str, Any]:
        """
        Получает информацию о последней загрузке для ВСЕХ таблиц в схеме staging.
        
        Returns:
            Словарь с информацией о последней загрузке:
            {
                'last_load_ts': datetime,        # Максимальная дата загрузки среди всех таблиц
                'tables': {                       # Информация по каждой таблице
                    'organizations': {
                        'last_update': datetime,
                        'row_count': int,
                        'status': 'loaded' | 'empty' | 'error'
                    },
                    ...
                },
                'summary': {
                    'total_tables': int,
                    'loaded_tables': int,
                    'empty_tables': int
                }
            }
        """
        result = {
            'last_load_ts': None,
            'tables': {},
            'summary': {
                'total_tables': 0,
                'loaded_tables': 0,
                'empty_tables': 0
            }
        }
        
        # Получаем список ВСЕХ таблиц в схеме staging
        try:
            self.pg_cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """, (self.pg_schema,))
            
            tables = [row[0] for row in self.pg_cursor.fetchall()]
            result['summary']['total_tables'] = len(tables)
            
            max_ts = None
            
            for table_name in tables:
                table_info = self._get_table_load_info(table_name)
                result['tables'][table_name] = table_info
                
                # Обновляем статусы
                if table_info['row_count'] > 0:
                    result['summary']['loaded_tables'] += 1
                    
                    # Ищем максимальную дату
                    if table_info['last_update']:
                        if max_ts is None or table_info['last_update'] > max_ts:
                            max_ts = table_info['last_update']
                else:
                    result['summary']['empty_tables'] += 1
            
            result['last_load_ts'] = max_ts
            
        except Exception as e:
            logger.error(f"Ошибка получения информации о загрузке: {e}")
        
        return result


    def _get_table_load_info(self, table_name: str) -> Dict[str, Any]:
        """
        Получает информацию о загрузке конкретной таблицы.
        
        Args:
            table_name: Название таблицы
            
        Returns:
            Словарь с информацией о таблице
        """
        info = {
            'last_update': None,
            'row_count': 0,
            'status': 'empty'
        }
        
        try:
            # Получаем количество строк и максимальную дату обновления
            self.pg_cursor.execute(f"""
                SELECT 
                    COUNT(*) as row_count,
                    MAX(update_ts) as last_update
                FROM {self.pg_schema}.{table_name}
            """)
            
            row = self.pg_cursor.fetchone()
            
            if row:
                info['row_count'] = row[0] or 0
                info['last_update'] = row[1]
                
                if info['row_count'] > 0:
                    info['status'] = 'loaded'
                else:
                    info['status'] = 'empty'
                    
        except Exception as e:
            info['status'] = 'error'
            info['error'] = str(e)
            logger.warning(f"Не удалось получить информацию о таблице {table_name}: {e}")
        
        return info


    def get_last_load_timestamp(self) -> Optional[datetime]:
        """
        Быстрый метод — возвращает ТОЛЬКО максимальную дату последней загрузки.
        
        Returns:
            datetime последней загрузки или None, если данных нет
        """
        try:
            self.pg_cursor.execute(f"""
                SELECT MAX(max_ts) FROM (
                    SELECT MAX(update_ts) as max_ts 
                    FROM {self.pg_schema}.organizations
                    UNION ALL
                    SELECT MAX(update_ts) 
                    FROM {self.pg_schema}.warehouses
                    UNION ALL
                    SELECT MAX(update_ts) 
                    FROM {self.pg_schema}.product_categories
                    UNION ALL
                    SELECT MAX(update_ts) 
                    FROM {self.pg_schema}.nomenclature
                    UNION ALL
                    SELECT MAX(update_ts) 
                    FROM {self.pg_schema}.price_types
                    UNION ALL
                    SELECT MAX(update_ts) 
                    FROM {self.pg_schema}.prices
                    UNION ALL
                    SELECT MAX(update_ts) 
                    FROM {self.pg_schema}.counterparties
                    UNION ALL
                    SELECT MAX(update_ts) 
                    FROM {self.pg_schema}.customer_orders
                    UNION ALL
                    SELECT MAX(update_ts) 
                    FROM {self.pg_schema}.sales
                    UNION ALL
                    SELECT MAX(update_ts) 
                    FROM {self.pg_schema}.purchases
                    UNION ALL
                    SELECT MAX(update_ts) 
                    FROM {self.pg_schema}.transfers
                    UNION ALL
                    SELECT MAX(update_ts) 
                    FROM {self.pg_schema}.inventory_balances
                    UNION ALL
                    SELECT MAX(update_ts) 
                    FROM {self.pg_schema}.sales_turnover
                ) subq
            """)
            
            result = self.pg_cursor.fetchone()
            return result[0] if result and result[0] else None
            
        except Exception as e:
            logger.warning(f"Не удалось получить timestamp последней загрузки: {e}")
            return None


    def print_load_status(self) -> None:
        """
        Выводит красивый отчёт о состоянии загрузки всех таблиц.
        """
        info = self.get_last_load_info()
        
        print("\n" + "=" * 70)
        print("📊 СТАТУС ЗАГРУЗКИ ДАННЫХ")
        print("=" * 70)
        
        if info['last_load_ts']:
            print(f"Последняя загрузка: {info['last_load_ts'].strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("Последняя загрузка: НЕТ ДАННЫХ")
        
        print(f"\nВсего таблиц: {info['summary']['total_tables']}")
        print(f"Загружено: {info['summary']['loaded_tables']}")
        print(f"Пустых: {info['summary']['empty_tables']}")
        
        print("\n" + "-" * 70)
        print(f"{'Таблица':<25} {'Строк':<10} {'Последнее обновление':<25} {'Статус':<10}")
        print("-" * 70)
        
        for table_name, table_info in info['tables'].items():
            status_icon = {
                'loaded': '✅',
                'empty': '⚠️',
                'error': '❌'
            }.get(table_info['status'], '❓')
            
            last_update = table_info['last_update']
            last_update_str = last_update.strftime('%Y-%m-%d %H:%M:%S') if last_update else 'N/A'
            
            print(f"{table_name:<25} {table_info['row_count']:<10} {last_update_str:<25} {status_icon} {table_info['status']}")
        
        print("=" * 70 + "\n")

