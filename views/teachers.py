from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Avg, Count
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy

from django.db.models import Max
from django.utils.decorators import method_decorator
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView, View, FormView)
from django.db import IntegrityError
from classroom import views
from ..decorators import teacher_required
from ..forms import TeacherSignUpForm, DocumentForm,AssignmentForm,AllotMarksForm,StudentInterestsForm,CommentForm,CommentAssgnForm,TAForm, UploadForm,FForm
from ..models import Course, User, Document, Student, Submission,Assignment,TA,Comment,CommentAssgn,Attendance,Vote,Myfiles,File


class TeacherSignUpView(CreateView):
    model = User
    form_class = TeacherSignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'teacher'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "you have registered successfully!")
        return redirect('course_add')

@method_decorator([login_required, teacher_required], name='dispatch')
class ProfileUpdateView(UpdateView):
    model = User
    fields = ('username','first_name','last_name','email', )
    template_name = 'classroom/students/profile.html'

    def get_success_url(self):
        messages.success(self.request,'profile updated successfully!')
        return reverse('home')

@method_decorator([login_required, teacher_required], name='dispatch')
class CourseCreateView(CreateView):
    model = Course
    fields = ('course_title', 'course_code','semester', 'about','totalclasses')
    template_name = 'classroom/teachers/quiz_change_list.html'

    def form_valid(self, form):
        course = form.save(commit=False)
        course.owner = self.request.user
        course.save()
        messages.success(self.request, '%s course created successfully!' % course.course_title)
        return redirect('course_add')

@login_required
@teacher_required
def xadd_comment_view(request, pk):
    document = get_object_or_404(Document, pk=pk)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.document = document
            comment.user = request.user
            comment.save()
            form.save()
            return redirect('course_add')
    else:
        form = CommentForm()

    return render(request, 'classroom/teachers/comment.html',{'document': document, 'form': form })


#not used
@method_decorator([login_required, teacher_required], name='dispatch')
class CourseListView(ListView):
    model = Course
    ordering = ('semester',)
    context_object_name = 'courses'
    template_name = 'classroom/teachers/quiz_add_form.html'


    def get_queryset(self):
        queryset = self.request.user.courses.all()
        return queryset

@login_required
@teacher_required
def teacherview(request):
    courses = request.user.courses.all()
    one = courses.filter(semester=1)
    two = courses.filter(semester=2)
    three = courses.filter(semester=3)
    four = courses.filter(semester=4)
    five = courses.filter(semester=5)
    six = courses.filter(semester=6)
    seven = courses.filter(semester=7)
    eight = courses.filter(semester=8)
    return render(request, 'classroom/teachers/quiz_add_form.html', {'courses': courses,'one':one,'two':two,'three':three,'four':four,'five':five,'six':six,'seven':seven,'eight':eight })



@method_decorator([login_required, teacher_required], name='dispatch')
class studentDetailView(DetailView):
    model = Course
    context_object_name = 'interests'
    template_name = 'classroom/teachers/student_detail.html'

    def get_context_data(self, **kwargs):
        kwargs['interested_students'] = self.get_object().interested_students.annotate()
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return reverse('course_view', kwargs={'pk': self.object.pk})


@method_decorator([login_required, teacher_required], name='dispatch')
class CourseUpdateView(UpdateView):
    model = Course
    fields = ('course_title', 'course_code', 'semester', 'about','totalclasses','classestaken')
    context_object_name = 'course'
    template_name = 'classroom/teachers/course_edit_form.html'

    def get_queryset(self):
        '''
        This method is an implicit object-level permission management
        This view will only match the ids of existing courses that belongs
        to the logged in user.
        '''
        return self.request.user.courses.all()

    def get_success_url(self):
        course = self.get_object()
        messages.success(self.request, '%s   course updated successfully ' % course.course_title )
        return reverse('course_view', kwargs={'pk': self.object.pk})


@method_decorator([login_required, teacher_required], name='dispatch')
class ClassUpdateView(UpdateView):
    model = Course
    fields = ('totalclasses','classestaken')
    context_object_name = 'course'
    template_name = 'classroom/teachers/class_edit_form.html'

    def get_queryset(self):
        '''
        This method is an implicit object-level permission management
        This view will only match the ids of existing courses that belongs
        to the logged in user.
        '''
        return self.request.user.courses.all()

    def get_success_url(self):
        course = self.get_object()
        messages.success(self.request, 'No of class of %s course is updated successfully ' % course.course_title )
        return reverse('attendance', kwargs={'pk': self.object.pk})


