from django.contrib import messages
from django.contrib.auth import login
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render, render_to_response
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, UpdateView, DetailView,DeleteView

from ..decorators import ta_required
from ..forms import  TaSignUpForm,CommentForm,TACourseForm,CommentAssgnForm,FForm
from ..models import Course, Student, User,TA, Assignment, Submission, Document,Comment,CommentAssgn,File


class TaSignUpView(CreateView):
    model = User
    form_class = TaSignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'Teaching Assistant'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('ta_course_list')

@method_decorator([login_required], name='dispatch')
class ProfileUpdateView(UpdateView):
    model = User
    fields = ('username','first_name','last_name', 'email',)
    template_name = 'classroom/students/profile.html'

    def get_success_url(self):
        messages.success(self.request,'profile updated successfully!')
        return reverse('home')

@login_required
@ta_required
def CourseregView(request):
    student = TA.objects.get(pk=request.user.id)
    courses = student.interests.all()

    return render(request,'classroom/ta/home_ta.html', {
        "student": student,
        "courses": courses,
    })


@login_required
@ta_required
def tamyprivate(request):
    files = File.objects.all().filter(owner=request.user)
    return render(request,'classroom/ta/ta_private_files.html',{'files':files })

@login_required
@ta_required
def taaddfiles(request):

    if request.method == 'POST':
        form = FForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.owner = request.user
            document.save()
            form.save()
            messages.success(request, '%s File added succesfully!' % document.file_name)
            return redirect('ta_private')

    else:
        form = FForm()

    return render(request, 'classroom/ta/ta_add_file.html', {'form': form})

@method_decorator([login_required, ta_required], name='dispatch')
class TAInterestsView(UpdateView):
    model = TA
    form_class = TACourseForm
    template_name = 'classroom/ta/ta_update_form.html'

    def form_valid(self, form):
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, ' courses updated successfully '  )
        return reverse('ta_course_list')


@method_decorator([login_required, ta_required], name='dispatch')
class CourseDetailView(DetailView):
    model = Course
    context_object_name = 'course'
    template_name = 'classroom/ta/ta_course_detail.html'

    def get_context_data(self, **kwargs):
        kwargs['documents'] = self.get_object().documents.annotate()
        kwargs['assignments'] = self.get_object().assignments.annotate()
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return reverse('course_ta_view', kwargs={'pk': self.object.pk})

@method_decorator([login_required, ta_required], name='dispatch')
class FileDeleteView(DeleteView):
    model = File
    context_object_name = 'document'
    template_name = 'classroom/ta/file_delete.html'
    success_url = reverse_lazy('ta_private')

    def delete(self, request, *args, **kwargs):
        assignment = self.get_object()
        messages.success(request, ' %s file deleted successfully!' % assignment.file_name)
        return super().delete(request, *args, **kwargs)


@login_required
@ta_required
def detailview(request,pk):
    course = get_object_or_404(Course, pk=pk)
    documents = Document.objects.all().filter(course=course)
    ta =get_object_or_404(TA,user=request.user)
    assignments = Assignment.objects.all().filter(course=course,ta=ta )
    return render(request, 'classroom/ta/detail_view.html',{ 'documents':documents,'assignments':assignments,'course':course})

@login_required
@ta_required
def submitview(request,course_pk,assignment_pk):
    course = get_object_or_404(Course, pk=course_pk)
    assignment = get_object_or_404(Assignment,pk=assignment_pk)
    submits = Submission.objects.all().filter(course=course,assignment=assignment)
    return render(request, 'classroom/ta/ta_student_submission_view.html',{'submits': submits, 'assignment':assignment,'course':course})


@method_decorator([login_required, ta_required], name='dispatch')
class AssignDeleteView(DeleteView):
    model = Assignment
    context_object_name = 'assignment'
    template_name = 'classroom/ta/ta_assign_delete_confirm.html'
    success_url = reverse_lazy('ta_course_list')

    def delete(self, request, *args, **kwargs):
        assignment = self.get_object()
        messages.success(request, 'The course %s was deleted with success!' % assignment.file_name)
        return super().delete(request, *args, **kwargs)


@method_decorator([login_required, ta_required], name='dispatch')
class NotesDeleteView(DeleteView):
    model =Document
    context_object_name = 'assignment'
    template_name = 'classroom/ta/ta_assign_delete_confirm.html'
    success_url = reverse_lazy('ta_course_list')

    def delete(self, request, *args, **kwargs):
        assignment = self.get_object()
        messages.success(request, 'The notes %s was deleted with success!' % assignment.file_name)
        return super().delete(request, *args, **kwargs)


@method_decorator([login_required, ta_required], name='dispatch')
class AllotMark(UpdateView):
    model = Submission
    fields = ('mark', 'feedback',)
    template_name = 'classroom/ta/ta_allot_marks.html'

    def get_context_data(self, **kwargs):
        kwargs['submissions'] = self.get_object()
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        messages.success(self.request, ' Marks alloted successfully ')
        return reverse('ta_student_submissions', kwargs={'course_pk': self.object.course.pk, 'assignment_pk': self.object.assignment.pk})


@login_required
@ta_required
def view_discussion(request,pk):
    document = get_object_or_404(Document,pk=pk)
    comments =Comment.objects.all().filter(document=document)
    return render(request, 'classroom/ta/ta_discussion.html',{'document': document,'comments':comments })




