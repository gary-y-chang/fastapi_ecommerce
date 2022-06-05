from datetime import timedelta, datetime
from itertools import product
from random import random
from re import S
import pony.orm as pny
from uuid import uuid4, UUID

from pony.orm.core import desc
from models.entities import ProductAnalytics, ProductBrowsed, ShopAnalytics, Shop, Product, ProductCategory, ShopBrowsed, ShopFollower, SponsorLevel, Stock, User, SearchHistory, Sponsor
from math import floor
import json

from pony.orm.ormtypes import raw_sql

PAGE_SIZE = 12 # paging
ENTROPY = 3 # 混亂程度

@pny.db_session
def getShopAnalitics(user_id: UUID, page: int, mode: str='defualt', keyword: str=None, category_id: int=None, **kwargs):
    if not user_id: user_id = uuid4() # gen guest_id
    if page == 0: # refresh
        pny.delete(a for a in ShopAnalytics if a.user_id == user_id and a.mode == mode)

        now = datetime.now()
        pyCommand = "pny.left_join( (s) for s in Shop for p in s.products if not s.is_deleted and not p.is_deleted and p.for_sale and pny.count(p.id)>0" # `Sponsor` 會造成 `Shop` 重複
        pyCommand2 = "pny.select( (s,sp) for s in Shop for sp in s.sponsor if not s.is_deleted and not s.sponsor.is_empty() and sp.expired_at>now"
        if keyword != None:
            SearchHistory(search_category='shop', keyword=keyword)
            pyCommand += " and keyword in s.title"
            pyCommand2 += " and keyword in s.title"
        if category_id != None:
            pyCommand += " and category_id in s.categorys.id"
            pyCommand2 += " and category_id in s.categorys.id"
        # 所有店鋪
        all_shop = eval(pyCommand+')')
        # 贊助店鋪
        sp = eval(pyCommand2+')')

        # 排序
        if mode == 'overall':
            # shops.sort(key=lambda x: (x['rating'],x['sponsor_sort']), reverse=True)
            all_shop = list(all_shop[:])
            sp = sp.order_by(lambda s,sp: pny.desc(sp.probability))
        elif mode == 'new':
            all_shop = list(all_shop.order_by(lambda s: (pny.desc(s.created_at), pny.desc(s.title)))[:])
            sp = sp.order_by(lambda s,sp: (pny.desc(sp.probability), pny.desc(s.created_at), pny.desc(s.title)))
        elif mode == 'top_sale':
            # shops.sort(key=lambda x: (x['sum_of_purchasing_qty'],x['sponsor_sort']), reverse=True)
            all_shop = list(all_shop[:])
            sp = sp.order_by(lambda s,sp: pny.desc(sp.probability))
        elif mode == 'default':
            all_shop = list(all_shop.order_by(lambda s: pny.desc(s.title))[:])
            sp = sp.order_by(lambda s,sp: (pny.desc(sp.probability), pny.desc(s.title)))

        # 贊助分類
        sp1 = sp.filter(lambda s,sp: sp.sponsor_level.description=='尊榮' or sp.sponsor_level.description=='至尊')
        if sp1.exists():
            s1,sp1 = zip(*sp1[:])
            s1,sp1 = list(s1), list(sp1)
        else:
            sp1 = []
        sp2 = sp.filter(lambda s,sp: sp.sponsor_level.description=='榮耀')
        if sp2.exists():
            s2,sp2 = zip(*sp2[:])
            s2,sp2 = list(s2),list(sp2)
        else:
            sp2 = []
        sp3 = sp.filter(lambda s,sp: sp.sponsor_level.description=='卓越')
        if sp3.exists():
            s3,sp3 = zip(*sp3[:])
            s3,sp3 = list(s3),list(sp3)
        else:
            sp3 = []

        # 存入暫存表
        total_cnt = len(all_shop)
        for i in range(total_cnt):
            # print(all_shop[i].id, user_id, mode, i+1)
            r = random()
            prob = 0
            if len(sp1): # 要避免len(QueryResult)，否則會再向DB查詢一次
                prob += sp1[0].probability # sponsor.probability
                if prob>r:
                    ShopAnalytics(shop_id=s1[0].id, user_id=user_id, mode=mode, seq=i+1)
                    all_shop.remove(s1[0]) # pop the item
                    s1.remove(s1[0])
                    sp1.remove(sp1[0])
                    continue
            if len(sp2):
                prob += sp2[0].probability
                if prob>r:
                    ShopAnalytics(shop_id=s2[0].id, user_id=user_id, mode=mode, seq=i+1)
                    all_shop.remove(s2[0])
                    s2.remove(s2[0])
                    sp2.remove(sp2[0])
                    continue
            if len(sp3):
                prob += sp3[0].probability
                if prob>r:
                    ShopAnalytics(shop_id=s3[0].id, user_id=user_id, mode=mode, seq=i+1)
                    all_shop.remove(s3[0])
                    s3.remove(s3[0])
                    sp3.remove(sp3[0])
                    continue
            ShopAnalytics(shop_id=all_shop[0].id, user_id=user_id, mode=mode, seq=i+1)
            try:
                i = s1.index(all_shop[0])
                del sp1[i], s1[i]
            except (ValueError,UnboundLocalError): # item not found
                try:
                    i = s2.index(all_shop[0])
                    del sp2[i], s2[i]
                except (ValueError,UnboundLocalError):
                    try:
                        i = s3.index(all_shop[0])
                        del sp3[i], s3[i]
                    except (ValueError,UnboundLocalError):
                        pass
            all_shop.remove(all_shop[0])
    user = User.get(id=user_id)
    offset = page*PAGE_SIZE
    from .entities import db
    q = db.select('''
        `s`.`id`, 
        `s`.`title`, 
        `s`.`icon`, 
        `s`.`created_at`, 
        `sa`.`user_id`,
        (
            SELECT COUNT(DISTINCT `shopfollower`.`shop_id`, `shopfollower`.`user_id`)
            FROM `ShopFollower` `shopfollower`
            WHERE `s`.`id` = `shopfollower`.`shop_id`
        ), 
        (
            SELECT COUNT(DISTINCT `f`.`shop_id`, `f`.`user_id`)
            FROM `ShopFollower` `f`
            WHERE `s`.`id` = `f`.`shop_id`
            AND `f`.`user_id` = UNHEX(REPLACE($user_id, '-', ''))
        ), 
        `sp`.`sponsor_level`,
        `sp`.`background_is_show`,
        `sp`.`badge_is_show`,
        `sp`.`frame_is_show`
        FROM `Shop` `s`
        LEFT JOIN `Sponsor` `sp`
            ON `s`.`id` = `sp`.`shop_id`
                AND `sp`.expired_at > $now
        LEFT JOIN `ShopAnalytics` `sa`
            ON `s`.`id` = `sa`.`shop_id`
        WHERE `s`.`id` = `sa`.`shop_id`
        AND `sa`.`user_id` = UNHEX(REPLACE($user_id, '-', ''))
        AND `sa`.`mode` = $mode
        ORDER BY `sa`.`seq` + RAND()*$ENTROPY*2 - $ENTROPY
        LIMIT $offset, $PAGE_SIZE
    ''')
    # q = pny.left_join(
    #     (
    #         s, 
    #         sa, 
    #         pny.count(s.followers), 
    #         pny.count(f for f in s.followers if f.user_id == user),
    #         sp
    #     ) 
    #     for s in Shop for sp in s.sponsor for sa in s.analytics if s == sa.shop_id and sa.user_id == user_id and sa.mode == mode 
    # ).order_by(pny.raw_sql('''
    #     sa.seq + RAND()*{} - {}
    # '''.format(ENTROPY*2, ENTROPY)))
    # if page>q.count()/PAGE_SIZE:
    #     page = floor(q.count()/PAGE_SIZE)
    shops = []
    # for shop in q.page(page+1,PAGE_SIZE)[:]: # shop, shop_analytics, follower_count, is_follow
    for id,title,icon,created_at,user_id,follower_count,is_follow,sponsor_level,background_is_show,badge_is_show,frame_is_show in q:
        # tShop = shop[0].to_dict(only=['id', 'title', 'icon', 'created_at'], with_collections=True)
        tShop = {}
        tShop['id'] = id
        tShop['title'] = title
        tShop['icon'] = icon
        tShop['created_at'] = created_at
        tShop['user_id'] = user_id
        tShop['follower_count'] = follower_count
        tShop['is_follow'] = is_follow
        if sponsor_level:
            tShop['sponsor_level'] = sponsor_level
            tShop['background_is_show'] = background_is_show
            tShop['badge_is_show'] = badge_is_show
            tShop['frame_is_show'] = frame_is_show
        else:
            tShop['sponsor_level'] = None
            tShop['background_is_show'] = 'N'
            tShop['badge_is_show'] = 'N'
            tShop['frame_is_show'] = 'N'
        tShop['shop_id'] = id
        # ※ 評價 完成後，再將選擇3張評價最高的商品圖片邏輯加入
        pics = pny.select(pic.src for s in Shop for p in s.products for pic in p.pictures if s.id==UUID(bytes=id))[:3]
        tShop['src'] = [ pics[i%len(pics)] for i in range(3) ] # 最多最少3張圖片
        shops.append(tShop)
        ShopBrowsed(user_id=user_id, shop_id=tShop['id'])
    return shops

