from re import U
from fastapi import APIRouter,Depends, File, UploadFile, Form, HTTPException, Body, Query
from models import products,shops
from typing import Optional,List
from uuid import UUID
from .util import upload_to_gcs
from models.entities import ProductCategory
from .req_models import FreightData, ProductData,ProductList,ProductStatus, ProductCategoryData, SpecData, SpecStockData, StockData
from .res_models import ResponseCreatePic, ResponseProductCategory, ResponseCreateProductCategory, ResponseFreight, ResponseSpecStock, ResponseCreateProduct, ResponseProduct
from utils.upload_tools import upload_file , delete_file
import json
from auth import Auth
from fastapi.encoders import jsonable_encoder

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

auth = Auth()

tag_meta = {
    'name': 'Products',
    'description': '商品資料相關操作: 新增商品、上下架、更新 .....',
}

@router.post(
    "/category/add", 
    name='新增商品分類', 
    description='要注意是否有父類別, 若本身即為父類別，則parent_id為空值'
)
def create_product_category(cate_data: ProductCategoryData):
    cate = products.createProductCategory(**cate_data.dict())
    return {"product-category": cate.name, "id": cate.id}

@router.get(
    '/category/all', 
    name='取得商品分類', 
    description='若本身即為父類別，則parent_id為空值'
)
def get_all_categories(parent_id: int=None):
    return [c.to_dict() for c in products.getProductCategory(parent_id)]

@router.put(
    "/add/save-pic", 
    name='店家新增商品，商品圖片上傳', 
    description='form submit',
    response_model=List[ResponseCreatePic]
)
async def create_product(prod_id: str = Form(...), files: List[UploadFile] = File(...)):    
    try:
        products.deleteProductPic(product_id=prod_id)
        pics = []
        for idx, f in enumerate(files):
            print(idx, f.filename)
            cover = lambda i: i==0
            pic_url = upload_to_gcs(f)
            pic = products.addProductPic(src=pic_url, is_cover=cover(idx), product_id=prod_id)
            pics.append({"pic_id": pic.id, "path": pic_url})
    except Exception as e:
        raise HTTPException(status_code=409, detail='Failed to save product pictures')    
    
    return pics

@router.post(
    "/add/save-data", 
    name='店家新增商品，資料儲存', 
    description='',
    response_model=ResponseCreateProduct,
)
def create_product_no_pic(productData: ProductData):
    data = {k:v for k,v in productData.dict().items() if k !='shop_id'}
    # prod_id = products.saveAndUpdateProduct(shop_id=productData.shop_id, **data).id
    prod_id = products.createProduct(shop_id=productData.shop_id, **data).id
    return {"product-id": prod_id, "updated": True}
    # shipments=jsonable_encoder(productData)
    # print(shipments['freights'])
    # product=products.addProduct(productData.shop_id,productData.category_id,productData.name,productData.description,productData.weight,productData.length,productData.width,productData.height,productData.long_leadtime,productData.is_active,productData.is_new,productData.for_sale,productData.spec_header,shipments['freights'])
    # #圖片上傳DB
    # productPicURL=[]
    # for file in files:
    #     print(file.filename)
    #     productPicURL.append(upload_file(file,'images/product_fastapi/',suffix="img"))
    # #處理cover
    # for index,product_pic_url in enumerate(productPicURL):      
    #     # 寫入資料庫
    #     if index==0:
    #         products.addProductPic(product_pic_url,1,product)
    #     else :
    #         products.addProductPic(product_pic_url,0,product)
    # #規格
    # if not productData.spec_detail: 
    #     products.addProductStock(productData.price,productData.quantity,product)
    # else:
    #     for spec in productData.spec_detail:
    #         detail={}
    #         keys=list(spec.keys())
    #         detail.update({keys[0]:spec[keys[0]]})
    #         detail.update({keys[1]:spec[keys[1]]})
    #         products.addProductSpec(detail,spec['price'],spec['quantity'],product)
    # return product
    #return productData

@router.post(
    "/{product_id}/save-freights", 
    name='儲存/更新 商品之運費資料', 
    response_model=ResponseProduct,
)
def edit_product_freights(
    product_id, 
    freight_data: FreightData = Body(
        ...,
        examples={
            "normal":{
                "summary": "Normal Example",
                "value":{
                    "weight": 3,
                    "length": 5,
                    "width": 7,
                    "height":11,
                    "sync_shop": False,
                    "delivers":[
                        {
                            "shipment": "順豐速運",
                            "fee": 0,
                            "on": True
                        }
                    ],
                }
            }
        }
    )
):
        
    update_dict = freight_data.dict() 
    # update_dict['freights'] = json.dumps(update_dict['delivers'], ensure_ascii=False)
    update_dict['freights'] = update_dict['delivers']
    del update_dict['delivers']
    del update_dict['sync_shop']
    p = products.updateProduct(product_id, **update_dict)
    if freight_data.sync_shop:
        shipment = {}
        for s in update_dict['freights']:
            shipment.update({s['shipment']:s['on']})
        shops.updateShop({'id':p.shop_id.id,'shipment':shipment})
    ret = p.to_dict()
    ret['delivers'] = ret.pop('freights')
    return ret

