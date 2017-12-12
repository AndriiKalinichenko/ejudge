from __future__ import absolute_import
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.template.defaultfilters import slugify
from django.conf import settings
from taggit.managers import TaggableManager
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from .managers import ChallengeManager, ContestManager
from .managers import ActiveContestManager,\
    InactiveContestManager


class Contest(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    start = models.DateTimeField(default=timezone.now)
    finish = models.DateTimeField(default=timezone.now)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, null=True)

    objects = ContestManager()
    active = ActiveContestManager()
    inactive = InactiveContestManager()

    class Meta:
        verbose_name = _('Contest')
        verbose_name_plural = _('Contests')

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.id:
            self.slug = slugify(self.name)
        super(Contest, self).save(*args, **kwargs)

    @property
    def is_active(self):
        t = timezone.now()
        return t>self.start and t<self.finish

    @property
    def is_finished(self):
        return self.end <= timezone.now()

    @property
    def has_started(self):
        return self.start >= timezone.now()

    @property
    def status(self):
        if self.is_active:
            return 'active'
        elif self.is_finished:
            return 'finished'
        else:
            return 'due'

    @property
    def score_max(self):
        return sum([ch.score for ch in self.challenge_set.all()])

    def get_participant_scores(self, participant):
        challenges_submissions_scores = []
        score = {"participant": participant,
                 "challenges": challenges_submissions_scores,
                 "score": 0,
                 "graded": True}
        sub_exist = False
        for ch in self.challenge_set.all():
            sub, sc = ch.get_submission_score(participant)
            if sub is not None:
                sub_exist = True
            if sc["graded"]:
                score["score"] += sc["score"]
            else:
                score["graded"] = False
            challenges_submissions_scores.append((ch, sub, sc))
        # if there is no submission then contest could not be graded
        if not sub_exist:
            score["graded"] = False
        return score

    def get_participants_scores(self):
        """ Returns [{
                     "participant": participant,
                     "challenges": [(challenge, submission, score), ...],
                     "score": score,
                     "graded" : True/False,
                    },...]
        """
        scores = []
        for participant in self.participants.all():
            scores.append(self.get_participant_scores(participant))
        return scores


def get_or_create_default_contest():
    """ Default contest is the first one created. If not create one."""
    try:
        contest = Contest.objects.all().order_by('id')[0]
    except IndexError:
        contest = Contest(name='Initial contest')
        contest.save()
    return contest


class Challenge(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    problem = models.TextField(default="")
    submission_template = models.TextField(default="")
    # tags = TaggableManager()
    contest = models.ForeignKey(Contest, null=False,
                                default=get_or_create_default_contest)
    score = models.IntegerField(default=5)

    objects = ChallengeManager()

    class Meta:
        verbose_name = _('Challenge')
        verbose_name_plural = _('Challenges')

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.id:
            self.slug = slugify(self.name)
        super(Challenge, self).save(*args, **kwargs)

    def has_view_permission(self, request, for_user):
        # Only staff can view challenge for certain user, i.e. as certain user
        if request.user.is_staff:
            return True
        # Others can view challenge only as themselves if contest is active
        # and they are participants
        if request.user==for_user and self.contest.is_active and \
            request.user in self.contest.participants.all():
            return True
        return False

    def has_view_report_permission(self, request, for_user):
        # Only staff can view challenge report for certain user
        if request.user.is_staff:
            return True
        # Others can view their own reports if contest is finished
        # and they were participants
        if request.user==for_user and self.contest.is_finished and \
            request.user in self.contest.participants.all():
            return True
        return False

    def get_submission_score(self, participant):
        score = {"score": 0,
                 "graded": False}
        try:
            sub = Submission.objects.get(author=participant, challenge=self)
        except ObjectDoesNotExist:
            sub = None
            # if there is no submission score is 0
            score["graded"] = True
        else:
            if sub.score_percentage!=-1:
                score["score"] = sub.score
                score["graded"] = True
        return (sub, score)


class Submission(models.Model):
    STATUSES = (
                ("NT", _('Untested')),
                ("CE", _('Compile Error')),
                ("PD", _('Pending')),
                ("TS", _('Tested')),
               )
    RESULTS = STATUSES + (
                          ("OK", _('Accepted')),
                          ("FA", _('Failed')),
                         )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                              on_delete=models.SET_NULL)
    code = models.TextField(default="", blank=True)
    challenge = models.ForeignKey(Challenge)
    status = models.CharField(max_length=2, default="NT",
                              choices=STATUSES)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(editable=False)
    score_percentage = models.IntegerField(default=-1)
    #language = models.ForeignKey()
    is_public = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not kwargs.pop('skip_modified', False):
            self.modified = timezone.now()
        super(Submission, self).save(*args, **kwargs)

    class Meta:
        unique_together = ("author", "challenge")
        verbose_name = _('Submission')
        verbose_name_plural = _('Submissions')
        ordering = ['-modified']
        permissions = (
            ('can_test_submission', 'Can test submission'),
        )

    @property
    def result(self):
        if self.status!="TS":
            return self.status
        failed_results = self.test_results.exclude(result__in=["OK", "PE"])
        return "OK" if len(failed_results)==0 else "FA"

    @property
    def score(self):
        return self.score_percentage*self.challenge.score/100 if self.score_percentage!=-1 else -1

    def test_results_summaryp(self):
        test_results = self.test_results.all()
        return "%d/%d/%d" % (len(test_results.filter(result__in=['OK', 'PE'])),
                             len(test_results.filter(status='OK')),
                             len(test_results))
    test_results_summaryp.short_description = _("Result summary")
    test_results_summary = property(test_results_summaryp)

    def has_view_results_permission(self, request, for_user):
        # Only staff can view submission results for certain user
        if request.user.is_staff:
            return True
        # Others can view challenge only as themselves if contest has started
        # and they are participants
        contest = self.challenge.contest
        if request.user==for_user and contest.has_started and \
            request.user in contest.participants.all():
            return True
        return False


