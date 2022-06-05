from http.client import OK
from fastapi import APIRouter, Depends,HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from auth import Auth, Guard
from typing import List
from datetime import datetime
from models import shoppingcarts, products, orders, transactions
from collections import defaultdict
from routers.req_models import OrderData, Spec, StockData, PayNotify
import requests
from uuid import uuid4, UUID
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes
from base64 import b64encode, b64decode
from Crypto.Hash import SHA256
import calendar
import time
import json
import binascii

router = APIRouter(
    prefix="/shopping",
    tags=["購物車"]
)

auth = Auth()

tag_meta = {
    'name': '購物車',
    'description': '購物車操作: 購買商品、計算價格、結帳 .....',
}

@router.get('/cart/item-list', name='列出購物車詳細內容')
def get_shoppingcart_by_userId(user_id=Depends(Guard())):
    cart_items = shoppingcarts.getShoppingcartUserId(user_id)
    # cart_items = ShoppingCart.select(lambda c: c.user_id==UUID(user_id) and c.checked_out==False)[:]
    shop_items = []
    s_items = defaultdict(list)
    for i in cart_items:
        p = products.getProductFreights(str(i.prod_id))
        fre_list = [f for f in p.freights]
        it = i.to_dict()
        it['ship_options'] = fre_list
        s_items[str(i.shop_id)].append(it)

    for k,v in s_items.items():
        s = {'shop_id':k, 'shop_title': v[0]['shop_title'], 'shop_icon': v[0]['shop_icon'], 'items': v} 
        shop_items.append(s)
 
    # items = [item.to_dict(exclude='cart_id') for item in ct.cart_items]
    # cart = ct.to_dict() 
    # cart['cart_items'] = shop_items
    return shop_items

@router.post('/add-item/{prod_id}', name='選購商品加入購物車')
def add_product_to_shoppingcart(stock: StockData,prod_id: str, user_id=Depends(Guard())):
    pd = products.getProductAllInfo(prod_id)
    cover = list(filter(lambda p: p.is_cover==True, pd.pictures))[0]
    # query product default shipment and its freight
    item_info = {'user_id':user_id, 'prod_id':pd.id, 'prod_name':pd.name, 'prod_img':cover.src, 
         'qty':1, 'price':stock.price,'shop_id':pd.shop_id.id, 'shop_title':pd.shop_id.title,
         'shop_icon':pd.shop_id.icon, 'ship_by':'郵政', 'freight':0, 'checked_out':False, 'created_at':datetime.now(), 'updated_at':datetime.now()}

    # this is for testing
    # item_info = {'user_id':UUID(user_id), 'prod_id':UUID(prod_id), 'prod_name':'測試品', 'prod_img':'https://storage.googleapis.com/hkshopu.appspot.com/refactor/396a8f12443a5c4daa8b7c8ade3ed568', 
    #     'qty':1, 'price':stock.price,'shop_id':'d251602d-86da-4186-934a-582d57dd1266', 'shop_title':'包包大王',
    #     'shop_icon':'no icon', 'ship_by':'郵政', 'freight':0, 'checked_out':False, 'created_at':datetime.now(), 'updated_at':datetime.now()}    
    
    if stock.spec:
        item_spec = {stock.spec.spec_name: stock.spec.spec_val}
        item_info['spec'] = item_spec
    else:
        item_info['spec'] = {}    

    item = shoppingcarts.addShoppingcartItem(**item_info)    
    # shoppingcarts.updateShoppingcart(str(ct.id), total_price=ct.total_price+stock.price)
    return item.to_dict()


@router.patch('/cart/item/{item_id}/update', name='更新購物車內某項商品之數量或運送方式')    
def update_item_in_cart():
    pass


 
