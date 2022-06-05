from fastapi import APIRouter,Response,status
from auth import Auth, Guard
from models import sponsor,wallet
from .req_models import SponsorJoinShop, SponsorJoinBuyer
from datetime import datetime
import httpx
from decouple import config
import json
from uuid import UUID
from http import HTTPStatus

config.encoding = 'utf-8'
camunda_api_url = config('CAMUNDA_API_URL')
camunda_sponsor_model = config('CAMUNDA_SPONSOR_MODEL')

router = APIRouter(
    prefix="/sponsor",
    tags=["Sponsor"]
)

auth = Auth()

tag_meta = {
    'name': 'Sponsor',
    'description': '贊助相關操作: 加入贊助、取得贊助身分',
}

@router.get('/level')
async def get_all_level():
    levels = sponsor.getSponsorLevel()
    return levels

@router.get(
    '/current-status',    
    responses={204: {
        "model": None,
        "description": "Successful Response With Null Data",
    }},
)
async def get_sponsor_status(user_id:UUID=None,shop_id:UUID=None):
    '''
        買家贊助給user_id\n
        店鋪贊助給shop_id
    '''
    if user_id:
        sp = sponsor.getSponsor(user_id=user_id)
    elif shop_id:
        sp = sponsor.getSponsor(shop_id=shop_id)
    if sp:
        return sp
    else:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post('/join/shop')
async def join_sponsor_shop(req_data:SponsorJoinShop):
    # 檢查餘額?
    # 成立訂單
    order = sponsor.createSponsorOrder(**req_data.dict(),paid_at=datetime.now())
    # 扣款
    w = wallet.deductWalletBySponsor(req_data.wallet_id, order['sponsor_level'])
    # start camunda process
    url = camunda_api_url + '/process-definition/key/' + camunda_sponsor_model + '/start'
    headers = {'Content-Type': 'application/json'}
    data = {
        "variables": {
            "wallet-id":{
                "value":str(w.id),
                "type":"String"
            },
            "payment":{
                "value":"wallet",
                "type":"String"
            }
        },
        "businessKey" : order['sponsor_number']
    }
    with httpx.Client() as client:
        response = client.post(url=url,headers=headers,json=data)
        json_data = json.loads(response.text)
    
    sponsor.updateSponsorOrder(order['sponsor_number'], process_id=json_data['id'])
    # create sponsor
    s = sponsor.createSponsor(sponsor_number=order['sponsor_number'],**req_data.dict())
    order = sponsor.getSponsorOrderByNumber(order['sponsor_number'])
    return order

@router.post('/join/buyer')
async def join_sponsor_buyer(req_data:SponsorJoinBuyer):
    # 成立訂單
    order = sponsor.createSponsorOrder(**req_data.dict())
    # start camunda process
    url = camunda_api_url + '/process-definition/key/' + camunda_sponsor_model + '/start'
    headers = {'Content-Type': 'application/json'}
    req_data = {
        "variables": {
            "user-id":{
                "value":str(order['user_id']),
                "type":"String"
            },
            "payment":{
                "value":"fps",
                "type":"String"
            }
        },
        "businessKey" : order['sponsor_number']
    }
    with httpx.Client() as client:
        response = client.post(url=url,headers=headers,json=req_data)
        json_data = json.loads(response.text)
    
    sponsor.updateSponsorOrder(order['sponsor_number'], process_id=json_data['id'])
    return order

@router.post('/join/buyer/set-payment-info')
async def set_payment_info(sponsor_number:str): # 輸入付款資訊
    # 設定 轉數快 付款資訊
    # ...
    # get sponsor order
    order = sponsor.getSponsorOrderByNumber(sponsor_number)
    # get task id by instance id
    url = camunda_api_url + '/task'
    headers = {'Content-Type': 'application/json'}
    params = {'processInstanceId': order['process_id']}
    with httpx.Client() as client:
        response = client.get(url=url,headers=headers,params=params)
        if response.status_code == httpx.codes.OK:
            task_data = response.json()
            # complete 完成至下一個task -> 付款審核中
            url = camunda_api_url + '/task/{id}/complete'.format(id=task_data[0].get('id'))
            headers = {'Content-Type': 'application/json'}
            data = {"variables": {}}
            response = client.post(url=url,headers=headers,json=data)
            if response.status_code == httpx.codes.NO_CONTENT:
                return True
    return False

@router.post('/join/buyer/review')
async def review_join_sponsor_buyer(sponsor_number:str, payment_verified:bool): # 轉數快對帳
    # update paid_at
    sponsor.updateSponsorOrder(sponsor_number,paid_at=datetime.now())
    # get sponsor order
    order = sponsor.getSponsorOrderByNumber(sponsor_number)
    # get task id by instance idurl = camunda_api_url + '/task'
    url = camunda_api_url + '/task'
    headers = {'Content-Type': 'application/json'}
    params = {'processInstanceId': order['process_id']}
    with httpx.Client() as client:
        response = client.get(url=url,headers=headers,params=params)
        if response.status_code == httpx.codes.OK:
            task_data = response.json()
            print(task_data)
            # complete 完成至下一個task -> 付款審核中
            url = camunda_api_url + '/task/{id}/complete'.format(id=task_data[0].get('id'))
            headers = {'Content-Type': 'application/json'}
            data = {"variables": {
                "payment_verified":{
                    "value":payment_verified,
                    "type":"Boolean"
                }
            }}
            response = client.post(url=url,headers=headers,json=data)
            if response.status_code == httpx.codes.NO_CONTENT:                
                # create sponsor
                s = sponsor.createSponsor(sponsor_level=order['sponsor_level'],sponsor_number=order['sponsor_number'],user_id=order['user_id'])
                return {"success": True}
    return {"success": False}
