from __future__ import absolute_import
import os
import json
from .tasks import test_code
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
from taggit.utils import parse_tags
from celery.result import AsyncResult
from .forms import ChallengeProblemForm, ChallengeTemplateForm, SubmissionForm
from .models import TestResult, Contest, Problem, Submission
from adsite.settings import OJ_COMPILE_COMMAND, OJ_PROGRAM_ROOT
from .utils import login_and_active_required, check_output, ajax_required, \
    get_object_for_user_or_404, build_url, user_id_staff_required
# from djcelery.models import TaskMeta


@require_GET
def index(request):
    contests = []
    for con in (Contest.objects.for_user(request.user)
                                .filter(problem__isnull=False).distinct()):
        con.score = con.get_contestant_score(request.user)
        problems = []
        for ch in con.problem_set.all():
            try:
                submission = ch.submission_set.get(author=request.user)
            except ObjectDoesNotExist:
                submission = {'result': 'NT'}
            ch.score_calculated = ch.get_submission_score(request.user)[1]
            problems.append((ch, submission))
        if problems:
            contests.append((con, problems))

    return render_to_response("dreamcode/index.html",
                              {
                               "contests": contests,
                               },
                              RequestContext(request),
                              )


#TODO: add django logs
@require_GET
@user_id_staff_required
@login_and_active_required
def problem(request, user, slug):
    """ Main problem view with all required forms. """
    problem = get_object_or_404(Problem, slug=slug)
    if not problem.has_view_permission(request, for_user=user):
        return HttpResponseForbidden()

    problem_form = ChallengeProblemForm({
                                         'problem': problem.statement})
    problem_form.helper.form_action = reverse('problem_update',
                                              kwargs={'slug': problem.slug})

    template_form = ChallengeTemplateForm(
                  {'submission_template': problem.submission_template})
    template_form.helper.form_action = reverse('problem_update',
                                               kwargs={'slug': problem.slug})

    submission, created = Submission.objects.get_or_create(
                                                       problem=problem,
                                                       author=user,
                                                       defaults={"code": ""})
    public_submissions = Submission.objects.filter(problem=problem,
                                                   is_public=True)
    if created or submission.code.strip()=="":
        submission.code = problem.statement
    submission_form = SubmissionForm(
                          {
                           'author': str(submission.author.id),
                           'problem': str(submission.problem.id),
                           'code': submission.code,
                          }, user=user)
    submission_form.helper.form_action = reverse(
                                             'submission_test',
                                             kwargs={'slug': problem.slug})
    public_test_cases = problem.testcase_set.filter(is_public=True)
    return render_to_response("dreamcode/problem.html",
                              {
                               "problem_problem_form": problem_form,
                               "problem_template_form": template_form,
                               "submission_form": submission_form,
                               "problem": problem,
                               "public_test_cases": public_test_cases,
                               "public_submissions": public_submissions,
                               },
                               RequestContext(request),
                              )


@require_GET
@user_id_staff_required
def problem_report(request, user, slug):
    """
    Challenge report uses the same template as problem only without
    submission form.

    """
    problem = get_object_or_404(Problem, slug=slug)
    if not problem.has_view_report_permission(request, for_user=user):
        return HttpResponseForbidden()

    contest = problem.contest
    submission, score = problem.get_submission_score(user)
    public_submissions = Submission.objects.filter(problem=problem,
                                                   is_public=True)
    return render_to_response("dreamcode/problem_report.html",
                              {
                               "user": user,
                               "contest": contest,
                               "problem": problem,
                               "score": score,
                               "submission": submission,
                               "public_submissions": public_submissions,
                               },
                               RequestContext(request),
                              )


@require_POST
@permission_required('dreamcode.can_change_problem')
def problem_update(request, slug):
    """ Used for updating problem, tags and template via frontend. """
    problem = get_object_for_user_or_404(Problem, request.user, slug=slug)
    if "problem" in request.POST:
        problem.problem = request.POST["problem"]
    if "submission_template" in request.POST:
        problem.submission_template = request.POST["submission_template"]
    problem.save()
    return HttpResponseRedirect(reverse('problem', kwargs={'slug': slug}))


@ajax_required
@require_GET
@permission_required('dreamcode.add_submission')
def problem_submission_template(request, slug):
    ch = get_object_for_user_or_404(Problem, request.user, slug=slug)
    return HttpResponse(json.dumps({"template": ch.submission_template}),
                        content_type='application/json')


