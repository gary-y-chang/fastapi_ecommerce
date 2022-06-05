import pony.orm as pny
from datetime import datetime

from pony.orm.core import Required
from models.entities import SponsorLevel,SponsorOrder,Sponsor,Wallet,Shop,User
from models.wallet import addHistory
from uuid import UUID

@pny.db_session
def getSponsorLevel():
    levels = pny.select(s for s in SponsorLevel)[:]
    return [ l.to_dict() for l in levels ]

@pny.db_session
def getSponsorLevelById(id):
    return SponsorLevel[id]

@pny.db_session
def getSponsorNumber():
    HEADER = 'SR'
    result = pny.select(pny.count(c) for c in SponsorOrder if c.created_at.date()==datetime.now().date())[:]
    return HEADER + datetime.now().strftime('%Y%m%d') + str(result[0]+1).zfill(5)

@pny.db_session
def createSponsorOrder(sponsor_level:int, payment:str, wallet_id:UUID=None, user_id:UUID=None, paid_at:datetime=None):
    sponsor_number = getSponsorNumber()
    sponsor_order = SponsorOrder(
        sponsor_number=sponsor_number,
        wallet_id=wallet_id,
        user_id=user_id,
        sponsor_level=sponsor_level,
        payment=payment,
        paid_at=paid_at)#,
        # wallet_history=wallet_history)
    return sponsor_order.to_dict()

@pny.db_session
def getSponsorOrderByNumber(sponsor_number:str):
    return SponsorOrder[sponsor_number].to_dict()


@pny.db_session
def updateSponsorOrder(sponsor_number:str, **kwargs):
    return SponsorOrder[sponsor_number].set(**kwargs)

@pny.db_session
def createSponsor(sponsor_level:int, sponsor_number:str, wallet_id:UUID=None, user_id:UUID=None, **kwargs):
    DESCRIPTION = '贊助扣值'
    if wallet_id:
        wallet_history = addHistory(wallet_id, description=DESCRIPTION)
        updateSponsorOrder(sponsor_number=sponsor_number,wallet_history=wallet_history)
        shop_id = Wallet[wallet_id].shop_id
    else:
        shop_id = None
    level = SponsorLevel[sponsor_level]
    
    sponsor = Sponsor(
        shop_id=shop_id,
        user_id=user_id,
        sponsor_level=level,
        probability=level.probability,
        sponsor_order=sponsor_number
    )
    return sponsor.to_dict()

@pny.db_session
def updateSponsor(id, **kwargs):
    return Sponsor[id].set(**kwargs)

@pny.db_session
def getSponsor(shop_id:UUID=None,user_id:UUID=None):
    now = datetime.now()
    if shop_id:
        shop = Shop[shop_id]
        sp = pny.select(sp for sp in Sponsor if sp.shop_id==shop and sp.expired_at>now)[:]
    elif user_id:
        user = User[user_id]
        sp = pny.select(sp for sp in Sponsor if sp.user_id==user and sp.expired_at>now)[:]
    if sp:
        return sp[0].to_dict()
    return None