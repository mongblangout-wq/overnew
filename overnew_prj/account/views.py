# account/views.py (통합 및 수정 완료)
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from .tokens import account_activation_token
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
import json
import random
import time

from .models import NewsCategory, Media, UserNews, UserMedia, Notification
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

# --- 템플릿 렌더링 뷰 (GET) ---

def splash(request):
    return render(request, "account/index.html")


def info_step1(request):
    if request.method == 'POST':
        user_name = request.POST.get('user-name')
        age = request.POST.get('user-age')
        gender = request.POST.get('gender')

        signup_data = request.session.get('signup_data', {})
        signup_data.update({
            'name': user_name,
            'age': age,
            'gender': gender,
        })
        request.session['signup_data'] = signup_data

        return redirect('account:info_step2')

    return render(request, "account/info-step1.html")


def info_step2(request):
    if request.method == 'POST':
        stance = request.POST.get('stance')

        signup_data = request.session.get('signup_data', {})
        signup_data['stance'] = stance
        request.session['signup_data'] = signup_data

        return redirect('account:info_step3')

    signup_data = request.session.get('signup_data', {})
    user_name = signup_data.get('name', '')

    return render(request, "account/info-step2.html", {'user_name': user_name})


def info_step3(request):
    if request.method == 'POST':
        preferred_categories = request.POST.getlist('topic')

        signup_data = request.session.get('signup_data', {})
        signup_data['preferred_categories'] = preferred_categories
        request.session['signup_data'] = signup_data

        return redirect('account:info_step4')

    signup_data = request.session.get('signup_data', {})
    user_name = signup_data.get('name', '')

    categories = NewsCategory.objects.all()
    return render(request, "account/info-step3.html", {
        'categories': categories,
        'user_name': user_name,
    })


def info_step4(request):
    if request.method == 'POST':
        preferred_media = request.POST.getlist('media')

        signup_data = request.session.get('signup_data', {})
        signup_data['preferred_media'] = preferred_media
        request.session['signup_data'] = signup_data

        return redirect('account:info_step5')

    signup_data = request.session.get('signup_data', {})
    user_name = signup_data.get('name', '')

    media_list = Media.objects.all()
    return render(request, "account/info-step4.html", {
        'media_list': media_list,
        'user_name': user_name,
    })

def info_step5(request):
    return render(request, "account/info-step5.html")


def signup_complete(request):
    return render(request, "account/signup-complete.html")


@login_required(login_url='account:login')
def notifications_view(request):
    notifications = request.user.notifications.all()[:100]
    return render(request, "account/notifications.html", {"notifications": notifications})


@require_POST
@login_required(login_url='account:login')
def api_notification_read(request, notif_id):
    """알림 1개를 읽음 처리 (본인 알림만)"""
    Notification.objects.filter(pk=notif_id, recipient=request.user).update(is_read=True)
    return JsonResponse({"ok": True})


@require_POST
@login_required(login_url='account:login')
def api_notification_read_all(request):
    """내 알림 전체 읽음 처리"""
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return JsonResponse({"ok": True})


@require_GET
def api_notification_unread_count(request):
    """종 아이콘 배지용 - 비로그인이면 0"""
    if not request.user.is_authenticated:
        return JsonResponse({"count": 0})
    return JsonResponse({"count": request.user.notifications.filter(is_read=False).count()})


def settings_view(request):
    if request.user.is_authenticated:
        return render(request, "account/settings-logged-in.html", {
            "user": request.user
        })
    else:
        return render(request, "account/settings-logged-out.html")


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('feed:feed')
        else:
            messages.error(request, '아이디 또는 비밀번호가 올바르지 않습니다.')
            return render(request, 'account/login.html')

    return render(request, 'account/login.html')


@login_required(login_url='account:login')
def profile_edit_view(request):
    """프로필 수정 페이지 렌더링 (로그인한 사용자의 현재 정보를 서버에서 내려줌)"""
    user = request.user
    user_data = {
        "nickname": user.nickname,
        "age": user.age,
        "gender": user.gender,
        "topics": list(user.acc_usernews_set.values_list('category__code', flat=True)),
        "media": list(user.acc_usermedia_set.values_list('media__code', flat=True)),
    }
    return render(request, "account/profile-edit.html", {"user_data": user_data})


@require_POST
@login_required(login_url='account:login')
@transaction.atomic
def api_profile_update(request):
    """세션 로그인된 사용자의 프로필 정보를 저장 (API)"""
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "잘못된 JSON 형식입니다."}, status=400)

    user = request.user
    nickname = (data.get('nickname') or '').strip()
    age = data.get('age')
    gender = data.get('gender')
    topics = data.get('topics', [])
    media_codes = data.get('media', [])

    if nickname and nickname != user.nickname:
        if User.objects.filter(nickname=nickname).exclude(pk=user.pk).exists():
            return JsonResponse({"ok": False, "error": "이미 사용 중인 닉네임입니다."}, status=409)
        user.nickname = nickname

    if age:
        user.age = age
    if gender:
        user.gender = gender
    user.save()

    UserNews.objects.filter(user=user).delete()
    for category in NewsCategory.objects.filter(code__in=topics):
        UserNews.objects.create(user=user, category=category)

    UserMedia.objects.filter(user=user).delete()
    for media_item in Media.objects.filter(code__in=media_codes):
        UserMedia.objects.create(user=user, media=media_item)

    return JsonResponse({"ok": True})


