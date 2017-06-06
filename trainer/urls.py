from django.conf.urls import url

from . import views

urlpatterns = [
    # ex: /polls/
    url(r'^$', views.task, name='task'),
    url(r'^start$', views.start),
    url(r'^submit_task1$', views.submit_task1),
    url(r'^submit_task_correct_commas$', views.submit_task_correct_commas),
    url(r'^submit_task_explain_commas$', views.submit_task_explain_commas, name='submit_task_explain_commas'),
    url(r'^delete_user$', views.delete_user),
    url(r'^logout$', views.logout),
    url(r'^sentence/([0-9]+)$', views.sentence, name='sentence'),  # ajax load html for single correct sentence
    url(r'^help$', views.help, name='help'),
    url(r'^stats$', views.stats, name='stats')
    # ex: /polls/5/
    #url(r'^(?P<question_id>[0-9]+)/$', views.detail, name='detail'),
    # ex: /polls/5/results/
    #url(r'^(?P<question_id>[0-9]+)/results/$', views.results, name='results'),
    # ex: /polls/5/vote/
    #url(r'^(?P<question_id>[0-9]+)/vote/$', views.vote, name='vote'),
]