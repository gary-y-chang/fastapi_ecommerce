from fastapi import Form
from pydantic import BaseModel,Json,EmailStr
from datetime import date
from uuid import UUID
from typing import List,Set,Optional,Dict
import json

class UserAuth(BaseModel):
    email: EmailStr
    password: str

class SocialAuth(BaseModel):
    account_id: str
    email: EmailStr
    account_type: str    

class UserEmailCheck(BaseModel):
    email: EmailStr

class SignupVerify(BaseModel):
    email: EmailStr
    valid_code: str

class UserDetailData(BaseModel):
    user_id: UUID
    account_name: str = None
    first_name: str = None
    last_name: str = None
    phone: str = None
    gender: str = None
    birthday: date = None
    avatar: str = None

class UserPhone(BaseModel):
    phone: str
    phone_show: bool

class UserAddressData(BaseModel):
    regon: str
    district: str
    street: str
    street_no: str
    floor: str = None
    room: str = None
    extra: str = None
    is_default: bool = None
    receiver: str = None  # by default, receiver=first_name+last_name
    receiver_call: str = None  # by default, UserDetail.phone

class ShopCategoryData(BaseModel):
    name: str
    selected_icon: str = None
    unselected_icon: str = None
    bg_color: str = None
    ordinal: int = None

class ShopCategories(BaseModel):
    id: List[int]

class ShopDescription(BaseModel):
    description: str

class ShopAddressData(BaseModel):
    name: str
    country_code: str
    phone: str
    area: str
    district: str
    road: str
    rd_number: str
    floor: str = None
    room: str = None
    extra: str
    addr_on: bool = None
    is_default: bool = None

class ShopAddressDataUpdate(ShopAddressData):
    name: str = None
    country_code: str = None
    phone: str = None
    area: str = None
    district: str = None
    road: str = None
    rd_number: str = None
    extra: str = None


class ShopBankAccountData(BaseModel):
    bank_name: str
    bank_code: str
    account_number: str
    account_name: str
    is_default: bool = None

class ShopData(BaseModel):
    title: str
    user_id: str
    cate_ids: str # shop_category id with , cascading the ids, ex. "2,3,7"
    bank_name: str
    bank_code: str
    account_number: str
    account_name: str
    name: str  #商店地址顯示之商號名稱或人名
    country_code: str
    phone: str
    area: str
    district: str
    road: str 
    rd_number: str
    floor: str = None
    room: str = None
    extra: str = None
    
    @classmethod
    def as_form(cls, title: str=Form(...), user_id: str=Form(...), cate_ids: str=Form(..., description='店鋪類別 id 字串, 逗號間隔， ex. 2,3,6'),
        bank_name: str=Form(...), bank_code: str=Form(...), account_name: str=Form(...),
        account_number: str=Form(...), name: str=Form(...), country_code: str=Form(...),
        phone: str=Form(...), area: str=Form(...), district: str=Form(...), road: str=Form(...),
        rd_number: str=Form(...), floor: str=Form(None), room: str=Form(None), extra: str=Form(None)):
        return cls(title=title, user_id=user_id, cate_ids=cate_ids, bank_name=bank_name,
            bank_code=bank_code, account_number=account_number, account_name=account_name,
            name=name, country_code=country_code, phone=phone, area=area,district=district,
            road=road, rd_number=rd_number, floor=floor, room=room, extra=extra)

class SpecData(BaseModel):
    __root__: Dict[str, List[str]] # dynamic field name e.g. {'規格':['菊花','鬱金香']}

class Spec(BaseModel):
    spec_name: str
    spec_val: str

class StockData(BaseModel):
    price: int
    qty: int
    spec: Dict[str,str] = None

class SpecStockData(BaseModel):
    specs: List[SpecData]
    stocks: List[StockData]

class Deliver(BaseModel):
    shipment: str
    fee: int
    on: bool
     
class FreightData(BaseModel):
    weight: int
    length: int
    width: int
    height: int
    sync_shop: bool
    delivers: List[Deliver]


