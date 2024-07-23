# -*- coding: utf-8 -*-
# @Time    : 2024/5/14 15:05
# @Author  : 刘希
# @FileName: login.py
# @Software: PyCharm
import json
import datetime
import time
# from django.core.cache import cache

from django.contrib import auth
from django.core.mail import send_mail
from django.forms import model_to_dict
from django.shortcuts import get_object_or_404
from ninja import Router, ModelSchema, Query, Schema, Field

from fuadmin.settings import SECRET_KEY, TOKEN_LIFETIME
from system.models import Users, Role, MenuButton, MenuColumnField
from utils.fu_jwt import FuJwt
from utils.fu_response import FuResponse
from utils.request_util import save_login_log
from utils.usual import get_user_info_from_token
from django.contrib.auth.hashers import make_password
from utils.fu_crud import create, delete, retrieve, update
import smtplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from email.header import Header

router = Router()


class SchemaOut(ModelSchema):
    homePath: str = Field(None, alias="home_path")

    class Config:
        model = Users
        model_exclude = ['password', 'role', 'post']


class LoginSchema(Schema):
    username: str = Field(None, alias="username")
    password: str = Field(None, alias="password")
    sms: str = Field(None, alias="sms")


class RegisterSchema(Schema):
    username: str = Field(None, alias="username")
    password: str = Field(None, alias="password")
    mobile: str = Field(None, alias="mobile")
    sms: str = Field(None, alias="sms")
    email: str = Field(None, alias="email")


class Out(Schema):
    multi_depart: str
    sysAllDictItems: str
    departs: str
    userInfo: SchemaOut
    token: str


@router.post("/login", response=Out, auth=None)
def login(request, data: LoginSchema):
    user_obj = auth.authenticate(request, **data.dict())
    if user_obj:
        if data.username == "superadmin" or data.sms == request.session['verify']:
            request.user = user_obj
            role = user_obj.role.all().values('id')
            post = list(user_obj.post.all().values('id'))
            role_list = []
            post_list = []
            for item in role:
                role_list.append(item['id'])
            for item in post:
                post_list.append(item['id'])
            user_obj_dic = model_to_dict(user_obj)
            user_obj_dic['post'] = post_list
            user_obj_dic['role'] = role_list
            del user_obj_dic['password']
            del user_obj_dic['avatar']

            time_now = int(datetime.datetime.now().timestamp())
            jwt = FuJwt(SECRET_KEY, user_obj_dic, valid_to=time_now + TOKEN_LIFETIME)
            # 将生成的token加入缓存
            # cache.set(user_obj.id, jwt.encode())
            token = f"bearer {jwt.encode()}"
            data = {
                "multi_depart": 1,
                "sysAllDictItems": "q",
                "departs": "e",
                'userInfo': user_obj_dic,
                'token': token
            }
            save_login_log(request=request)
            return data
        else:
            return FuResponse(code=500, msg="验证码错误")
    else:
        return FuResponse(code=500, msg="账号/密码错误")


@router.get("/logout", auth=None)
def get_post(request):
    # 删除缓存
    user_info = get_user_info_from_token(request)
    # cache.delete(user_info['id'])
    return FuResponse(msg="注销成功")


@router.get("/userinfo", response=SchemaOut)
def get_userinfo(request):
    user_info = get_user_info_from_token(request)
    user = get_object_or_404(Users, id=user_info['id'])
    return user


@router.get("/permCode")
def route_menu_tree(request):
    """用于前端获取当前用户的按钮权限"""
    token_user = get_user_info_from_token(request)
    user = Users.objects.get(id=token_user['id'])

    if not token_user['is_superuser']:
        menu_button_ids = user.role.values_list('permission__id', flat=True)
        menu_column_ids = user.role.values_list('column__id', flat=True)

        # queryset = MenuButton.objects.filter(id__in=menuIds, status=1).values()
        queryset_button = MenuButton.objects.filter(id__in=menu_button_ids)
        queryset_column = MenuColumnField.objects.filter(id__in=menu_column_ids)
    else:
        queryset_button = MenuButton.objects.all()
        queryset_column = MenuColumnField.objects.all()

    queryset = [*queryset_button, *queryset_column]
    code_list = []
    for item in queryset:
        code_list.append(item.code)
    return FuResponse(data=code_list)