@method_decorator([login_required, teacher_required], name='dispatch')
class AssignmentUpdateView(UpdateView):
    model = Assignment
    fields = ('course', 'file_name', 'file_upload',)
    #context_object_name = 'course'
    template_name = 'classroom/teachers/assign_edit_form.html'

    def get_context_data(self, **kwargs):
        kwargs['assignments'] = self.get_object()
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return reverse('edit_assign', kwargs={'pk': self.object.pk})


@login_required
@teacher_required
def assignview(request,pk):
    assignment =get_object_or_404(Assignment, pk=pk)
    course = assignment.course
    ta = TA.objects.all().filter(interests=course)
    if request.method == 'POST':
        form = TAForm(course,request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'gjj course registered with successfully! ')
            return redirect('course_view',)
    else:
        form = TAForm(course)

    return render(request, 'classroom/teachers/ta_reg_form.html',{'assignment':assignment, 'form': form,})


@method_decorator([login_required, teacher_required], name='dispatch')
class AssignView(UpdateView):
    model = Assignment
    form_class = StudentInterestsForm
    template_name = 'classroom/teachers/ta_reg_form.html'

    def get_success_url(self):
        messages.success(self.request, ' TA alloted successfully ')
        return reverse('course_view', kwargs={'pk': self.object.course.pk})


@method_decorator([login_required, teacher_required], name='dispatch')
class AllotMark(UpdateView):
    model = Submission
    fields = ('mark', 'feedback',)
    template_name = 'classroom/teachers/x.html'

    def get_success_url(self):
        submission = self.get_object()
        if(self.object.assignment.max_marks < self.object.mark):
            messages.success(self.request, 'marks is greater than maximum marks')
            return reverse('allot_marks', kwargs={'pk': self.object.pk})
        else:
            messages.success(self.request, ' Marks alloted successfully for %s ' % submission.student)
        return reverse('student_submissions', kwargs={'course_pk': self.object.course.pk, 'assignment_pk': self.object.assignment.pk})


@method_decorator([login_required, teacher_required], name='dispatch')
class PermissionUpdateView(UpdateView):
    model = Assignment
    fields = ('visible',)
    template_name ='classroom/teachers/update_permission.html'

    def get_success_url(self):
        messages.success(self.request, 'permission updated!')
        return reverse('course_view', kwargs={'pk': self.object.course.pk})


@method_decorator([login_required, teacher_required], name='dispatch')
class AttendanceUpdateView(UpdateView):
    model = Attendance
    fields = ('at',)
    template_name ='classroom/teachers/update_attendance.html'

    def get_success_url(self):
        messages.success(self.request, 'Attendance updated!')
        return reverse('attendance', kwargs={'pk': self.object.course.pk})

@method_decorator([login_required, teacher_required], name='dispatch')
class ResultUpdateView(UpdateView):
    model = Vote
    fields = ('winner',)
    template_name ='classroom/teachers/declare_result.html'

    def get_context_data(self, **kwargs):
        kwargs['candidate'] = self.get_object()
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        messages.success(self.request, 'CR candidate is declared')
        return reverse('declare_result', kwargs={'pk': self.object.pk})

@method_decorator([login_required, teacher_required], name='dispatch')
class ApproveUpdateView(UpdateView):
    model = Vote
    fields = ('approve',)
    template_name ='classroom/teachers/cr_teacher_reg.html'

    def get_context_data(self, **kwargs):
        kwargs['candidate'] = self.get_object()
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        messages.success(self.request, 'approved for CR elections')
        return reverse('approve_cr', kwargs={'pk': self.object.pk })


@login_required
@teacher_required
def attendance(request, pk):
    course = get_object_or_404(Course,pk=pk)
    student = Student.objects.all().filter(interests=course)
    att = Attendance.objects.all().filter(course=course,student__in=student).order_by('student__user__RollNo')
    return render(request,'classroom/teachers/attendance.html' , {'student':student, 'course':course,'att':att })


