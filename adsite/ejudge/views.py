from __future__ import absolute_import
import os
import json
import subprocess
from subprocess import PIPE
from datetime import datetime
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import permission_required
from django.template.context import RequestContext
from django.http.response import HttpResponseRedirect, HttpResponse, \
    HttpResponseForbidden
from django.core.urlresolvers import reverse
from django import forms
from django.utils.html import escape
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.http import require_GET, require_POST
# from taggit.utils import parse_tags
# from celery.result import AsyncResult
# from .forms import ChallengeProblemForm, ChallengeTemplateForm, SubmissionForm
# from .models import TestResult, Contest, Challenge, Submission
# # from .settings import OJ_COMPILE_COMMAND, OJ_PROGRAM_ROOT
# # from .tasks import run_popen
# # from .utils import login_and_active_required, check_output, ajax_required, \
#     get_object_for_user_or_404, build_url, user_id_staff_required
# from djcelery.models import TaskMeta# Create your views here.
