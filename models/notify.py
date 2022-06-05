import pony.orm as pny
from models.entities import NotificationHistory, NotificationMessage, Order, User, Shop
import sys
from uuid import UUID
from datetime import datetime,timedelta

@pny.db_session
def getOrderNotification(identity:str, code:int, odr_no:str):
    template = NotificationMessage.get(identity=identity, code=code)
    notification_history = NotificationHistory.get(odr_no=odr_no, message=template)
    return notification_history, template

@pny.db_session
def getNotificationByUser(user_id: UUID):
    history = NotificationHistory.select(lambda history: history.user_id==User[user_id])
    return history
@pny.db_session
def getNotificationByShop(shop_id: UUID):
    history = NotificationHistory.select(lambda history: history.shop_id==Shop[shop_id])
    return history

@pny.db_session
def firebaseCloudMessagingMapping(identity:str, code: int, **kwargs):
    template = NotificationMessage.get(identity=identity, code=code)
    mapping_tool = FCMMappingTool(template.notify_body, **kwargs)
    
    # order = Order.get(process_id=process_id) # business_key?
    # buyer = order.user_id
    for tag in mapping_tool.getTags(template.notify_body):
        mapping_tool.func.get(tag)
    return mapping_tool.content

@pny.db_session
def createOrderNotification(identity:str, code:int, odr_no:str):
    template = NotificationMessage.get(identity=identity, code=code)
    mapping_tool = FCMMappingTool(template.notify_body, odr_no=odr_no)
    notify_content = mapping_tool.content
    notify = NotificationHistory(
        message=template,
        odr_no=mapping_tool.Order,
        user_id=mapping_tool.User,
        shop_id=mapping_tool.Shop,
        content=notify_content
    )
    return notify, template

@pny.db_session
def updateNotification(id, **kwargs):
    notify = NotificationHistory[id]
    notify.set(**kwargs)
    return notify

class FCMMappingTool:
    '''
    Available To Use:
        order_number        =>  訂單編號
        product             =>  商品名稱
        ship_by             =>  透過<ship_by>發貨
        ship_at             =>  請於<ship_at>前完成發貨

    To Be Done:
        buyer               =>  買家名稱
        paid_at             =>  付款時間
        ship_number         =>  寄件編號
        退貨退款日期
        贊助編號
        贊助失效日期
    '''
    TAG_START = '<'
    TAG_END = '>'
    DATE_FORMAT = '%d/%m/%Y' # DD/MM/YYYY
    def __init__(self, content:str, odr_no: UUID=None, user_id: UUID=None, shop_id: UUID=None, **kwargs):
        self.content = content
        self.Order = kwargs.get('Order')
        self.odr_no = odr_no
        self.User = kwargs.get('User')
        self.user_id = user_id
        self.Shop = kwargs.get('Shop')
        self.shop_id = shop_id
        # function to replace template's TAG
        self.func = {
            'order_number': self.order_number,
            'buyer': self.buyer,
            'ship_by': self.ship_by,
            'ship_at': self.ship_at,
        }
        self.replace_tags()
    def _decorate(self, s:str):
        return self.TAG_START+s+self.TAG_END
    def _getTags(self, s:str):
        pos = []
        for i in range(len(s)):
            c = s[i]
            if c == self.TAG_START:
                pos.append(i+1)
            elif c== self.TAG_END:
                pos.append(i)
        return [s[start:end]for start, end in zip(pos[0::2], pos[1::2])]
    def _autoDefined(self, **kwargs):
        for table_name,val in kwargs.items():
            if not eval('isinstance(self.{},{})'.format(table_name,table_name)):
                if val!=None:
                    eval('setattr(self,"{}",{}["{}"])'.format(table_name,table_name,val))
                    # set related table (one-to-one)
                    if table_name == 'Order':
                        if not isinstance(self.User,User):
                            self.User = User[self.Order.user_id]
                        if not isinstance(self.Shop,Shop):
                            self.Shop = Shop[self.Order.shop_id]
                else:
                    raise Exception('self.{} not defined'.format(table_name))
    
    def replace_tags(self):
        tags = self._getTags(self.content)
        err_count = 0
        while len(tags)>0:            
            # self.func.get(tags[0])()
            # tags.pop(0)
            # err_count = 0
            try:
                self.func.get(tags[0])()
                tags.pop(0)
                err_count = 0
            except Exception as e:
                tags.append(tags.pop(0))
                err_count += 1
            if len(tags)>0 and err_count == len(tags):
                raise Exception(tags)
    def order_number(self):
        self._autoDefined(Order=self.odr_no)
        self.content = self.content.replace(self._decorate('order_number'),self.Order.odr_no)
    def buyer(self):
        self._autoDefined(User=self.user_id)
        if self.User.user_detail.account_name:
            buyer_name = self.User.user_detail.account_name
        elif self.User.user_detail.first_name or self.User.user_detail.last_name:
            buyer_name = (self.User.user_detail.first_name + ' ' + self.User.user_detail.last_name).strip()
        else:
            buyer_name = self.User.email.split('@',1)[0]
        self.content = self.content.replace(self._decorate('buyer'),buyer_name)
    def ship_by(self):
        self._autoDefined(Order=self.odr_no)
        self.content = self.content.replace(self._decorate('ship_by', self.Order.ship_by))
    def ship_at(self):
        self._autoDefined(Order=self.odr_no)
        self.content = self.content.replace(self._decorate('ship_at'), self.Order.ship_at.strftime(self.DATE_FORMAT))
