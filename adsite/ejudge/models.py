from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from .managers import ContestManager, ProblemManager, ActiveContestManager, InactiveContestManager


class Contest(models.Model):
    name = models.CharField(max_length=255)
    slug_name = models.SlugField(unique=True)
    start = models.DateTimeField(default=timezone.now)
    end = models.DateTimeField(default=timezone.now)
    contestants = models.ManyToManyField(settings.AUTH_USER_MODEL, null=True)

    objects = ContestManager()
    active = ActiveContestManager()
    inactive = InactiveContestManager()

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.id:
            self.slug_name = slugify(self.name)
        super(Contest, self).save(*args, **kwargs)

    @property
    def is_active(self):
        t = timezone.now()
        return self.start <= t < self.end

    @property
    def has_finished(self):
        return self.end >= timezone.now

    @property
    def has_started(self):
        return self.start >= timezone.now

    @property
    def status(self):
        if self.is_active:
            return 'active'
        elif self.has_finished:
            return 'finished'
        else:
            return 'due'

    @property
    def get_max_score(self):
        return sum([problem.max_score for problem in self.problem_set.all()])

    def get_contestant_score(self, contestant):
        problem_scores = []
        score = {
            "contestant": contestant,
            "problem_scores": problem_scores,
            "total_score": 0,
            "isTested": True
        }
        submission_exists = False

        for problem in self.problem_set.all():
            submission, problem_score = problem.get_submission_score(contestant)

            if submission is not None:
                submission_exists = True
            if problem_score["isTested"]:
                score["total_score"] += problem_score["score"]
            else:
                # If at leas one problem is not tested, then the whole contest score is not tested.
                score["isTested"] = False

            problem_scores.append((problem, submission, problem_score))

        if not submission_exists:
            score["isTested"] = False
        return score

    def get_all_contestants_scores(self):
        scores = []

        for contestant in self.contestants.all():
            scores.append(self.get_contestant_score(contestant))

        return scores


def get_or_create_default_contest():
    # Try to get the latest created contest. If none exists, create new.
    try:
        contest = Contest.objects.all().order_by('id')[0]
    except IndexError:
        contest = Contest(name='First contest')
        contest.save()
    return contest


class Problem(models.Model):
    contest = models.ForeignKey(Contest,
                                null=True,
                                default=get_or_create_default_contest,
                                on_delete=models.SET_NULL)

    name = models.CharField(max_length=255)
    slug_name = models.SlugField(unique=True)
    statement = models.TextField(default='')
    submission_template = models.TextField(default="")
    max_score = models.IntegerField(default=500)

    objects = ProblemManager()

    # todo: tags

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.id:
            self.slug = slugify(self.name)
        super(Problem, self).save(*args, **kwargs)

    def has_view_permission(self, request, for_user):
        # Staff can view all problems.
        if request.user.is_staff:
            return True
        # Others can view problem only as themselves if contest is active and they are contestants.
        if request.user == for_user and self.contest.is_active and request.user in self.contest.contestants.all():
            return True
        return False

    def has_view_report_permission(self, request, for_user):
        # Staff can view all reports.
        if request.user.is_staff:
            return True
        # Others can view their own reports if contest has finished and they were contestants.
        if request.user == for_user and self.contest.has_finished and request.user in self.contest.contestants.all():
            return True
        return False

    def get_submission_score(self, contestant):
        score = {"score": 0,
                 "isTested": False}
        try:
            sub = Submission.objects.get(author=contestant, challenge=self)
        except ObjectDoesNotExist:
            sub = None
            # if there is no submission score is 0
            score["isTested"] = True
        else:
            score["score"] = sub.get_score
            if score["score"] != -1:
                score["isTested"] = True
        return sub, score


