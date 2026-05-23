-- =============================================================================
-- СКРИПТ ИНИЦИАЛИЗАЦИИ БД POSTGRESQL (С ИНКРЕМЕНТАЛЬНОЙ ЗАГРУЗКОЙ)
-- =============================================================================

-- Создаём схему stg для сырых данных из MongoDB
CREATE SCHEMA IF NOT EXISTS stg;

-- =============================================================================
-- 1. ОРГАНИЗАЦИИ
-- =============================================================================
CREATE TABLE IF NOT EXISTS stg.organizations (
    id              VARCHAR(24) PRIMARY KEY,           -- ObjectId из MongoDB
    name            VARCHAR(200) NOT NULL,
    inn             VARCHAR(12),
    is_our_org      BOOLEAN DEFAULT FALSE,
    update_ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 2. СКЛАДЫ
-- =============================================================================
CREATE TABLE IF NOT EXISTS stg.warehouses (
    id              VARCHAR(24) PRIMARY KEY,
    name            VARCHAR(150) NOT NULL,
    address         VARCHAR(300),
    update_ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 3. КАТЕГОРИИ ТОВАРОВ (иерархия)
-- =============================================================================
CREATE TABLE IF NOT EXISTS stg.product_categories (
    id              VARCHAR(24) PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    parent_id       VARCHAR(24) REFERENCES stg.product_categories(id),
    update_ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 4. НОМЕНКЛАТУРА (ТОВАРЫ)
-- =============================================================================
CREATE TABLE IF NOT EXISTS stg.nomenclature (
    id              VARCHAR(24) PRIMARY KEY,
    article         VARCHAR(20) NOT NULL,
    name            VARCHAR(250) NOT NULL,
    category_id     VARCHAR(24) NOT NULL REFERENCES stg.product_categories(id),
    base_unit       VARCHAR(10) DEFAULT 'шт',
    vat_rate        NUMERIC(5,2) DEFAULT 20.00,
    update_ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 5. ТИПЫ ЦЕН
-- =============================================================================
CREATE TABLE IF NOT EXISTS stg.price_types (
    id              VARCHAR(24) PRIMARY KEY,
    name            VARCHAR(50) NOT NULL,
    currency        VARCHAR(3) DEFAULT 'RUB',
    update_ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 6. ЦЕНЫ
-- =============================================================================
CREATE TABLE IF NOT EXISTS stg.prices (
    id              VARCHAR(24) PRIMARY KEY,
    nomenclature_id VARCHAR(24) NOT NULL REFERENCES stg.nomenclature(id),
    price_type_id   VARCHAR(24) NOT NULL REFERENCES stg.price_types(id),
    price           NUMERIC(12,2) NOT NULL,
    valid_from      DATE NOT NULL DEFAULT CURRENT_DATE,
    update_ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 7. КОНТРАГЕНТЫ
-- =============================================================================
CREATE TABLE IF NOT EXISTS stg.counterparties (
    id              VARCHAR(24) PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    type            VARCHAR(20) CHECK (type IN ('client', 'supplier', 'both')),
    phone           VARCHAR(20),
    email           VARCHAR(100),
    update_ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 8. ЗАКАЗЫ КЛИЕНТОВ
-- =============================================================================
CREATE TABLE IF NOT EXISTS stg.customer_orders (
    id              VARCHAR(24) PRIMARY KEY,
    number          VARCHAR(20) NOT NULL,
    date            DATE NOT NULL,
    organization_id VARCHAR(24) NOT NULL REFERENCES stg.organizations(id),
    counterparty_id VARCHAR(24) NOT NULL REFERENCES stg.counterparties(id),
    warehouse_id    VARCHAR(24) NOT NULL REFERENCES stg.warehouses(id),
    status          VARCHAR(20) DEFAULT 'completed',
    items           JSONB DEFAULT '[]'::jsonb,
    update_ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 9. ПРОДАЖИ
-- =============================================================================
CREATE TABLE IF NOT EXISTS stg.sales (
    id              VARCHAR(24) PRIMARY KEY,
    number          VARCHAR(20) NOT NULL,
    date            DATE NOT NULL,
    organization_id VARCHAR(24) NOT NULL REFERENCES stg.organizations(id),
    counterparty_id VARCHAR(24) NOT NULL REFERENCES stg.counterparties(id),
    warehouse_id    VARCHAR(24) NOT NULL REFERENCES stg.warehouses(id),
    order_id        VARCHAR(24) REFERENCES stg.customer_orders(id),
    items           JSONB DEFAULT '[]'::jsonb,
    update_ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 10. ЗАКУПКИ
-- =============================================================================
CREATE TABLE IF NOT EXISTS stg.purchases (
    id              VARCHAR(24) PRIMARY KEY,
    number          VARCHAR(20) NOT NULL,
    date            DATE NOT NULL,
    organization_id VARCHAR(24) NOT NULL REFERENCES stg.organizations(id),
    counterparty_id VARCHAR(24) NOT NULL REFERENCES stg.counterparties(id),
    warehouse_id    VARCHAR(24) NOT NULL REFERENCES stg.warehouses(id),
    items           JSONB DEFAULT '[]'::jsonb,
    update_ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 11. ТРАНСФЕРЫ (ПЕРЕМЕЩЕНИЯ МЕЖДУ СКЛАДАМИ)
-- =============================================================================
CREATE TABLE IF NOT EXISTS stg.transfers (
    id                  VARCHAR(24) PRIMARY KEY,
    number              VARCHAR(20) NOT NULL,
    date                DATE NOT NULL,
    from_warehouse_id   VARCHAR(24) NOT NULL REFERENCES stg.warehouses(id),
    to_warehouse_id     VARCHAR(24) NOT NULL REFERENCES stg.warehouses(id),
    items               JSONB DEFAULT '[]'::jsonb,
    update_ts           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 12. ОСТАТКИ ТОВАРОВ НА СКЛАДАХ
-- =============================================================================
CREATE TABLE IF NOT EXISTS stg.inventory_balances (
    id              VARCHAR(24) PRIMARY KEY,
    warehouse_id    VARCHAR(24) NOT NULL REFERENCES stg.warehouses(id),
    nomenclature_id VARCHAR(24) NOT NULL REFERENCES stg.nomenclature(id),
    quantity        NUMERIC(12,3) NOT NULL DEFAULT 0,
    total_cost      NUMERIC(12,2) NOT NULL DEFAULT 0,
    avg_cost        NUMERIC(12,2) DEFAULT 0,
    update_ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 13. ОБОРОТЫ ПРОДАЖ (ДЛЯ АНАЛИТИКИ)
-- =============================================================================
CREATE TABLE IF NOT EXISTS stg.sales_turnover (
    id              VARCHAR(24) PRIMARY KEY,
    date            DATE NOT NULL,
    nomenclature_id VARCHAR(24) NOT NULL REFERENCES stg.nomenclature(id),
    warehouse_id    VARCHAR(24) NOT NULL REFERENCES stg.warehouses(id),
    quantity        NUMERIC(12,3) NOT NULL,
    revenue         NUMERIC(12,2) NOT NULL,
    cost_total      NUMERIC(12,2) NOT NULL,
    update_ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- ИНДЕКСЫ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_inv_wh_prod
    ON stg.inventory_balances(warehouse_id, nomenclature_id);

CREATE INDEX IF NOT EXISTS idx_sales_date
    ON stg.sales(date);

CREATE INDEX IF NOT EXISTS idx_sales_order
    ON stg.sales(order_id);

CREATE INDEX IF NOT EXISTS idx_purchases_date
    ON stg.purchases(date);

CREATE INDEX IF NOT EXISTS idx_turnover_date
    ON stg.sales_turnover(date);

CREATE INDEX IF NOT EXISTS idx_orders_date
    ON stg.customer_orders(date);

CREATE INDEX IF NOT EXISTS idx_prices_prod_type
    ON stg.prices(nomenclature_id, price_type_id);

CREATE INDEX IF NOT EXISTS idx_nomenclature_article
    ON stg.nomenclature(article);

CREATE INDEX IF NOT EXISTS idx_counterparties_type
    ON stg.counterparties(type);

-- =============================================================================
-- ТРИГГЕРЫ ДЛЯ АВТОМАТИЧЕСКОГО ОБНОВЛЕНИЯ update_ts
-- =============================================================================
CREATE OR REPLACE FUNCTION stg.update_update_ts()
RETURNS TRIGGER AS $$
BEGIN
    NEW.update_ts = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Применяем триггер ко всем таблицам
DO $$
DECLARE
    tbl_name TEXT;
BEGIN
    FOR tbl_name IN
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'stg'
          AND table_type = 'BASE TABLE'
    LOOP
        EXECUTE format(
            'CREATE TRIGGER trg_update_ts_%I
             BEFORE UPDATE ON stg.%I
             FOR EACH ROW
             EXECUTE FUNCTION stg.update_update_ts()',
            tbl_name, tbl_name
        );
    END LOOP;
END;
$$;

-- =============================================================================
-- ГОТОВО
-- =============================================================================
SELECT 'Инициализация БД завершена!' AS status;