@router.post(
    "/{product_id}/save-stocks", 
    name='儲存/更新 商品之規格、庫存與價格',
    response_model=ResponseSpecStock,
)
# def edit_spec_stocks(product_id, specs: List[SpecData],stock: List[StockData]):
def edit_spec_stocks(product_id, data: SpecStockData= Body(
        ...,
        examples={
            "normal":{
                "summary": "Normal Example",
                "value": {
                    "specs": [{'規格':['菊花','鬱金香']},{'尺寸':['高70cm','高50cm']}],
                    "stocks": [
                        {
                            'price': 100,
                            'qty': 10,
                            'spec': {'菊花':'高70cm'}
                        },
                        {
                            'price': 80,
                            'qty': 8,
                            'spec': {'菊花':'高50cm'}
                        },
                        {
                            'price': 100,
                            'qty': 15,
                            'spec': {'鬱金香':'高70cm'}
                        },
                        {
                            'price': 80,
                            'qty': 10,
                            'spec': {'鬱金香':'高50cm'}
                        }
                    ]
                },
            }
        }
    )):
    specs = [spec.__root__ for spec in data.specs]
    # for s in specs:
    #     spec_dict[s.name] = s.value   
    # sp = json.dumps(spec_dict, ensure_ascii=False)
    products.updateProduct(product_id, specs=specs)
    
    products.deleteProductStockAll(product_id)
    stock_list = [] 
    for k in data.stocks:
       
        # spec_list = []
        # for spec in k.spec:
        #     sp = {}
        #     sp[spec.spec_name] = spec.spec_val
        #     spec_list.append(sp) 
        # spec[k.spec.spec_name] = k.spec.spec_val
        psk = products.saveProductStock(product_id, k.price, k.qty, k.spec)
        stock_list.append(psk.to_dict(exclude='product_id'))
    return {'product_id': product_id, 'specs': specs, 'stocks': stock_list}

@router.patch(
    '/{product_id}/save-data',
    name='店家編輯商品，資料儲存',
    response_model=ResponseCreateProduct
)
def update_product_no_pic(product_id: str, productData: ProductData):
    p = products.updateProduct(prod_id=product_id, **productData.dict())
    return {"product-id": product_id, "updated": True}

@router.patch(
    '/{product_id}/for-sale/{act}',
    name='商品 上/下 架', 
    description='act值 = up(上架) / down(下架)',
    response_model=ResponseProduct,
)
def product_for_sale(product_id, act: str):
    try:
        p = products.getProductAllInfo(product_id)
        if act=='up':
    #    check UI 紅點星號的欄位 是否都有值
            if p.name == None:
                raise AttributeError("'商品名稱' attribute missing in Product")
            elif p.description == '':
                raise AttributeError("'商品描述' attribute missing in Product")    
            elif p.category_id == None:
                raise AttributeError("'商品分類' attribute missing in Product")   
            elif p.is_new == None:
                raise AttributeError("'商品保存狀況' attribute missing in Product")      
            elif not p.freights:
                raise AttributeError("'運費' attribute missing in Product")     
            elif (not p.specs and p.price == None) or (len(p.stocks)==0 and p.specs):
                raise AttributeError("'商品價格' attribute missing in Product")   
            elif (not p.specs and p.qty == None) or (p.specs and len(p.stocks)==0):
                raise AttributeError("'商品數量' attribute missing in Product")
        
            p = products.updateProduct(product_id, for_sale=True)
        elif act=='down':
            p = products.updateProduct(product_id, for_sale=False)
        else:
            raise Warning("API parameter 'act' can only be 'up' or 'down'")   
    except (AttributeError, Warning) as e:        
        raise HTTPException(status_code=409, detail=str(e))    

    ret = p.to_dict()
    ret['delivers'] = ret.pop('freights')
    return ret

@router.get("/{product_id}", name='商品頁詳細資料')
def get_product_by_id(product_id):
    p = products.getProductAllInfo(product_id)  
    p_dic = p.to_dict(with_lazy=True)
    p_dic['pictures'] = []
    p_dic['stocks'] = []
    for t in p.pictures:
        p_dic['pictures'].append(t.to_dict(only=['src','is_cover']))
    
    for s in p.stocks:
        p_dic['stocks'].append(s.to_dict(only=['price','qty','spec']))      
    
    p_dic['category'] = p.category_id.to_dict(only=['id','name'])
    p_dic['shop'] = p.shop_id.to_dict(only=['id','title','icon'])
    del p_dic['category_id']
    del p_dic['shop_id']
    return p_dic



@router.get("/product_list")
def product_list(shop_id:UUID, keyword:str, product_status:str=Query(...,description="架上商品 or 已售完 or 未上架")):
    return products.getProductList(shop_id,keyword,product_status)

# @router.get("/categories/{shop_id}")
# def get_product_categories():
#     pass

@router.get("/shop_product/{shop_id}",deprecated=True)
def shop_product(shop_id: UUID):
    return products.getProductsByShopId(shop_id)

@router.get(
    "/product_info/{product_id}",
    # response_model=List[ResponseProductInfo]
)
def product_info(product_id:UUID):
    return products.productInfo(product_id)

# @router.post("/product_list")
# def product_list(data: ProductList):
#     return products.getProductList(data.shop_id,data.keyword,data.product_status)

# @router.get("/testGetProduct")
# def testGetProduct():
#     return [product.to_dict() for product in products.getAllProducts()]

# @router.get("/testGetShop")
# def testGetShop():
#     return [shop.to_dict() for shop in products.getAllShops()]

@router.put("/update_status")
async def update_status(status_data: ProductStatus, deprecated=True):
    return products.update_status(status_data.product_id,status_data.status)

@router.delete("/delete/{product_id}")
async def delete(product_id: UUID):
    return products.delete(product_id)
