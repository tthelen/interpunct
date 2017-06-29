from django.conf.urls import url

from . import views

urlpatterns = [
    # ex: /polls/
    url(r'^$', views.task, name='task'),
    url(r'^start$', views.start, name='start'),
    url(r'^submit_task1$', views.submit_task1),
    url(r'^submit_task_correct_commas$', views.submit_task_correct_commas),
    url(r'^submit_task_explain_commas$', views.submit_task_explain_commas, name='submit_task_explain_commas'),
    url(r'^delete_user$', views.delete_user),
    url(r'^logout$', views.logout),
    url(r'^sentence/([0-9]+)$', views.sentence, name='sentence'),  # ajax load html for single correct sentence
    url(r'^help$', views.help, name='help'),
    url(r'^mystats$', views.mystats, name='mystats'),
    url(r'^mystats_rule/$', views.mystats_rule, name='mystats_rule'), # ajax load for single rule stat
    url(r'^stats$', views.stats, name='stats'),
    url(r'^allstats$', views.allstats, name='allstats'),
    url(r'^nocookies$', views.nocookies, name='nocookies')

]