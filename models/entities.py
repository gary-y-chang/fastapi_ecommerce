from ast import Index
from datetime import date, datetime, timedelta
from enum import unique
from decouple import config
from uuid import UUID, uuid4
from pony.orm import *
from decimal import Decimal
from dateutil.relativedelta import relativedelta

config.encoding = 'utf-8'
debug_mode = config('DEBUG', cast=bool)
db_host = config('MYSQL_HOST')
db_port = config('MYSQL_PORT', cast=int)
db_user = config('MYSQL_USER')
db_pwd = config('MYSQL_PASS')

db = Database()
db.bind(provider='mysql', user=db_user, password=db_pwd, host=db_host, port=db_port, database='hkshopu_db')

class User(db.Entity):
    _table_ = 'User'
    id = PrimaryKey(UUID, auto=True)
    user_no = Optional(str, 32, unique=True, index='unumber')  # 用戶編號 yyyymmdd0001(S)
    google_id = Optional(str, 50, nullable=True)
    fb_id = Optional(str, 50, nullable=True)
    apple_id = Optional(str, 50, nullable=True)
    email = Required(str, 64, unique=True, index='umail')
    password = Required(str, 128)
    is_active = Required(bool, default=False)
    created_at = Required(datetime)
    user_detail = Optional('UserDetail', lazy = True)
    addresses = Set('UserAddress')
    shop_follow = Set('ShopFollower')
    product_like = Set('ProductLike')
    notifications = Set('NotificationHistory')
    sponsor = Optional("Sponsor", lazy=True)
    sponsor_order = Optional('SponsorOrder', lazy=True)

class UserDetail(db.Entity):
    _table_ = 'UserDetail'
    user_id = PrimaryKey(User)
    account_name = Optional(str, 50, nullable=True, index='actname')
    first_name = Optional(str, 50, nullable=True, index='ftname')
    last_name = Optional(str, 50, nullable=True, index='ltname')
    phone = Optional(str, 32, nullable=True)
    gender = Optional(str, 2, nullable=True)
    birthday = Optional(date, nullable=True)
    avatar = Optional(str, 256, nullable=True)

class UserAddress(db.Entity):
    _table_ = 'UserAddress'
    regon = Optional(str, 64, nullable=True)
    district = Optional(str, 64, nullable=True)
    street = Optional(str, 64, nullable=True)
    street_no = Optional(str, 32, nullable=True)
    floor = Optional(str, 16, nullable=True)
    room = Optional(str, 16, nullable=True)
    extra = Optional(str, 64, nullable=True)
    user_id = Required(User)
    is_default = Optional(bool, default=True)
    receiver = Optional(str, 32)  # by default, receiver=first_name+last_name
    receiver_call = Optional(str, 32)  # by default, UserDetail.phone    

class ShopCategory(db.Entity):
    _table_ = 'ShopCategory'
    id = PrimaryKey(int, auto=True)
    name = Required(str, 64, unique=True, index='sctname')
    selected_icon = Optional(str, 255, nullable=True)
    unselected_icon = Optional(str, 255, nullable=True)
    bg_color = Optional(str, 8, nullable=True)
    ordinal = Optional(int, default=0)
    shops = Set('Shop')

class Shop(db.Entity):
    _table_ = 'Shop'
    id = PrimaryKey(UUID, auto=True)
    title = Required(str, 64, index='sptitle')
    title_updated_at = Optional(datetime)
    description = Optional(LongStr, nullable=True, sql_type='text')
    code = Required(str, 16, index='spcode')  # HKAAAAA
    icon = Optional(str, 255, nullable=True)
    pic = Optional(str, 255, nullable=True)
    user_id = Required(UUID, index='spuid')
    user_account = Required(str, 64, index='spuact')
    shipment = Required(Json, default="{\'郵政\': true, \'順豐速運\': true}")
    phone = Optional(str, 16, nullable=True)
    phone_on = Optional(bool, default=False)
    email = Optional(str, 64, nullable=True) # default = User的email
    email_on = Optional(bool, default=False)
    facebook_on = Optional(bool, default=False)
    instagram_on = Optional(bool, default=False)
    categorys = Set(ShopCategory)
    addresses = Set('ShopAddress')
    bank_accounts = Set('ShopBankAccount')
    products = Set('Product')
    followers = Set('ShopFollower')
    analytics = Set('ShopAnalytics')
    browses = Set('ShopBrowsed')
    notifications = Set('NotificationHistory')
    wallet = Optional('Wallet', lazy=True)
    sponsor = Set('Sponsor')
    created_at = Required(datetime)
    updated_at = Optional(datetime)
    is_deleted = Optional(bool, default=False)

