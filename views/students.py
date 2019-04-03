from django.contrib import messages
from django.contrib.auth import login
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render, render_to_response
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, UpdateView, DetailView, DeleteView
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from ..decorators import student_required
from ..forms import StudentSignUpForm, StudentRegForm, SubmissionForm, CommentForm, CommentAssgnForm,FilesForm
from ..models import Course, Student, User, Assignment, Submission, Comment, Document, CommentAssgn,Attendance,Vote,Myfiles


class StudentSignUpView(CreateView):
    model = User
    form_class = StudentSignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'student'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, 'you have registered successfully!')
        return redirect('coursereg_list',self.request.user.id)


@method_decorator([login_required, student_required], name='dispatch')
class XYCourseregView(ListView):
    model = Course
    context_object_name = 'student'
    template_name = 'classroom/students/course_form.html'

    def get_queryset(self):
        queryset = self.request.user.student.all()
        return queryset

    def get_success_url(self):
        return reverse('course_list', kwargs={'pk': self.object.pk})


@method_decorator([login_required, student_required], name='dispatch')
class SemUpdateView(UpdateView):
    model = User
    fields = ('semester',)
    template_name = 'classroom/students/sem_update.html'

    def get_context_data(self, **kwargs):
        kwargs['user'] = self.get_object()
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        messages.success(self.request, 'semester updated successfully!')
        return reverse('coursereg_list', kwargs={'pk': self.object.pk})

@method_decorator([login_required, student_required], name='dispatch')
class ProfileUpdateView(UpdateView):
    model = User
    fields = ('username', 'semester', 'first_name','last_name','RollNo', 'email', )
    template_name = 'classroom/students/profile.html'

    def get_success_url(self):
        messages.success(self.request,'profile updated successfully!')
        return reverse('home')

@login_required
@student_required
def private(request):
    student = get_object_or_404(Student, user=request.user)
    files = Myfiles.objects.all().filter(owner=student)
    return render(request,'classroom/students/privatefiles.html',{ 'files':files })


@login_required
@student_required
def addfiles(request):
    student = get_object_or_404(Student, user=request.user)
    if request.method == 'POST':
        form = FilesForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.owner = student
            document.save()
            form.save()
            messages.success(request, '%s File added succesfully!' % document.file_name)
            return redirect('private')

    else:
        form = FilesForm()

    return render(request, 'classroom/students/add_file.html', {'form': form})

@login_required
@student_required
def CourseregView(request, pk):
    student = Student.objects.get(pk=pk)
    courses = student.interests.all()

    return render(request,'classroom/students/course_form.html', {
        "student": student,
        "courses": courses,
    })

@login_required
@student_required
def crview(request):
    x = request.user.semester
    att = Vote.objects.all().filter(semester=x, approve=True)
    return render(request,'classroom/students/cr_view.html', { "att":att, })


@login_required
@student_required
def crvote(request,pk):
    x = request.user.semester
    user = request.user
    student = Student.objects.all().filter(user=user)
    if not user.vote :
        object = get_object_or_404(Vote, pk=pk)
        object.count = object.count + 1
        user.vote = True
        user.save()
        object.save()
        messages.success(request, ' your vote is registered successfully:-)')
    else :
        messages.success(request, 'Can not vote more than once!')
    att = Vote.objects.all().filter(semester=x, approve=True)
    return render(request,'classroom/students/cr_view.html', { "att":att, })

@login_required
@student_required
def temp(request,pk):
    student = Student.objects.get(pk=pk)
    courses = student.interests.all()
    for c in courses:
        Attendance.objects.create(course=c, student=student, at=0)
    return render(request, 'classroom/students/course_form.html', {
        "student": student,
        "courses": courses,
    })
@login_required
@student_required
def crregview(request,pk):
    candi = get_object_or_404(Student, pk=request.user.id)
    vote = Vote.objects.filter(candidate=candi).count()
    if(vote==0):
        Vote.objects.create(candidate=candi,semester=request.user.semester)
        messages.success(request, 'successfully registered!')
    else:
        messages.success(request, 'already registered!')
    return redirect('coursereg_list', request.user.id)

@login_required
@student_required
def attendanceview(request,pk):
    course = get_object_or_404(Course, pk=pk)
    student = get_object_or_404(Student, user=request.user)
    att = get_object_or_404(Attendance,course=course,student=student)
    p = att.at*100/course.classestaken
    return render(request, 'classroom/students/att_view.html',{'course':course,'student':student,'att':att,'p':p })


