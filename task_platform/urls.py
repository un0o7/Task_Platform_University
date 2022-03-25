from django.urls import path, re_path
from django.conf import settings
from django.views.static import serve
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create-task/', views.create_task, name='create-task'),
    path('detail/tk<int:task_id>/', views.detail, name='detail'),
    #<int:task_id>可以通过url传递参数，在这个位置放入对应的值
    path('upload/', views.sceneImgUpload, name='uploadimg'),
    path('upload/&responseType=json', views.sceneImgUpload),
    path('profile/', views.profile, name='profile'),
    path('chatroom/<str:room_id>', views.chatroom, name='chatroom'),
    path('guide/', views.guide, name='guide'),#name是一种别名
    path('about/', views.about, name='about'),
    path('image/<str:img_id>', views.image_sight, name='image'),
    path('task-search/', views.search, name='search'),
]
