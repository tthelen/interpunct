from django.conf.urls import url

from . import views

urlpatterns = [
    # ex: /polls/
    url(r'^$', views.task, name='task'),
    url(r'^index$', views.index, name='index'),
    url(r'^start$', views.start, name='start'),
    url(r'^submit_task_set_commas$', views.submit_task_set_commas),
    url(r'^submit_task_correct_commas$', views.submit_task_correct_commas),
    url(r'^submit_task_explain_commas$', views.submit_task_explain_commas, name='submit_task_explain_commas'),
    url(r'^submit_adaptivity_questionnaire$', views.submit_adaptivity_questionnaire, name='submit_adaptivity_questionnaire'),
    url(r'^delete_user$', views.delete_user),
    url(r'^logout$', views.logout),
    url(r'^sentence/([0-9]+)$', views.sentence, name='sentence'),  # ajax load html for single correct sentence
    url(r'^help$', views.help, name='help'),
    url(r'^mystats$', views.mystats, name='mystats'),
    url(r'^mystats_rule/$', views.mystats_rule, name='mystats_rule'),  # ajax load for single rule stat
    url(r'^allstats_sentence/$', views.allstats_sentence, name='allstats_sentence'),  # ajax load for single sentence stats
    url(r'^allstats_correct_sentence/$', views.allstats_correct_sentence, name='allstats_correct_sentence'),  # ajax load for single sentence stats
    url(r'^stats$', views.stats, name='stats'),
    url(r'^stats2$', views.stats2, name='stats2'), # stats for leitner/bayes experiment
    url(r'^ustats$', views.ustats, name='ustats'),
    url(r'^allstats$', views.allstats, name='allstats'),  # sentence statistics for "set comma" task
    url(r'^allstats_correct$', views.allstats_correct, name='allstats_correct'),  # sentence statistics for "correct comma" task
    url(r'^nocookies$', views.nocookies, name='nocookies'),
    url(r'^vanillalm$', views.vanillalm, name='vanillalm'),
    url(r'^assignment/1/', views.LTIAssignment1View.as_view()),

]