{{
    config(
        materialized='incremental',
        incremental_strategy='append',
        unique_key='order_id'
    )
}}

with customer_orders as (
    select 
        id as order_id,
        number as order_number ,
        date as order_date ,
        organization_id,
        counterparty_id ,
        warehouse_id ,
        status ,
        element::json->>'price' as price,
        element::json->>'amount' as amount,
        element::json->>'quantity' as quantity,
        element::json->>'nomenclature_id' as nomenclature_id
    from {{
        source(
            'staging_shop_ecom',
            'customer_orders'
        )
    }}
    cross join lateral json_array_elements(items::json) as element
)

select *
from customer_orders
{% if is_incremental() %}
    where order_date > (
        select
            coalesce(
                max(order_date),
                '1900-01-01'
            )
        from {{ this }}
    )
{% endif %}