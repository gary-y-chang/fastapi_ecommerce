from collections import namedtuple
import json
from typing import List, Optional
from pydantic import BaseModel, Json
from pydantic.fields import Field
from pydantic.schema import schema
from uuid import UUID
from .req_models import ShopCategoryData, ShopBankAccountData, ShopAddressData, ProductCategoryData, FreightData, Deliver, SpecData, StockData, ProductData,UserAddressData,SpecStockData
from datetime import datetime
from pony.orm.ormtypes import TrackedDict


class ResponseSignup(BaseModel):
    user_id: UUID

class ResponseOperationStatus(BaseModel):
    success: bool

class ResponseLogin(BaseModel):
    user_id: UUID
    access_token: str
    refresh_token: str

class ResponseUserAddress(UserAddressData):
    address_id: str

class ResponseShop(BaseModel):
    id: UUID
    title : str
    title_updated_at: datetime=None
    description : str=None
    code : str
    icon : str=None
    pic : str=None
    user_id : UUID
    user_account : str
    shipment : TrackedDict
    phone: str=None
    phone_on: bool=None
    email: str=None
    email_on: bool=None
    facebook_on : bool=None
    instagram_on : bool=None
    created_at : datetime
    updated_at : datetime=None
    is_deleted : bool=None
    categorys : List[str]

class ResponseSponsor(BaseModel):
    sponsor_level: Optional[int]
    background_is_show: bool
    badge_is_show: bool
    frame_is_show: bool

class ResponseShopSponsor(ResponseShop,ResponseSponsor):
    pass

class ResponseShopInfo(ResponseShop):
    product_count: int
    follower_count: int
    rate: float

class ResponseShopInfoBuyer(BaseModel):
    shop_id: UUID
    title: str
    icon: str
    follower_count: int = 0
    rate: float = 0
    rate_count: int = 0
    is_follow: int
    src: List[str] # 3張 產品圖片

class ResponseShopCategory(ShopCategoryData):
    id: int

class ResponseCreateShopCategory(BaseModel):
    shop_category: str = Field(..., alias='shop-category')
    id: int

class ResponseShopBankAccount(ShopBankAccountData):
    id: int

class ResponseShopAddress(ShopAddressData):
    id: int

class ResponseCreateShop(BaseModel):
    shop_id: UUID

class ResponseCreateProductCategory(BaseModel):
    product_category: str = Field(None, alias='product-category')
    id: int

class ResponseProductCategory(ProductCategoryData):
    id: int

class ResponseCreateProduct(BaseModel):
    product_id: UUID = Field(..., alias='product-id')
    updated: bool

class ResponseCreatePic(BaseModel):
    pic_id: int
    path: str

class ResponseFreight(BaseModel):
    weight: int
    length: int
    width: int
    height: int
    id: UUID
    freights: List[Deliver] = Field(..., alias='delivers')

class ResponseProduct(ProductData,ResponseFreight):
    id: UUID
    shop_id: UUID

class ResponseSpecStock(SpecStockData):
    product_id: UUID

class ResponseBrowseShopBase(BaseModel):
    id: UUID
    title: str
    icon: str
    follower_count: int
    is_follow: int

class ResponseBrowseShop(ResponseBrowseShopBase,ResponseShopInfoBuyer,ResponseSponsor):
    created_at: datetime
    user_id: UUID

class ResponseBrowseProductBase(BaseModel):
    id: UUID
    name: str
    cover: str
    min_price: Optional[float]
    max_price: Optional[float]

class ResponseBrowseProduct(ResponseBrowseProductBase,ResponseSponsor):
    title: str # shop title
    price: float
    user_id: UUID
    has_spec: bool
    like_count: int
    is_like: int

class ResponseBrowseRecommendShop(BaseModel):
    id: UUID
    icon: str
    title: str
    rate: float = 0
    is_follow: int
    product_pics: List[str]

class ResponseBrowseRecommendProduct(BaseModel):
    id: UUID
    category_id: int
    name: str
    description: str
    is_like: int
    has_spec: bool
    src: str
    price: float
    min_price: Optional[float]
    max_price: Optional[float]
    shop_title: str

class ResponseBrowseSameShopProduct(BaseModel):
    shop: ResponseBrowseShop
    products: List[ResponseBrowseProductBase]

class ResponseSimilarProduct(ResponseBrowseProductBase):
    description: str
    has_spec: bool
    price: float
    shop_title: str

class ResponseWalletCharge(BaseModel):
    charge_no: str
    wallet_id: UUID
    amount: float
    history: int
    paid_at: datetime = None
    payment: str
    process_id: UUID
    created_at: datetime
    status: int