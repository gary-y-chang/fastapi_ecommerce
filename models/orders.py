import pony.orm as pny
from pony.orm.core import select
from datetime import datetime
from uuid import UUID
from typing import List
from models.entities import Shop, Order, OrderItem

@pny.db_session
def getOrderNo(shop_id: str):
    shop_code = Shop[UUID(shop_id)].code
    yyyymmdd = datetime.now().strftime("%Y%m%d")
    c = select(o for o in Order if o.odr_no.startswith(shop_code+yyyymmdd)).count()
    odr_no = shop_code + yyyymmdd + str(c+1).zfill(5)
    print('count:', odr_no)
    return odr_no    

@pny.db_session
def createOrder(odr_dict, items: List[dict]):
    # shop_code = Shop[UUID(odr_dict['shop_id'])].code
    # yyyymmdd = datetime.now().strftime("%Y%m%d")

    # q = select(o for o in Order if o.odr_no.startswith(shop_code+yyyymmdd)).count()
    # odr_no = shop_code + yyyymmdd + str(q+1).zfill(5)
    # print('count:', odr_no)
    # odr_dict['odr_no'] = odr_no
    order = Order(**odr_dict)
    
    for item_dict in items:
        item_dict['order_no']=order.odr_no
        odr_item = OrderItem(**item_dict)
        order.items.add(odr_item)

    # item_dict['order_no'] = order.odr_no
    # odr_item = OrderItem(**item_dict)
    # order.items.add(odr_item)
    return order