@login_required
@teacher_required
def student_attendance(request, pk):
    object = get_object_or_404(Attendance,pk=pk)
    object.at = object.at + 1
    object.save()
    course = object.course
    student = Student.objects.all().filter(interests=course)
    att = Attendance.objects.all().filter(course=course,student__in=student).order_by('student__user__RollNo')
    return render(request, 'classroom/teachers/attendance.html', {'student': student, 'course': course, 'att': att})


@method_decorator([login_required, teacher_required], name='dispatch')
class CourseDeleteView(DeleteView):
    model = Course
    context_object_name = 'course'
    template_name = 'classroom/teachers/course_delete_confirm.html'
    success_url = reverse_lazy('course_add')

    def delete(self, request, *args, **kwargs):
        course = self.get_object()
        messages.success(request, 'The course %s was deleted with success!' % course.course_title)
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return self.request.user.courses.all()


@method_decorator([login_required, teacher_required], name='dispatch')
class AssignDeleteView(DeleteView):
    model = Assignment
    context_object_name = 'assignment'
    template_name = 'classroom/teachers/assign_delete_confirm.html'

    def get_success_url(self):
        # I cannot access the 'pk' of the deleted object here
        return reverse('course_view', kwargs={'pk': self.object.course.pk})


    def delete(self, request, *args, **kwargs):
        assignment = self.get_object()
        messages.success(request, ' %s  file deleted successfully!' % assignment.file_name)
        return super().delete(request, *args, **kwargs)

@method_decorator([login_required, teacher_required], name='dispatch')
class VoteDeleteView(DeleteView):
    model = Vote
    context_object_name = 'vote'
    template_name = 'classroom/teachers/cr_delete_confirm.html'

    def get_success_url(self):
        # I cannot access the 'pk' of the deleted object here
        return reverse('assign_ccc', kwargs={'pk': self.object.semester})


    def delete(self, request, *args, **kwargs):
        assignment = self.get_object()
        messages.success(request, ' %s  CR candidate deleted successfully!' % assignment.candidate)
        return super().delete(request, *args, **kwargs)


@method_decorator([login_required, teacher_required], name='dispatch')
class NotesDeleteView(DeleteView):
    model = Document
    context_object_name = 'document'
    template_name = 'classroom/teachers/notes_delete_confirm.html'

    def get_success_url(self):
        # I cannot access the 'pk' of the deleted object here
        return reverse('course_view', kwargs={'pk': self.object.course.pk})

    def delete(self, request, *args, **kwargs):
        assignment = self.get_object()
        messages.success(request, ' %s class notes deleted successfully!' % assignment.file_name)
        return super().delete(request, *args, **kwargs)


@method_decorator([login_required, teacher_required], name='dispatch')
class FileDeleteView(DeleteView):
    model = File
    context_object_name = 'document'
    template_name = 'classroom/teachers/file_delete_confirm.html'
    success_url = reverse_lazy('my_private')

    def delete(self, request, *args, **kwargs):
        assignment = self.get_object()
        messages.success(request, ' %s file deleted successfully!' % assignment.file_name)
        return super().delete(request, *args, **kwargs)



@login_required
@teacher_required
def dsdescription_add(request, pk):
    course = get_object_or_404(Course, pk=pk)

    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.course = course
            document.save()
            form.save()
            return redirect('course_view', pk)
    else:
        form = UploadForm()

    contexts = {
        'form': form, 'course':course,
    }

    return render(request, 'classroom/teachers/question_add_form.html', contexts)

@login_required
@teacher_required
def myprivate(request):
    files = File.objects.all().filter(owner=request.user)
    return render(request,'classroom/teachers/private_files.html',{'files':files })

@login_required
@teacher_required
def myaddfiles(request):

    if request.method == 'POST':
        form = FForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.owner = request.user
            document.save()
            form.save()
            messages.success(request, '%s File added succesfully!' % document.file_name)
            return redirect('my_private')

    else:
        form = FForm()

    return render(request, 'classroom/teachers/my_add_file.html', {'form': form})


