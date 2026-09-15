from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path("favicon.ico", views.favicon),
    path('media/', views.media, name='media'),
    path('images/', views.images, name='images'),
    path('scripts/', views.scripts, name='scripts'),
    path('preassign_script/', views.preassign_script, name='preassign_script'),

    path('error', views.error_logs, name='error_logger'),
    path('hook', views.hook_logs, name='hook_logs'),
    path('mutation', views.mutation_logs, name='mutation_logs'),
    path('poll', views.poll_logs, name='poll_logs'),
    path('counter', views.extension_state_counter, name='extension_state_counter'),
    path("coverage", views.coverage_logs, name="coverage"),
    path("state", views.state_logs, name="state"),
    path("proxy", views.proxy_logs, name="proxy"),
]