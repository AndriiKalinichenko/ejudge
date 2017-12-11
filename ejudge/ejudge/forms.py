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

    code = forms.CharField(required=False)
    language = forms.ChoiceField(choices=LANGUAGES)
    # todo: submit button on the form

    def __init__(self, *args, **kwargs):
        self.contest_slug_name = kwargs.pop("contest", None)
        # todo: test if it works
        self.fields["problems"] = forms.ChoiceField(choices=self.get_all_problems_for_contest(self.contest_slug_name))
        # user = kwargs.pop('user', AnonymousUser())
        super(SubmissionForm, self).__init__(*args, **kwargs)

    # todo: contest - parameter
    # todo: upload button visibility
