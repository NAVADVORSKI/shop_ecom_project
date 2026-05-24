{{
    config(
        materialized='incremental',
        incremental_strategy='append',
        unique_key='sale_number'
    )
}}

select 
	sale_number  ,
	sale_date ,
	organization_name ,
	counterparty_name ,
	counterparty_type,
	warehouse_name ,
	cost_price,
	sale_amount ,
	sale_quantity ,
	base_unit,
	nomenclature_name,
	parent_category_name ,
	sub_category_name
from {{ ref('int_sales') }} as int_sales
left join {{ ref('dim_counterparties') }} as dim_counterparties on dim_counterparties.counterparty_id = int_sales.counterparty_id 
left join {{ ref('dim_nomenclature') }} as dim_nomenclature on int_sales.nomenclature_id = dim_nomenclature.nomenclature_id 
left join {{ ref('dim_organizations') }} as dim_organizations on dim_organizations.organization_id = int_sales.organization_id 
left join {{ ref('dim_warehouses') }} as dim_warehouses on int_sales.warehouse_id = dim_warehouses.warehouse_id 