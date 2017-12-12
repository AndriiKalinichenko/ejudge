import re
import urllib
from itertools import repeat
import difflib
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import user_passes_test, login_required
from django.http.response import Http404, HttpResponseForbidden
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

active_required = user_passes_test(lambda u: u.is_active, login_url='/')


def login_and_active_required(view_func):
    decorated_view_func = login_required(active_required(view_func))
    return decorated_view_func


def get_object_for_user_or_404(klass, user, *args, **kwargs):
    """ Assumes that default manager is having for_user method. """
    manager = klass._default_manager
    try:
        return manager.for_user(user).get(*args, **kwargs)
    except AttributeError:
        raise Exception('Manager for %s does not implement for_user method.' %
                        manager.model._meta.object_name)
    except manager.model.DoesNotExist:
        raise Http404('No %s matches the given query.' %
                      manager.model._meta.object_name)


def ajax_required(f):
    """
    AJAX request required decorator
    use it in your views:

    @ajax_required
    def my_view(request):
        ....

    """
    def wrap(request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest()
        return f(request, *args, **kwargs)
    wrap.__doc__=f.__doc__
    wrap.__name__=f.__name__
    return wrap


def build_url(*args, **kwargs):
    get = kwargs.pop('get', {})
    url = reverse(*args, **kwargs)
    if get:
        url += '?' + urllib.urlencode(get)
    return url


def user_id_staff_required(f):
    """
    Gets user from GET/POST parameters and pass it on, but only if request.user
    is staff or if it is actually the same user. The staff can view anything
    logic is implemented in models permission methods, also.

    """
    @login_required
    def wrap(request, *args, **kwargs):
        user_id = request.GET.get('user_id', None)
        if user_id is not None:
            user = get_object_or_404(User, id=user_id)
            if user!=request.user and not request.user.is_staff:
                return HttpResponseForbidden()
        else:
            user = request.user
        return f(request, user, *args, **kwargs)
    wrap.__doc__=f.__doc__
    wrap.__name__=f.__name__
    return wrap


# ------ Test submission utils
def normalize(lines):
    """ Join lines and replace all whitespace-like characters with space. """
    return re.sub('\s+', ' ', "".join(lines)).strip()


def check_output(testcaseout, outfile):
    #TODO: read line by line and compare to reduce memory usage
    with open(testcaseout, "r") as f:
        testoutlines = f.readlines()
    with open(outfile, "r") as f:
        outlines = f.readlines()
    if testoutlines==outlines:
        return "OK"
    elif normalize(testoutlines)==normalize(outlines):
        return "PE"
    return "FA"


def comment_remover(code):
    " Remove c comments."
    def replacer(match):
        s = match.group(0)
        if s.startswith('/'):
            return ""
        else:
            return s
    pattern = re.compile(
        r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
        re.DOTALL | re.MULTILINE
    )
    return re.sub(pattern, replacer, code)


def check_mandatory_deny(md_testcase, code):
    """
    Returns comments list.
    """
    assert md_testcase.type=="MD"
    ret = []
    template = md_testcase.problem.submission_template
    template = comment_remover(''.join(template)).splitlines(True)
    code = comment_remover(''.join(code)).splitlines(True)
    new_code = []
    for line in difflib.ndiff(template, code):
        if line.startswith('+'):
            new_code.append(line[2:])
    with open(md_testcase.input.path, "r") as f:
        mandatory = f.readlines()
    with open(md_testcase.output.path, "r") as f:
        deny = f.readlines()

    def get_pattern_comment(pattern_string, is_mandatory):
        try:
            pattern_string, comment = pattern_string.split("#", 2)
        except ValueError:
            comment = _("Mandatory `%s`") if is_mandatory else _("Denied `%s`")
            comment = comment % pattern_string
        pattern = re.compile(pattern_string.strip())
        return pattern, comment

    for line in mandatory:
        pattern, comment = get_pattern_comment(line, True)
        if not any(list(map(re.search, repeat(pattern), new_code))):
            ret.append(comment)
    for line in deny:
        pattern, comment = get_pattern_comment(line, False)
        if any(list(map(re.search, repeat(pattern), new_code))):
            ret.append(comment)
    return "  \n".join(ret)
