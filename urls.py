from django.urls import include, path
from django.contrib import admin
from . import views
from classroom.views import classroom, students, teachers, ta
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('blog/comments/', include('fluent_comments.urls')),


    path('', include('classroom.urls')),



    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/signup/', classroom.SignUpView.as_view(), name='signup'),
    path('accounts/signup/student/', students.StudentSignUpView.as_view(), name='student_signup'),
    path('accounts/signup/teacher/', teachers.TeacherSignUpView.as_view(), name='teacher_signup'),
    path('accounts/signup/ta/', ta.TaSignUpView.as_view(), name='ta_signup'),
    path('accounts/signup/teacher/teach/', views.homepage, name='index'),
    path('accounts/signup/student/<int:pk>/', views.mypage, name='myindex'),
    path('changepassword/',students.change_password, name='change_password'),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)