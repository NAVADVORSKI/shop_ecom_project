{{
    config(
        materialized='incremental',
        incremental_strategy='append',
        unique_key='order_number'
    )
}}

select 
	order_number ,
	order_date,
	organization_name ,
	counterparty_name ,
	counterparty_type,
	warehouse_name ,
	status,
	price,
	amount ,
	quantity ,
	base_unit,
	email_address ,
	nomenclature_name,
	parent_category_name ,
	sub_category_name
from {{ ref('int_customer_orders') }} as int_customer_orders
left join {{ ref('dim_counterparties') }} as dim_counterparties on dim_counterparties.counterparty_id = int_customer_orders.counterparty_id 
left join {{ ref('dim_nomenclature') }} as dim_nomenclature on int_customer_orders.nomenclature_id = dim_nomenclature.nomenclature_id 
left join {{ ref('dim_organizations') }} as dim_organizations on dim_organizations.organization_id = int_customer_orders.organization_id 
left join {{ ref('dim_warehouses') }} as dim_warehouses on int_customer_orders.warehouse_id = dim_warehouses.warehouse_id 