@method_decorator([login_required, student_required], name='dispatch')
class CoursexListView(ListView):
    model = Course
    ordering = ('course_code',)
    context_object_name = 'courses'
    template_name = 'classroom/students/course_form.html'
    success_url = reverse_lazy('coursereg_list')


@method_decorator([login_required, student_required], name='dispatch')
class CourseDetailView(DetailView):
    model = Course
    context_object_name = 'course'
    template_name = 'classroom/students/course_detail.html'

    def get_context_data(self, **kwargs):
        kwargs['documents'] = self.get_object().documents.annotate()
        kwargs['assignments'] = self.get_object().assignments.annotate()
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return reverse('course_stu_view', kwargs={'pk': self.object.pk})

@method_decorator([login_required, student_required], name='dispatch')
class FileDeleteView(DeleteView):
    model = Myfiles
    context_object_name = 'document'
    template_name = 'classroom/students/stu_file_delete.html'
    success_url = reverse_lazy('private')

    def delete(self, request, *args, **kwargs):
        assignment = self.get_object()
        messages.success(request, ' %s file deleted successfully!' % assignment.file_name)
        return super().delete(request, *args, **kwargs)


@login_required
@student_required
def submission_add(request, course_pk, assignment_pk):
    # By filtering the quiz by the url keyword argument `pk` and
    # by the owner, which is the logged in user, we are protecting
    # this view at the object-level. Meaning only the owner of
    # quiz will be able to add questions to it.
    course = get_object_or_404(Course, pk=course_pk)
    student = get_object_or_404(Student, user_id=request.user.id)
    assignment = get_object_or_404(Assignment, pk=assignment_pk, course=course)
    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.course = course
            document.student = student
            document.assignment = assignment
            document.user = request.user
            document.save()
            form.save()
            messages.success(request,'Assignment submitted successfully!')
            return redirect('course_stu_view', course.id)

    else:
        form = SubmissionForm()

    return render(request, 'classroom/students/submission_add.html', {'student': student,'course': course,'form': form,'assignment':assignment})


@login_required
@student_required
def courselistview(request):
    x = request.user.semester
    courses = Course.objects.all().filter(semester=x)
    if request.method == 'POST':
        form = StudentRegForm(x,request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.user = request.user
            course.save()
            form.save()
            messages.success(request, ' course registered successfully! ' )
            return redirect('temp', request.user.id)
    else:
        form = StudentRegForm(x)

    return render(request, 'classroom/students/course_reg.html',{'courses':courses, 'form': form ,})



@method_decorator([login_required, student_required], name='dispatch')
class CRregCreateView(CreateView):
    model = Vote
    fields =  ('semester',)
    template_name = 'classroom/students/CR_reg_view.html'

    def form_valid(self, form):
        course = form.save(commit=False)
        course.candidate = get_object_or_404(Student, pk=self.request.user.id)
        course.save()
        #Document.objects.create(file_upload=each, Course=instance)
        messages.success(self.request, '%s registered successfully!' % self.request.user)
        return redirect('cr_reg',self.request.user.id)


@method_decorator([login_required, student_required], name='dispatch')
class CourseListView(CreateView):
    model = Student
    form_class = StudentRegForm
    template_name = 'classroom/students/course_reg_form.html'
    success_url = reverse_lazy('coursereg_list')

    def form_valid(self, form):
        student = form.save(commit=False)
        student.user = self.request.user
        student.save()
        form.save()
        messages.success(self.request, ' courses  registered successfully! ')
        return redirect('coursereg_list', self.request.user.id)

@login_required
@student_required
def submitview(request,course_pk,assignment_pk):
    course = get_object_or_404(Course, pk=course_pk)
    assignment = get_object_or_404(Assignment, pk=assignment_pk)
    submits = Submission.objects.all().filter(course=course, student_id=request.user.id, assignment=assignment)
    return render(request, 'classroom/students/submission_view.html',{'submits': submits, 'course':course ,'assignment':assignment })


@login_required
@student_required
def mysubmitview(request,course_pk):
    course = get_object_or_404(Course, pk=course_pk)
    submits = Submission.objects.all().filter(course=course, student_id=request.user.id)
    return render(request, 'classroom/students/my_submission_view.html',{'submits': submits, 'course':course })


@method_decorator([login_required, student_required], name='dispatch')
class XCourseSubmitView(DetailView):
    model = Student
    context_object_name = 'course'
    template_name = 'classroom/students/submission_view.html'

    def get_context_data(self, **kwargs):
        kwargs['submits'] = self.get_object().interests.annotate()
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return reverse('submit_stu_view', kwargs={'pk': self.object.pk})


@method_decorator([login_required, student_required], name='dispatch')
class CoursexSubmitView(ListView):
    model = Submission
    context_object_name = 'submissions'
    template_name = 'classroom/students/submit.html'

    def get_queryset(self):
        queryset = self.request.user.submissions.all()
        return queryset

@method_decorator([login_required, student_required], name='dispatch')
class xCourseSubmitView(ListView):
    model = Submission
    context_object_name = 'submissions'
    template_name = 'classroom/students/submit.html'

    def get_queryset(self):
        queryset = self.request.user.student.submissions
        return queryset


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password updated successfully!')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'classroom/students/password.html', {
        'form': form
    })

