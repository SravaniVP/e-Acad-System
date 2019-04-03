from django.contrib import admin
from .models import Student,Course, User, Document, Assignment,Submission,TA,Comment,CommentAssgn,Attendance,Vote,Myfiles,File

admin.site.register(User)
admin.site.register(Student)
admin.site.register(TA)
admin.site.register(Course)
admin.site.register(Document)
admin.site.register(Assignment)
admin.site.register(Submission)
admin.site.register(Comment)
admin.site.register(CommentAssgn)
admin.site.register(Attendance)
admin.site.register(Vote)
admin.site.register(Myfiles)
admin.site.register(File)

