# -*- coding: utf-8 -*-
# login/views.py

import hashlib
import datetime
import time
import random
import os
from decimal import *
from django.conf import settings
from django.shortcuts import render, redirect
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from captcha.models import CaptchaStore
from captcha.helpers import captcha_image_url
from .forms import UserForm, RegisterForm
from . import models
from .pay import AliPay
os.path.abspath('../')
import task_platform.models as task_models

# 对username进行MD5哈希得到房间号
@csrf_exempt
def get_notice_room_id(username):
    md5 = hashlib.md5()
    md5.update(username.encode())
    return md5.hexdigest()

# 以Admin的身份向username发送消息message
@csrf_exempt
def send_notice(username, message):
    # 创建新的消息记录
    notice = task_models.Chatinfo.objects.create(room_id=get_notice_room_id(username))
    notice.sender = 'Admin'
    notice.message = message
    notice.save()
    # 创建消息查看记录
    flag = task_models.ChatVision.objects.create(room_id=get_notice_room_id(username))
    flag.username = username
    flag.has_seen = False
    flag.save()

@csrf_exempt
def hash_code(s, salt='hx+ltq+wzy+hxj'):# 加点盐
    h = hashlib.sha256()
    h.update((s + salt).encode())  # update方法只接收bytes类型
    return h.hexdigest()

def make_confirm_string(user):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    code = hash_code(user.name, now)
    models.ConfirmString.objects.create(code=code, user=user)
    return code