class ProductData(BaseModel):
    shop_id: str
    name: str
    category_id: int = None
    description: str = None
    price: int = None
    qty: int = None
    long_leadtime: int = None
    is_new: bool = None
    for_sale: bool = False
    is_deleted: bool = None
    # weight: int = None
    # length: int = None
    # width: int = None
    # height: int = None

    # @classmethod
    # def as_form(cls, shop_id: str=Form(..., description='商品所屬店鋪的ID'), name: str=Form(..., description='商品名稱'), cate_id: str=Form(None),
    #     description: str=Form(None), price: int=Form(None), qty: int=Form(None), leadtime: int=Form(None), is_new: bool=Form(None),
    #     f_sale: bool=Form(None), is_deleted: int=Form(None), weight: int=Form(None), length: int=Form(None), width: int=Form(None),
    #     height: int=Form(None)):
    #     return cls(shop_id=shop_id, name=name, category_id=cate_id, description=description, price=price, qty=qty, 
    #         long_leadtime=leadtime, is_new=is_new, for_sale=f_sale, is_deleted=is_deleted, weight=weight, length=length,
    #         width=width,height=height)

class ProductCategoryData(BaseModel):
    parent_id: int 
    name: str
    selected_icon: str = None
    unselected_icon: str = None
    bg_color: str = None
    seq: int
   
    # @classmethod
    # def as_form(cls, name: str=Form(...), s_icon: str=Form(None), u_icon: str=Form(None), bg_color: str=Form(None), seq: int=Form(...)):
    #     return cls(name=name, selected_icon=s_icon, unselected_icon=u_icon, bg_color=bg_color, seq=seq)


class OrderItemData(BaseModel):
    prod_id: str
    prod_name: str
    prod_img: str
    qty: int
    price: int
    freight: int
    ship_by: str
    spec: List[Spec] = None

class OrderData(BaseModel):
    shop_id: str
    shop_title: str
    shop_icon: str
    ship_info: str
    payment: str
    items: List[OrderItemData]

class ShopUpdate(BaseModel):
    title: str = None
    description: str = None
    shipment: Json = None
    phone: str = None
    phone_on: bool = None
    email: str = None
    email_on: bool = None
    facebook_on: bool = None
    instagram_on: bool = None
    # @classmethod
    # def __get_validators__(cls):
    #     yield cls.validate_to_json

    # @classmethod
    # def validate_to_json(cls, value):
    #     if isinstance(value, str):
    #         return cls(**json.loads(value))
    #     return value

class ProductShipment(BaseModel):
    shipment:str
    freight:int
    on:bool      

class ProductCreation(BaseModel):
    shop_id :UUID
    category_id : int
    name :str
    description :str
    weight : int
    length: int
    width : int
    height : int
    long_leadtime : int
    is_active : bool
    is_new: bool
    for_sale: bool
#     specs='''[
#   {
#     "規格":"蘭花",
#     "尺寸":"高70cm",
#     "price":150,
#     "quantity":60
#   },
#   {
#     "規格":"蘭花",
#     "尺寸":"高50cm",
#     "price":200,
#     "quantity":56
#   }]'''
    spec_header:Json ='{"規格":["蘭花","鬱金香"], "尺寸":["高70cm","高50cm"]}'
    spec_detail:Json ='[{"規格":"蘭花", "尺寸":"高70cm","price":150, "quantity":60 },{ "規格":"蘭花","尺寸":"高50cm","price":200,"quantity":56},{"規格":"鬱金香", "尺寸":"高70cm", "price":245,"quantity":30},{ "規格":"鬱金香", "尺寸":"高50cm","price":556,"quantity":88}]'
    freights : List[ProductShipment]
    price:int
    quantity:int
    @classmethod
    def __get_validators__(cls):
        yield cls.validate_to_json

    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value

class ProductList(BaseModel):
    shop_id :UUID
    keyword : str
    product_status :str = '架上商品 or 已售完 or 未上架'

class ProductStatus(BaseModel):
    product_id: UUID
    status: str

class WalletChargeHistory(BaseModel):
    wallet_id: UUID
    charge_no: str
    description: str
    
class WalletCharge(BaseModel):
    wallet_id: UUID
    amount: float
    payment: str

class SponsorJoinBase(BaseModel):
    sponsor_level: int    
    payment: str # 付款方式

class SponsorJoinShop(SponsorJoinBase):
    wallet_id: UUID

class SponsorJoinBuyer(SponsorJoinBase):
    user_id: UUID

class PayNotify(BaseModel):
    Status: str
    MerchantID: str 
    TradeInfo: str
    TradeSha: str
    EncryptType: int
