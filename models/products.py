import pony.orm as pny
from pony.orm.core import select
from models.entities import Product, ProductCategory, ProductPic, Stock,Shop
from uuid import uuid4, UUID
from datetime import datetime
from operator import attrgetter
import json

@pny.db_session
def createProductCategory(**kwargs):
    # parent_id = kwargs.get('parent_id')
    # if parent_id == None:
    #     return ProductCategory(**kwargs)
    # else:
    #    parent = ProductCategory[parent_id]
    #    return ProductCategory(parent_id=parent, **kwargs)   
    return ProductCategory(**kwargs)

@pny.db_session
def getProductCategory(parent_id=None):
    if parent_id == None:
        return [c for c in select(c for c in ProductCategory if c.parent_id==None).order_by(ProductCategory.seq)[:]]
    else:
        return sorted([sub for sub in ProductCategory[parent_id].sub_categories], key=attrgetter('seq'))

@pny.db_session
def createProduct(shop_id: str, **kwargs):
        return Product(shop_id=UUID(shop_id), **kwargs)

@pny.db_session
def getProductAllInfo(prod_id: str):
    p = Product[UUID(prod_id)]
    p.load()
    p.pictures.load()
    p.category_id.load()
    p.shop_id.load()
    p.stocks.load()
    # # for k in p.pictures:
    # #      print(k.id,k.src)
    # pdic = p.to_dict(with_lazy=True, with_collections=True, related_objects=True)   
    # print(pdic)
    return p

@pny.db_session
def getProductFreights(prod_id: str):
    p = Product[UUID(prod_id)] 
    # p.freights
    return p

@pny.db_session
def getProductLeadtime(prod_id: str):
    p = Product[UUID(prod_id)] 
    return p.long_leadtime 
    
@pny.db_session
def updateProduct(prod_id: str, **kwargs):
    p = Product[UUID(prod_id)]
    p.set(**kwargs)
    p.set(updated_at=datetime.now())
    return p

@pny.db_session
def saveProductStock(prod_id: str, price: int, qty:int, spec: list):
    p = Product[UUID(prod_id)]
    stock = Stock(price=price, qty=qty, spec=spec, product_id=p) 
    return stock

@pny.db_session
def deleteProductStockAll(prod_id: UUID):
    p = Product[prod_id]
    p = pny.select(s for s in Stock if s.product_id==p).delete()
    
@pny.db_session
def addProductPic(src,is_cover,product_id):
    pic = ProductPic(src=src,is_cover=is_cover,product_id=product_id)
    return pic

@pny.db_session
def deleteProductPic(product_id):
    p = Product[product_id]
    pny.select(pic for pic in ProductPic if pic.product_id==p).delete()


@pny.db_session
def update_status(product_id:UUID,status:str):
    if status=="draft":
        Product[product_id].set(for_sale=False)
        return {'status':0,'ret_val':'上架/下架成功!'}
    elif status=="active":
        Product[product_id].set(for_sale=True)
        return {'status':0,'ret_val':'上架/下架成功!'}
    else:
        return {'status':-1,'ret_val':'上架/下架失敗!'}

@pny.db_session
def delete(product_id:UUID):
    Product[product_id].set(is_delete=True)
    return {'status':0,'ret_val':'刪除成功!'}

@pny.db_session
def getAllProducts():
    products = pny.select(u for u in Product)[:]
    print(type(products))
    print(products)
    return products

@pny.db_session
def getAllShops():
    shops = pny.select(u for u in Shop)[:]
    print(type(shops))
    print(shops)
    return shops

