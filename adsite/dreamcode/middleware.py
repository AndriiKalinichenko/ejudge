from __future__ import absolute_import
from django.http import HttpResponseForbidden

from adsite.settings import OJ_IP_FILTER, OJ_USERS_IPS, OJ_PROXY_SIGNATURE, \
    OJ_REMOTE_ADDR


def get_ip(request):
    return request.META.get("HTTP_X_FORWARDED_FOR", "").strip().split(',')[0]


def get_proxy(request):
    return request.META.get("HTTP_VIA", "").strip().split(',')[0]


def get_remote_addr(request):
    return request.META.get("REMOTE_ADDR", "").strip()


class UserIPFilter(object):
    def process_request(self, request):
        if not OJ_IP_FILTER:
            return None
        #TODO: check if user is in request
        if request.user.is_superuser:
            return None

        for_user_ip = dict(OJ_USERS_IPS).get(request.user.username, None)
        real_ip = get_ip(request)

        user_is_inside = real_ip in dict(OJ_USERS_IPS).values()
        #protect access to other accounts from the inside
        if (user_is_inside and not request.user.is_anonymous() and
                for_user_ip!=real_ip):
            return HttpResponseForbidden()

        #protect access to the user account from the outside
        if for_user_ip is None:
            return None
        proxy = get_proxy(request)
        remote_addr = get_remote_addr(request)
        if (for_user_ip!=real_ip or proxy!=OJ_PROXY_SIGNATURE or
                remote_addr!=OJ_REMOTE_ADDR):
            return HttpResponseForbidden()