def testcasein_upload_path(instance, filename):
    return "/".join(["testcases", "input_"+str(instance.challenge.id)])+'.txt'


def testcaseout_upload_path(instance, filename):
    return "/".join(["testcases", "output_"+str(instance.challenge.id)])+'.txt'


class TestCase(models.Model):
    TEST_CASE_TYPES = (
                       ("IO", _('Input - Output')),
                       ("MD", _('Mandatory - Denied')),
                       )
    input = models.FileField(upload_to=testcasein_upload_path,
                             help_text=_("Input or mandatory"))
    output = models.FileField(upload_to=testcaseout_upload_path,
                              help_text=_("Output or deny"))
    challenge = models.ForeignKey(Challenge)
    cpu_time_limit = models.IntegerField(default=2000)
    wallclock_time_limit = models.IntegerField(default=6000)
    memory_limit = models.IntegerField(default=8*1024*1024)
    disk_limit = models.IntegerField(default=0)  # not used
    is_public = models.BooleanField(default=False)
    hint = models.TextField(default="", blank=True,
                            help_text=_("Only the first line is shown in "
                                        "hint. If test case is public, hint "
                                        "is appended to the challenge text."))
    type = models.CharField(max_length=2, default="IO",
                            choices=TEST_CASE_TYPES)

    class Meta:
        ordering = ['-is_public']

    @property
    def hint_short(self):
        return "%s" % self.hint[:30]

    def display_input(self):
        with open(self.input.path) as fp:
            return fp.read()

    def display_output(self):
        with open(self.output.path) as fp:
            return fp.read()


class TestResult(models.Model):
    STATUSES = (
                ("PD", _("Pending")),
                ("OK", _("Okay")),
                ("RF", _("Restricted Function")),
                ("ML", _("Memory Limit Exceed")),
                ("OL", _("Output Limit Exceed")),
                ("TL", _("Time Limit Exceed")),
                ("RT", _("Run Time Error (SIGSEGV, SIGFPE, ...)")),
                ("AT", _("Abnormal Termination")),
                ("IE", _("Internal Error (of sandbox executor)")),
                ("BP", _("Bad Policy")),
                ("R0", _("Reserved result type 0")),
                ("R1", _("Reserved result type 1")),
                ("R2", _("Reserved result type 2")),
                ("R3", _("Reserved result type 3")),
                ("R4", _("Reserved result type 4")),
                ("R5", _("Reserved result type 5")),
                ("EX", _("Exception")),
                )
    RESULTS = (
               ("PD", _("Pending")),
               ("OK", _("Accepted")),
               ("PE", _("Presentation error")),
               ("FA", _("Failed")),
              )
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE,
                                   related_name='test_results')
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE,
                                  related_name='test_results')
    task_id = models.CharField(max_length=255, default='')
    status = models.CharField(max_length=2, default="PD", choices=STATUSES)
    memory = models.IntegerField(default=0)
    cputime = models.IntegerField(default=0)
    result = models.CharField(max_length=2, default="PD", choices=RESULTS)

    class Meta:
        unique_together = ("submission", "test_case")

    def save(self, *args, **kwargs):
        if self.status not in ["OK", "PD"]:
            self.result = "FA"
        if self.status=="PD":
            self.result = "PD"
        super(TestResult, self).save(*args, **kwargs)