class ShopBankAccount(db.Entity):
    _table_ = 'ShopBankAccount'
    shop_id = Required(Shop)
    bank_name = Required(str, 64)
    bank_code = Required(str, 16)
    account_number = Required(str, 64)
    account_name = Required(str, 32)
    is_default = Optional(bool, default=True)

class ShopAddress(db.Entity):
    _table_ = 'ShopAddress'
    shop_id = Required(Shop)
    name = Required(str, 32)
    country_code = Required(str, 8)
    phone = Required(str, 16)
    area = Required(str, 16)
    district = Required(str, 16)
    road = Required(str, 32)
    rd_number = Required(str, 16)
    floor = Optional(str, 8, nullable=True)
    room = Optional(str, 8, nullable=True)
    extra = Optional(str, 32)
    addr_on = Optional(bool, default=False)
    is_default = Optional(bool, default=True)

class Product(db.Entity):
    _table_ = 'Product'
    id = PrimaryKey(UUID, auto=True)
    name = Required(str, 128, index='pdname')
    description = Optional(LongStr, sql_type='text')
    code = Optional(str, 64, index='pdcode')  # shop_code + 大類碼 + 小類碼 +流水號  HKAAAAB-0101-OOOOO-規格號碼(ID)
    is_new = Optional(bool, default=True)  # 新品 or 二手品
    for_sale = Required(bool, default=False)  # 上架 yes or no
    is_deleted = Optional(bool, default=False)
    weight = Optional(int, default=0)
    length = Optional(int, default=0)
    width = Optional(int, default=0)
    height = Optional(int, default=0)
    pictures = Set('ProductPic')
    shop_id = Required(Shop)
    category_id = Optional('ProductCategory')
    stocks = Set('Stock')
    specs = Optional(Json)
    # {
    #   "color": ["blue", "red", "green"],
    #   "size": ["L", "M", "S"]
    # }
    price = Optional(int, default=0)
    qty = Optional(int, default=0)
    freights = Optional(Json)
    # [
    # {
    # " shipment": "郵政",
    # "freight": 100,
    # "on": true
    # },
    # {
    # " shipment": "順豐速運",
    # "freight": 90,
    # "on": true
    # }
    # ]
    long_leadtime = Optional(int, default=0)
    qty_sold = Optional(int, default=0)
    like = Set('ProductLike')
    analytics = Set('ProductAnalytics')
    browses = Set('ProductBrowsed')
    created_at = Required(datetime, default=datetime.now())
    updated_at = Optional(datetime)

class ProductCategory(db.Entity):
    _table_ = 'ProductCategory'
    id = PrimaryKey(int, auto=True)
    products = Set(Product)
    name = Required(str, 64, index='pdcname')
    selected_icon = Optional(str, 255)
    unselected_icon = Optional(str, 255)
    bg_color = Optional(str, 16)
    seq = Optional(int)
    sub_categories = Set('ProductCategory', reverse='parent_id')
    parent_id = Optional('ProductCategory', reverse='sub_categories')

class Stock(db.Entity):
    _table_ = 'Stock'
    id = PrimaryKey(int, auto=True)
    price = Required(int, default=0)
    qty = Required(int, default=0)
    spec = Optional(Json)
    # { 
    #   name_1: value,
    #   name_2: value
    # }
    product_id = Required(Product)

class ProductPic(db.Entity):
    _table_ = 'ProductPic'
    id = PrimaryKey(int, auto=True)
    src = Required(str, 255)
    is_cover = Optional(bool, default=False)
    product_id = Required(Product)


class ShoppingCart(db.Entity):
    _table_ = 'ShoppingCart'
    id = PrimaryKey(UUID, auto=True)
    user_id = Required(UUID)
    prod_id = Required(UUID)
    prod_name = Required(str, 128)
    prod_img = Required(str, 255)
    qty = Required(int, default=1)  # 購買數量
    price = Required(int)  # 商品單價
    spec = Optional(Json)
    shop_id = Required(UUID)
    shop_title = Optional(str, 64)
    shop_icon = Optional(str, 255)
    ship_by = Required(str)
    ship_info = Optional(str, 255)
    freight = Required(int)
    checked_out = Required(bool, default=False)  # 是否已結帳
    created_at = Required(datetime)
    updated_at = Optional(datetime)

