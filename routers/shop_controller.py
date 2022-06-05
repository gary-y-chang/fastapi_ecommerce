from fastapi import APIRouter, HTTPException, UploadFile, Depends, File, Form, Response, status, Body
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from models.entities import Shop
from .req_models import ShopAddressDataUpdate, ShopData, ShopUpdate, ShopCategories, ShopCategoryData, ShopBankAccountData, ShopAddressData, ShopDescription
from .res_models import ResponseOperationStatus, ResponseShop, ResponseShopInfo, ResponseShopCategory, ResponseCreateShop, ResponseShopBankAccount, ResponseShopAddress, ResponseCreateShopCategory, ResponseShopSponsor
from auth import Auth, Guard
from models import shops
from typing import List
from .util import upload_to_gcs
from datetime import datetime, timedelta
from uuid import UUID

router = APIRouter(
    prefix="/shops",
    tags=["Shops"]
)
auth = Auth()

tag_meta = {
    'name': 'Shops',
    'description': '店鋪資料相關操作: 新增店鋪、編輯、.....',
}

@router.get('/category/{shop_category_id}')
def get_shops_by_category(shop_category_id):
    category_data = shops.getShopsByCategory(shop_category_id)
    return category_data

@router.get(
    '/categorys/all',
    response_model=List[ResponseShopCategory],
)
def get_categorys():
    category_data = shops.getAllCategorys()
    return category_data

@router.get(
    '/owner/{user_id}',
    response_model=List[ResponseShopInfo],
)
def get_shops_by_userId(user_id: str):
    shop = shops.getShopsByUserId(user_id)
    for i in range(len(shop)):
        shop[i]['product_count'] = len(shop[i]['products'])
        shop[i]['follower_count'] = len(shop[i]['followers'])
        shop[i]['income'] = 0 # 該店的進帳金額
        shop[i]['rate'] = 0 # 該店的評價
    return shop

@router.delete(
    '/delete',
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response
)
async def delete_shop(shop_id:UUID, uid=Depends(Guard())) -> None:
    shops.updateShop({'id':shop_id, 'is_deleted':True})

@router.get(
    '/update/check',
    response_model=ResponseOperationStatus,
)
def exist_shop_title(title: str, uid=Depends(Guard())):    
    shop = shops.getShopByCol(title=title, is_deleted=False)
    if shop:
        return {"success": True}
    return {"success": False}

@router.post(
    '/category/add',
    response_model=ResponseCreateShopCategory
)
def create_shop_category(data: ShopCategoryData):
    s = shops.createShopCategory(**data.dict())
    return {"shop-category": s.name, "id": s.id}

@router.get(
    '/categorys/',
    response_model=List[ResponseShopCategory],
)
def get_shop_categorys(shop_id: UUID):
    category_data = shops.getShopCategorys(shop_id)
    return category_data

# @router.get('/categorys')
# def get_shop_categorys(shop_id: str, uid=Depends(Guard())):
#     
#     c  = list(shops.getShopCategorys(shop_id))
#     c.sort()
#     return c

@router.post(
    '/categorys',
    response_model=ResponseOperationStatus,
)
def set_shop_categorys(shop_id: str, categorys: ShopCategories, uid=Depends(Guard())):    
    shops.setCategorys(shop_id, categorys.dict())
    return {"success": True}

@router.get(
    '/bank_accounts',
    response_model=List[ResponseShopBankAccount],
)
def get_bank_accounts(shop_id: str, uid=Depends(Guard())):    
    banks = shops.getBankAccounts(shop_id)
    for i in range(len(banks)):
        banks[i]['account_number'] = '*'+banks[i]['account_number'][-4:]

    return banks

@router.post(
    '/bank_accounts',    
    response_model=ResponseShopBankAccount,
)
def create_bank_accounts(shop_id: str, bank_accounts: ShopBankAccountData, uid=Depends(Guard())):    
    bank_accounts = shops.createBankAccounts(shop_id,[bank_accounts])
    return bank_accounts[0]

@router.patch(
    '/bank_accounts/{id}',
    response_model=ResponseOperationStatus,
)
def default_bank_accounts(id, uid=Depends(Guard())):    
    shops.defaultBankAccounts(id)
    return {"success": True}

@router.delete(
    '/bank_accounts',
    response_model=ResponseOperationStatus,
)
def delete_bank_accounts(id:str, uid=Depends(Guard())):    
    shops.deleteBankAccounts([id])
    return {"success": True}

@router.get(
    '/addresses',
    response_model=List[ResponseShopAddress],
)
def get_addresses(shop_id: str, uid=Depends(Guard())):    
    addresses = shops.getAddresses(shop_id)
    return addresses

@router.post(
    '/addresses',
    response_model=ResponseShopAddress,
)
def create_addresses(shop_id: str, addresses: ShopAddressData, uid=Depends(Guard())):    
    addresses = shops.createAddresses(shop_id, [addresses])
    return addresses[0]

