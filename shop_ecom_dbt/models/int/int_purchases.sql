with purchases as (

    select 
        id as purchase_id,
        number as purchase_number ,
        date as purchase_date ,
        organization_id,
        counterparty_id ,
        warehouse_id ,
        element::json->>'price' as price,
        element::json->>'amount' as amount,
        element::json->>'quantity' as quantity,
        element::json->>'nomenclature_id' as nomenclature_id
    from {{
        source(
            'staging_shop_ecom',
            'purchases'
        )
    }}
    cross join lateral json_array_elements(items::json) as element

)

select *
from purchases