from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, File, UploadFile, Form, Body, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from http import HTTPStatus
from google.auth import credentials
from models import users
from auth import Auth, Guard
from models.entities import UserAddress
from .util import File_Size_Checker, upload_to_gcs
from .req_models import UserAddressData, UserAuth, SocialAuth, UserEmailCheck, SignupVerify, UserDetailData
from .res_models import ResponseOperationStatus, ResponseLogin, ResponseSignup, ResponseShopInfoBuyer, ResponseUserAddress, ResponseBrowseProduct
import random
from redis import Redis
import os
from decouple import config
from google.cloud import storage
from google.cloud.storage import Blob
from google.oauth2 import service_account
from pony.orm import TransactionIntegrityError
from uuid import UUID
from typing import List

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

auth = Auth()

config.encoding = 'utf-8'
redis_host = config('REDIS_HOST')
redis_port = config('REDIS_PORT')

tag_meta = {
    'name': 'Users',
    'description': '用戶資料相關操作: 註冊、驗證碼、.....',
}


@router.get('/')
async def get_all_users():
    return users.getAllUsers()

@router.post(
    '/email-checking',
    response_model=ResponseOperationStatus
)
async def check_email_exist(
    data: UserEmailCheck = Body(
        ...,
        examples={
            "normal":{
                "summary": "Normal Example",
                "value": {
                    "email": "rogerwang@times-transform.com",
                },
            },
            'validation_error':{
                "summary": "Validation Error",
                "value":{
                    "email": "wrong.a"
                }
            }
        }
    )
):
    ''' return true if the email already existing,\n
        return false if the email not registerd\n
        request body: {"email": "the_email_to_be_checked"}
    '''
    try:
        res = users.getUserByCol(**data.dict())
        return {"success": True} if res else {"success": False}
    except: # MultipleObjectsFoundError 
        pass


@router.post(
    '/signup', 
    name='用戶註冊', 
    description='新用戶輸入個人電郵與自訂密碼',
    response_model=ResponseSignup,
    responses={
        409:{
            "content": {"application/json": {}},
            "description": "Transaction Integrity Error",
        },
    }
)
async def signup(
    background_tasks: BackgroundTasks,
    user_data: UserAuth = Body(
        ...,
        examples={
            "normal":{
                "summary": "Normal Example",
                "value": {
                    "email": "rogerwang@times-transform.com",
                    "password": "string"
                }
            }
        }
    ),
):
    try:
        hashed_password = auth.encode_password(user_data.password)
        uid = users.addUser(user_data.email, hashed_password)
        # if success insert into db, then send eamil verification code
        rand_str = ''.join([random.choice('0123456789') for a in range(4)])
    
        rds = Redis(redis_host, redis_port)
        rds.set(user_data.email, rand_str, ex=600) # verify code will expire on 10 min
        
        send_email_background(background_tasks, 'HKShopU - 會員電子郵件驗證',
            user_data.email, {'static':os.getcwd(),'validation_code':rand_str})
        return {"user_id": uid}
    except TransactionIntegrityError as err:
        raise HTTPException(status_code=409, detail=str(err))
        
@router.post(
    '/reset-pwd',
    description='重設用戶密碼',
    response_model=ResponseOperationStatus
)
async def reset_pwd(user_data: UserAuth, uid=Depends(Guard())):
    try:
        u = users.getUserByCol(**{'email':user_data.email})
        hashed_password = auth.encode_password(user_data.password)
        users.updateUser(uid, **{'password':hashed_password})
    except:
        raise HTTPException(status_code=409, detail='Failed to reset password')
    return {"success": True}

@router.post(
    '/login',
    response_model=ResponseLogin,
    responses={401:{
            "content": {"application/json": {}},
            "description": "Email not found or password invalid",
        }
    }
)
async def login(
    user_data: UserAuth = Body(
        ...,
        examples={
            "normal":{
                "summary": "Normal Example",
                "value":{
                    "email": "rogerwang@times-transform.com",
                    "password": "string"
                }
            }
        }
    )
):
    user = users.getUserByEmail(user_data.email)
    if (user is None):
        raise HTTPException(status_code=401, detail='Email invalid or not found')
    if (not auth.verify_password(user_data.password, user.password)):
        raise HTTPException(status_code=401, detail='Invalid password')
    
    access_token = auth.encode_token(user.id, user.email)
    refresh_token = auth.encode_refresh_token(user.id, user.email)

    return {'user_id': str(user.id),'access_token': access_token, 'refresh_token': refresh_token}

