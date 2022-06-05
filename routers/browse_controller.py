from fastapi import APIRouter
from models import browse
from .res_models import ResponseBrowseShop, ResponseBrowseProduct, ResponseBrowseRecommendShop, ResponseBrowseRecommendProduct, ResponseBrowseSameShopProduct, ResponseSimilarProduct
from typing import List
from uuid import UUID

router = APIRouter(
    prefix="/browse",
    tags=["Browse"]
)

tag_meta = {
    'name': 'Browse',
    'description': '買、賣家的瀏覽和搜尋(店鋪、商品)',
}

@router.get(
    '/shop',
    response_model=List[ResponseBrowseShop],
)
async def browse_shop(user_id: UUID=None, page: int=0, mode: str='default'):
    '''
        訪客時，Request user_id可為空，Response會回傳假的user_id，以查詢後續頁面的資料\n
        **Sample Query**
        ```
        ?user_id=&page=0&mode=default
        ```
        ## 參數說明\n
        **mode:** \n 
        * new - 最新\n
        * top_sale - 最熱銷\n
        * overall - 綜合排行\n
        * default - \n
    '''
    shops = browse.getShopAnalitics(**locals())
    return shops

@router.get(
    '/product',
    response_model=List[ResponseBrowseProduct],
)
async def browse_product(user_id: UUID=None, page: int=0, mode: str='new'):
    '''
        訪客時，Request user_id可為空，Response會回傳假的user_id，以查詢後續頁面的資料\n
        **Sample Query**
        ```
        ?user_id=&page=0&mode=new
        ```
        ## 參數說明\n
        **mode:** \n 
        * new - 最新\n
        * top_sale - 最熱銷\n
        * lower_price - 最低價\n
        * higher_price - 最高價\n
        * overall - 綜合排行\n
    '''
    products = browse.getProductAnalitics(**locals())
    return products

@router.get(
    '/shop-keyword',
    name='關鍵字搜尋(店鋪)',
    response_model=List[ResponseBrowseShop],
)
async def search_shop(keyword: str, user_id: UUID=None, page: int=0, mode: str='default'):
    '''
        訪客時，Request user_id可為空，Response會回傳假的user_id，以查詢後續頁面的資料\n
        **Sample Query**
        ```
        ?user_id=&page=0&mode=default
        ```
        ## 參數說明\n
        **mode:** \n 
        * new - 最新\n
        * top_sale - 最熱銷\n
        * overall - 綜合排行\n
        * default - \n
    '''
    shops = browse.getShopAnalitics(**locals())
    return shops

@router.get(
    '/product-keyword',
    name='關鍵字搜尋(商品)',
    response_model=List[ResponseBrowseProduct],
)
async def search_product(keyword: str, user_id: UUID=None, page: int=0, mode: str='new'):
    '''
        訪客時，Request user_id可為空，Response會回傳假的user_id，以查詢後續頁面的資料\n
        **Sample Query**
        ```
        ?user_id=&page=0&mode=new
        ```
        ## 參數說明\n
        **mode:** \n 
        * new - 最新\n
        * top_sale - 最熱銷\n
        * lower_price - 最低價\n
        * higher_price - 最高價\n
        * overall - 綜合排行\n
    '''
    products = browse.getProductAnalitics(**locals())
    return products

@router.get(
    '/shop-category',
    name='依分類搜尋(店鋪)',
    response_model=List[ResponseBrowseShop],
)
async def search_shop_by_category(category_id: int, user_id: UUID=None, page: int=0, mode: str='default'):
    '''
        訪客時，Request user_id可為空，Response會回傳假的user_id，以查詢後續頁面的資料\n
        **Sample Query**
        ```
        ?user_id=&page=0&mode=default
        ```
        ## 參數說明\n
        **mode:** \n 
        * new - 最新\n
        * top_sale - 最熱銷\n
        * overall - 綜合排行\n
        * default - \n
    '''
    shops = browse.getShopAnalitics(**locals())
    return shops

@router.get(
    '/product-category',
     name='依分類搜尋(商品)',
    response_model=List[ResponseBrowseProduct],
)
async def search_product_by_category(category_id: int, user_id: UUID=None, page: int=0, mode: str='new'):
    '''
        訪客時，Request user_id可為空，Response會回傳假的user_id，以查詢後續頁面的資料\n
        **Sample Query**
        ```
        ?user_id=&page=0&mode=new
        ```
        ## 參數說明\n
        **mode:** \n 
        * new - 最新\n
        * top_sale - 最熱銷\n
        * lower_price - 最低價\n
        * higher_price - 最高價\n
        * overall - 綜合排行\n
    '''
    products = browse.getProductAnalitics(**locals())
    return products

@router.get(
    '/shop-recommend',
    name='推薦(店鋪)',
    response_model=List[ResponseBrowseRecommendShop],
)
async def browse_recommend_shop(user_id: UUID=None):
    shops = browse.getRecommendShop(user_id)
    return shops

@router.get(
    '/product-recommend',
    name='推薦(商品)',
    response_model=List[ResponseBrowseRecommendProduct]
)
async def browse_reccommend_product(user_id: UUID=None):
    products = browse.getRecommendProduct(user_id)
    return products

@router.get(
    '/same-shop-product',
    name='該店的商品前三名',
    response_model=ResponseBrowseSameShopProduct,
)
async def get_top_3_products_in_shop(product_id: UUID, user_id: UUID=None):
    products = browse.getSameShopProduct(**locals())
    return products
  
@router.get(
    '/similar-product/',
    name='相似的商品',
    response_model=List[ResponseSimilarProduct],
)
async def get_similar_products(product_id:UUID, user_id: UUID=None):
    products = browse.getSimilarProduct(**locals())
    return products

@router.get('/shop/product', name='該店的其他商品')
async def browse_all_products_in_shop(shop_id: UUID, user_id: UUID=None, mode: str = 'new'):
    products = browse.getShopProducts(**locals())
    return products