@method_decorator([login_required, ta_required], name='dispatch')
class PermissionUpdateView(UpdateView):
    model = Assignment
    fields = ('visible',)
    template_name ='classroom/ta/ta_update_permission.html'

    def get_success_url(self):
        messages.success(self.request, 'permission updated!')
        return reverse('course_ta_view', kwargs={'pk': self.object.course.pk})



@login_required
@ta_required
def add_comment_to_post_ta(request, course_pk, notes_pk):
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
    return render(request, 'classroom/ta/add_comment.html', {'course':course, 'document':document, 'comments':comments, 'comment_form':comment_form})



@method_decorator([login_required, ta_required], name='dispatch')
class comment_remove_ta(DeleteView):
    model = Comment
    template_name = 'classroom/ta/comment_delete_confirm.html'
    def get_success_url(self):
        return reverse('add_comment_to_post_ta', kwargs={'course_pk': self.object.document.course.pk, 'notes_pk': self.object.document.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'comment deleted successfully!')
        return super().delete(request, *args, **kwargs)




@method_decorator([login_required, ta_required], name='dispatch')
class comment_approve_ta(UpdateView):
    model = Comment
    fields = ('text',)
    template_name = 'classroom/ta/comment_edit_form.html'

    def get_queryset(self):
        '''
        This method is an implicit object-level permission management
        This view will only match the ids of existing courses that belongs
        to the logged in user.
        '''
        return self.request.user.comments.all()

    def get_success_url(self):
        messages.success(self.request, ' comment updated successfully '  )
        return reverse('add_comment_to_post_ta', kwargs={'course_pk': self.object.document.course.pk, 'notes_pk': self.object.document.pk})


@method_decorator([login_required, ta_required], name='dispatch')
class reply_remove_ta(DeleteView):
    model = Comment
    template_name = 'classroom/ta/reply_delete_confirm.html'
    def get_success_url(self):
        return reverse('add_comment_to_post_ta', kwargs={'course_pk': self.object.document.course.pk, 'notes_pk': self.object.document.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Reply deleted successfully!')
        return super().delete(request, *args, **kwargs)




@method_decorator([login_required, ta_required], name='dispatch')
class reply_approve_ta(UpdateView):
    model = Comment
    fields = ('text',)
    template_name = 'classroom/ta/reply_edit_form.html'

    def get_queryset(self):
        '''
        This method is an implicit object-level permission management
        This view will only match the ids of existing courses that belongs
        to the logged in user.
        '''
        return self.request.user.comments.all()

    def get_success_url(self):
        messages.success(self.request, ' Reply updated successfully '  )
        return reverse('add_comment_to_post_ta', kwargs={'course_pk': self.object.document.course.pk, 'notes_pk': self.object.document.pk})



@login_required
@ta_required
def add_comment_to_post_ta_assgn(request, course_pk, assgn_pk):
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
    return render(request, 'classroom/ta/add_comment_assgn.html', { 'course':course,'assignment':assignment, 'AssgnComments':AssgnComments, 'commentassgn_form':commentassgn_form})


@method_decorator([login_required, ta_required], name='dispatch')
class comment_remove_ta_assgn(DeleteView):
    model = CommentAssgn
    template_name = 'classroom/ta/comment_delete_assgn_confirm.html'

    def get_success_url(self):
        return reverse('add_comment_to_post_ta_assgn', kwargs={'course_pk': self.object.assignment.course.pk, 'assgn_pk': self.object.assignment.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'comment deleted successfully!')
        return super().delete(request, *args, **kwargs)




@method_decorator([login_required, ta_required], name='dispatch')
class comment_approve_ta_assgn(UpdateView):
    model = CommentAssgn
    fields = ('text',)
    template_name = 'classroom/ta/comment_edit_assgn.html'

    def get_queryset(self):
        '''
        This method is an implicit object-level permission management
        This view will only match the ids of existing courses that belongs
        to the logged in user.
        '''
        return self.request.user.commentsassg.all()

    def get_success_url(self):
        messages.success(self.request, ' comment updated successfully '  )
        return reverse('add_comment_to_post_ta_assgn', kwargs={'course_pk': self.object.assignment.course.pk, 'assgn_pk': self.object.assignment.pk})


@method_decorator([login_required, ta_required], name='dispatch')
class reply_remove_ta_assgn(DeleteView):
    model = CommentAssgn
    template_name = 'classroom/ta/reply_delete_assgn.html'

    def get_success_url(self):
        return reverse('add_comment_to_post_ta_assgn', kwargs={'course_pk': self.object.assignment.course.pk, 'assgn_pk': self.object.assignment.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Reply deleted successfully!')
        return super().delete(request, *args, **kwargs)




@method_decorator([login_required, ta_required], name='dispatch')
class reply_approve_ta_assgn(UpdateView):
    model = CommentAssgn
    fields = ('text',)
    template_name = 'classroom/ta/reply_edit_assgn.html'

    def get_queryset(self):
        '''
        This method is an implicit object-level permission management
        This view will only match the ids of existing courses that belongs
        to the logged in user.
        '''
        return self.request.user.commentsassg.all()

    def get_success_url(self):
        messages.success(self.request, ' Reply updated successfully '  )
        return reverse('add_comment_to_post_ta_assgn', kwargs={'course_pk': self.object.assignment.course.pk, 'assgn_pk': self.object.assignment.pk})
