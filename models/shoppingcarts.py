from uuid import UUID
from datetime import datetime
import pony.orm as pny
from models.entities import ShoppingCart

# @pny.db_session
# def createShoppingcart(user_id: str):
#     cart = ShoppingCart(user_id=UUID(user_id), created_at=datetime.now(), updated_at=datetime.now(), total_freight=0, total_price=0)
#     return cart

# @pny.db_session
# def updateShoppingcart(cart_id: str, **kwargs):
#     cart = ShoppingCart[UUID(cart_id)].set(**kwargs)
#     return cart

# @pny.db_session
# def getShoppingcartAllItems(cart_id: str=None):
#     if ShoppingCart.exists(id=cart_id):
#         cart = ShoppingCart[UUID(cart_id)]
#         cart.cart_items.load()
#         return cart
#     else:
#         return False    

@pny.db_session
def getShoppingcartUserId(user_id: str): # checked_out = False
    return ShoppingCart.select(lambda c: c.user_id==UUID(user_id) and c.checked_out==False)[:]
   

@pny.db_session
def addShoppingcartItem(**kwargs):
    uid = kwargs.get('user_id')
    pid = kwargs.get('prod_id')
    price = kwargs.get('price')
    spec = kwargs.get('spec')
    item = ShoppingCart.select(lambda c: c.user_id==uid and c.prod_id==pid and c.spec==spec).get()
    if not item: 
        item = ShoppingCart(**kwargs)
    else:
        item.qty+=1       
        item.price+=price
    return item