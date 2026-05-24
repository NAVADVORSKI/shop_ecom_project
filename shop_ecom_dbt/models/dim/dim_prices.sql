with prices as (
    select
        id price_id,
        nomenclature_id as price_nomenclature_id,
        price_type_id,
        price,
        valid_from as price_valid_from
    from {{ source('staging_shop_ecom', 'prices') }}
),
price_types as (
    select
        id,
        name as price_type_name,
        currency
    from {{
        source(
            'staging_shop_ecom',
            'price_types'
        )
    }}
),
nomenclatures as (
    select
        nomenclature_id,
        nomenclature_name,
        parent_category_name,
        sub_category_name
    from {{
        ref(
            'dim_nomenclature'
        )
    }}
)

select 
    nomenclature_name,
    parent_category_name,
    sub_category_name,
    price_type_name,
    currency,
    price,
    price_valid_from
from prices
left join price_types on prices.price_type_id = price_types.id
left join nomenclatures on nomenclatures.nomenclature_id = prices.price_nomenclature_id