# class ShoppingCart(db.Entity):
#     _table_ = 'ShoppingCart'
#     id = PrimaryKey(UUID, auto=True)
#     user_id = Required(UUID)
#     created_at = Required(datetime)
#     updated_at = Optional(datetime)
#     total_price = Required(int)
#     total_freight = Required(int)
#     payment = Optional(str)  # 付款方式
#     checked_out = Optional(bool, default=False)  # 是否已結帳付款
#     cart_items = Set('CartItem')

# class CartItem(db.Entity):
#     _table_ = 'CartItem'
#     id = PrimaryKey(UUID, auto=True)
#     cart_id = Required(ShoppingCart)
#     prod_id = Required(UUID)
#     prod_name = Required(str, 128)
#     prod_img = Required(str, 255)
#     qty = Required(int, default=1)  # 購買數量
#     price = Required(int)  # 商品單價
#     spec = Optional(Json)
#     shop_id = Required(UUID)
#     shop_title = Optional(str, 64)
#     shop_icon = Optional(str, 255)
#     ship_by = Optional(str)
#     ship_info = Optional(str, 255)
#     freight = Required(int)

class Order(db.Entity):
    _table_ = 'Order' 
    odr_no = PrimaryKey(str, 32)  # 訂單編號，按照訂單編號產生邏輯
    user_id = Required(UUID)  # 買家
    shop_id = Required(UUID)
    shop_title = Optional(str, 64)
    shop_icon = Optional(str, 255)
    # payment = Required(str)  # 付款方式
    total_price = Required(int)  # 訂單金額
    created_at = Required(datetime)
    leadtime = Required(int, default=3)  # 備貨天數 預設3天
    prod_img = Optional(str, 255)
    ship_by = Required(str)
    ship_info = Required(str, 255)  # 收件地址
    items = Set('OrderItem')
    # paid_at = Optional(datetime)  # 付款時間
    ship_at = Optional(date)  # 預計發貨日期
    process_id = Optional(str)
    txn_no = Required('Transaction')
    notifications = Set('NotificationHistory')

class OrderItem(db.Entity):
    _table_ = 'OrderItem'
    prod_id = Required(UUID)
    order_no = Required(Order)
    prod_name = Required(str, 128)
    prod_img = Required(str, 255)
    qty = Required(int)
    price = Required(int)
    spec = Optional(Json)
    freight = Required(int)
    PrimaryKey(prod_id, order_no)

class Transaction(db.Entity):
    _table_ = 'Transaction'
    txn_no = PrimaryKey(str)  # 對應藍新API回傳參數 MerchantOrderNo
    trade_no = Optional(str)  # 藍新金流交易序號 
    amount = Required(int)
    payment_agent = Optional(str)  # 金流方式, 藍新、PayPal
    payment_type = Optional(str)  # 支付方式, 信用卡、ATM
    created_at = Required(datetime)
    pay_time = Optional(datetime)  # 支付完成時間
    orders = Set(Order)    

class ShopFollower(db.Entity):
    _table_ = 'ShopFollower'
    shop_id = Required(Shop)
    user_id = Required(User)
    PrimaryKey(shop_id, user_id)

class ShopAnalytics(db.Entity): # 商店分頁資料
    _table_ = 'ShopAnalytics'
    shop_id = Required(Shop)
    user_id = Required(UUID)
    mode = Required(str)
    seq = Required(int)
    PrimaryKey(user_id, mode, seq)

class ProductAnalytics(db.Entity): # 商品分頁資料
    _table_ = 'ProductAnalytics'
    product_id = Required(Product)
    user_id = Required(UUID)
    mode = Required(str)
    seq = Required(int)
    PrimaryKey(user_id, mode, seq)

class SearchHistory(db.Entity): # 搜尋紀錄
    _table_ = 'SearchHistory'
    search_category = Required(str)
    keyword =  Required(str)
    created_at = Required(datetime, default=datetime.now())

