# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
from datetime import datetime

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.http.response import JsonResponse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View

from django_auth.models import User
from django_auth.views.base import api_common, get_ip


class APIUserLoginView(View):
    def post(self, request):
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        mobilecode = request.POST.get('mobilecode', '')
        keepLogin = request.POST.get('keepLogin', '')

        if mobilecode and mobilecode is not None and mobilecode != '':
            # mobile + code
            verfication_code = request.session.get('verfication_code', '')
            request.session['verfication_code'] = ''
            if settings.DEBUG or (verfication_code and str(verfication_code) == str(mobilecode)):
                ggac_user = User.objects.get_user(mobile=username)
                if ggac_user is None:
                    response = api_common({}, -1, _("User not exist"))
                    return JsonResponse(response)
            else:
                response = api_common({}, -2, _("Incorrect code"))
                return JsonResponse(response)
        else:
            # username/mobile + password
            ggac_user = User.objects.get_user(username=username)
            wrong_passwd = False
            if ggac_user:
                # username + password
                user = authenticate(username=username, password=password)
                if not user:
                    wrong_passwd = True
            else:
                # mobile + password
                ggac_user = User.objects.get_user(mobile=username)
                if ggac_user:
                    user = authenticate(username=ggac_user.username, password=password)
                    if not user:
                        wrong_passwd = True
            if ggac_user and not ggac_user.is_active:
                response = api_common({}, -3, _("User banned"))
                return JsonResponse(response)
            if wrong_passwd:
                response = api_common({}, -4, _("Incorrect password"))
                return JsonResponse(response)

        if ggac_user and ggac_user.is_active:
            login(request, ggac_user)
            if keepLogin == 'true':
                request.session.set_expiry(datetime.today().year + 1)
            response = api_common({})
            return JsonResponse(response)
        else:
            response = api_common({}, -5, _("User not exist"))
            return JsonResponse(response)


class APIUserLogoutView(View):
    def post(self, request):
        if request.user.is_authenticated():
            logout(request)
        response = api_common({})
        return JsonResponse(response)


class APIUserRegisterView(View):
    def is_valid(self, str):
        for i in str:
            if i in ['\'', '"', '\\']:
                return 0
        return 1

    def post(self, request):
        country_code = request.POST.get('country_code', '')
        mobile = request.POST.get('mobile', '')
        mobilecode = request.POST.get('mobilecode', '')
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')

        if country_code:
            find_lst = re.findall("\d+\.?\d*", country_code)
            country_code = str([int(item) for item in find_lst][0])

        verfication_code = request.session.get('verfication_code', '')
        request.session['verfication_code'] = ''

        if settings.DEBUG or (verfication_code and str(verfication_code) == str(mobilecode)):
            if not self.is_valid(username):
                response = api_common({}, -1, _("Incorrect username"))
                return JsonResponse(response)
            if not self.is_valid(password):
                response = api_common({}, -2, _("Incorrect password"))
                return JsonResponse(response)

            ggacUser = User.objects.filter(mobile=mobile).first()
            if ggacUser:
                response = api_common({}, -3, _("Mobile has been registered"))
                return JsonResponse(response)

            ggacUser = User.objects.filter(username=username).first()
            if ggacUser:
                response = api_common({}, -4, _("Username has been registered"))
                return JsonResponse(response)

            user = User.objects.create_user(username=username, email=None, password=password)
            user.country_code = country_code
            user.mobile = mobile
            user.save(request=request)

            # Login after registered
            login(request, user)
            request.session.set_expiry(datetime.today().year + 1)

            response = api_common({})
            return JsonResponse(response)
        else:
            response = api_common({}, -5, _("Incorrect code"))
            return JsonResponse(response)
