from django.http import HttpResponse
from forms import SubmissionForm
from django.shortcuts import render


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


def submit_solution(request, problem_slug):
    if request.method == "POST":
        # todo: process form data
        return 0
    else:
        form = SubmissionForm()

    return render(request, "submission_form.html", {"form": form, })
