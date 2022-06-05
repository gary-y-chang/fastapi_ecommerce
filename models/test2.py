from uuid import uuid4, UUID
from datetime import datetime
import calendar
import time
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
from base64 import b64encode, b64decode
from Crypto.Hash import SHA256
import binascii
import json
from json import dumps
from urllib.parse import parse_qs

ts = calendar.timegm(time.gmtime())
print('timestamp >> ', ts)
notify_url = 'https://a31d-116-89-136-219.ngrok.io/shopping/pay/notify'
data = "MerchantID=MS329717003&RespondType=JSON&TimeStamp="+ str(ts) +"&Version=2.0&MerchantOrderNo=BUY202201290001&Amt=299&ItemDesc=testing-product&LoginType=0&CREDIT=1&WEBATM=1&VACC=1"
key = b"VZdpeJmunJU6jdGbz6tpMwSgmuHDF0O6"
iv = b"C1oyruhKj3nwHPsP"
block_size = 32
def _pad(s): 
    return s + (block_size - len(s) % block_size) * chr(block_size - len(s) % block_size)
    # l =  len(s)
    # pad = block_size - (l % block_size)
    # return s + (chr(pad) * pad)
    


# return s + (block_size - len(s) % block_size) * chr(block_size - len(s) % block_size)

# $len = strlen($string); 
# $pad = $blocksize - ($len % $blocksize); 
# $string .= str_repeat(chr($pad), $pad); 
# return $string; 

print('Padding >> ', _pad(data))

print('key > ', key)
cipher = AES.new(key, AES.MODE_CBC, iv)
# ct_bytes = cipher.encrypt(_pad(data).encode())
ct_bytes = cipher.encrypt(pad(data.encode(), 32))
# iv = b64encode(cipher.iv).decode('utf-8')
# ct = b64encode(ct_bytes).decode('utf-8')
iv = binascii.hexlify(cipher.iv).decode('utf-8')
ct = binascii.hexlify(ct_bytes).decode('utf-8')
# result = json.dumps({'iv':iv, 'ciphertext':ct})
# print(result)
print("TradeInfo >> ", ct)

trade_sha = "HashKey=VZdpeJmunJU6jdGbz6tpMwSgmuHDF0O6&"+ ct +"&HashIV=C1oyruhKj3nwHPsP"
# trade_sha = 'HashKey=VZdpeJmunJU6jdGbz6tpMwSgmuHDF0O6&da4a7f59ee4f12f8389df700fad417459ed60a2959b7e36082493554c1214a9b9719e4b40972d33bfc3ee1d064f6cbb018337913d6186e0f6519d299c8908cc2e0459b744157fac97e477a4ccfe939a59b6007723c05d7cfacc2909f1aec67dc45d59f0ba186ea5508ff32d490e22cb3ca4c36e22a5bad0d4504cf812d964c42bcde62f27c23916e35549835dc835c346d8315039d0ddcc44d41432bf1068fc3be34d6933a6454b77d97b99e79a4eb50d7748dcb0534d2740d330c1e3d1e409e&HashIV=C1oyruhKj3nwHPsP'
hash = SHA256.new()
hash.update(trade_sha.encode())
print("TradeSha >> ",hash.hexdigest().upper())


body = b'Status=SUCCESS&MerchantID=MS329717003&Version=2.0&TradeInfo=8db74b0afac02363f6e4db9f2afee94a7e6fea43f3b4e6900984b095708e9a018de9ba1c7731a93ce733935288ba693bfde358dfebe1f907bbe051bbade1e02ca52d88510bd8d2cc15f7fc55a907150929d481b8a6550d7fd393724e7b8701adb3b1c8791b4728f005ea79fc787ccbf92d251db716bdae3cf7bb389c25b3186bb0c75d79129fd8726b94bd1fa6f754db097ede10224d5978f1125676a736b866b9e9ff05b6cbf3dc8fcc0f3dd31220f8deeff362b7caadc2e9233f2c90825ec1072b376f831f6f6e06c1740754e34952c85cb4878704f6519c01fefc266055ab0644776ff2f28841841dfa07456397c2cb2895bb11da071ae06a7a9a0a29a5db52d7c50ae567b31e8052eb74e8d20c69231398e894a9268e5913939df5137c374cbbfa77ca02da4917a81b729b81c8a193c361be58e52c2d1021049faa145b3b25c975116446bc66abb820679dce2630520bb548ebbb1b3184d2277875af42ee411a2d805059058eaa971e20e15264be6a84e7a0f2267d751de11c4e53e0988a62dca0b31efe6132c6fde96c218887dfee1eca625e65c2e67a567b70dee05979700fc069a17d80ddd52d58ee2e365eb1d1dd0a8bada6f7d6ac39a24cfd455144280642e3bf3deb2b38bee8b9e249bd9455086bfbb5a6b6c6fe080d6c72f6c0dc&TradeSha=F8D19F13E1E1E18C2C948C09597BD52C1EF36F254B94CDF2F50930863DC251F0'
bson = json.loads(dumps(parse_qs(body.decode())))

print(bson['Status'][0])
print(bson['TradeSha'][0])
msg = str(bson['TradeInfo'][0])
print('TradeInfo', msg)

# print('timestamp --> ', datetime.utcnow().timestamp())
# print('timestamp --> ',  'BUY'+ str(datetime.now().timestamp()*1000))

try:
    b64 = json.loads("{\"iv\": \"QzFveXJ1aEtqM253SFBzUA==\", \"ciphertext\": \"2kp/We5PEvg4nfcA+tQXRZ7WCilZt+Nggkk1VMEhSpuXGeS0CXLTO/w+4dBk9suwirwFDfrbFMkxdQ9ns07/2LOgFAsMCNPPhZmYWLkNJGV7jxjPh2cLCsYlS7ocN+7+rEs5wdoGWKQb4lq5zMjMsPqH+Z3xuiQ8+QCjkVMz1I+UJunK/FRetS+kNDins7PeXQdcopoIwpTWFsI9fRREp4tdEn7qZ6AMVUaoPjJkdg8RxhsBU8MD7kMliF9BtD26996hO2u4mslFo5KHtkJqvk+nJ0wGzikuuBtfj8hYiIexU4GTBH1Y8XQgDsVTxS6K\"}")
    # iv = b64decode(b64['iv'])
    iv = b"C1oyruhKj3nwHPsP"
    # ct = b64decode(b64['ciphertext'])
    # print(iv, ct)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    pt = unpad(cipher.decrypt(binascii.unhexlify(msg)), 32)
    print("The message was: ", pt.decode('utf-8'))
except (ValueError, KeyError):
    print("Incorrect decryption")



print('--- done ---')


 