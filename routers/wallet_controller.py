from uuid import UUID
from fastapi import APIRouter,Query
from models import wallet
from uuid import UUID
from .req_models import WalletChargeHistory, WalletCharge
from .res_models import ResponseOperationStatus,ResponseWalletCharge
import httpx
import asyncio
from decouple import config
import json
from typing import List
from datetime import datetime,timezone
from dateutil.relativedelta import relativedelta

config.encoding = 'utf-8'
camunda_api_url = config('CAMUNDA_API_URL')
camunda_wallet_model = config('CAMUNDA_WALLET_MODEL')

router = APIRouter(
    prefix="/wallet",
    tags=["Wallet"]
)

tag_meta = {
    'name': 'Wallet',
    'description': '錢包的相關操作: 取得錢包資料、錢包紀錄、充值 ......',
}

@router.get('')
async def get_wallet(shop_id:UUID):
    return wallet.getWallet(shop_id)

@router.get('/history')
async def get_history(wallet_id:UUID):
    return [ w.to_dict() for w in wallet.getHistory(wallet_id=wallet_id) ]


@router.post('/history/charge')
async def add_hisotory_of_charge(history:WalletChargeHistory):
    return wallet.addHistory(history)

@router.get(
    '/charge',
    response_model=List[ResponseWalletCharge],
)
async def get_charge(wallet_id:UUID, status:List[int]=Query(...)):
    '''
        ## status:\n
        * 1: 繼續付款\n
        * 2: 審查中\n
        * 3: 儲值失敗\n
        * 4: 儲值成功
    '''
    process_instance_ids = []
    month_ago = (datetime.now(timezone.utc) - relativedelta(months=1)).strftime('%Y-%m-%dT%H:%M:%S')
    with httpx.Client() as client:
        req_active_url = camunda_api_url + '/process-instance'
        req_hitory_url = camunda_api_url + '/history/process-instance'
        headers = {'Content-Type': 'application/json'}
        mapping_list = {}# classify by status
        for s in status:
            req_body = {"variables": [
                    {
                        "name":"status",
                        "operator":"eq",
                        "value":s
                    }
                ]
            }            
            if s in [1,2]:
                response = client.post(url=req_active_url,headers=headers,json=req_body)
            elif s in [3,4]:
                req_body['finishedafter'] = month_ago # 取近一個月的資料
                response = client.post(url=req_hitory_url,headers=headers,json=req_body)
            if response.status_code == httpx.codes.OK:
                ids = [ data['id'] for data in response.json()]
                process_instance_ids.extend(ids)
                mapping_list[s] = ids
    charge_list = wallet.getChargeList(process_instance_ids)
    for i in range(len(charge_list)):
        for key in mapping_list:
            if charge_list[i]['process_id'] in mapping_list[key]:
                charge_list[i]['status'] = key
                mapping_list[key].remove(charge_list[i]['process_id'])
                break
    return charge_list
    

@router.post(
    '/charge',
    response_model=ResponseWalletCharge,
)
async def charge(charge:WalletCharge):
    # create WalletHistory & WalletCharge
    w = wallet.createCharge(**charge.dict())
    # start camunda instance 
    url = camunda_api_url + '/process-definition/key/' + camunda_wallet_model + '/start'
    headers = {'Content-Type': 'application/json'}
    data = {
        "variables": {
            "wallet-id":{
                "value":str(w.get('wallet_id')),
                "type":"String"
            }
        },
        "businessKey" : w.get('charge_no')
    }
    with httpx.Client() as client:
        response = client.post(url=url,headers=headers,json=data)
        json_data = json.loads(response.text)
    # update WalletCharge
    wallet.updateCharge(w.get('charge_no'), process_id=json_data['id'])
    
    return w

# 繼續付款 -> 付款審核
@router.post(
    '/charge/set',    
    response_model=ResponseOperationStatus,
)
async def set_charge_info(charge_no:str):
    # get WalletCharge
    charge = wallet.getChargeByCol(charge_no=charge_no)
    # get task id by instance id
    url = camunda_api_url + '/task'
    headers = {'Content-Type': 'application/json'}
    params = {'processInstanceId': charge.process_id}
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
                return {"success": True}
    return {"success": False}

# 付款審核 -> 結束
@router.post(
    '/charge/review',
    response_model=ResponseOperationStatus,
)
async def review_charge(charge_no:str,payment_verified:bool):
    # get WalletCharge
    charge = wallet.getChargeByCol(charge_no=charge_no)
    # get task id by instance idurl = camunda_api_url + '/task'
    url = camunda_api_url + '/task'
    headers = {'Content-Type': 'application/json'}
    params = {'processInstanceId': charge.process_id}
    with httpx.Client() as client:
        response = client.get(url=url,headers=headers,params=params)
        if response.status_code == httpx.codes.OK:
            task_data = response.json()
            # complete 完成至下一個task -> 結束
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
                wallet.updateCharge(charge_no,paid_at=datetime.now())
                return {"success": True}
    return {"success": False}
    