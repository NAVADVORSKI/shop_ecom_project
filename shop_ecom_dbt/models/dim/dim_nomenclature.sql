with nomenclature as (
    select
        id as nomenclature_id,
        article,
        name as nomenclature_name,
        category_id,
        base_unit,
        vat_rate
    from {{
        source(
            'staging_shop_ecom',
            'nomenclature'
        )
    }}
),
sub_categories as (
    select
        id as sub_category_id,
        name as sub_category_name,
        parent_id
    from {{
        source(
            'staging_shop_ecom',
            'product_categories'
        )
    }}
),
parent_categories as (
    select
        id as parent_category_id,
        name as parent_category_name
    from {{
        source(
            'staging_shop_ecom',
            'product_categories'
        )
    }}
    where parent_id is NULL
)
select
    nomenclature_id,
    article ,
    nomenclature_name ,
    CASE 
    	WHEN parent_category_name IS NULL THEN sub_category_name
    	ELSE parent_category_name 
    END AS parent_category_name,
    sub_category_name,
    base_unit ,
    vat_rate AS nomenclature_vat_rate
from nomenclature
left join sub_categories on sub_categories.sub_category_id = nomenclature.category_id
left join parent_categories on parent_categories.parent_category_id = sub_categories.parent_id