{{
    config(
        materialized='incremental',
        incremental_strategy='append',
        unique_key='sale_number',
		post_hook=[
		'alter table {{ this }} alter column sale_date type timestamp using sale_date::timestamp;',
		'alter table {{ this }} alter column marginality type float using marginality::float;',
		'alter table {{ this }} alter column margin type float using margin::float;',
		'alter table {{ this }} alter column sale_price type float using sale_price::float;',
		'alter table {{ this }} alter column cost_price type float using cost_price::float;',
		'alter table {{ this }} alter column sale_amount type float using sale_amount::float;',
		'alter table {{ this }} alter column sale_quantity type integer using sale_quantity::integer;'
		]
    )
}}

select 
	sale_number  ,
	sale_date ,
	organization_name ,
	counterparty_name ,
	counterparty_type,
	warehouse_name ,
	cost_price::float,
	sale_price::float,
	sale_amount::float,
	round(((sale_price::float - cost_price::float) / sale_price::float)::numeric, 2)::float as marginality,
	round((sale_price::float - cost_price::float)::numeric,2)::float as margin,
	sale_quantity::int,
	base_unit,
	nomenclature_name,
	parent_category_name ,
	sub_category_name
from {{ ref('int_sales') }} as int_sales
left join {{ ref('dim_counterparties') }} as dim_counterparties on dim_counterparties.counterparty_id = int_sales.counterparty_id 
left join {{ ref('dim_nomenclature') }} as dim_nomenclature on int_sales.nomenclature_id = dim_nomenclature.nomenclature_id 
left join {{ ref('dim_organizations') }} as dim_organizations on dim_organizations.organization_id = int_sales.organization_id 
left join {{ ref('dim_warehouses') }} as dim_warehouses on int_sales.warehouse_id = dim_warehouses.warehouse_id 
{% if is_incremental() %}
	where sale_date > (
		select
			coalesce(
				max(
					sale_date
				),
				'1900-01-01'
			)
			from {{ this }}
	)
{% endif %}