with sales as (

    select 
        id as sale_id,
        number as sale_number,
        date as sale_date,
        organization_id ,
        counterparty_id ,
        warehouse_id ,
        order_id ,
        element::jsonb->>'price' as sale_price,
        element::jsonb->>'quantity' as sale_quantity,
        element::jsonb->>'amount' as sale_amount,
        element::jsonb->>'cost_price' as cost_price,
        element::jsonb->>'nomenclature_id' as nomenclature_id
    from {{
        source(
            'staging_shop_ecom',
            'sales'
        )
    }}
    cross join lateral jsonb_array_elements(items) as element

)

select *
from sales