@login_required
@teacher_required
def description_add(request, pk):
    # By filtering the quiz by the url keyword argument `pk` and
    # by the owner, which is the logged in user, we are protecting
    # this view at the object-level. Meaning only the owner of
    # quiz will be able to add questions to it.
    course = get_object_or_404(Course, pk=pk, owner=request.user)

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.course = course
            document.save()
            form.save()
            messages.success(request, '%s Class Notes added succesfully!' % document.file_name)
            return redirect('course_view', pk)

    else:
        form = DocumentForm()

    return render(request, 'classroom/teachers/question_add_form.html', {'course': course, 'form': form})



@method_decorator([login_required, teacher_required], name='dispatch')
class adescription_add(FormView):
    model = Document
    template_name = 'classroom/teachers/form.html'
    form_class = UploadForm

    def get_success_url(self):
        # I cannot access the 'pk' of the deleted object here
        return reverse('course_view', kwargs={'pk': self.object.course.pk})


    def form_valid(self,form):
        for each in form.cleaned_data['documents']:
            Document.objects.create(file_upload=each)
        return super(UploadView, self).form_valid(form)



@method_decorator([login_required, teacher_required], name='dispatch')
class BasicUploadView(View):
    def get(self, request):
        document_list = Document.objects.all()
        return render(self.request, 'classroom/teachers/index.html', {'documents': document_list})

    def post(self, request):
        form = DocumentForm(self.request.POST, self.request.FILES)
        if form.is_valid():
            document = form.save()
            data = {'is_valid': True, 'name': document.file_upload.name, 'url': document.file_upload.url}
        else:
            data = {'is_valid': False}
        return JsonResponse(data)


@login_required
@teacher_required
def add_comment_view(request, pk):
    document = get_object_or_404(Document, pk=pk)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.document = document
            comment.user = request.user
            comment.save()
            form.save()
            return redirect('course_add')
    else:
        form = CommentForm()

    return render(request, 'classroom/teachers/comment.html', {'document': document, 'form': form })


@login_required
@teacher_required
def assignment_add(request, pk):
    # By filtering the quiz by the url keyword argument `pk` and
    # by the owner, which is the logged in user, we are protecting
    # this view at the object-level. Meaning only the owner of
    # quiz will be able to add questions to it.
    course = get_object_or_404(Course, pk=pk, owner=request.user)

    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.course = course
            document.save()
            form.save()
            messages.success(request,'%s assignment added succesfully' % document.file_name)
            return redirect('course_view', pk)

    else:
        form = AssignmentForm()

    return render(request, 'classroom/teachers/assignment_add.html', {'course': course, 'form': form})


@login_required
@teacher_required
def xsubmitview(request,course_pk,assignment_pk):
    course = get_object_or_404(Course, pk=course_pk)
    assignment = get_object_or_404(Assignment,pk=assignment_pk)
    submits = Submission.objects.all().filter(course=course,assignment=assignment)
    if request.method == 'POST':
        form = AllotMarksForm(request.POST)
        if form.is_valid():
            marks = form.save(commit=False)
            marks.course = course
            marks.assignment = assignment
            marks. student = Submission(
                student = request.POST['student']
            )
            marks.save()
            form.save()
            return redirect('student_submissions',course_pk, assignment_pk)
    else:
        form = AllotMarksForm()

    return render(request, 'classroom/teachers/student_submission_view.html',{ 'form':form ,'submits': submits, 'course':course})


@login_required
@teacher_required
def submitview(request,course_pk,assignment_pk):
    course = get_object_or_404(Course, pk=course_pk)
    assignment = get_object_or_404(Assignment,pk=assignment_pk)
    submits = Submission.objects.all().filter(course=course,assignment=assignment).order_by('student__user__RollNo')
    return render(request, 'classroom/teachers/student_submission_view.html',{'submits': submits, 'assignment':assignment,'course':course})


@login_required
@teacher_required
def view_discussion(request,pk):
    document = get_object_or_404(Document,pk=pk)
    comments =Comment.objects.all().filter(document=document)
    return render(request, 'classroom/teachers/discussion.html',{'document': document,'comments':comments })


@login_required
@teacher_required
def listsubmitview(request,course_pk,assignment_pk):
    course = get_object_or_404(Course, pk=course_pk)
    assignment = get_object_or_404(Assignment,pk=assignment_pk)
    submits = Submission.objects.all().filter(course=course,assignment=assignment).order_by('student__user__RollNo')
    return render(request, 'classroom/teachers/list_submission_view.html',{'submits': submits, 'assignment':assignment,'course':course})