class Submission(models.Model):
    STATUSES = (
        ("NT", _('Not Tested')),
        ("CE", _('Compile Error')),
        ("PD", _('Pending')),
        ("TS", _('Tested')),
    )
    RESULTS = STATUSES + (
        ("OK", _('Accepted')),
        ("FA", _('Failed')),
    )
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

    code = models.TextField(default="", blank=True)
    status = models.CharField(max_length=2, default="NT", choices=STATUSES)
    score_percent = models.IntegerField(default=-1)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    is_public = models.BooleanField(default=False)

    class Meta:
        unique_together = ("author", "problem")
        permissions = (
            ("can_test_submission", "Can test submission")
        )

    def save(self, *args, **kwargs):
        if not kwargs.pop('skip_modified', False):
            self.modified_at = timezone.now
        super(Submission, self).save(*args, **kwargs)

    @property
    def get_result(self):
        if self.status != "TS":
            return self.status
        failed_tests = self.test_results.exclude(result__in=["OK"])  # todo: PE?
        return "OK" if len(failed_tests) == 0 else "FA"

    @property
    def get_score(self):
        return self.score_percent * self.problem.max_score / 100.0 if self.score_percent != -1 else -1

    def get_submission_summary(self):
        test_results = self.test_results.all()
        # todo: Presentation Error?
        return "Passed: %d\nTotal: %d" % (len(test_results.filter(status="OK")), len(test_results))

    def has_view_results_permission(self, request, for_user):
        # Only staff can view submission results for certain user
        if request.user.is_staff:
            return True
        # Others can view challenge only as themselves if contest has started # and they are participants
        contest = self.problem.contest
        if request.user == for_user and contest.has_started and request.user in contest.contestants.all():
            return True
        return False


def test_case_input_path(instance, file):
    return "test_cases/input_" + str(instance.problem.id) + ".txt"


def test_case_output_path(instance, file):
    return "test_cases/output_" + str(instance.problem.id) + ".txt"


class TestCase(models.Model):
    TEST_CASE_TYPES = (
        ("IO", _('Input - Output')),
        ("MD", _('Mandatory - Denied')),
    )

    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)

    input = models.FileField(upload_to=test_case_input_path)  # todo hint
    output = models.FileField(upload_to=test_case_output_path)  # todo hint

    cpu_time_limit = models.IntegerField(default=2000)
    wall_clock_time_limit = models.IntegerField(default=6000)
    memory_limit = models.IntegerField(default=8 * 1024 * 1024)

    is_public = models.BooleanField(default=False)

    hint = models.TextField(default="", blank=True)

    type = models.CharField(max_length=2, default="IO", choices=TEST_CASE_TYPES)

    @property
    def short_hint(self):
        return "%s" % self.hint[:30]

    def get_input(self):
        with open(self.input.path) as fp:
            return fp.read()

    def get_output(self):
        with open(self.output.path) as fp:
            return fp.read()


class TestResult(models.Model):
    STATUSES = (
        ("PD", _("Pending")),  # gettext
        ("OK", _("Okay")),
        ("RF", _("Restricted Function")),
        ("ML", _("Memory Limit Exceed")),
        ("OL", _("Output Limit Exceed")),
        ("TL", _("Time Limit Exceed")),
        ("RT", _("Run Time Error (SIGSEGV, SIGFPE, ...)")),
        ("AT", _("Abnormal Termination")),
        ("IE", _("Internal Error (of sandbox executor)")),
        ("BP", _("Bad Policy")),
        ("R0", _("Reserved result type 0")),  # todo: do we need these?
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

    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='test_results')
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name='test_results')

    task_id = models.CharField(max_length=255, default='')
    status = models.CharField(max_length=2, default="PD", choices=STATUSES)
    memory = models.IntegerField(default=0)
    cpu_time = models.IntegerField(default=0)
    result = models.CharField(max_length=2, default="PD", choices=RESULTS)

    class Meta:
        unique_together = ("submission", "test_case")

    def save(self, *args, **kwargs):
        if self.status not in ["OK", "PD"]:
            self.result = "FA"
        if self.status == "PD":
            self.result = "PD"
        super(TestResult, self).save(*args, **kwargs)