@router.patch(
    '/addresses/{id}',
    response_model=ResponseShopAddress,
)
def update_addresses(id, addresses: ShopAddressDataUpdate=Body(
            ...,
            examples={
                "edit_all":{
                    "summary": "Edit All",
                    "value":{
                        "name": "foo-name",
                        "country_code": "066",
                        "phone": "0987654321",
                        "area": "area1",
                        "district": "1 d.t.",
                        "road": "king road",
                        "rd_number": "no. 99",
                        "floor": "",
                        "room": "",
                        "extra": "",
                        "addr_on": True,
                        "is_default": True
                    }
                },
                "show_addr":{
                    "summary": "Show Default Address",
                    "value":{
                        "addr_on": True
                    }
                },
                "default_addr":{
                    "summary": "Set Default Address",
                    "value":{
                        "is_default": True
                    }
                }
            }
        ), uid=Depends(Guard())
    ):
    '''
    只會更新送出的欄位。\n
    更新is_default=True時，會將該店其餘地址設為False
    '''
    update_dict = { k:v for k,v in addresses.dict().items() if v!=None} # update if value not equal to None
    try:
        addr = shops.updateAddresses(id, address_data=update_dict)
    except ValueError as e: # when updated column is required
        return Response(status_code=status.HTTP_409_CONFLICT,content=str(e),media_type="application/text")
    return addr

@router.delete(
    '/addresses',
    response_model=ResponseOperationStatus,
)
def delete_addresses(id: str, uid=Depends(Guard())):    
    shops.deleteAddresses([id])
    return {"success": True}


@router.get(
    '/{shop_id}',
    response_model=ResponseShopSponsor,
    responses={204: {
        "model": None,
        "description": "Successful Response With Null",
    }},
)
async def get_shop(shop_id:UUID, uid=Depends(Guard())):
    s = shops.getShop(shop_id=shop_id)
    if s:
        return s
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post(
    '/add',
    name='初次新增店鋪', 
    description='全部資料放進一個 form submit',
    response_model=ResponseCreateShop,
)
async def create_shop(shop_data: ShopData = Depends(ShopData.as_form), icon: UploadFile = File(...)):
    icon_url = upload_to_gcs(icon)
    shop_id = shops.createShop(icon_url, **shop_data.dict())
    return {"shop_id": shop_id}
    
@router.patch(
    '/{shop_id}',
    response_model=ResponseShop
)
async def update_shop_info(shop_id:UUID, 
        shop_data:ShopUpdate=Body(
            ...,
            examples={
                "title":{
                    "summary": "Update Title",
                    "value":{
                        "title": "foo-title"
                    }
                },
                "desc":{
                    "summary": "Update Description",
                    "value":{
                        "description": "The example content."
                    }
                },
                "shipment":{
                    "summary": "Update Shipment",
                    "value":{
                        "shipment": '''[{"郵政": true}, {"順豐速運": false}]'''
                    }
                },
                "phone":{
                    "summary": "Update Phone",
                    "value":{
                        "phone": "0987654321",
                        "phone_on": True
                    }
                },
                "email":{
                    "summary": "Update Email",
                    "value":{
                        "email": "foo@example.mail",
                        "email_on": True
                    }
                },
                "link_fb": {
                    "summary": "Link To Facebook",
                    "value":{
                        "facebook_on": True
                    }
                },                
                "link_ig": {
                    "summary": "Link To Instagram",
                    "value":{
                        "instagram_on": True
                    }
                }
            }
        ), uid=Depends(Guard())
    ):
    update_dict = { k:v for k,v in shop_data.dict().items() if v!=None} # update if value not equal to None
    if shop_data.title:
        now = datetime.now()
        limit = timedelta(days=30) # 30天內只能更改一次店鋪名稱
        s = shops.getShopByCol(id=shop_id,is_deleted=False)
        if s.title_updated_at and now-s.title_updated_at<=limit:
            raise HTTPException(status_code=409, detail='Refuse shop title changed until '+(s.title_updated_at+timedelta(days=30)).strftime("%d/%m/%Y %H:%M:%S"))
        elif now-s.created_at<=limit:
            raise HTTPException(status_code=409, detail='Refuse shop title changed until '+(s.created_at+timedelta(days=30)).strftime("%d/%m/%Y %H:%M:%S"))
        update_dict['title_updated_at'] = now
    s = shops.updateShop({'id':shop_id,**update_dict})
    return s

@router.patch(
    '/{shop_id}/images',
)
async def update_shop_images(shop_id:UUID, icon:UploadFile=File(None), pic:UploadFile=File(None), uid=Depends(Guard())):
    update_dict = {} # update if value is not None
    if icon:
        update_dict['icon'] = upload_to_gcs(icon)
    if pic:
        update_dict['pic'] = upload_to_gcs(pic)
    s = shops.updateShop({'id':shop_id,**update_dict})
    return s