@login_required
@student_required
def add_comment_to_post_stu(request, course_pk, notes_pk):
    #get document object
    course = get_object_or_404(Course,pk=course_pk)
    document = get_object_or_404(Document, pk=notes_pk)
    #list of active parent comments
    comments = document.comments.filter(approved_comment=True, parent__isnull=True)
    if request.method == 'POST':
        #comment has been added
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            parent_obj = None
            #get parent comment id from hidden input
            try:
                #id integer e.g. 15
                parent_id = int(request.POST.get('parent_id'))
            except:
                parent_id = None
            #if parent_id has been submitted get parent_obj id
            if parent_id:
                parent_obj = Comment.objects.get(id=parent_id)
                #if parent object exist
                if parent_obj:
                    #create replay comment object
                    replay_comment = comment_form.save(commit=False)
                    #assign parent_obj to replay comment
                    replay_comment.parent = parent_obj
            #normal comment
            #create  comment object but do not save to database
            new_comment = comment_form.save(commit=False)
            # assign ship to the comment

            new_comment.course = course
            new_comment.document = document
            #save
            new_comment.user = request.user
            new_comment.save()
            return redirect('.')
    else:
        comment_form = CommentForm()
    return render(request, 'classroom/students/add_comment.html', {'course':course, 'document':document, 'comments':comments, 'comment_form':comment_form})

