from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('login/', views.login_page, name='login'),
    path('feedbacks/', views.home, name='home'),
    path('submit/', views.submit_feedback, name='submit_feedback'),
    path('issues/', views.issues_view, name='issues'),
    path('submit_issue/', views.submit_issue, name='submit_issue'),
    path('submit_suggestion/', views.submit_suggestion, name='submit_suggestion'),
    path('upvote/<int:suggestion_id>/', views.upvote_suggestion, name='upvote_suggestion'),
    path('gallery/', views.gallery_view, name='gallery'),
    path('gallery/upload/', views.upload_photo, name='upload_photo'),
    path('gallery/like/<int:photo_id>/', views.like_photo, name='like_photo'),
    path('gallery/comment/<int:photo_id>/', views.add_comment, name='add_comment'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/approve/<int:feedback_id>/', views.approve_feedback, name='approve_feedback'),
    path('admin-dashboard/delete/<int:feedback_id>/', views.delete_feedback, name='delete_feedback'),
    path('admin-dashboard/update-issue/<int:issue_id>/', views.update_issue_status, name='update_issue_status'),
    path('admin-dashboard/delete-suggestion/<int:suggestion_id>/', views.delete_suggestion, name='delete_suggestion'),
    path('admin-dashboard/delete-photo/<int:photo_id>/', views.delete_photo, name='delete_photo'),
    path('admin-dashboard/delete-issue/<int:issue_id>/', views.delete_issue, name='delete_issue'),
]
