{{
    config(
        materialized='incremental',
        unique_key='purchase_number',
        incremental_strategy='append'
    )
}}

select 
	purchase_number  ,
	purchase_date ,
	organization_name ,
	counterparty_name ,
	counterparty_type,
	warehouse_name ,
	price,
	amount ,
	quantity ,
	base_unit,
	nomenclature_name,
	parent_category_name ,
	sub_category_name
from {{ ref('int_purchases') }} as int_purchases
left join {{ ref('dim_counterparties') }} as dim_counterparties on dim_counterparties.counterparty_id = int_purchases.counterparty_id 
left join {{ ref('dim_nomenclature') }} as dim_nomenclature on int_purchases.nomenclature_id = dim_nomenclature.nomenclature_id 
left join {{ ref('dim_organizations') }} as dim_organizations on dim_organizations.organization_id = int_purchases.organization_id 
left join {{ ref('dim_warehouses') }} as dim_warehouses on int_purchases.warehouse_id = dim_warehouses.warehouse_id 