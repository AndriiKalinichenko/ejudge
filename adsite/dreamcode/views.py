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
                  {'submission_template': problem.statement})
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
    if "tags" in request.POST:
        tags = request.POST["tags"]
        try:
            tags = parse_tags(tags)
        except ValueError:
            raise forms.ValidationError(
                _("Please provide a comma-separated list of tags."))
        problem.tags.clear()
        problem.tags.add(*tags)
    return HttpResponseRedirect(reverse('problem', kwargs={'slug': slug}))


@ajax_required
@require_GET
@permission_required('dreamcode.add_submission')
def problem_submission_template(request, slug):
    ch = get_object_for_user_or_404(Problem, request.user, slug=slug)
    return HttpResponse(json.dumps({"template": ch.submission_template}),
                        content_type='application/json')


@ajax_required
@require_POST
@user_id_staff_required
@permission_required('dreamcode.can_test_submission')
def submission_test(request, user, slug):
    """ Saves and tests posted submission. """
    problem = get_object_or_404(Problem, slug=slug)
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

    # Compile code
    #TODO: move to celery task as chain
    program_name = "program_%s_%s_%s" % (
                                     problem.slug, user.username,
                                     datetime.now().strftime("%y%m%d-%H%M%S"))
    program = os.path.join(OJ_PROGRAM_ROOT, program_name)
    source_file = program+".c"
    with open(source_file, "w") as f:
        f.write(submission.code.encode('utf-8').replace('\r', ''))
    c = subprocess.Popen((OJ_COMPILE_COMMAND % {'program': program}).split(),
                          stdin=PIPE, stdout=PIPE, stderr=PIPE)
    (compile_out, compile_err) = c.communicate()
    ret = c.poll()
    os.remove(source_file)
    if ret!=0:
        submission_status = "CE"  # Compile error
    else:
        test_cases = problem.testcase_set.filter(type="IO")
        # Run testcases
        for (i, tc) in enumerate(test_cases):
            outpath = "%s_out%03d.txt" % (program, i)
            errpath = "%s_err%03d.txt" % (program, i)
            task_configuration = {
                'args': [program],
                'inpath': tc.input.path,
                'outpath': outpath,
                'errpath': errpath,
                'quota': dict(
                              wallclock=tc.wallclock_time_limit,
                              cpu=tc.cpu_time_limit,
                              memory=tc.memory_limit,
                              # This is stdout limit since stdout is disk file.
                              disk=tc.output.size*2
                              #disk=tc.disk_limit
                              ),
                }
            # Nonblocking call
            #result = run_popen.delay(**task_configuration)  #@UndefinedVariable
            #res = run.delay(**task_configuration)  #nonblocking
            test_result, _created = TestResult.objects.get_or_create(
                                                         submission=submission,
                                                         test_case=tc)
            #test_result.task_id = result.id
            test_result.status = "PD"  # Pending
            test_result.save()
        if len(test_cases)>0:
            submission_status = "PD"
        else:
            submission_status = "NT"  # Not tested
    submission.status = submission_status
    submission.save()
    return HttpResponse(
        json.dumps({"submission_status": submission.status,
                    "compile_out": escape(compile_out.replace(program,
                                                              'program')),
                    "compile_err": escape(compile_err.replace(program,
                                                              'program')),
                    }),
        content_type='application/json')


@ajax_required
@require_GET
@user_id_staff_required
@permission_required('dreamcode.can_test_submission')
def submission_results(request, user, slug):
    """ Returns existing submissions results for IO test cases. """
    problem = get_object_or_404(Problem, slug=slug)
    submission = get_object_or_404(Submission, problem=problem,
                                   author=user,)
    if not submission.has_view_results_permission(request, for_user=user):
        return HttpResponseForbidden()

    trace = ""
    result = None
    for tr in TestResult.objects.filter(submission=submission, status="PD"):
        async_result = AsyncResult(tr.task_id)
        if async_result.ready():
            result = async_result.result
            trace = str(result)
            # regular run task result is either Exception instance or dict
            #if isinstance(result, Exception):  # for regular run task
            # run_popen check if in result string there is Exception traceback
            if "Traceback" in trace:
                tr.status = 'EX'
            else:
                # run_popen task result is json string so convert it to dict
                result = json.loads(trace)
                tr.status = result['status']
                tr.memory = result['memory']
                tr.cputime = result['cputime']
                tr.result = check_output(tr.test_case.output.path,
                                         result['outpath'])
            # remove celery task meta from the database
            # try:
            #     tm = TaskMeta.objects.get(task_id=tr.task_id)
            # except TaskMeta.DoesNotExist:
            #     pass
            # else:
            #     tm.delete()
            os.remove(result['outpath'])
            os.remove(result['errpath'])
            tr.save()
    #if there are no pending test results delete program
    if len(TestResult.objects.filter(submission=submission, status="PD"))==0:
        if result is not None:
            os.remove(result['program'])
    test_results = TestResult.objects.filter(submission=submission)
    trs = [{'status': dict(TestResult.STATUSES)[tr.status],
            'status_code': tr.status.lower(),
            'result': dict(TestResult.RESULTS)[tr.result],
            'result_code': tr.result.lower(),
            'memory': tr.memory,
            'cputime': tr.cputime,
            'test_case': tr.test_case,
            }
           for tr in test_results]
    if (len(test_results)>0 and len(test_results.filter(status="PD"))==0 and
            submission.status!="TS"):
        submission.status = "TS"  # Tested
        submission.save()
    return render_to_response(
        "dreamcode/partials/submission_results.html",
        {
         "submission": submission,
         "submission_result_code": submission.result.lower(),
         "submission_result": dict(Submission.RESULTS)[submission.result],
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