@router.post(
    '/social-login',
    response_model=ResponseLogin,
    description='account_type: [google | fb | apple]',
    responses={401:{
            "content": {"application/json": {}},
            "description": "Failed to signup user",
        }
    }
)
async def social_login(
    user_data: SocialAuth = Body(
        ...,
        examples={
            "google":{
                "summary": "Google",
                "value": {
                    "account_id": "string",
                    "email": "rogerwang@times-transform.com",
                    "account_type": "google",
                }
            },
            "fb":{
                "summary": "Facebook",
                "value":{
                    "account_id": "string",
                    "email": "rogerwang@times-transform.com",
                    "account_type": "fb",
                }
            },
            "apple":{
                "summary": "Apple",
                "value":{
                    "account_id": "string",
                    "email": "rogerwang@times-transform.com",
                    "account_type": "apple",
                }
            },
        }
    )
):
    user = users.getUserByCol(**{'email':user_data.email})
    if user:
        if user_data.account_type == 'google' and not user.google_id:
            users.updateUser(user.id,**{'google_id':user_data.account_id})
        elif user_data.account_type == 'fb' and not user.fb_id:
            users.updateUser(user.id,**{'fb_id':user_data.account_id})
        elif user_data.account_type == 'apple' and not user.apple_id:
            users.updateUser(user.id,**{'apple_id':user_data.account_id})
        access_token = auth.encode_token(user.id, user_data.email)
        refresh_token = auth.encode_refresh_token(user.id, user_data.email)
        return {'user_id': str(user.id),'access_token': access_token, 'refresh_token': refresh_token}
    else:
        try:
            uid = users.addUserSocial(**user_data.dict())
            user = users.getUserByCol(**{'email':user_data.email})
            access_token = auth.encode_token(user.id, user_data.email)
            refresh_token = auth.encode_refresh_token(user.id, user_data.email)
            return {'user_id': str(user.id),'access_token': access_token, 'refresh_token': refresh_token}
        except:
            raise HTTPException(status_code=409, detail='Failed to signup user')

@router.get('/user')
async def get_current_user(uid=Depends(Guard())):
    u = users.getUserById(uid)
    del u['password']
    return u

@router.get('/refresh-token')
def refresh_token(new_token=Depends(Guard())):
# def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    # refresh_token = credentials.credentials
    # new_token = auth.refresh_token(refresh_token)
    print('refresh ----------->', new_token)
    return {'access_token': new_token}

# @router.get('/demo-protected', dependencies=[Depends(Guard())])
@router.get('/demo-protected')
def demo_protected_resource(uid=Depends(Guard())):
    print('----------->', uid)
    return {"success": True}

@router.get('/demo-protected-auth', dependencies=[Depends(Guard())])
def demo_protected_resource():
    return {"success": True}    

@router.put(
    '/verify-signup-code',
    response_model=ResponseLogin,
    responses={406:{
            "content": {"application/json": {}},
            "description": "Sign-up code invalid",
        }
    }
)
async def verify_signup_code(verify_data: SignupVerify):
    rds = Redis(redis_host, redis_port)
    print('valid_code', verify_data.valid_code)
    code = rds.get(verify_data.email)
    print(code.decode())
    
    if code.decode() == verify_data.valid_code:
        user = users.getUserByCol(**{'email':verify_data.email})
        users.updateUser(user.id, **{'is_active':1})
        access_token = auth.encode_token(user.id, user.email)
        refresh_token = auth.encode_refresh_token(user.id, user.email)
        return {'user_id': str(user.id), 'access_token':access_token, 'refresh_token':refresh_token} 
    
    raise HTTPException(status_code=406, detail='sign-up code invalid')

@router.get(
    '/resend-signup-code/{user_email}',
    description='寄送驗證碼',
    response_model=ResponseOperationStatus,
)
async def send_verification_code_via_gmail(user_email,background_tasks: BackgroundTasks):
    user = users.getUserByCol(**{'email':user_email})
    if user:
        rand_str = ''.join([random.choice('0123456789') for a in range(4)])
        rds = Redis(redis_host, redis_port)
        rds.set(user_email, rand_str, ex=600)
        send_email_background(background_tasks, 'HKShopU - 會員電子郵件驗證',
            user_email, {'static':os.getcwd(),'validation_code':rand_str})
        return {"success": True}

    raise HTTPException(status_code=406, detail='user email not exists') 

@router.post(
    '/user-detail',
    response_model=UserDetailData,
)
async def add_user_detail(detail_data: UserDetailData):
    try:
        detail = users.addUserDetail(**detail_data.dict())
        return detail
    except Exception as e:
        print(e)
        raise HTTPException(status_code=409, detail=str(e))