def sendMessage(email):  # 发送邮件并返回验证码
    # 生成验证码
    import random
    str1 = '0123456789'
    rand_str = ''
    for i in range(0, 6):
        rand_str += str1[random.randrange(0, len(str1))]
    # 发送邮件：
    # send_mail的参数分别是  邮件标题，邮件内容，发件箱(settings.py中设置过的那个)，收件箱列表(可以发送给多个人),失败静默(若发送失败，报错提示我们)
    message = "您的验证码是" + rand_str + "，10分钟内有效，请尽快填写"
    # emailBox = []
    # emailBox.append(email)
    # ali_send_email('noreply@possumic.com', 'Nrpy@i5i6#24', email, message)
    send_mail1(to_emails=email,textMessage=message)
    # send_mail('怪奇物语', message, 'noreply@possumic.com', emailBox, fail_silently=False)
    return rand_str


# 验证该用户是否已存在 created = 1 存在
def existUser(email):
    created = 1
    try:
        Users.objects.get(email=email)
    except:
        created = 0
    return created


@router.post("/sendSMS", response=Out, auth=None)
def login(request, data: LoginSchema):
    user_obj = auth.authenticate(request, **data.dict())
    if user_obj:
        email = user_obj.email
        response = {"state": False, "errmsg": ""}
        # if existUser(email):
        #     response['errmsg'] = '该用户已存在，请登录'
        # else:
        try:
            # flag = True
            # request.session.setdefault('email', '')
            # if request.session['email'] == email:
            #     while flag:
            #         for minute in range(1, -1, -1):
            #             if minute == 0:
            #                 flag = False
            #                 request.session['email'] = ""
            #                 break
            #             for second in range(59, -1, -1):
            #                 time.sleep(1)
            #                 print(f"{minute - 1:02}:{second:02}")
            # else:
            rand_str = sendMessage(email)  # 发送邮件
            # request.session['email'] = email
            request.session['verify'] = rand_str  # 验证码存入session，用于做注册验证
            response['state'] = True
            request.session.set_expiry(10*60)
        except:
            response['errmsg'] = '验证码发送失败，请检查邮箱地址'
        return FuResponse(json.dumps(response))


@router.post("/regSMS", response=Out, auth=None)
def reg(request, data: RegisterSchema):
    if request.request_data["email"]:
        email = request.request_data["email"]
        response = {"state": False, "errmsg": ""}

        # if existUser(email):
        #     response['errmsg'] = '该用户已存在，请登录'
        # else:
        try:
            # flag = True
            # request.session.setdefault('email', '')
            # if request.session['email'] == email:
            #     response['errmsg'] = '验证码发送发送频繁，请1分钟后重试'
            #     while flag:
            #         for minute in range(1, -1, -1):
            #             if minute == 0:
            #                 flag = False
            #                 request.session['email'] = ""
            #                 break
            #             for second in range(59, -1, -1):
            #                 time.sleep(1)
            #                 print(f"{minute - 1:02}:{second:02}")
            # else:
            rand_str = sendMessage(email)  # 发送邮件
            # request.session['email'] = email
            request.session['verify'] = rand_str  # 验证码存入session，用于做注册验证
            response['state'] = True
            request.session.set_expiry(10*60)
        except:
            response['errmsg'] = '验证码发送失败，请检查邮箱地址'
        return FuResponse(json.dumps(response))