@login_required
@teacher_required
def liststudentview(request,course_pk):
    one = 1
    zero = 0
    course = get_object_or_404(Course, pk=course_pk)
    #assignment = get_object_or_404(Assignment,pk=assignment_pk)
    students = Student.objects.all().filter(interests=course).order_by('user__RollNo')
    count = Student.objects.all().filter(interests=course).count()
    return render(request, 'classroom/teachers/student_detail.html',{'students': students,'course':course,'count':count, 'one':one,'zero':zero})

@login_required
@teacher_required
def listcrcandidates(request,pk):
    course = get_object_or_404(Course, pk=pk)
    x = course.semester
    votes = Vote.objects.all().filter(semester=x)
    return render(request, 'classroom/teachers/cr_detail.html',{'course':course,'votes':votes })
#using
@login_required
@teacher_required
def xlistcrcandidates(request,pk):
    votes = Vote.objects.all().filter(semester=pk)
    return render(request, 'classroom/teachers/cr_detail.html',{'pk':pk,'votes':votes })



@login_required
@teacher_required
def checkvotes(request,pk):
    x = pk
    votes = Vote.objects.all().filter(semester=x, approve=True)
    max = votes.aggregate(m=Max('count'))
    kl = max.get('m')
    high = Vote.objects.all().filter(semester=x, approve=True, count=kl)

    return render(request,'classroom/teachers/view_votes.html',{ 'x':x,'votes':votes,'max':max,'kl':kl,'high':high })


@login_required
@teacher_required
def xsubmitview(request, course_pk, assignment_pk):
    course = get_object_or_404(Course, pk=course_pk)
    assignment = get_object_or_404(Assignment, pk=assignment_pk)
    submits = Submission.objects.all().filter(course=course, assignment=assignment)
    x = Submission(
        mark = request.POST.get('mark',''),
    )
    x.save()
    return render(request, 'classroom/teachers/student_submission_view.html', {'submits': submits, 'course': course})


#not used
@method_decorator([login_required, teacher_required], name='dispatch')
class CoursexDetailView(DetailView):
    model = Course
    context_object_name = 'course'
    template_name = 'classroom/teachers/quiz_change_form.html'

    def mydef(request, pk):
        course = get_object_or_404(Course, pk=pk, owner=request.user)
        documents = Document.objects.all()
        return render(request, 'classroom/teachers/quiz_change_form.html', {'documents': documents, 'course': course})

    def get_queryset(self):
        '''
        This method is an implicit object-level permission management
        This view will only match the ids of existing quizzes that belongs
        to the logged in user.
        '''
        return Document.objects.filter(course__owner=self.request.user)

    def get_success_url(self):
        return reverse('course_view', kwargs={'pk': self.object.pk})


@method_decorator([login_required, teacher_required], name='dispatch')
class CourseDetailView(DetailView):
    model = Course
    context_object_name = 'course'
    template_name = 'classroom/teachers/quiz_change_form.html'

    def get_context_data(self, **kwargs):
        kwargs['documents'] = self.get_object().documents.annotate()
        kwargs['assignments'] = self.get_object().assignments.annotate()
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        '''
        This method is an implicit object-level permission management
        This view will only match the ids of existing quizzes that belongs
        to the logged in user.
        '''
        return self.request.user.courses.all()

    def get_success_url(self):
        return reverse('course_view', kwargs={'pk': self.object.pk})

@login_required
@teacher_required
def add_comment_to_post(request,course_pk, notes_pk):
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
    return render(request, 'classroom/teachers/add_comment.html', {'course':course,'document':document, 'comments':comments, 'comment_form':comment_form})



