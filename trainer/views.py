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

    # get user
    user_id = "testuser"
    user = User.objects.get(user_id="testuser")
    rank = user.get_user_rank_display()
    # task randomizer
    index = random.randint(0, 3)
    # for AllKommaSetzen.html + AllKommaErklärenI.html
    if index < 2:
        # choose a sentence from roulette wheel (the bigger the error for
        # a certain rule, the more likely one will get a sentence with that rule)
        sentence = user.roulette_wheel_selection()
        # pack all words of this sentence in a list
        words = sentence.get_words()
        # pack all commas [0,1,2] in a list
        comma = sentence.get_commalist()
        # pack all comma types [['A2.1'],...] of this sentence in a list
        comma_types = sentence.get_commatypelist()

        # for AllKommaSetzen.html
        if index == 0:
            # pack all selects in a list
            comma_select = sentence.get_commaselectlist()
            # dirty trick to make the comma_select and comma_types the same length as words
            comma_select.append('0')
            comma_types.append([])
            # get total amount of submits
            submits = sentence.total_submits

            # printing out user results
            dictionary = user.comma_type_false
            # generating tooltip content
            collection = []
            for i in range(len(comma_types)):
                if submits != 0:
                    collection.append((comma_types[i], int((int(comma_select[i])/submits)*100)))
                else:
                    collection.append((comma_types[i], 0))

            return render(request, 'trainer/AllKommaSetzen.html', locals())

        # for AllKommaErklärenI.html
        elif index == 1:
            # generating radio buttons content
            explanations = []
            # list of indexes of correct solution
            index_arr = []
            print(sentence)
            for i in range(len(comma_types)):
                if len(comma_types[i]) != 0:
                    exp, index = sentence.get_explanations(comma_types[i][0],user)
                    explanations.append(exp)
                    index_arr.append(index)

            return render(request, 'trainer/AllKommaErklärenI.html', locals())
    # for KannKommaSetzen.html + KannKommaLöschen.html
    elif index >= 2 and index < 4:
        # choose a sentence containing "may" commas from roulette wheel (the bigger the error for
        # a certain rule, the more likely one will get a sentence with that rule)
        sentence = user.may_roulette_wheel_selection()
        # pack all words of this sentence in a list
        words = sentence.get_words()
        # pack all commas [0,1,2] in a list
        comma = sentence.get_commalist()
        # pack all comma types [['A2.1'],...] of this sentence in a list
        comma_types = sentence.get_commatypelist()
        # pack all selects in a list
        comma_select = sentence.get_commaselectlist()
        # dirty trick to make the comma_select and comma_types the same length as words
        comma_select.append('0')
        comma_types.append([])
        # get total amount of submits
        submits = sentence.total_submits

        # printing out user results
        dictionary = user.comma_type_false
        rank = user.get_user_rank_display()
        # generating tooltip content
        collection = []
        for i in range(len(comma_types)):
            if submits != 0:
                collection.append((comma_types[i], int((int(comma_select[i]) / submits) * 100)))
            else:
                collection.append((comma_types[i], 0))
        if index == 2:
            return render(request, 'trainer/KannKommaSetzen.html', locals())
        else:
            return render(request, 'trainer/KannKommaLöschen.html', locals())

def profile(request):
    user_id = "testuser"
    user = User.objects.get(user_id="testuser")
    dictionary = user.get_dictionary()
    new_dictionary = {}
    for i in dictionary:
        if i != 'KK':
            a, b = re.split(r'/', dictionary[i])
            rule_desc = Rule.objects.get(code=i).slug
            if b != '0':
                new_dictionary[rule_desc] = str(100-int((int(a)/int(b))*100))
            else:
                new_dictionary[rule_desc] = str(0)
    rank = user.get_user_rank_display()
    tasks = []
    for roots, directs, files in os.walk("trainer/templates/trainer"):
        for file in files:
            tasks.append(file[:-5]);
    return render(request, 'user_profile.html', locals())

def submit_task1(request):
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
    user.count_false_types_task1(user_solution, sentence.get_commatypelist())
    user.update_rank()
    return JsonResponse({'submit': 'ok'})

def submit_task2(request):
    """
    Receives an AJAX GET request containing a solution bitfield for a sentence.
    Saves solution and user_id to database.

    :param request: Django request
    :return: nothing
    """
    sentence = Sentence.objects.get(id=request.GET['id'])
    sentence.update_submits()
    user = User.objects.get(user_id="testuser")
    user.update_rank()
    chckbx_sol = request.GET['chckbx_sol']
    user.count_false_types_task2(chckbx_sol, sentence.get_commatypelist())
    return JsonResponse({'submit': 'ok'})

def submit_task3(request):
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
    user.count_false_types_task3(user_solution, sentence.get_commatypelist())
    user.update_rank()
    return JsonResponse({'submit': 'ok'})

def submit_task4(request):
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
    user.count_false_types_task4(user_solution, sentence.get_commatypelist())
    user.update_rank()
    return JsonResponse({'submit': 'ok'})