class ProductLike(db.Entity):
    _table_ = 'ProductLike'
    user_id = Required(User)
    product_id = Required(Product)
    PrimaryKey(user_id, product_id)

class ShopBrowsed(db.Entity): # 店鋪瀏覽紀錄 
    _table_ = 'ShopBrowse'
    id = PrimaryKey(int, size=64, auto=True)
    user_id = Optional(UUID)
    shop_id = Required(Shop)
    created_at = Required(datetime, default=datetime.now())

class ProductBrowsed(db.Entity): # 商品瀏覽紀錄
    _table_ = 'ProductBrowse'
    id = PrimaryKey(int, size=64, auto=True)
    user_id = Optional(UUID)
    product_id = Required(Product)
    created_at = Required(datetime, default=datetime.now())

class NotificationMessage(db.Entity): # 通知訊息模板
    _table_ = 'NotificationMessage'
    id = PrimaryKey(int, auto=True)
    identity = Required(str) # 通知對象的身分
    code = Required(int) # 訊息代號
    notify_body = Required(str)
    notify_title = Required(str)
    history = Set('NotificationHistory')

class NotificationHistory(db.Entity):
    _table_ = 'NotificationHistory'
    id = PrimaryKey(int, size=64, auto=True)
    message = Required(NotificationMessage)
    odr_no = Optional(Order)
    user_id = Optional(User)
    shop_id = Optional(Shop)
    content = Required(str)
    is_click = Required(bool, default=False)
    created_at = Required(datetime, default=datetime.now())

class Wallet(db.Entity):
    _table_ = 'Wallet'
    id = PrimaryKey(UUID, auto=True)
    shop_id = Required(Shop)
    balance = Required(Decimal, default=0)
    is_active = Required(bool, default=True)
    histories = Set('WalletHistory')
    charges = Set('WalletCharge')
    sponsor_orders = Set('SponsorOrder')
    created_at = Required(datetime, default=datetime.now())
    updated_at = Optional(datetime)

class WalletHistory(db.Entity):
    _table_ = 'WalletHistory'
    wallet_id = Required(Wallet)
    charge_no = Optional('WalletCharge')
    sponsor_number = Optional('SponsorOrder')
    description = Optional(str)

class WalletCharge(db.Entity):
    _table_ = 'WalletCharge'
    charge_no = PrimaryKey(str, 32)
    wallet_id = Required(Wallet)
    amount = Required(Decimal)
    history = Required(WalletHistory)
    paid_at = Optional(datetime)  # 付款時間
    payment = Required(str)  # 付款方式
    process_id = Optional(str)
    created_at = Required(datetime, default=datetime.now())

class SponsorLevel(db.Entity):
    _table_ = 'SponsorLevel'
    id = PrimaryKey(int, auto=True)
    description = Required(str)
    price = Required(Decimal)
    identity = Required(str) # 買家(buyer) 或 店家(shop)
    probability = Optional(Decimal) # 瀏覽顯示機率
    sponsors = Set('Sponsor')
    sponsor_orders = Set('SponsorOrder')

class Sponsor(db.Entity):
    _table_ = 'Sponsor'
    id = PrimaryKey(int, auto=True)
    shop_id = Optional(Shop)
    user_id = Optional(User)
    sponsor_level = Required(SponsorLevel) # 贊助等級
    probability = Optional(Decimal) # 瀏覽顯示機率
    background_is_show = Required(bool, default=True) # 背景
    badge_is_show = Required(bool, default=True) # 徽章
    frame_is_show = Required(bool, default=True) # 外框?
    sponsor_order = Required("SponsorOrder") # 贊助訂單
    expired_at = Required(datetime, index='expiry', default=datetime.today() - timedelta(days=1) + relativedelta(months=1))

class SponsorOrder(db.Entity):
    _table_ = 'SponsorOrder'
    sponsor_number = PrimaryKey(str)
    wallet_id = Optional(Wallet)
    user_id = Optional(User)
    sponsor_level = Required(SponsorLevel) # 贊助等級
    sponsor = Optional(Sponsor)
    wallet_history = Optional(WalletHistory)
    paid_at = Optional(datetime)
    payment = Required(str) # 付款方式
    process_id = Optional(str)
    created_at = Required(datetime, default=datetime.now())

db.generate_mapping(create_tables=False)
set_sql_debug(debug_mode)
