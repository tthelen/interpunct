from django.conf.urls import url

from . import views

urlpatterns = [
    # ex: /polls/
    url(r'^$', views.task, name='task'),
    url(r'^submit_task1$', views.submit_task1),
    url(r'^submit_task2$', views.submit_task2),
    url(r'^submit_task3$', views.submit_task3),
    url(r'^submit_task4$', views.submit_task4),
    url(r'^profile$', views.profile),
    # ex: /polls/5/
    #url(r'^(?P<question_id>[0-9]+)/$', views.detail, name='detail'),
    # ex: /polls/5/results/
    #url(r'^(?P<question_id>[0-9]+)/results/$', views.results, name='results'),
    # ex: /polls/5/vote/
    #url(r'^(?P<question_id>[0-9]+)/vote/$', views.vote, name='vote'),
]