from django.utils.translation import ugettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Button
from django import forms
from django_ace import AceWidget
from taggit.forms import TagField
from django.contrib.auth.models import AnonymousUser


class ChallengeProblemForm(forms.Form):
    problem = forms.CharField(widget=AceWidget(
                   mode='markdown', theme='monokai', width="100%",
                   wordwrap=True, minlines=21, maxlines=-1))
    tags = TagField()

    def __init__(self, *args, **kwargs):
        super(ChallengeProblemForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'challenge'
        self.helper.layout = Layout(
            Submit('Submit', _('Save'), css_class='top'),
            Field('tags'),
            Field('problem'),
        )
        self.helper.form_show_labels = False


class ChallengeTemplateForm(forms.Form):
    submission_template = forms.CharField(widget=AceWidget(
                                   mode='c_cpp', theme='merbivore_soft',
                                   width="100%", minlines=21, maxlines=-1))

    def __init__(self, *args, **kwargs):
        super(ChallengeTemplateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Submit('Submit', _('Save'), css_class='top'),
            Field('submission_template'),
        )
        self.helper.form_show_labels = False


class SubmissionForm(forms.Form):
    code = forms.CharField(widget=AceWidget(
                                mode='c_cpp', theme='merbivore_soft',
                                width="100%", minlines=21, maxlines=-1),
                           required=False)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', AnonymousUser())
        super(SubmissionForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'submission'
        fields = [
            Button('Reset', _('Reset'), css_class='top btn-warning',
                   css_id="reset"),
            Field('code'),
        ]
        if user.has_perm('onlinejudge.can_test_submission'):
            fields = [Submit('Submit', _('Submit & Run'), css_class='top'),
                      ] + fields
        self.helper.layout = Layout(*fields)
        self.helper.form_show_labels = False
