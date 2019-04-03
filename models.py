from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db import IntegrityError
from django.utils.html import escape, mark_safe
from django.utils import timezone


class User(AbstractUser):
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    is_ta = models.BooleanField(default=False)
    semester = models.IntegerField(default=0)
    RollNo = models.CharField(max_length=100, default='')
    vote = models.BooleanField(default=False)


class Course(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    semester = models.IntegerField(default=0)
    course_code = models.CharField(max_length=100, default='course_code')
    course_title = models.CharField(max_length=100, default='course_title')
    about = models.TextField(default='anything about course')
    totalclasses = models.IntegerField(default=0)
    classestaken = models.IntegerField(default=0)

    def __str__(self):
        return self.course_title


class Student(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, primary_key=True, related_name='student')
    interests = models.ManyToManyField(Course, related_name='interested_students')

    def __str__(self):
        return self.user.username


class Attendance(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE,related_name='attendance_course')
    student = models.ForeignKey(Student, on_delete=models.CASCADE,related_name='student')
    at = models.IntegerField(default=0)


class Vote(models.Model):
    candidate = models.ForeignKey(Student, on_delete=models.CASCADE,related_name='candidate')
    semester = models.IntegerField(default=0)
    count = models.IntegerField(default=0)
    approve = models.BooleanField(default=False)
    winner = models.BooleanField(default=False)

    def __str__(self):
        return self.candidate.user.username


class TA(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, primary_key=True, related_name='ta')
    interests = models.ManyToManyField(Course, related_name='interested_tas')

    def __str__(self):
        return self.user.username

class Document(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='documents')
    file_name = models.CharField(max_length=500, default='')
    file_upload = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(default=timezone.now)

    def approved_comments(self):
        return self.comments.filter(approved_comment=True)

    def __str__(self):
        return self.file_name


class Myfiles(models.Model):
    owner = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='files')
    file_name = models.CharField(max_length=500, default='')
    desc = models.CharField(max_length=10000,default='')
    file_upload = models.FileField(upload_to='private_files/')
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.file_name

class File(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='file')
    file_name = models.CharField(max_length=500, default='')
    desc = models.CharField(max_length=10000,default='')
    file_upload = models.FileField(upload_to='private_files/')
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.file_name


class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    file_name = models.CharField(max_length=500, default='')
    file_upload = models.FileField(upload_to='assignments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    max_marks = models.FloatField()
    ta = models.ManyToManyField(TA,default=None, related_name='tas')
    visible = models.BooleanField(default=False)

    def approved_comments(self):
        return self.commentsassg.filter(approved_comment=True)

    def __str__(self):
        return self.file_name


class Submission(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='submissions')
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    file_name = models.CharField(max_length=500, default='')
    file_upload = models.FileField(upload_to='submissions/')
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True)
    mark = models.FloatField(default=0)
    feedback = models.CharField(max_length=200, default='Not updated yet!')

    def __str__(self):
        return self.file_name


class Marks(models.Model):
    mark = models.FloatField()
    feedback = models.CharField(max_length=200, default='')
    student = models.ForeignKey(Student, on_delete=models.CASCADE,related_name='marks')

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='comments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='comments')
    text = models.CharField(max_length=1000)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)
    approved_comment = models.BooleanField(default=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')

    class Meta:
        ordering = ('created_date',)

    def approve(self):
        self.approved_comment = True
        self.save()

    def __str__(self):
        return 'Comment by {}'.format(self.user)

class CommentAssgn(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='commentsassg')
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='commentsassg')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='commentsassg')
    text = models.CharField(max_length=1000)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)
    approve_comment = models.BooleanField(default=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='reply')

    class Meta:
        ordering = ('created_date',)

    def approve(self):
        self.approve_comment = True
        self.save()

    def __str__(self):
        return 'Comment by {}'.format(self.user)