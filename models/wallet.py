from uuid import UUID
import pony.orm as pny
from models.entities import Wallet, WalletHistory, WalletCharge, Shop, SponsorLevel
from uuid import UUID
from datetime import datetime

@pny.db_session
def create():
    pass

@pny.db_session
def getWallet(shop_id:UUID):
    shop = Shop.get(id=shop_id,is_deleted=False)
    if not shop:
        shop = Wallet(shop_id=shop_id)
    wallet =  Wallet.get(shop_id=shop)
    if wallet == None:
        wallet = Wallet(shop_id=shop)
    return wallet.to_dict()

@pny.db_session
def deductWalletBySponsor(wallet_id:UUID, sponsor_level_id:int):
    level = SponsorLevel[sponsor_level_id]
    w = Wallet[wallet_id]
    w.set(balance=w.balance-level.price)
    return w

@pny.db_session
def getHistory(wallet_id:UUID):
    wallet = Wallet[wallet_id]
    return WalletHistory.select(lambda w: w.wallet_id==wallet)

@pny.db_session
def addHistory(wallet_id:UUID, description:str, charge_no:str=None, sponsor_number:str=None):
    return WalletHistory(wallet_id=wallet_id,description=description,charge_no=charge_no,sponsor_number=sponsor_number)

@pny.db_session
def getChargeNo():
    HEADER = 'SA'
    result = pny.select(pny.count(c) for c in WalletCharge if c.created_at.date()==datetime.now().date())[:]
    return HEADER + datetime.now().strftime('%Y%m%d') + str(result[0]+1).zfill(5)

@pny.db_session
def createCharge(wallet_id:UUID, amount:float, payment: str, process_id:str=''):
    DESCRIPTION = '錢包充值'
    charge_no = getChargeNo()
    history = addHistory(wallet_id, description=DESCRIPTION)
    charge = WalletCharge(charge_no=charge_no, wallet_id=wallet_id, amount=amount, payment=payment, history=history, process_id=process_id)
    return charge.to_dict()

@pny.db_session
def updateCharge(charge_no,**kwargs):
    return WalletCharge[charge_no].set(**kwargs)

@pny.db_session
def getChargeByCol(**kwargs):
    return WalletCharge.get(**kwargs)

@pny.db_session
def getChargeList(ids:list):
    return [ c.to_dict() for c in pny.select(c for c in WalletCharge if c.process_id in ids)[:] ]