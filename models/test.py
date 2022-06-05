import pony.orm as pny
from uuid import uuid4, UUID
from datetime import datetime
from pony.orm.core import select, desc
from entities import *
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
from base64 import b64encode, b64decode
from Crypto.Hash import SHA256

import json

# data = b"secret"
data = b"MerchantID=MS329717003&RespondType=JSON&TimeStamp=1643414863&Version=2.0&MerchantOrderNo=202201290001&Amt=299&ItemDesc=testing-product&Email=garychang@times-transform&LoginType=0&NotifyURL=http://d2f3-1-175-216-17.ngrok.io/shopping/pay/notify&CREDIT=1&WEBATM=1&VACC=1"
# key = get_random_bytes(16)
key = b"VZdpeJmunJU6jdGbz6tpMwSgmuHDF0O6"
iv = b"C1oyruhKj3nwHPsP"


print('key > ', key)
cipher = AES.new(key, AES.MODE_CBC, iv)
ct_bytes = cipher.encrypt(pad(data, AES.block_size))
iv = b64encode(cipher.iv).decode('utf-8')
ct = b64encode(ct_bytes).decode('utf-8')
# result = json.dumps({'iv':iv, 'ciphertext':ct})
print("TradeInfo >> ", ct)

trade_sha = "HashKey=VZdpeJmunJU6jdGbz6tpMwSgmuHDF0O6&"+ ct +"&HashIV=C1oyruhKj3nwHPsP"
hash = SHA256.new()
hash.update(trade_sha.encode())
print("TradeSha >> ",hash.hexdigest().upper())

print('timestamp --> ', datetime.utcnow().timestamp())
print('timestamp --> ',  'BUY'+ str(datetime.now().timestamp()*1000))

# try:
#     b64 = json.loads("{\"iv\": \"QzFveXJ1aEtqM253SFBzUA==\", \"ciphertext\": \"TxDjAZuxjmfHn0SbEoQQXQ==\"}")
#     # iv = b64decode(b64['iv'])
#     iv = b"C1oyruhKj3nwHPsP"
#     ct = b64decode(b64['ciphertext'])
#     print(iv, ct)
#     cipher = AES.new(key, AES.MODE_CBC, iv)
#     pt = unpad(cipher.decrypt(ct), AES.block_size)
#     print("The message was: ", pt.decode('utf-8'))
# except (ValueError, KeyError):
#     print("Incorrect decryption")


@pny.db_session
def getAllUsers():
    users = pny.select(u for u in User)[:]
    print(type(users))
    return users


@pny.db_session
def getUserById():
    return User[UUID('5ea0c7fd-92ad-4fa0-9f4f-ea82e7abd996')]      

@pny.db_session
def addUser():
    u = User(id=uuid4(), email='gary@gmai.com', password='1234', created_at=datetime.now())

@pny.db_session
def getUserByEmailAndPasswd(email: str, password: str):
    u = User.select(lambda u: u.email==email and u.password==password).first()
    return u  

@pny.db_session
def addShopBankAccount():
    s = Shop.get(title='麥味登')
    return ShopBankAccount(shop_id=s, bank_name='City Bank', bank_code='898', account_name='Lee Beuce', account_number='000100898742')

@pny.db_session
def getShop():
    # s = Shop.get(title='麥味登')
    # s.bank_accounts.load()
    s = Shop.select(lambda x: x.title=='麥味登')
    return s.get()

@pny.db_session
def getAllCategorys():
    s = select(s for s in Shop).order_by(desc(Shop.code)).first()
    return s
    # return ShopCategory.select()[:]

@pny.db_session
def getProduct(prod_id: str):
    p = Product[UUID(prod_id)]
    p.pictures.load()
    p.category_id.load()
    p.shop_id.load()
    p.stocks.load()
    return p

@pny.db_session
def getShopsByCategory(cate_id: int):
    shop_cate = ShopCategory[cate_id]
    shops = [shop for shop in shop_cate.shops]
    for s in shops:
        print(type(s), s.title)
    return shops

@pny.db_session
def createProductCategory(parent_id=None, **kwargs):
    if parent_id == None:
        return ProductCategory(**kwargs)
    else:
       parent = ProductCategory[parent_id]
       return ProductCategory(parent_id=parent, **kwargs)    

@pny.db_session
def getProductCategory(parent_id=None):
    if parent_id == None:
        return [c for c in select(c for c in ProductCategory if c.parent_id==None)[:]]
    else:
        return [sub for sub in ProductCategory[parent_id].sub_categories]