def send_email(email, code):
    from django.core.mail import EmailMultiAlternatives
    subject = '来自SCU-reward-platform的注册确认邮件'
    text_content = '''感谢注册，这里是四川大学任务悬赏，\
                    如果你看到这条消息，说明你的邮箱服务器不提供HTML链接功能，请联系管理员！'''
    html_content = '''
                    <p>感谢注册<a href="http://{}/confirm/?code={}" target=blank>SCU-reward-platform</a></p>
                    <p>这里是任务悬赏平台注册系统</p>
                    <p>请点击站点链接完成注册确认！</p>
                    <p>此链接有效期为{}天！</p>
                    '''.format('127.0.0.1:8000', code, settings.CONFIRM_DAYS)
    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, [email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def login(request):
    hashkey = CaptchaStore.generate_key()
    imgage_url = captcha_image_url(hashkey)#生成对应的图形验证码，会通过render渲染到前端
    if request.session.get('is_login',None):
         return redirect('/')
    if request.method == "POST":
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        login_form = UserForm(request.POST)#这里时前端POST提交的表单，提交的信息在这
        message = "{}, 请检查填写的内容！".format(username)
        if login_form.is_valid():#判断图形验证码是否正确，没有通过的话就会提示上面的messgae
            try:
                user = models.User.objects.get(name=username)
                if not user.has_confirmed:#没有通过邮箱进行验证
                    message = '请前往您的邮箱' + user.stu_id + '@stu.scu.edu.cn 进行确认！'
                    return render(request, 'login/login.html', locals())
                if user.password == hash_code(password):  # 哈希值和数据库内的值进行比对
                    request.session['is_login'] = True
                    request.session['user_id'] = user.id
                    request.session['user_name'] = user.name
                    user.money = Decimal(10)
                    user.save()
                    return redirect('/')
                else:
                    message = "密码不正确！"
            except:
                message = "用户"+ username + "不存在" 
            return render(request, 'login/login.html', locals())

    login_form = UserForm()
    return render(request, 'login/login.html', locals())

def register(request):
    hashkey = CaptchaStore.generate_key()
    imgage_url = captcha_image_url(hashkey)
    if request.session.get('is_login', None):#避免重复登录
        return redirect("/")

    if request.method == "POST":
        username = request.POST.get('username', '')
        student_id = request.POST.get('student_id', '')
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        phone = request.POST.get('phone', '')
        register_form = RegisterForm(request.POST)
        message = "请检查填写的内容, "+username+"!"
        if register_form.is_valid():  # 获取数据
            message = "验证码对了， 但是请检查填写的内容！"
            email = student_id + '@stu.scu.edu.cn' # SCU邮箱
            if password1 != password2:  # 判断两次密码是否相同
                message = "两次输入的密码不同！"
                return render(request, 'login/register.html', locals())
            else:
                same_name_user = models.User.objects.filter(name=username)
                if same_name_user and list(same_name_user)[0].has_confirmed:  # 用户名唯一
                    message = '用户已经存在，请重新选择用户名！'
                    return render(request, 'login/register.html', locals())
                elif same_name_user and list(same_name_user)[0].has_confirmed == False:
                    same_name_user.delete()
                same_stu_id = models.User.objects.filter(stu_id=student_id)
                if same_stu_id and list(same_stu_id)[0].has_confirmed:   # 学号唯一
                    message = '学生邮箱已被注册，请重新输入邮箱！'
                    return render(request, 'login/register.html', locals())
                elif same_stu_id and list(same_stu_id)[0].has_confirmed == False:
                    same_stu_id.delete()
                same_phone = models.User.objects.filter(phone=phone)
                if same_phone and list(same_phone)[0].has_confirmed:   # 学号唯一
                    message = '手机号码已被注册，请重新输入手机号码！'
                    return render(request, 'login/register.html', locals())
                elif same_phone and list(same_phone)[0].has_confirmed == False:
                    same_phone.delete()
                # 当一切都OK的情况下，创建新用户
                
                new_user = models.User.objects.create()
                new_user.name = username
                new_user.stu_id = student_id
                new_user.password = hash_code(password1)  # 使用加密密码
                new_user.phone = phone
                new_user.save()

                code = make_confirm_string(new_user)
                send_email(email, code)
                message = '请前往邮箱确认！'
                return render(request, 'login/confirm.html') # 跳转确认页面
        else:
            message = '可能是验证码填写错误！'        
    return render(request, 'login/register.html', locals())


def logout(request):
    if not request.session.get('is_login', None):
        return redirect("/")
    request.session.flush()
    # 或者使用下面的方法
    # del request.session['is_login']
    # del request.session['user_id']
    # del request.session['user_name']
    return redirect("/")

def user_confirm(request):
    code = request.GET.get('code', None)
    message = ''
    try:
        confirm = models.ConfirmString.objects.get(code=code)
    except:
        message = '无效的确认请求!'
        return render(request, 'login/confirm.html', locals())

    c_time = confirm.c_time
    now = timezone.now()
    if now > c_time + datetime.timedelta(settings.CONFIRM_DAYS):
        confirm.user.delete()
        message = '您的邮件已经过期！请重新注册!'
        return render(request, 'login/confirm.html', locals())
    else:
        confirm.user.has_confirmed = True
        confirm.user.save()
        confirm.delete()
        message = '感谢确认，请使用账户登录！'
        # 发送消息
        send_notice(confirm.user.name, '恭喜您，账号创建成功，开始您的赏金之旅吧！')
        return render(request, 'login/confirm.html', locals())

# 充值赏金
def recharge(request):
    if not request.session.get('user_name', None):
        return render(request, 'login/login.html', locals())
    return render(request, 'login/recharge.html', locals())

def alipay_pay(request):
    if not request.session.get('user_name', None):
        return redirect('/login/')
    alipayview = AlipayView()
    alipay = alipayview.dispatch(request)
    money = float(request.POST.get('money'))
    trade_no = str(time.time() + random.randint(0, 100))
    query_params = alipay.direct_pay(
        subject='任务悬赏平台<赏金币充值>',
        out_trade_no=trade_no,
        total_amount=money,
    )
    pay_url = "https://openapi.alipaydev.com/gateway.do?{}".format(query_params)#
    username = request.session.get('user_name', None)
    models.OrderInfo.objects.create(order_sn=trade_no, username=username)

    return redirect(pay_url)

def alipay_return(request):
    alipayview = AlipayView()
    alipay = alipayview.dispatch(request)
    if request.method == 'POST':
        alipayview.post(request)
    else:
        alipayview.get(request)
    return redirect('/')


class AlipayView(object):
    """
    支付宝支付
    get方法实现支付宝return_url，如果没有实现也无所谓，post同样可以更新状态
    post方法实现支付宝notify_url，异步更新
    """
    def dispatch(self, request, *args, **kwargs):
        self.alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=settings.APP_NOTIFY_URL,
            app_private_key_path=settings.APP_PRIVATE_KEY_PATH,
            alipay_public_key_path=settings.ALIPAY_PUBLIC_KEY_PATH,
            debug=settings.ALIPAY_DEBUG,
            return_url=settings.RETURN_URL
        )
        #处理返回的url参数
        return self.alipay
        # return super(AlipayView, self).dispatch(request, *args, **kwargs)

    def get(self, request):
        """处理支付宝return_url返回"""
        callback_data = {}
        for key, value in request.GET.items():
            callback_data[key] = value
        sign = callback_data.pop('sign', None)
        self.order_sn = callback_data.get('out_trade_no', None) #订单号
        self.trade_no = callback_data.get('trade_no', None) #支付宝订单号
        self.order_mount = Decimal(callback_data.get('total_amount', None)) # 订单金额

        # 验证签名
        self.verify = self.alipay.verify(callback_data, sign)
        if self.verify:
            self.deposit()
            #返回个人中心页面
        return redirect('/') # 返回主页

    def post(self, request):
        """
        处理notify_url
        """
        callback_data = {}
        for key, value in request.GET.items():
            callback_data[key] = value
        sign = callback_data.pop('sign', None)
        self.order_sn = callback_data.get('out_trade_no', None) #订单号
        self.trade_no = callback_data.get('trade_no', None) #支付宝订单号
        self.order_mount = float(callback_data.get('total_amount', None))
        self.order.save()
        # 验证签名
        self.verify = self.alipay.verify(callback_data, sign)
        if self.verify:
            self.deposit()
        return redirect('/')

    def deposit(self):
        """充值操作

        1.更新用户的金币信息
        2.更新订单状态为交易成功
        """
        def convert_rmb_to_money(rmb):
            return float(rmb) * settings.EXCHANGE_RATE
        # 数据库中查询订单记录
        order = models.OrderInfo.objects.get(order_sn=self.order_sn)
        order.trade_no = self.trade_no

        # 把人民币转换成对应的金币
        rmb = self.order_mount
        money = convert_rmb_to_money(rmb)
        # 更新用户的金币
        user = models.User.objects.get(name=order.username)
        user.money = user.money + Decimal.from_float(money)
        user.save()
        # 订单状态置为交易成功
        order.pay_status = 'TRADE_SUCCESS'
        order.save()