@method_decorator([login_required, teacher_required], name='dispatch')
class comment_remove(DeleteView):
    model = Comment
    template_name = 'classroom/teachers/comment_delete_confirm.html'


    def get_success_url(self):
        return reverse('add_comment_to_post', kwargs={'course_pk': self.object.document.course.pk, 'notes_pk': self.object.document.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'comment deleted successfully!')
        return super().delete(request, *args, **kwargs)


@method_decorator([login_required, teacher_required], name='dispatch')
class comment_approve(UpdateView):
    model = Comment
    fields = ('text',)
    template_name = 'classroom/teachers/comment_edit_form.html'

    def get_queryset(self):
        '''
        This method is an implicit object-level permission management
        This view will only match the ids of existing courses that belongs
        to the logged in user.
        '''
        return self.request.user.comments.all()

    def get_success_url(self):
        messages.success(self.request, ' comment updated successfully '  )
        return reverse('add_comment_to_post', kwargs={'course_pk': self.object.document.course.pk, 'notes_pk': self.object.document.pk})


@method_decorator([login_required, teacher_required], name='dispatch')
class reply_remove(DeleteView):
    model = Comment
    template_name = 'classroom/teachers/reply_delete_confirm.html'


    def get_success_url(self):
        return reverse('add_comment_to_post', kwargs={'course_pk': self.object.document.course.pk, 'notes_pk': self.object.document.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Reply deleted successfully!')
        return super().delete(request, *args, **kwargs)


@method_decorator([login_required, teacher_required], name='dispatch')
class reply_approve(UpdateView):
    model = Comment
    fields = ('text',)
    template_name = 'classroom/teachers/reply_edit_form.html'

    def get_queryset(self):
        '''
        This method is an implicit object-level permission management
        This view will only match the ids of existing courses that belongs
        to the logged in user.
        '''
        return self.request.user.comments.all()

    def get_success_url(self):
        messages.success(self.request, ' Reply updated successfully '  )
        return reverse('add_comment_to_post', kwargs={'course_pk': self.object.document.course.pk, 'notes_pk': self.object.document.pk})


@login_required
@teacher_required
def add_comment_to_post_assgn(request, course_pk, assgn_pk):
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
    return render(request, 'classroom/teachers/add_comment_assgn.html', { 'course':course,'assignment':assignment, 'AssgnComments':AssgnComments, 'commentassgn_form':commentassgn_form})


@method_decorator([login_required, teacher_required], name='dispatch')
class comment_remove_assgn(DeleteView):
    model = CommentAssgn
    context_object_name = 'commentsassg'
    template_name = 'classroom/teachers/comment_delete_assgn_confirm.html'

    def get_success_url(self):
        return reverse('add_comment_to_post_assgn', kwargs={'course_pk': self.object.assignment.course.pk, 'assgn_pk': self.object.assignment.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'comment deleted successfully!')
        return super().delete(request, *args, **kwargs)


@method_decorator([login_required, teacher_required], name='dispatch')
class comment_approve_assgn(UpdateView):
    model = CommentAssgn
    fields = ('text',)
    template_name = 'classroom/teachers/comment_edit_assgn.html'

    def get_queryset(self):
        '''
        This method is an implicit object-level permission management
        This view will only match the ids of existing courses that belongs
        to the logged in user.
        '''
        return self.request.user.commentsassg.all()

    def get_success_url(self):
        messages.success(self.request, ' comment updated successfully '  )
        return reverse('add_comment_to_post_assgn', kwargs={'course_pk': self.object.assignment.course.pk, 'assgn_pk': self.object.assignment.pk})



@method_decorator([login_required, teacher_required], name='dispatch')
class reply_remove_assgn(DeleteView):
    model = CommentAssgn
    template_name = 'classroom/teachers/reply_delete_assgn.html'

    def get_success_url(self):
        return reverse('add_comment_to_post_assgn', kwargs={'course_pk': self.object.assignment.course.pk, 'assgn_pk': self.object.assignment.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'reply deleted successfully!')
        return super().delete(request, *args, **kwargs)




@method_decorator([login_required, teacher_required], name='dispatch')
class reply_approve_assgn(UpdateView):
    model = CommentAssgn
    fields = ('text',)
    template_name = 'classroom/teachers/reply_edit_assgn.html'

    def get_queryset(self):
        '''
        This method is an implicit object-level permission management
        This view will only match the ids of existing courses that belongs
        to the logged in user.
        '''
        return self.request.user.commentsassg.all()

    def get_success_url(self):
        messages.success(self.request, ' reply updated successfully '  )
        return reverse('add_comment_to_post_assgn', kwargs={'course_pk': self.object.assignment.course.pk, 'assgn_pk': self.object.assignment.pk})

