from os import name
from re import split
import pony.orm as pny
from pony.orm.core import select, desc
from models.entities import Shop, ShopCategory, ShopAddress, ShopBankAccount, User, Sponsor
from uuid import UUID
from datetime import datetime
from routers.util import shop_code_generator


@pny.db_session
def createShopCategory(**kwargs):
    return ShopCategory(**kwargs)

@pny.db_session
def getAllCategorys():
    return [ category.to_dict() for category in ShopCategory.select()[:] ]

@pny.db_session
def getShop(shop_id:UUID): # merchant view
    s = Shop.get(id=shop_id)
    now = datetime.now()
    if s:
        data = s.to_dict(with_lazy=True,with_collections=True)
        sp = pny.select(sp for sp in s.sponsor if sp and sp.expired_at>now)[:]
        if sp:
            sp = sp[0].to_dict(only=['sponsor_level','background_is_show','badge_is_show','frame_is_show'])
        else:
            sp = {'sponsor_level':None,'background_is_show':False,'badge_is_show':False,'frame_is_show':False}
        data.update(sp)
        return data
    return s

@pny.db_session
def createShop(icon_url:str = None, **kwargs):
    cate_id_list = kwargs.get('cate_ids').split(',')
    uid = kwargs.get('user_id')
    user = User[UUID(uid)]
    user.user_no = user.user_no+'S'
    actname = user.email.split('@')[0]
    user_phone = kwargs.get('phone')
    # if user.user_detail:
    #     actname = user.user_detail.account_name
    #     user_phone = user.user_detail.phone

    new_code = 'HKAAAAA'    
    s = select(s for s in Shop).order_by(desc(Shop.code)).first()
    if s: 
        new_code = 'HK'+ shop_code_generator(s.code[2:])
    
    shop = Shop(title=kwargs.get('title'), user_id=UUID(uid), user_account=actname, shipment={'郵政': True, '順豐速運': True},
        icon=icon_url, code=new_code, created_at=datetime.now(), phone=user_phone, email=user.email)
    
    for cid in cate_id_list:
        shop.categorys.add(ShopCategory[int(cid)])
    
    addr = ShopAddress(shop_id=shop, name=kwargs.get('name'), country_code=kwargs.get('country_code'), phone=kwargs.get('phone'), area=kwargs.get('area'),
        district=kwargs.get('district'), road=kwargs.get('road'), rd_number=kwargs.get('rd_number'), is_default=True)
    shop.addresses.add(addr)   
    
    bank = ShopBankAccount(shop_id=shop, bank_name=kwargs.get('bank_name'), bank_code=kwargs.get('bank_code'), 
        account_number=kwargs.get('account_number'), account_name=kwargs.get('account_name'))
    shop.bank_accounts.add(bank)
   
    return shop.id

@pny.db_session
def getShopCodeById(shop_id: str):
    return Shop[UUID(shop_id)].code

@pny.db_session
def getShopsByUserId(user_id: str):
    return [ s.to_dict(with_collections=True,with_lazy=True) for s in Shop.select(lambda s: s.user_id == UUID(user_id) and s.is_deleted == False)[:] ]

@pny.db_session
def getShopsByCategory(cate_id: int):
    shop_cate = ShopCategory[cate_id]
    shops = [shop.to_dict() for shop in shop_cate.shops]
    # for s in shops:
    #     print(type(s), s.title)
    
    return shops
        
@pny.db_session
def addShop(shop: dict):
    categories = shop.pop('categorys')
    shop_address = shop.pop('addresses')
    shop_bank_account = shop.pop('bank_accounts')
    s1 = Shop(**shop)
    for cid in categories['id']:
        s1.categorys.add(ShopCategory[cid])
    shop_address['shop_id'] = str(s1.id)
    ShopAddress(**shop_address)
    shop_bank_account['shop_id'] = str(s1.id)
    ShopBankAccount(**shop_bank_account)
    return str(s1.id)

@pny.db_session
def updateShop(shop: dict):
    id = shop.pop('id')
    s1 = Shop[id]
    s1.set(**shop)
    return s1.to_dict(with_lazy=True,with_collections=True)

@pny.db_session
def getShopCategorys(shop_id: str):
    return [ c.to_dict() for c in pny.select(c for s in Shop for c in s.categorys)[:] ]

@pny.db_session
def setCategorys(shop_id:str, categories: dict):
    s1 = Shop[shop_id]
    for c in s1.categorys:
        if c.id not in categories['id']:
            s1.categorys.remove(ShopCategory[c.id])
    for cid in categories['id']:
        t = ShopCategory[cid]
        if t not in s1.categorys:
            s1.categorys.add(t)

@pny.db_session
def getBankAccounts(shop_id: str):
    accounts = ShopBankAccount.select(lambda d: d.shop_id.id == UUID(shop_id)).order_by(lambda d: pny.desc(d.is_default))[:]
    return [ a.to_dict() for a in accounts ]

@pny.db_session
def createBankAccounts(shop_id: str, bank_accounts: list):
    r = []
    for data in bank_accounts:
        r.append(ShopBankAccount(shop_id=shop_id, **data.dict()).to_dict())
    return r

@pny.db_session
def defaultBankAccounts(id: str):
    b1 = ShopBankAccount[id]
    for b in ShopBankAccount.select(lambda d: d.shop_id.id==b1.shop_id.id and d.is_default==True):
        b.is_default=False
    b1.set(is_default=True)

@pny.db_session
def deleteBankAccounts(ids: list):
    t_ids = [int(id) for id in ids]
    ShopBankAccount.select(lambda b: b.id in t_ids).delete(bulk=True)
    
@pny.db_session
def getShopByCol(**kwargs):
    return Shop.get(**kwargs)

@pny.db_session
def getAddresses(shop_id: str):
    return [ a.to_dict() for a in ShopAddress.select(lambda a: a.shop_id.id == UUID(shop_id)).order_by(lambda d: pny.desc(d.is_default))[:]]

@pny.db_session
def createAddresses(shop_id: str, addresses: list):
    r = []
    for addr in addresses:
        r.append(ShopAddress(shop_id=shop_id, **addr.dict()).to_dict())
    return r

@pny.db_session
def updateAddresses(id: str, address_data: dict):
    a1 = ShopAddress[id]
    # set this shop's addresses to not default
    if 'is_default' in address_data and address_data['is_default']:
        for address in ShopAddress.select(lambda a: a.shop_id==a1.shop_id and a.is_default==True):
            address.is_default=False
    a1.set(**address_data)
    return a1.to_dict()

@pny.db_session
def defaultAddresses(id:str):
    default = ShopAddress[id]
    for address in ShopAddress.select(lambda a: a.shop_id==default.shop_id and a.is_default==True):
        address.is_default=False
    default.set(is_default=True)
    
@pny.db_session
def deleteAddresses(ids: list):
    t_ids = [int(id) for id in ids]
    ShopAddress.select(lambda a: a.id in t_ids).delete(bulk=True)
    ShopAddress.select(lambda a: a.id in t_ids).delete(bulk=True)