@pny.db_session
def getProductAnalitics(user_id: UUID, page: int, mode: str='new', keyword: str=None, category_id: int=None, **kwargs):
    now = datetime.now()
    if not user_id: user_id = uuid4() # gen guest_id
    if page == 0: # refresh
        pny.delete(p for p in ProductAnalytics if p.user_id == user_id and p.mode == mode)

        all_product,sp = productBrowseLogic(mode=mode, category_id=category_id, keyword=keyword)
        all_product = [ p for p,min_price,max_price in all_product[:] ]

        # 贊助分類
        sp1 = sp.filter(lambda p, min_price, max_price, sp: sp.sponsor_level.description=='尊榮' or sp.sponsor_level.description=='至尊')
        if sp1.exists():
            sp1 = sp1[:]
            p1,sp1 = [ p for p,x1,x2,sp in sp1 ], [ sp for p,x1,x2,sp in sp1 ]
        else:
            sp1 = []
        sp2 = sp.filter(lambda p, min_price, max_price, sp: sp.sponsor_level.description=='榮耀')
        if sp2.exists():
            sp2 = sp2[:]
            p2,sp2 = [ p for p,x1,x2,sp in sp2 ], [ sp for p,x1,x2,sp in sp2 ]
        else:
            sp2 = []
        sp3 = sp.filter(lambda p, min_price, max_price, sp: sp.sponsor_level.description=='卓越')
        if sp3.exists():
            sp3 = sp3[:]
            p3,sp3 = [ p for p,x1,x2,sp in sp3 ], [ sp for p,x1,x2,sp in sp3 ]
        else:
            sp3 = []

        # 存入暫存表
        total_cnt = len(all_product)
        for i in range(total_cnt):
            # print(all_shop[i].id, user_id, mode, i+1)
            r = random()
            prob = 0
            if len(sp1): # 要避免len(QueryResult)，否則會再向DB查詢一次
                prob += sp1[0].probability # sponsor.probability
                if prob>r:
                    ProductAnalytics(product_id=p1[0].id, user_id=user_id, mode=mode, seq=i+1)
                    all_product.remove(p1[0]) # pop the item
                    p1.remove(p1[0])
                    sp1.remove(sp1[0])
                    continue
            if len(sp2):
                prob += sp2[0].probability
                if prob>r:
                    ProductAnalytics(product_id=p2[0].id, user_id=user_id, mode=mode, seq=i+1)
                    all_product.remove(p2[0])
                    p2.remove(p2[0])
                    sp2.remove(sp2[0])
                    continue
            if len(sp3):
                prob += sp3[0].probability
                if prob>r:
                    ProductAnalytics(product_id=p3[0].id, user_id=user_id, mode=mode, seq=i+1)
                    all_product.remove(p3[0])
                    p3.remove(p3[0])
                    sp3.remove(sp3[0])
                    continue
            ProductAnalytics(product_id=all_product[0].id, user_id=user_id, mode=mode, seq=i+1)
            try:
                i = p1.index(all_product[0])
                del sp1[i], p1[i]
            except (ValueError,UnboundLocalError): # item not found
                try:
                    i = p2.index(all_product[0])
                    del sp2[i], p2[i]
                except (ValueError,UnboundLocalError):
                    try:
                        i = p3.index(all_product[0])
                        del sp3[i], p3[i]
                    except (ValueError,UnboundLocalError):
                        pass
            all_product.remove(all_product[0])
    user = User.get(id=user_id)
    # q = pny.left_join(
    #     (
    #         p,
    #         pa.user_id,
    #         pic.src,
    #         pny.min(p.stocks.price), 
    #         pny.max(p.stocks.price), 
    #         pny.count(p.like), 
    #         pny.count(l for l in p.like if l.user_id == user),
    #         sp,
    #         s
    #     )
    #     for p in Product for pa in p.analytics for pic in p.pictures for s in p.shop_id for sp in s.sponsor if p == pa.product_id and pa.user_id == user_id and pa.mode == mode and pic.is_cover and sp.expired_at>now
    # ).order_by(pny.raw_sql('''
    #     pa.seq + RAND()*{} - {}
    # '''.format(ENTROPY*2, ENTROPY)))
    from .entities import db
    row_count = pny.select(pa for pa in ProductAnalytics if pa.user_id==user_id and pa.mode==mode).count()
    offset = page*PAGE_SIZE
    q = db.select('''
            `p`.`id`, 
            `p`.`name`,
            `p`.`price`,
            `p`.`specs`,
            `pa`.`user_id`, 
            `pic`.`src`, 
            (
                SELECT MIN(`stock`.`price`)
                FROM `Stock` `stock`
                WHERE `p`.`id` = `stock`.`product_id`
            ), 
            (
                SELECT MAX(`stock`.`price`)
                FROM `Stock` `stock`
                WHERE `p`.`id` = `stock`.`product_id`
            ), 
            (
                SELECT COUNT(DISTINCT `productlike`.`user_id`, `productlike`.`product_id`)
                FROM `ProductLike` `productlike`
                WHERE `p`.`id` = `productlike`.`product_id`
            ), 
            (
                SELECT COUNT(DISTINCT `l`.`user_id`, `l`.`product_id`)
                FROM `ProductLike` `l`
                WHERE `p`.`id` = `l`.`product_id`
                AND `l`.`user_id` IS NULL
            ), 
            `sp`.`sponsor_level`, 
            `sp`.`background_is_show`,
            `sp`.`badge_is_show`,
            `sp`.`frame_is_show`,
            `s`.`title`
        FROM `ProductAnalytics` `pa`
        LEFT JOIN `ProductPic` `pic`
            ON `pa`.`product_id` = `pic`.`product_id`
        LEFT JOIN `Product` `p`
            ON `pa`.`product_id` = `p`.`id`
        LEFT JOIN `Sponsor` `sp`
            ON `p`.`shop_id` = `sp`.`shop_id`
            AND `sp`.expired_at > $now
        LEFT JOIN `Shop` `s`
            ON `p`.`shop_id` = `s`.`id`
        WHERE `p`.`id` = `pa`.`product_id`
        AND `pa`.`user_id` = UNHEX(REPLACE($user_id, '-', ''))
        AND `pa`.`mode` = $mode
        AND `pic`.`is_cover`
        ORDER BY `pa`.`seq` + RAND()*$ENTROPY*2 - $ENTROPY
        LIMIT $offset, $PAGE_SIZE
    ''')
    # if page>q.count()/PAGE_SIZE:
    #     page = floor(q.count()/PAGE_SIZE)
    products = []
    for id,name,price,specs,user_id,src,min_price,max_price,like_count,is_like,sponsor_level,background_is_show,badge_is_show,frame_is_show,title in q:
        tProduct = {}
        tProduct['id'] = id
        tProduct['name'] = name
        tProduct['price'] = price
        tProduct['has_spec'] = True if specs else False
        tProduct['user_id'] = user_id
        tProduct['cover'] = src
        tProduct['min_price'] = min_price if min_price else 0
        tProduct['max_price'] = max_price if max_price else 0
        tProduct['like_count'] = like_count
        tProduct['is_like'] = is_like
        if sponsor_level:
            tProduct['sponsor_level'] = sponsor_level
            tProduct['background_is_show'] = background_is_show
            tProduct['badge_is_show'] = badge_is_show
            tProduct['frame_is_show'] = frame_is_show
        else:
            tProduct['sponsor_level'] = None
            tProduct['background_is_show'] = 'N'
            tProduct['badge_is_show'] = 'N'
            tProduct['frame_is_show'] = 'N'
        tProduct['title']=title
        products.append(tProduct)
        ProductBrowsed(user_id=user_id, product_id=tProduct['id'])
    return products

