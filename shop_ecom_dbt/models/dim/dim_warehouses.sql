with warehouses as (

    select
        id as warehouse_id,
        name as warehouse_name
    from {{ source('staging_shop_ecom', 'warehouses') }}

)

select *
from warehouses