@pny.db_session
def createProduct(shop_id: str, **kwargs):
    return Product(shop_id=UUID(shop_id), **kwargs)

@pny.db_session
def addProductPic(src,is_cover,product_id):
    p = ProductPic(src=src,is_cover=is_cover,product_id=product_id)
    return p

@pny.db_session
def getProductPic(product_id):
    pd = Product[UUID(product_id)]    
    print(pd.name)
    pd.pictures.load()

    img = filter(lambda p: p.is_cover==True, pd.pictures)
    return list(img)

# @pny.db_session
# def getStockBySpec():
#     # Product.select(lambda p: p.info['display']['size'] > 5)
#     # s = Stock.select(lambda s: s.spec['型號']=='豪華型')
#     # print(type(s), s.get())
#     item = CartItem[UUID('89e0f446-31df-4ec2-87f2-85e77c3e071c'), UUID('fd20fb19-29e4-418c-874d-51ca665fbe9e')]
#     print(item.prod_name, item.spec)


@pny.db_session
def createOrder(odr_dict, item_dict):
    shop_code = Shop[UUID(odr_dict['shop_id'])].code
    yyyymmdd = datetime.now().strftime("%Y%m%d")

    q = select(o for o in Order if o.odr_no.startswith(shop_code+yyyymmdd)).count()
    odr_no = shop_code + yyyymmdd + str(q+1).zfill(5)
    print('count:', odr_no)
    odr_dict['odr_no'] = odr_no
    order = Order(**odr_dict)
    
    item_dict['order_no'] = odr_no
    odr_item =OrderItem(**item_dict)

    order.items.add(odr_item)
    return order
    # prod_id = Required(UUID)
    # order_no = Required(Order)
    # prod_name = Required(str, 128)
    # prod_img = Required(str, 255)
    # qty = Required(int)
    # price = Required(int)
    # spec = Optional(Json)
    # freight = Required(int)
   
@pny.db_session
def getShoppingcartUserId(user_id: str): # checked_out = False
    cart_items = ShoppingCart.select(lambda c: c.user_id==UUID(user_id) and c.checked_out==False)[:]
    # return [ i.to_dict() for i in cart_items ]
    return cart_items

# items = getShoppingcartUserId('269e1495-e246-4106-ae48-71f7c9a78371')
# for i in items:
#     print(i.id, i.prod_name, i.ship_by)

# ordict = {}
# # ordict['odr_no']='HKAAAABB2021110300002'
# ordict['user_id']='5a093ae0-ff0a-42b8-b4f6-4a505f95af97'
# ordict['cart_id']='88680cdd-38a1-48e6-a587-d35818efaa60'
# ordict['shop_id']='d251602d-86da-4186-934a-582d57dd1266'
# ordict['shop_title']='Play'
# ordict['payment']='PayPal'
# ordict['total_price']=120
# ordict['created_at']= datetime.now()
# ordict['leadtime']=3
# ordict['ship_by']='郵政'
# ordict['ship_info']='灣仔'
# ordict['process_id']='qwertoasd-12'

# item_dict = {}
# item_dict['prod_id'] = 'a7704919-b3b4-4817-9672-dab424ebbe8e'
# item_dict['prod_name'] = '潮牌背包'
# item_dict['prod_img'] = 'storage.com'
# item_dict['qty'] = 1
# item_dict['price'] = 25
# item_dict['spec'] = [{"品種": "蕨類"}, {"尺寸": "微型"}]
# item_dict['freight'] = 80

# ord = createOrder(ordict, item_dict)
# print(ord)

# now = datetime.now().strftime("%Y%m%d")
# print(now)

# img_list = getProductPic('86273445-7c83-430a-a446-f780cc66cfac')
# print(img_list[0].src)

# cart = getShoppingcartInUseByUserId('5a093ae0-ff0a-42b8-b4f6-4a505f95af97')
# print(cart.id)

# p = getProduct('d7d4e29c-94d9-41ad-ba74-8e42888ddef4')
# print(p.name, p.shop_id.id, p.shop_id.title)
# cover = lambda i: i==0
# pic = addProductPic(src='http://storage.google/test', is_cover=cover(1), product_id='86273445-7c83-430a-a446-f780cc66cfac')
# print('pictur id: ', pic.id)

# s = getAllCategorys()
# print(s.title, s.code)

# code = 'HK'+shop_code_generator('BBBBE')
# print(code)
# cates = getAllCategorys()
# for c in cates:
#     print(c.id, c.name)




print('--- done ---')


 