# Order logic:
# first, group by Shop
# second, group by ship 
@router.post('/cart/check-out', name='購物車商品結帳')
async def check_out_a_cart(request: Request, order_data: List[OrderData], user_id=Depends(Guard())): 
    shop_list = []
    odr_no_list = []
    total_freight = 0
    amount = 0
    txn_no = 'BUY'+ str(datetime.now().timestamp()*1000)
    payment_agent = order_data[0].payment  #金流方式, 藍新、PayPal
    for order in order_data:
        shipment_dict = defaultdict(list)
        for i in order.items:
            shipment_dict[i.ship_by].append(i.dict())
        shop_dict = {}
        shop_dict['shop_title'] = order.shop_title
        shop_dict['shop_icon'] = order.shop_icon
        shop_dict['ship_info'] = order.ship_info 
        shop_dict['shop_id'] = order.shop_id 
        shop_dict[order.shop_id] = shipment_dict
        shop_list.append(shop_dict)
        
    for s in shop_list:
        # print(s['shop_title'], s['ship_info'])
        sid = s['shop_id']
        ordict = {}
        ordict['user_id']= user_id
        ordict['shop_id']= s['shop_id']
        ordict['shop_title']= s['shop_title']
        ordict['created_at']= datetime.now()
        ordict['leadtime']=3
        ordict['ship_info']= s['ship_info']

        for k,v in s[sid].items():
            # create Order and OrderItems to persist
            ordict['odr_no'] = orders.getOrderNo(s['shop_id'])
            ordict['ship_by'] = k
            ordict['total_price'] = sum([i['price']*i['qty'] for i in v])
            [i.pop('ship_by') for i in v]
            total_freight += sum([i['freight']for i in v])
            amount += ordict.get('total_price') + total_freight
           
            lead_time = max([products.getProductLeadtime(pid) for pid in [i['prod_id'] for i in v]])
            # leads = [products.getProductLeadtime(pid) for pid in pids]
            ordict['leadtime'] = lead_time

            # invoke Camunda REST API to init Process with order_no a
            # get response with process_id, and update Order with process_id
            try:
                  ## create a new Transaction here for 3rd party 
                txn = transactions.createTransaction(txn_no, amount, payment_agent)
                
                req_body =  {'variables': {'shop-id': {'value':sid,'type':'String' }, 'buyer-id': {'value':user_id,'type':'String' }, 'amount': {'value':amount,'type':'Integer' }}, 'businessKey': ordict['odr_no']}
                r = requests.post('http://ec2-18-166-213-0.ap-east-1.compute.amazonaws.com:8080/engine-rest/process-definition/key/order_flow_0.1/start', json=req_body)
                response = r.json()
                ordict['process_id'] = response['id']
                ordict['txn_no'] = txn_no
                o = orders.createOrder(ordict, v)
                odr_no_list.append(o.odr_no)
                print(k, v)
            except (Exception, Warning) as e:        
                raise HTTPException(status_code=409, detail=str(e))        

  
    ## call 藍新 payment API here  redirect to pay_test() API http://SITE_URL/shoppings/newebpay/test
    domain = request.url._url.replace(request.url.path, '')
    return RedirectResponse(domain + '/shopping/newebpay/api?txn_no='+ txn_no +'&amount='+ str(amount), status_code=303)
    # return {'transaction': txn, 'order_no': odr_no_list}


@router.post('/newebpay/notify', name='第三方支付交易完成回傳API')    
async def pay_notify(request: Request):
    body = await request.body()
    # data = json.loads(body)
    print(body)
    ## should update Transaction with response trade_no 藍新金流交易序號

    domain = request.url._url.replace(request.url.path, '')
    return RedirectResponse(domain + '/shopping/newebpay/api?txn_no=BUY20220220002&amount=8889', status_code=303)
    # return "OK"

@router.get('/newebpay/api', response_class=HTMLResponse, name='Call第三方支付交易API')    
def newebpay_api(txn_no: str, amount: str ):
    ts = calendar.timegm(time.gmtime())
    print('timestamp >> ', ts)
    # notify_url = 'https://a31d-116-89-136-219.ngrok.io/shopping/pay/notify'
    data = "MerchantID=MS329717003&RespondType=JSON&TimeStamp="+ str(ts) +"&Version=2.0&MerchantOrderNo="+ txn_no +"&Amt="+ amount +"&ItemDesc=購物車結帳&LoginType=0&CREDIT=1&WEBATM=1&VACC=1"
    key = b"VZdpeJmunJU6jdGbz6tpMwSgmuHDF0O6"
    iv = b"C1oyruhKj3nwHPsP"
    # block_size = 32

    print('key > ', key)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct_bytes = cipher.encrypt(pad(data.encode(), 32))
    iv = binascii.hexlify(cipher.iv).decode('utf-8')
    ct = binascii.hexlify(ct_bytes).decode('utf-8')
    # result = json.dumps({'iv':iv, 'ciphertext':ct})
    print("TradeInfo >> ", ct)

    trade_sha = "HashKey=VZdpeJmunJU6jdGbz6tpMwSgmuHDF0O6&"+ ct +"&HashIV=C1oyruhKj3nwHPsP"
    hash = SHA256.new()
    hash.update(trade_sha.encode())
    trsa = hash.hexdigest().upper()
    print("TradeSha >> ", trsa)

    content = f"""
        <htm>
        <body>
        <form id="myForm" action="https://ccore.newebpay.com/MPG/mpg_gateway" method="POST">
        <input type="hidden" name="MerchantID" value="MS329717003"/>
        <input type="hidden" name="TradeInfo" value="{ct}"/>
        <input type="hidden" name="TradeSha" value="{trsa}"/>
        <input type="hidden" name="Version" value="2.0"/>
        <input type="hidden" name="EncryptType" value="0"/>
        </form>
        <script type="text/javascript">
        document.getElementById("myForm").submit();
        </script>
        </body>
        </html>
    """
    return content
