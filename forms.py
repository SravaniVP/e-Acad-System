from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.forms.utils import ValidationError
from multiupload.fields import MultiFileField

from classroom.models import Student, User, Document, Course,Assignment, Submission, Marks, TA,Comment,CommentAssgn,Vote,Myfiles,File


class TeacherSignUpForm(UserCreationForm):

    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].required = True


    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_teacher = True
        if commit:
            user.save()
        return user


class StudentSignUpForm(UserCreationForm):

    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].required = True

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'semester','RollNo', 'email', )

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.is_student = True
        user.save()
        student = Student.objects.create(user=user)

        return user


class TaSignUpForm(UserCreationForm):
    interests = forms.ModelMultipleChoiceField(
        queryset= Course.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].required = True

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', )


    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.is_ta = True
        user.save()
        student = TA.objects.create(user=user)
        student.interests.add(*self.cleaned_data.get('interests'))

        return user


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ('file_name', 'file_upload', )

class FilesForm(forms.ModelForm):
    class Meta:
        model = Myfiles
        fields = ('file_name', 'desc','file_upload', )

class FForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ('file_name', 'desc','file_upload', )

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ('file_name', 'file_upload','max_marks', )


class UploadForm(forms.Form):
    documents = MultiFileField(min_num=1,max_num=3, max_file_size=1024*1024*5)

    class Meta:
        model = Course
        fields = '__all__'

    def save(self, commit=True):
        instance = super(UploadForm, self).save(commit)
        for each in self.cleaned_data['documents']:
            Document.objects.create(file_upload=each, Course=instance)
        return instance

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)


class CommentAssgnForm(forms.ModelForm):
    class Meta:
        model = CommentAssgn
        fields = ('text',)


class TACourseForm(forms.ModelForm):
    class Meta:
        model = TA
        fields = ('interests', )
        widgets = {
            'interests': forms.CheckboxSelectMultiple
        }



class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ('file_name', 'file_upload', )


class xStudentInterestsForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ('ta', )
        widgets = {
            'ta': forms.CheckboxSelectMultiple
        }


class StudentRegForm(forms.ModelForm):
    def __init__(self, x, *args, **kwargs):
        super(StudentRegForm, self).__init__(*args, **kwargs)
        self.fields['interests'].queryset = Course.objects.filter(semester=x)

    class Meta:
        model = Student
        fields = ('interests',)
        widgets = {
            'interests': forms.CheckboxSelectMultiple
        }


class TAForm(forms.ModelForm):
    def __init__(self,course, *args, **kwargs):
        super(TAForm, self).__init__(*args, **kwargs)
        self.fields['ta'].queryset = TA.objects.all().filter(interests=course)

    class Meta:
        model = Assignment
        fields = ('ta',)


class StudentInterestsForm(forms.ModelForm):

    class Meta:
        model = Assignment
        fields = ('ta',)
        widgets = {
            'ta': forms.CheckboxSelectMultiple
        }




class xStudentRegForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(StudentRegForm, self).__init__(*args, **kwargs)
        self.fields['interests'].queryset = Course.objects.filter(semister=self.request.user.semister)

    interests = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    class Meta:
        model = Student
        fields = ('interests',)




class xTARegForm(forms.ModelForm):
    ta = forms.ModelMultipleChoiceField(
        queryset=TA.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    class Meta:
        model = TA
        fields = ('user',)


class AllotMarksForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ('mark', 'feedback', )



class StudentXRegForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ('interests', )
        widgets = {
            'interests': forms.CheckboxSelectMultiple
        }


