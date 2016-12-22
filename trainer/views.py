# from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import JsonResponse
from .models import Sentence, Solution, Rule, User
import re  # regex support
import os

def task(request):
    """
    Pick a task and show it.

    :param request: Django request
    :return: nothing
    """

    import random

    user_id = "testuser"
    user = User.objects.get(user_id="testuser")
    # get a random sentence
    #count = Sentence.objects.all().count()
    #sentence = Sentence.objects.all()[int(random.random() * count)]
    sentence = user.roulette_wheel_selection()

    # pack all words of this sentence in a list
    words = sentence.get_words()
    comma = sentence.get_commalist()

    # pack all comma types of this sentence in a list
    comma_types = sentence.get_commatypelist()
    comma_select = sentence.get_commaselectlist()
    # dirty trick to make the comma_select the same length as comma_types
    comma_select.append('0')
    comma_types.append([])
    submits = sentence.total_submits

    # printing out user results
    dictionary = user.comma_type_false
    rank = user.get_user_rank_display()
    # generating radio buttons content
    explanations = []
    index_arr = []
    for i in range(len(comma_types)):
        if len(comma_types[i]) != 0:
            exp, index = sentence.get_explanations(comma_types[i][0],user)
            explanations.append(exp)
            index_arr.append(index)
    # generating tooltip content
    collection = []
    for i in range(len(comma_types)):
        if submits!=0:
            collection.append((comma_types[i], int((int(comma_select[i])/submits)*100)))
        else:
            collection.append((comma_types[i], 0))
    # task randomizer
    index = random.randint(0, 1)
    if index == 0:
        return render(request, 'trainer/KommaSetzen.html', locals())
    else:
        return render(request, 'trainer/KommaErklärenI.html', locals())

def profile(request):
    user_id = "testuser"
    user = User.objects.get(user_id="testuser")
    dictionary = user.get_dictionary()
    for i in dictionary:
        if i != 'KK':
            a, b = re.split(r'/', dictionary[i])
            if b != '0':
                dictionary[i] = str(100-int((int(a)/int(b))*100))
            else:
                dictionary[i] = str(0)
    rank = user.get_user_rank_display()
    tasks = []
    for roots, directs, files in os.walk("trainer/templates/trainer"):
        for file in files:
            tasks.append(file[:-5]);
    return render(request, 'user_profile.html', locals())

def submit(request):
    """
    Receives an AJAX GET request containing a solution bitfield for a sentence.
    Saves solution and user_id to database.

    :param request: Django request
    :return: nothing
    """
    sentence = Sentence.objects.get(id=request.GET['id'])
    user_solution = request.GET['sol']
    sentence.set_comma_select(user_solution)
    sentence.update_submits()
    user = User.objects.get(user_id="testuser")
    comma_types = sentence.get_commatypelist()
    user.count_false_types_task1(user_solution, comma_types)
    user.update_rank()
    chckbx_sol = request.GET['chckbx_sol']
    user.count_false_types_task2(chckbx_sol, comma_types)
    return JsonResponse({'submit': 'ok'})