@router.post("/register", response=Out, auth=None)
def register(request, data: RegisterSchema):
    if data.sms == request.session['verify']:
        print(request.request_data)
        tempUser = {
            "password": make_password(data.password),
            "is_superuser": 0,
            "is_staff": 0,
            "is_active": 1,
            "date_joined": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
            "update_datetime": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
            "create_datetime": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
            "username": data.username,
            "email": data.email,
            "mobile": data.mobile,
            "name": data.username,
            "gender": 1,
            "user_type": 0,
            "status": 0,
        }
        Users.objects.create(**tempUser)
        return FuResponse({"state": True, "msg": "注册成功"})


def ali_send_email(username, password, email, mes):
    subject = '测试邮件'
    content = mes

    messsage = MIMEText(content, 'plain', 'utf-8')
    messsage['From'] = Header(username, 'utf-8')
    messsage['To'] = Header(email, 'utf-8')
    messsage['Subject'] = Header(subject, 'utf-8')

    '''~~~开始连接验证服务~~~'''
    try:
        client = smtplib.SMTP_SSL('smtp.qiye.aliyun.com', 465)
        print('smtp_ssl----连接服务器成功，现在开始检查账号密码')
    except Exception as e1:
        client = smtplib.SMTP('smtp.qiye.aliyun.com', 25, timeout=5)
        print('smtp----连接服务器成功，现在开始检查账号密码')
    except Exception as e2:
        print('抱歉，连接服务超时')
        exit(1)
    try:
        client.login(username, password)
        print('账密验证成功')
    except:
        print('抱歉，账密验证失败')
        exit(1)

    '''~~~发送邮件并结束任务~~~'''
    client.sendmail(username, email, messsage.as_string())
    client.quit()
    print('邮件发送成功')

import time, datetime
import hmac
import base64
from urllib.parse import quote
import requests


def percentEncode(str):
    res = quote(str.encode('utf8'), '')
    res = res.replace('+', '%20')
    res = res.replace('*', '%2A')
    res = res.replace('%7E', '~')
    return res


def get_signature(method, data, accessSecret):
    CanonicalizedQueryString = '&'.join(
        [
            f'{percentEncode(k)}={percentEncode(v)}'
            for k, v in sorted(data.items(), key=lambda x: x[0])
        ]
    )
    StringToSign = (
        method
        + "&"
        + percentEncode("/")
        + "&"
        + percentEncode(CanonicalizedQueryString)
    ).encode('utf8')

    key = f'{accessSecret}&'.encode('utf8')
    h = hmac.new(key, StringToSign, digestmod='sha1')
    rv = base64.b64encode(h.digest()).decode()
    return StringToSign.decode(), rv


def send_mail1(
    to_emails,
    textMessage,
    subject='验证码',
    from_email='noreply@cs.possumic.com',
    accessKeyId='LTAI5tPdvFJ3KKsDjei8vdK7',
    accessSecret='95tUETsSGpa4rr1hwHGE7bYssDRVan',
):
    headers = {
        'Accept': 'application/json',
    }

    data = {
        'Action': 'SingleSendMail',
        'AccountName': from_email,
        'AddressType': '1',
        'ReplyToAddress': 'true',
        'Subject': subject,
        'ToAddress': to_emails,
        'ClickTrace': '1',
        'TextBody': textMessage,
        # sign
        'AccessKeyId': accessKeyId,
        'Version': '2015-11-23',
        'Format': 'JSON',
        'SignatureVersion': '1.0',
        'SignatureMethod': 'HMAC-SHA1',
        'SignatureNonce': str(int(time.time())),
        'Timestamp': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
    }

    str_to_sign, data['Signature'] = get_signature('POST', data, accessSecret)
    # print(data)
    try:
        response = requests.post('http://dm.aliyuncs.com/', headers=headers, data=data)
        # print(str_to_sign == response.json()['Message'].split(':', 1)[1].strip())
        return response.status_code == 200, response.json()
    except Exception as e:
        return False, e