@method_decorator([login_required, student_required], name='dispatch')
class comment_remove_stu(DeleteView):
    model = Comment
    template_name = 'classroom/students/comment_delete_confirm.html'
    def get_success_url(self):
        return reverse('add_comment_to_post_stu', kwargs={'course_pk': self.object.document.course.pk, 'notes_pk': self.object.document.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'comment deleted successfully!')
        return super().delete(request, *args, **kwargs)

@method_decorator([login_required, student_required], name='dispatch')
class comment_approve_stu(UpdateView):
    model = Comment
    fields = ('text',)
    template_name = 'classroom/students/comment_edit_form.html'

    def get_queryset(self):
        '''
        This method is an implicit object-level permission management
        This view will only match the ids of existing courses that belongs
        to the logged in user.
        '''
        return self.request.user.comments.all()

    def get_success_url(self):
        messages.success(self.request, ' comment updated successfully '  )
        return reverse('add_comment_to_post_stu', kwargs={'course_pk': self.object.document.course.pk, 'notes_pk': self.object.document.pk})

@method_decorator([login_required, student_required], name='dispatch')
class reply_remove_stu(DeleteView):
    model = Comment
    template_name = 'classroom/students/reply_delete_confirm.html'
    def get_success_url(self):
        return reverse('add_comment_to_post_stu', kwargs={'course_pk': self.object.document.course.pk, 'notes_pk': self.object.document.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Reply deleted successfully!')
        return super().delete(request, *args, **kwargs)

@method_decorator([login_required, student_required], name='dispatch')
class reply_approve_stu(UpdateView):
    model = Comment
    fields = ('text',)
    template_name = 'classroom/students/reply_edit_form.html'

    def get_queryset(self):
        '''
        This method is an implicit object-level permission management
        This view will only match the ids of existing courses that belongs
        to the logged in user.
        '''
        return self.request.user.comments.all()

    def get_success_url(self):
        messages.success(self.request, ' Reply updated successfully '  )
        return reverse('add_comment_to_post_stu', kwargs={'course_pk': self.object.document.course.pk, 'notes_pk': self.object.document.pk})

@login_required
@student_required
def add_comment_to_post_stu_assgn(request, course_pk, assgn_pk):
    #get document object
    course = get_object_or_404(Course, pk=course_pk)
    assignment = get_object_or_404(Assignment, pk=assgn_pk)
    #list of active parent comments
    AssgnComments = assignment.commentsassg.filter(approve_comment=True, parent__isnull=True)
    if request.method == 'POST':
        #comment has been added
        commentassgn_form = CommentAssgnForm(data=request.POST)
        if commentassgn_form.is_valid():
            parent_obj = None
            #get parent comment id from hidden input
            try:
                #id integer e.g. 15
                parent_assgn_id = int(request.POST.get('parent_id'))
            except:
                parent_assgn_id = None
            #if parent_id has been submitted get parent_obj id
            if parent_assgn_id:
                parent_assgn_obj = CommentAssgn.objects.get(id=parent_assgn_id)
                #if parent object exist
                if parent_assgn_obj:
                    #create replay comment object
                    reply_assgn_comment = commentassgn_form.save(commit=False)
                    #assign parent_obj to replay comment
                    reply_assgn_comment.parent = parent_assgn_obj
            #normal comment
            #create  comment object but do not save to database
            new_assgn_comment = commentassgn_form.save(commit=False)
            # assign ship to the comment
            new_assgn_comment.course = course
            new_assgn_comment.assignment = assignment
            #save
            new_assgn_comment.user = request.user
            new_assgn_comment.save()
            return redirect('.')
    else:
        commentassgn_form = CommentAssgnForm()
    return render(request, 'classroom/students/add_comment_assgn.html', { 'course':course,'assignment':assignment, 'AssgnComments':AssgnComments, 'commentassgn_form':commentassgn_form})

@method_decorator([login_required, student_required], name='dispatch')
class comment_remove_stu_assgn(DeleteView):
    model = CommentAssgn
    template_name = 'classroom/students/comment_delete_assgn_confirm.html'

    def get_success_url(self):
        return reverse('add_comment_to_post_stu_assgn', kwargs={'course_pk': self.object.assignment.course.pk, 'assgn_pk': self.object.assignment.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'comment deleted successfully!')
        return super().delete(request, *args, **kwargs)

@method_decorator([login_required, student_required], name='dispatch')
class comment_approve_stu_assgn(UpdateView):
    model = CommentAssgn
    fields = ('text',)
    template_name = 'classroom/students/comment_edit_assgn.html'

    def get_queryset(self):
        '''
        This method is an implicit object-level permission management
        This view will only match the ids of existing courses that belongs
        to the logged in user.
        '''
        return self.request.user.commentsassg.all()

    def get_success_url(self):
        messages.success(self.request, ' comment updated successfully '  )
        return reverse('add_comment_to_post_stu_assgn', kwargs={'course_pk': self.object.assignment.course.pk, 'assgn_pk': self.object.assignment.pk})

@method_decorator([login_required, student_required], name='dispatch')
class reply_remove_stu_assgn(DeleteView):
    model = CommentAssgn
    template_name = 'classroom/students/reply_delete_assgn.html'

    def get_success_url(self):
        return reverse('add_comment_to_post_stu_assgn', kwargs={'course_pk': self.object.assignment.course.pk, 'assgn_pk': self.object.assignment.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Reply deleted successfully!')
        return super().delete(request, *args, **kwargs)

@method_decorator([login_required, student_required], name='dispatch')
class reply_approve_stu_assgn(UpdateView):
    model = CommentAssgn
    fields = ('text',)
    template_name = 'classroom/students/reply_edit_assgn.html'

    def get_queryset(self):
        '''
        This method is an implicit object-level permission management
        This view will only match the ids of existing courses that belongs
        to the logged in user.
        '''
        return self.request.user.commentsassg.all()

    def get_success_url(self):
        messages.success(self.request, ' Reply updated successfully '  )
        return reverse('add_comment_to_post_stu_assgn', kwargs={'course_pk': self.object.assignment.course.pk, 'assgn_pk': self.object.assignment.pk})
