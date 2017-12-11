"""ejudge URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from . import views


from django.utils.translation import ugettext_lazy as _
from django.conf.urls import patterns, url

urlpatterns = patterns('ejudge.views',
    url(_(r"^$"),                                               "index",                         {}, "index"),
    # url(_(r"^problem/(?P<slug>[-\w]+)/$"),                    "problem",                     {}, "problem"),
    # url(_(r"^problem/(?P<slug>[-\w]+)/update/$"),             "problem_update",              {}, "problem_update"),
    # url(_(r"^problem/(?P<slug>[-\w]+)/report/$"),             "problem_report",              {}, "problem_report"),
    # url(_(r"^contest/(?P<slug>[-\w]+)/report/$"),               "contest_report",                {}, "contest_report"),
    # url(_(r"^submission/(?P<id>[\d]+)/grade/$"),                "grade_submission",              {}, "grade_submission"),
    # # ajax
    # url(_(r"^problem/(?P<slug>[-\w]+)/template/$"),           "problem_submission_template", {}, "problem_submission_template"),
    # url(_(r"^problem/(?P<slug>[-\w]+)/submission/test/$"),    "submission_test",               {}, "submission_test"),
    # url(_(r"^problem/(?P<slug>[-\w]+)/submission/results/$"), "submission_results",            {}, "submission_results"),
)