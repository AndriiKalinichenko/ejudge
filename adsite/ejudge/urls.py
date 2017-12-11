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
from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^problem/(?P<slug>[-\w]+)/$", views.problem, name="problem"),
    url(r"^problem/(?P<slug>[-\w]+)/update/$", views.problem_update, name="problem_update"),
    url(r"^problem/(?P<slug>[-\w]+)/report/$", views.problem_report, name="problem_report"),
    url(r"^contest/(?P<slug>[-\w]+)/report/$", views.contest_report, name="contest_report"),
    url(r"^submission/(?P<id>[\d]+)/grade/$", views.grade_submission, name="grade_submission"),
    # # ajax
    url(r"^problem/(?P<slug>[-\w]+)/template/$", views.problem_submission_template,
        name="problem_submission_template"),
    url(r"^problem/(?P<slug>[-\w]+)/submission/test/$", views.submission_test, name="submission_test"),
    url(r"^problem/(?P<slug>[-\w]+)/submission/results/$", views.submission_results,
        name="submission_results"),
    url(r"^$", views.index, name="index"),
]
