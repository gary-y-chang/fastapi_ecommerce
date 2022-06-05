from venv import create
import pony.orm as pny
from models.entities import Transaction
from datetime import datetime


@pny.db_session
def createTransaction(txn_no, amount, payment_agent):
    # txn_no = PrimaryKey(str)  # 對應藍新API回傳參數 MerchantOrderNo
    # trade_no = Optional(str)  # 藍新金流交易序號 
    # amount = Required(int)
    # payment = Optional(str)  # 支付方式 
    # created_at = Required(datetime)
    # pay_time = Optional(datetime)  # 支付完成時間
    return Transaction(txn_no=txn_no, amount=amount, payment_agent=payment_agent, created_at=datetime.now()).to_dict()
