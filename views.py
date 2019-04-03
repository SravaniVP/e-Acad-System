from django.shortcuts import render
from django.shortcuts import get_object_or_404
from classroom.models import Student, Course


def homepage(request):
    return render(request,'classroom/teachers/quiz_add_form.html')


def mypage(request, pk):
    student = get_object_or_404(Student, pk=pk, user=request.user)
    return render(request, 'classroom/students/home_t.html', {'student': student})