def submission_test(request, slug):
    """ Saves and tests posted submission. """
    problem = get_object_or_404(Problem, slug=slug)
    user = request.user
    submission = get_object_or_404(Submission, problem=problem,
                                   author=user)
    if not submission.problem.has_view_permission(request, for_user=user):
        return HttpResponseForbidden()

    #TODO: if submission is pending do not run again just return current status
    #if submission.status=="PD":
    #    return HttpResponse(simplejson.dumps({"submission":
    #                                         {"status": submission.status}}),
    #                content_type='application/json')

    # Update code
    if "code" in request.POST:
        submission.code = request.POST["code"]
        submission.language = "python"

    test_cases = problem.testcase_set.all()
    test_results = []
    for test_case in test_cases:
        response = test_code(submission.code, submission.language, test_case.input, test_case.output)
        test_result, _created = TestResult.objects.get_or_create(submission=submission, test_case=test_case)
        # test_result.task_id = response.id
        test_result.status = response#"PD"  # pending
        print(response)
        test_result.save()
        with open(str(test_case.input), 'r') as myfile:
            inp_scr = myfile.read()
        with open(str(test_case.output), 'r') as myfile:
            out_scr = myfile.read()
        test_results.append({"status": test_result.status, "input": inp_scr[:40], "output": out_scr[:40]})



    # if len(test_cases) > 0:
    #     submission_status = "PD"  # pending
    # else:
    #     submission_status = "NT"  # not tested
    #
    # submission.status = submission_status
    if (len(TestResult.objects.filter(submission=submission)) == len(TestResult.objects.filter(submission=submission, status="OK"))):
        submission.result = "OK"
    else:
        submission.result = "FA"
    submission.save()
    # return HttpResponse(
    #     json.dumps({"submission_status": submission.status}),
    #     content_type='application/json')
    return render_to_response(
        "dreamcode/partials/submission_results.html",
        {
            "problem": problem,
            "submission": submission,
            "test_results": test_results,  # TestResult.objects.filter(submission=submission),
            "submission_result": submission.result
        },
        RequestContext(request),
    )


@require_GET
def submission_results(request, slug):
    """ Returns existing submissions results for IO test cases. """
    problem = get_object_or_404(Problem, slug=slug)
    user = request.user
    submission = get_object_or_404(Submission, problem=problem,
                                   author=user,)
    if not submission.has_view_results_permission(request, for_user=user):
        return HttpResponseForbidden()
    
    trace = ""
    result = None
    for tr in TestResult.objects.filter(submission=submission, status="PD"):
        # async_result = AsyncResult(tr.task_id)
         if True:#async_result.ready():
            # result = async_result.result
            results = ["PD", "OK", "FA"]
            if result in results:
                tr.status = result
            else:
                tr.status = "EX"
            tr.save()

    if len(TestResult.objects.filter(submission=submission, status="PD"))==0:
        if result is not None:
            os.remove(result['program'])
    test_results = TestResult.objects.filter(submission=submission)
    trs = []
    for tr in test_results:
        print(tr.status)
        with open(str(tr.test_case.input), 'r') as myfile:
            inp_scr = myfile.read()
        with open(str(tr.test_case.output), 'r') as myfile:
            out_scr = myfile.read()
        trs.append({"status": tr.status, "input": inp_scr[:40], "output": out_scr[:40]})
    # for tr in list(test_results):
    #     trs.append({'status': tr.status,
    #         'result_code': tr.result,
    #         'test_case': tr.test_case,
    #         }
    #     )

    if (len(test_results) == len(test_results.filter(status="OK"))):
        submission.result = "OK"
    else:
        submission.result = "FA"
    submission.save()
    return render_to_response(
        "dreamcode/partials/submission_results.html",
        {
         "problem": problem,
         "submission": submission,
         "submission_result": submission.result,
         "test_results": trs,
         "trace": trace,
         },
         RequestContext(request),
     )


@require_GET
@staff_member_required
def contest_report(request, slug):
    contest = get_object_or_404(Contest, slug=slug)
    return render_to_response("dreamcode/contest_report.html",
                              {
                               "contest": contest,
                               "scores": contest.get_all_contestants_scores(),
                               },
                               RequestContext(request),
                              )


#TODO: temporary solution for grading
@require_POST
@staff_member_required
def grade_submission(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    score_percentage = int(request.POST.get("score_percentage", -1))
    if score_percentage>=-1 and score_percentage<=100:
        submission.score_percentage = score_percentage
        submission.save(skip_modified=True)
    return HttpResponseRedirect(
                            build_url("problem_report",
                                      args=[submission.problem.slug],
                                      get={'user_id': submission.author.id}))
