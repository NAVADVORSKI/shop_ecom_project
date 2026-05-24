with counterparties as (

    select
        id as counterparty_id,
        name as counterparty_name,
        type as counterparty_type,
        right(email, length(email) - position('@' in email)) as email_address
    from {{ source('staging_shop_ecom', 'counterparties') }}

)

select *
from counterparties