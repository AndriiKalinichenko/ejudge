from django import forms
from django.shortcuts import get_object_or_404

from models import *
# from django.contrib.auth.models import AnonymousUser


def get_all_problems_for_contest(contest_slug_name):
    # DoesNotExist exception is not caught on purpose.
    contest = get_object_or_404(Contest, slug_name=contest_slug_name)
    return contest.problem_set()


class SubmissionForm(forms.Form):
    LANGUAGES = (
        ("C++", "C++"),
        ("C", "C"),
        ("Python", "Python")
    )

    language = forms.ChoiceField(choices=LANGUAGES)
    code = forms.CharField(required=False)
    # todo: submit button on the form

    def __init__(self, *args, **kwargs):
        # todo: test if it works
        # user = kwargs.pop('user', AnonymousUser())
        super(SubmissionForm, self).__init__(*args, **kwargs)

    # todo: contest - parameter
    # todo: upload button visibility
