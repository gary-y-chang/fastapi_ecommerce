from operator import truediv
import pony.orm as pny
from pony.orm.core import select
from uuid import uuid4, UUID
from datetime import datetime
from models.entities import ProductLike, ShopAnalytics, User, UserAddress, UserDetail, ShopFollower, Shop, Product
from random import choice as r_choice
from math import floor

@pny.db_session
def getAllUsers():
    users = pny.select(u for u in User)[:]
    print(type(users))
    return [ u.to_dict() for u in users ]

@pny.db_session
def getUserById(user_id: str):
    return User[UUID(user_id)].to_dict()

@pny.db_session
def getUserByEmail(email: str):
    return User.select(lambda u: u.email==email).first()
    
@pny.db_session
def getUserByCol(**kwargs):
    return User.get(**kwargs)

@pny.db_session
def updateUser(user_id: str, **kwargs):
    return User[user_id].set(**kwargs)

@pny.db_session
def addUser(mail, passwd):
    yyyymmdd = datetime.now().strftime("%Y%m%d")
    c = select(u for u in User if u.user_no.startswith(yyyymmdd)).count()
    user_no = yyyymmdd + str(c+1).zfill(4)
    u = User(email=mail, password=passwd, user_no=user_no, created_at=datetime.now())
    return str(u.id)

@pny.db_session
def addUserSocial(**kwargs):
    kwargs['id'] = uuid4()
    if kwargs['account_type'] == 'google':
        attr = 'google_id'
    elif kwargs['account_type'] == 'fb':
        attr = 'fb_id'
    elif kwargs['account_type'] == 'apple':
        attr = 'apple_id'
    kwargs[attr] = kwargs['account_id']
    kwargs.pop('account_id')
    kwargs.pop('account_type')
    seed = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+'
    pwd = ''.join([r_choice(seed) for i in range(91)])
    kwargs['password'] = pwd
    kwargs['created_at'] = datetime.utcnow()
    u = User(**kwargs)
    return str(u.id)

@pny.db_session
def addUserDetail(**kwargs):
    return UserDetail(**kwargs).to_dict()

@pny.db_session
def updateUserDetail(user_id: str, **kwargs):
    u = UserDetail[user_id]
    u.set(**kwargs)
    return u.to_dict()

@pny.db_session
def getUserDetail(user_id):
    return UserDetail.get(user_id=User[user_id]).to_dict()

@pny.db_session
def addUserAddress(**kwargs):
    data = {**kwargs}
    if 'receiver' not in data or not data.get('receiver'):
        try:
            user_detail = UserDetail.get(user_id=data.get('user_id'))
            receiver = user_detail.account_name
            if not receiver:
                receiver = user_detail.first_name + user_detail.last_name
        except AttributeError: # when UserDetail return None type object
            user = User[data.get('user_id')]
            receiver = user.email.split('@',1)[0]
        data['receiver'] = receiver
    if 'receiver_call' not in data or not data.get('receiver_call'):
        user_detail = UserDetail.get(user_id=data.get('user_id'))
        data['receiver_call'] = user_detail.phone

    return UserAddress(**data).to_dict()

@pny.db_session
def updateUserAddress(id, **kwargs):
    return UserAddress[id].set(**kwargs)

@pny.db_session
def getUserAddressByUser(user_id):
    u = User[user_id]
    return [ a.to_dict() for a in pny.select(a for a in UserAddress if a.user_id==u)[:] ]

@pny.db_session
def deleteUserAddress(id,user_id):
    return UserAddress.get(id=id,user_id=user_id).delete()
    
@pny.db_session
def addShopFollower(user_id: UUID, shop_id: UUID):
    return ShopFollower(user_id=user_id, shop_id=shop_id)

@pny.db_session
def deleteShopFollower(user_id: UUID, shop_id: UUID):
    return ShopFollower[Shop[shop_id],User[user_id]].delete()

@pny.db_session
def getFollowShopList(user_id: UUID,keyword: str=''):
    u = User[user_id]
    shop = pny.select( 
        (
            f.shop_id.id,
            f.shop_id.title,
            f.shop_id.icon,
            pny.count(f.shop_id.followers),
            pny.group_concat(pic.src)
        ) for f in ShopFollower for s in f.shop_id for p in s.products for pic in p.pictures 
        if f.user_id==u and not s.is_deleted and not p.is_deleted and p.for_sale and pic.is_cover and keyword in f.shop_id.title)[:]
    # 關注人數
    # 評分
    # 評分總數
    # 是否已關注
    # 3張 產品圖片
    return shop

@pny.db_session
def likeProduct(user_id: UUID, product_id: UUID):
    return ProductLike(user_id=user_id, product_id=product_id)

@pny.db_session
def dislikeProduct(user_id: UUID, product_id: UUID):
    return ProductLike[User[user_id],Product[product_id]].delete()

@pny.db_session
def getLikeProduct(user_id:UUID):
    now = datetime.now()
    u = User[user_id]
    all_products = pny.left_join(
        (
            # p.name,
            # p.price,
            # p.specs,
            # p.created_at,
            p,
            pic.src,
            pny.min(stock.price),
            pny.max(stock.price),
            s,
            pny.count(p.like),
            pny.count(l for l in p.like if l.user_id == User[user_id]),
        ) for l in ProductLike for p in l.product_id for stock in p.stocks for pic in p.pictures for s in p.shop_id 
        if l.user_id==u and p.for_sale and not p.is_deleted and not p.shop_id.is_deleted and pic.is_cover and not s.is_deleted
    ).order_by(pny.raw_sql('''p.name'''))[:]
    sponsor_products = list(pny.left_join(
            (p,sp) for l in ProductLike for p in l.product_id for s in p.shop_id for sp in s.sponsor 
            if l.user_id==u and p.for_sale and not p.is_deleted and not s.is_deleted and not s.sponsor.is_empty() and sp.expired_at>now
        ).order_by(lambda p,sp: p.name)[:])
    data = []
    for p_data in all_products:
        t_data = {
            **p_data[0].to_dict(only=['id','name','price','specs']),
            'cover':p_data[1],
            'min_price':p_data[2],
            'max_price':p_data[3],
            **p_data[4].to_dict(only=['title','user_id']),
            'like_count':p_data[5],
            'is_like':p_data[6]
        }
        t_data['has_spec'] = True if t_data.pop('specs') else False
        if len(sponsor_products)!=0 and p_data[0] == sponsor_products[0][0]:
            t_data.update(sponsor_products[0][1].to_dict(only=['sponsor_level','background_is_show','badge_is_show','frame_is_show']))
            del sponsor_products[0]
        else:
            t_data['sponsor_level'] = None
            t_data['background_is_show'] = False
            t_data['badge_is_show'] = False
            t_data['frame_is_show'] = False
        data.append(
            t_data
        )

    return data