@pny.db_session
def getRecommendShop(user_id: UUID=None):
    is_follow = ", pny.count(f for f in s.followers if f.user_id == User[user_id])" if user_id != None else ", 0"
    pyCommand = "pny.select((s{}) for s in Shop if not s.is_deleted).order_by(pny.raw_sql('RAND()*{} - {}'))[:8]".format(is_follow,ENTROPY*2,ENTROPY)
    shops = []
    for shop in eval(pyCommand):
        tShop = shop[0].to_dict(only=['id','icon','title'])
        tShop['is_follow'] = shop[1]
        # find top 3 product's cover
        pics = pny.select((pic.src) for p in Product for pic in p.pictures if p.shop_id == shop[0] and p.for_sale and not p.is_deleted and pic.is_cover)[:3]
        tShop['product_pics'] = [pic for pic in pics]
        shops.append(tShop)
        ShopBrowsed(user_id=user_id, shop_id=tShop['id'])
    return shops

@pny.db_session
def getRecommendProduct(user_id: UUID=None):
    try:
        user_id = User[user_id] if user_id else None
    except pny.ObjectNotFound:
        user_id = None
    is_like = "pny.count(l for l in p.like if l.user_id == {})".format(user_id) if user_id != None else "0"
    pyCommand = '''pny.select(
        (
            'id',           p.id,
            'category_id',  p.category_id.id,
            'name',         p.name,
            'description',  p.description,
            'is_like',      {},
            'has_spec',     p.specs,
            'src',          pic.src,
            'price',        p.price,
            'min_price',    pny.min(p.stocks.price),
            'max_price',    pny.max(p.stocks.price),
            'shop_title',   p.shop_id.title,
        )
        for p in Product for pic in p.pictures if not p.is_deleted and p.for_sale and pic.is_cover and not p.shop_id.is_deleted) \
        .order_by(pny.raw_sql('RAND()*{} - {}'))[:12]'''.format(is_like,ENTROPY*2,ENTROPY)
    p = eval(pyCommand)
    products = [ dict( (row[i],row[i+1] if not isinstance(row[i+1],dict) else True if row[i+1] else False) for i in range(0,len(row),2)) for row in p ]
    for p in products:
        ProductBrowsed(user_id=user_id.id if user_id else user_id, product_id=p['id'])
    return products

