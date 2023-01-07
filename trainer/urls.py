from django.urls import path

from . import views

urlpatterns = [
    path('', views.task, name='task'),
    path('start_new', views.start_new, name='start_new'),
    path('start_continue', views.start_continue, name='start_continue'),
    path('help', views.help, name='help'),
    path('rules', views.rules, name='rules'),
    path('nocookies', views.nocookies, name='nocookies'),
    path('impressum', views.impressum, name='impressum'),
    path('code', views.code, name='code'),
    path('logout', views.logout_view, name='logout'),

    # ajax routes for tasks
    path('submit_task_set_commas', views.submit_task_set_commas),
    path('submit_task_correct_commas', views.submit_task_correct_commas),
    path('submit_task_explain_commas', views.submit_task_explain_commas, name='submit_task_explain_commas'),
    path('delete_user', views.delete_user),
    path('sentence/<int:sentence_id>', views.sentence, name='sentence'),  # ajax load html for single correct sentence

    # statistics
    path('mystats', views.mystats, name='mystats'),
    path('mystats_rule/', views.mystats_rule, name='mystats_rule'),  # ajax load for single rule stat
    path('allstats_sentence/', views.allstats_sentence, name='allstats_sentence'),
    # ajax load for single sentence stats
    path('allstats_correct_sentence/', views.allstats_correct_sentence, name='allstats_correct_sentence'),
    # ajax load for single sentence stats
    path('stats', views.stats, name='stats'),
    path('ustats', views.ustats, name='ustats'),
    path('allstats', views.allstats, name='allstats'),  # sentence statistics for "set comma" task
    # sentence statistics for "correct comma" task
    path('allstats_correct', views.allstats_correct, name='allstats_correct'),

]