@require_POST
@login_required(login_url='account:login')
def api_delete_account(request):
    """로그인한 사용자의 계정을 실제로 삭제 (API)"""
    user = request.user
    logout(request)
    user.delete()
    return JsonResponse({"ok": True})


@login_required
def logout_view(request):
    logout(request)
    return redirect('account:login')


@csrf_exempt
@require_POST
def api_login(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "잘못된 JSON 형식입니다."}, status=400)

    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()

    if not username or not password:
        return JsonResponse({"ok": False, "error": "아이디와 비밀번호를 모두 입력해 주세요."}, status=400)

    user = authenticate(request, username=username, password=password)

    if user is not None:
        login(request, user)
        return JsonResponse({"ok": True, "message": "로그인 성공", "user": {"username": user.username, "nickname": user.nickname}})
    else:
        return JsonResponse({"ok": False, "error": "아이디 또는 비밀번호가 올바르지 않습니다."}, status=401)


@csrf_exempt
@require_POST
def send_signup_verification_code(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "잘못된 JSON 형식입니다."}, status=400)

    email = (data.get("email") or "").strip()

    if not email:
        return JsonResponse({"ok": False, "error": "이메일이 필요합니다."}, status=400)

    if User.objects.filter(email=email).exists():
        return JsonResponse({"ok": False, "error": "이미 사용 중인 이메일입니다."}, status=409)

    code_str = "".join([str(random.randint(0, 9)) for _ in range(6)])
    request.session["signup_email"] = email
    request.session["signup_verification_code"] = code_str
    request.session["signup_verification_expires"] = int(time.time()) + 60 * 10

    if not settings.EMAIL_VERIFICATION_REQUIRED:
        print(f"[DEV] {email} 인증번호: {code_str}")
        request.session["email_verified"] = True
        return JsonResponse({"ok": True})

    subject = "[OVERNEW] 회원가입 이메일 인증번호"
    message = f"회원가입을 위한 인증번호는 {code_str} 입니다.\n10분 이내에 입력해 주세요."
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER)

    try:
        send_mail(subject, message, from_email, [email], fail_silently=False)
    except Exception as e:
        return JsonResponse(
            {"ok": False, "error": f"이메일 전송 중 오류가 발생했습니다: {e}"},
            status=500,
        )

    return JsonResponse({"ok": True})


@csrf_exempt
@require_POST
def verify_signup_verification_code(request):
    if not settings.EMAIL_VERIFICATION_REQUIRED:
        request.session["email_verified"] = True
        return JsonResponse({"ok": True, "redirect_url": "/account/signup/step1/"})

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "잘못된 JSON 형식입니다."}, status=400)

    email = (data.get("email") or "").strip()
    code = (data.get("code") or "").strip()

    session_email = request.session.get("signup_email")
    session_code = request.session.get("signup_verification_code")
    session_expires = request.session.get("signup_verification_expires", 0)

    if not session_email or not session_code:
        return JsonResponse({"ok": False, "error": "인증번호를 다시 요청해 주세요."}, status=400)

    if int(time.time()) > session_expires:
        return JsonResponse({"ok": False, "error": "인증번호가 만료되었습니다. 다시 요청해 주세요."}, status=400)

    if email != session_email or code != session_code:
        return JsonResponse({"ok": False, "error": "인증번호가 일치하지 않습니다."}, status=400)

    request.session["email_verified"] = True

    return JsonResponse({"ok": True, "redirect_url": "/account/signup/step1/"})


@csrf_exempt
@require_POST
@transaction.atomic
def api_signup(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Invalid JSON"}, status=400)

    signup_data = request.session.get('signup_data', {})
    email = request.session.get('signup_email')
    is_verified = request.session.get('email_verified', False)

    if settings.EMAIL_VERIFICATION_REQUIRED and (not email or not is_verified):
        return JsonResponse({"ok": False, "error": "이메일 인증이 필요합니다."}, status=403)

    username = data.get('username')
    password = data.get('password')
    nickname = data.get('nickname')

    if User.objects.filter(username=username).exists():
        return JsonResponse({"ok": False, "error": "이미 사용 중인 ID입니다."}, status=409)
    if User.objects.filter(nickname=nickname).exists():
        return JsonResponse({"ok": False, "error": "이미 사용 중인 닉네임입니다."}, status=409)

    user_fields = {
        'username': username,
        'email': email,
        'nickname': nickname,
        'age': signup_data.get('age'),
        'gender': signup_data.get('gender'),
        'stance': signup_data.get('stance'),
    }

    try:
        user = User.objects.create_user(password=password, **user_fields)
    except ValueError as e:
        return JsonResponse({"ok": False, "error": f"User creation failed: {e}"}, status=400)

    category_codes = signup_data.get('preferred_categories', [])
    categories = NewsCategory.objects.filter(code__in=category_codes)
    for category in categories:
        UserNews.objects.create(user=user, category=category)

    media_codes = signup_data.get('preferred_media', [])
    media_list = Media.objects.filter(code__in=media_codes)
    for media_item in media_list:
        UserMedia.objects.create(user=user, media=media_item)

    for key in ['signup_data', 'signup_email', 'email_verified', 'signup_verification_code', 'signup_verification_expires']:
        if key in request.session:
            del request.session[key]

    return JsonResponse({"ok": True, "redirect_url": "/account/signup/complete/"})


def email_verify_view(request):
    return render(request, "account/email_verify.html")