@pny.db_session
def getSameShopProduct(product_id: UUID, user_id: UUID=None):
    current_product = Product[product_id]
    q1 = pny.select(
        (
            'id',               p.id,
            'name',             p.name,
            'cover',            pic.src,
            'min_price',        pny.min(p.stocks.price),
            'max_price',        pny.max(p.stocks.price),
        )
        for p in Product for pic in p.pictures if not p.is_deleted and p.for_sale and p != current_product and not p.shop_id.is_deleted and p.shop_id == current_product.shop_id and pic.is_cover) \
        .order_by(pny.raw_sql('RAND()*{} - {}'.format(ENTROPY*2,ENTROPY)))[:3]
    products = [ dict( (row[i],0 if row[i+1]==None else row[i+1] ) for i in range(0,len(row),2)) for row in q1 ]
    
    shop = current_product.shop_id.to_dict(only=['id','title','icon'])
    shop['follower_count'] = pny.count(current_product.shop_id.followers)
    shop['is_follow'] = 0 if not user_id else 1 if ShopFollower.exists(lambda f: f.user_id == User[user_id] and f.shop_id == current_product.shop_id) else 0
    r = {
        'shop': shop,
        'products': products
    }
    return r

@pny.db_session
def getSimilarProduct(product_id: UUID, user_id: UUID=None):
    # order by ( select average(rating) from shop product rating where product id = hkshopu_product.product_id) desc )
    current_product = Product[product_id]
    q1 = pny.select(
        (
            'id',           p.id,
            'name',         p.name,
            'cover',        pic.src,
            'description',  p.description,
            'has_spec',     p.specs,
            'price',        p.price,
            'min_price',    pny.min(p.stocks.price),
            'max_price',    pny.max(p.stocks.price),
            'shop_title',   p.shop_id.title,
        )
        for p in Product for pic in p.pictures if p.category_id == current_product.category_id and not p.is_deleted and p.for_sale and pic.is_cover and not p.shop_id.is_deleted
    ).order_by(pny.raw_sql('RAND()*{} - {}'.format(ENTROPY*2,ENTROPY)))[:3]
    products = [ dict( (row[i],row[i+1] if not isinstance(row[i+1],dict) else True if row[i+1] else False) for i in range(0,len(row),2)) for row in q1 ]
    return products

