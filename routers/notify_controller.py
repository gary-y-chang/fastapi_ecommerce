from re import template
from fastapi import APIRouter
from auth import Auth
from models import notify
from uuid import UUID

router = APIRouter(
    prefix="/notify",
    tags=["Notify"]
)

auth = Auth()

tag_meta = {
    'name': 'Notify',
    'description': 'FCM、In App通知',
}

# @router.get('')
# async def test_notify(identity:str, code:int, ord_no: str):
#     notify.getFCMMessaging(identity=identity,code=code,ord_no=ord_no)
#     return {}

@router.get('/fcm-message')
async def fcm_message(identity:str, code:int, odr_no: str):
    result,template = notify.getOrderNotification(identity=identity,code=code,odr_no=odr_no)
    return {**result.to_dict(),**template.to_dict(only=['notify_title'])}

@router.post('/order')
async def create_order_notification(identity:str, code:int, odr_no: str):
    result,template = notify.createOrderNotification(identity=identity,code=code,odr_no=odr_no)

    return {**result.to_dict(),**template.to_dict(only=['notify_title'])}

@router.patch('/{notify_id}', name='更新通知的點擊狀態')
async def update_is_clicked(notify_id,is_click: bool):
    result = notify.updateNotification(notify_id,is_click=is_click)
    return result.to_dict()

@router.get('/buyer')
async def get_buyer_notification(user_id: UUID):
    return [ x.to_dict() for x in notify.getNotificationByUser(user_id) ]

@router.get('/shop')
async def get_shop_notification(shop_id: UUID):
    return [ x.to_dict() for x in notify.getNotificationByShop(shop_id)]