@pny.db_session
def productInfo(product_id:UUID):
    # products=Product[product_id]
    # print(products.category_id)
    # for cid in products.category_id:
    # categorys=ProductCategory.select(lambda c: c.id==products.category_id)
    products=select((c.name, p) for c in ProductCategory for p in c.products if p.id==product_id)[:]
    products.show()
    print(type(products))
    ret_val=[]
    for product in products:
        info={
            
        }
        info.update({'category_name':product[0]})
        info.update(product[1].to_dict())
        specs=select(s for p in Product for s in p.stocks if p.id==product_id)[:]
        if len(specs)==0:
            ret_val.append(info)
            break
        else:
            spec_data=[]
            for spec in specs:
                print(spec)
                spec_data.append(spec.to_dict(exclude=['product_id','id']))
            info.update({'spec_detail':spec_data})
            ret_val.append(info)
        #取圖
        pics=select(pic for p in Product for pic in p.pictures if p.id==product_id)[:]
        pic_list=[]
        for pic in pics:
            pic_list.append(pic.to_dict(only='src')['src'])
        info.update({'pic_path':pic_list})
    print(ret_val)
    return ret_val

@pny.db_session
def getProductsByShopId(shop_id: UUID):
    # Product.select(lambda p: p.shop_id==UUID(shop_id))
    # p=Product.select().filter(shop_id=shop_id,is_active=True,is_delete=False)[:]
    ret_val=[]
    products=select((p,max(spec.price),min(spec.price),pic.src) for s in Shop for p in s.products for spec in p.stocks for pic in p.pictures if s.id==shop_id and p.for_sale==True and pic.is_cover==True and p.is_deleted==False)[:]
    products.show()
    for product in products:
        info={
            
        }
        info.update(product[0].to_dict())
        info.update({'max_price':product[1],'min_price':product[2],'pic_path':product[3]})
        ret_val.append(info)
    return ret_val


@pny.db_session
def getProductList(shop_id: UUID,keyword:str,product_status:str):
    # Product.select(lambda p: p.shop_id==UUID(shop_id))
    # p=Product.select().filter(shop_id=shop_id,is_active=True,is_delete=False)[:]
    ret_val=[]
    if product_status=='架上商品':
        products=select((p,max(spec.price),min(spec.price),pic.src) for s in Shop for p in s.products for spec in p.stocks for pic in p.pictures if s.id==shop_id and p.for_sale==True and p.is_deleted==False and pic.is_cover==True and sum(spec.qty)>0)[:]
        products_no_spec=select((p,pic.src) for s in Shop for p in s.products for pic in p.pictures if s.id==shop_id and p.for_sale==True and p.is_deleted==False and pic.is_cover==True and not p.specs and p.qty>0)[:]
    elif  product_status=='已售完':
        products=select((p,max(spec.price),min(spec.price),pic.src) for s in Shop for p in s.products for spec in p.stocks for pic in p.pictures if s.id==shop_id and p.for_sale==True and p.is_deleted==False and pic.is_cover==True and sum(spec.qty)<=0)[:]
        products_no_spec=select((p,pic.src) for s in Shop for p in s.products for pic in p.pictures if s.id==shop_id and p.for_sale==True and p.is_deleted==False and pic.is_cover==True and not p.specs and p.qty<=0)[:]
    elif  product_status=='未上架':
        products=select((p,max(spec.price),min(spec.price),pic.src) for s in Shop for p in s.products for spec in p.stocks for pic in p.pictures if s.id==shop_id and p.for_sale==False and p.is_deleted==False and pic.is_cover==True)[:]
        products_no_spec=select((p,pic.src) for s in Shop for p in s.products for pic in p.pictures if s.id==shop_id and p.for_sale==False and p.is_deleted==False and pic.is_cover==True and not p.specs)[:]
    products.show()
    products_no_spec.show()
    for product in products:
        info={
            
        }
        info.update(product[0].to_dict())
        info.update({'max_price':product[1],'min_price':product[2],'pic_path':product[3]})
        ret_val.append(info)
    for product in products_no_spec:
        info={}
        info.update(product[0].to_dict())
        info.update({'max_price':info['price'],'min_price':info['price'],'pic_path':product[1]})
        ret_val.append(info)
    return ret_val