@router.get(
    '/user-detail',
    response_model=UserDetailData,
    responses={204: {
        "model": None,
        "description": "Successful Response With Null",
    }},
)
async def get_user_detail(uid=Depends(Guard())):
    detail_data = users.getUserDetail(uid)
    if detail_data:
        return detail_data
    else:
        return Response(status_code=HTTPStatus.NO_CONTENT.value)

@router.put(
    '/user-detail',
    response_model=UserDetailData,
)
async def update_user_detail(detail_data:UserDetailData, uid=Depends(Guard())):
    detail_data = users.updateUserDetail(**detail_data.dict())
    return detail_data

@router.post("/upload-avatar/", dependencies=[Depends(Guard()),Depends(File_Size_Checker(300))])
async def create_upload_file(file: UploadFile = File(..., description='the file to upload'), user_id: str = Form(..., description='the User ID')):
    '''
    Summary of this api functionality
    - **param1**: param1 is doing the job1.
    - **param2**: param2 is doing the job2.
    '''
    public_url = upload_to_gcs(file)
    users.updateUserDetail(user_id, avatar=public_url)
    
    return {
        "avatar_url": public_url
    }

@router.post(
    '/address',
    response_model=ResponseUserAddress
)
async def add_user_address(user_address: UserAddressData, uid=Depends(Guard())):
    address_data = users.addUserAddress(**{**user_address.dict(),'user_id':uid})
    address_data['address_id'] = address_data.pop('id')
    return address_data

@router.get(
    '/address',
    response_model=List[ResponseUserAddress],
)
async def get_user_address(uid=Depends(Guard())):
    address_list = users.getUserAddressByUser(uid)
    for address in address_list:
        address['address_id'] = address.pop('id')
    return address_list

@router.delete(
    '/address/{address_id}',
    responses={204: {
        "model": None,
        "description": "Successful Response With Null",
    }},
)
async def delete_user_address(address_id,uid=Depends(Guard())):
    users.deleteUserAddress(address_id,uid)
    return Response(status_code=HTTPStatus.NO_CONTENT.value)

def send_email_background(background_tasks: BackgroundTasks, subject: str, email_to: str, template_body: dict):
    conf = ConnectionConfig(
        MAIL_USERNAME='hkshop-admin@hkshopu.com',
        MAIL_PASSWORD='kjlorxrvicukyvut',
        MAIL_FROM='info@hkshopu.com',
        MAIL_PORT=587,
        MAIL_SERVER='smtp.gmail.com',
        MAIL_FROM_NAME='info@hkshopu.com',
        MAIL_TLS=True,
        MAIL_SSL=False,
        TEMPLATE_FOLDER = 'templates',
    )
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        template_body=template_body,
        subtype='html',
    )
    fm = FastMail(conf)
    background_tasks.add_task(
       fm.send_message, message, template_name='validation_mail.html')

@router.post(
    '/follow-shop',
    response_model=ResponseOperationStatus,
)
async def follow_shop(shop_id: UUID, uid=Depends(Guard())):
    users.addShopFollower(uid, shop_id)
    return {"success": True}

@router.delete(
    '/follow-shop',
    response_model=ResponseOperationStatus
)
async def cancel_follow_shop(shop_id: UUID, uid=Depends(Guard())):
    users.deleteShopFollower(uid, shop_id)
    return {"success": True}

@router.get(
    '/follow-shop',
    response_model=List[ResponseShopInfoBuyer]
)
async def get_follow_shop(keyword:str='', uid=Depends(Guard())):
    shop_list = [ {'shop_id':shop_id,'title':title,'icon':icon,'follower_count':follower_count,'src':pic_src.split(',',3)[:3],'is_follow':True} for shop_id,title,icon,follower_count,pic_src in users.getFollowShopList(uid,keyword)]
    return shop_list

@router.get(
    '/like-product',
    response_model=List[ResponseBrowseProduct],
)
async def get_like_product(keyword:str='', uid=Depends(Guard())):
    return users.getLikeProduct(uid)

@router.post(
    '/like-product',
    response_model=ResponseOperationStatus)
async def like_product(product_id: UUID, uid=Depends(Guard())):
    users.likeProduct(uid,product_id)
    return {"success": True}

@router.delete(
    '/like-product',
    response_model=ResponseOperationStatus)
async def dislike_product(product_id: UUID, uid=Depends(Guard())):
    users.dislikeProduct(uid,product_id)
    return {"success": True}