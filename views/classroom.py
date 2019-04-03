from django.shortcuts import redirect, render
from django.views.generic import TemplateView


class SignUpView(TemplateView):
    template_name = 'registration/signup.html'


def home(request):
    if request.user.is_authenticated:
        if request.user.is_teacher:
            return redirect('course_add')
        elif request.user.is_student:
            return redirect('coursereg_list', request.user.id)
        else:
            return redirect('ta_course_list')
    return render(request, 'classroom/home.html')