@pny.db_session
def getShopProducts(shop_id: UUID, mode: str, user_id: UUID=None):
    all_products = productBrowseLogic(shop_id=shop_id, mode=mode, user_id=user_id)[:12]    
    products =[ 
        {
            'id':id,
            'name':name,
            'price':price,
            'has_spec':True if specs else False,
            'created_at':created_at,
            'min_price':min_price,
            'max_price':max_price,
            'like_count':like_count,
            'is_like':is_like
        }
        for id,name,price,specs,created_at,min_price,max_price,like_count,is_like in all_products
    ]
        
    return products

# core logic of product browsing
def productBrowseLogic(mode, category_id = None, keyword = None, shop_id = None, user_id = None):
    now = datetime.now()
    if shop_id: # for getShopProduct
        pyCommand = """pny.left_join(
            (
                p.id,
                p.name,
                p.price,
                p.specs,
                p.created_at,
                pny.min(stock.price),
                pny.max(stock.price),
                pny.count(p.like),
                pny.count(l for l in p.like if l.user_id == User[user_id])
            )
            for p in Product for stock in p.stocks if p.for_sale and not p.is_deleted and not p.shop_id.is_deleted
        """
    else: # mutiple shops
        # 所有商品
        pyCommand = "pny.left_join((p,pny.min(stock.price),pny.max(stock.price)) for p in Product for stock in p.stocks if p.for_sale and not p.is_deleted and not p.shop_id.is_deleted"
        # 贊助店鋪的商品
        pyCommand2 = '''pny.left_join(
            (
                p,
                pny.min(stock.price),
                pny.max(stock.price),
                sp
            ) for p in Product for stock in p.stocks for s in p.shop_id for sp in s.sponsor if p.for_sale and not p.is_deleted and not s.is_deleted and not s.sponsor.is_empty() and sp.expired_at>now
        '''
    if category_id != None: # add category logic
        SearchHistory(search_category='product', keyword=ProductCategory[category_id].name)
        pyCommand += " and p.category_id == ProductCategory[category_id]"
        pyCommand2 += " and p.category_id == ProductCategory[category_id]"
    if keyword != None: # add keyword logic
        SearchHistory(search_category='product', keyword=keyword)
        pyCommand += " and (keyword in p.name or keyword in p.description)"
        pyCommand2 += " and (keyword in p.name or keyword in p.description)"
    if shop_id != None:
        pyCommand += " and p.shop_id == Shop[shop_id]"
        pyCommand2 += " and p.shop_id == Shop[shop_id]"
    # 所有商品
    all_product = eval(pyCommand+')')
    # 贊助店鋪的商品
    if not shop_id:
        sp = eval(pyCommand2+')')

    if mode == 'new':
        if shop_id:
            all_product = all_product.order_by(lambda id, name, price, created_at, specs, min_price, max_price, like_count, is_like: pny.desc(created_at))
        else:
            all_product = all_product.order_by(lambda p, min_price, max_price: pny.desc(p.created_at))
            sp = sp.order_by(lambda p, min_price, max_price, sp: (pny.desc(sp.probability), pny.desc(p.created_at)))
    elif mode == 'top_sale':
        if not shop_id:
            sp = sp.order_by(
                pny.raw_sql('''
                    sp.probability DESC
                ''')
            )
    elif mode == 'lower_price':
        all_product = all_product.order_by(
            pny.raw_sql('''
                CASE
                    WHEN p.specs IS NULL OR p.specs=CAST('{}' AS JSON) THEN p.price
                    ELSE MIN(stock.price)
                END
            ''')
        )
        if not shop_id:
            sp = sp.order_by(
                pny.raw_sql('''
                    sp.probability DESC,
                    CASE
                        WHEN p.specs IS NULL OR p.specs=CAST('{}' AS JSON) THEN p.price
                        ELSE MIN(stock.price)
                    END
                ''')
            )
    elif mode == 'higher_price':
        all_product = all_product.order_by(
            pny.raw_sql('''
                CASE
                    WHEN p.specs IS NULL OR p.specs=CAST('{}' AS JSON) THEN p.price
                    ELSE MAX(stock.price)
                END
                DESC
            ''')
        )
        if not shop_id:
            sp = sp.order_by(
                pny.raw_sql('''
                    sp.probability DESC,
                    CASE
                        WHEN p.specs IS NULL OR p.specs=CAST('{}' AS JSON) THEN p.price
                        ELSE MIN(stock.price)
                    END
                    DESC
                ''')
            )
    elif mode == 'overall': # 贊助、商品評價
        if not shop_id:
            sp = sp.order_by(
                pny.raw_sql('''
                    sp.probability DESC
                ''')
            )


    try:
        return all_product, sp
    except NameError: # only in one shop
        return all_product

    

