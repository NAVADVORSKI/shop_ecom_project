{{
    config(
        materialized='incremental',
        incremental_strategy='merge',
        unique_key='organization_id'
    )
}}

with organizations as (

    select
        id as organization_id,
        name as organization_name,
        inn organization_inn
    from {{ source('staging_shop_ecom', 'organizations') }}

)

select *
from organizations