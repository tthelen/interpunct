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

    # get user from URL or session or default
    user_id = request.GET.get('user_id', request.session.get('user_id', "testuser00"))

    try:
        user = User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        user = User(user_id=user_id)
        user.save()

    if user.rules_activated_count == 0: # new user without activated rules
        user.rules_activated_count = 1  # activate first rule for next request
        user.save()
        return render(request, 'trainer/welcome.html', locals())
    else:
        new_rule = user.progress()
        level = user.rules_activated_count
        if new_rule:
            return render(request, 'trainer/level_progress.html', locals())

    rank = user.get_user_rank_display()
    level = user.level_display()
    # task randomizer
    # index = random.randint(0, 4)
    index = 0
    # for AllKommaSetzen.html + AllKommaErklärenI.html
    if index < 3:
        # choose a sentence from roulette wheel (the bigger the error for
        # a certain rule, the more likely one will get a sentence with that rule)
        #TODO: fetch errors
        sentence = user.roulette_wheel_selection()
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
        # generating tooltip content
        collection = []
        for i in range(len(comma_types)):
            if submits != 0:
                collection.append((comma_types[i], int((int(comma_select[i])/submits)*100)))
            else:
                collection.append((comma_types[i], 0))
        if index==0:
            return render(request, 'trainer/AllKommaSetzen.html', locals())

        # generating radio buttons content (2D array to be)
        explanations = []
        # list of indexes of correct solution (2D array to be)
        index_arr = []

        for i in range(len(comma_types)):
            if len(comma_types[i]) != 0:
                # In case there is only one comma type
                if len(comma_types[i]) == 1:
                    options, solution_index = sentence.get_explanations(comma_types[i][0], user)
                    explanations.append(options)
                    index_arr.append([solution_index])
                # If there are multiple types for one position
                else:
                    # Initial Indexing
                    non_taken_positions = [0, 1, 2, 3]
                    # Set of options
                    options = ["","","",""]
                    # Set of answer positions
                    answers = []
                    # Check all the muss rules
                    for j in range(len(comma_types[i])):
                        if Rule.objects.get(code=comma_types[i][j]).mode == 2:
                            solution_index = random.choice(non_taken_positions)
                            # Save the description of a comma
                            options[solution_index] = Rule.objects.get(code=comma_types[i][j]).description
                            # Save the index of a correct solution
                            answers.append(solution_index)
                            # "Mark" the index as "taken"
                            non_taken_positions.remove(solution_index)
                    # If there are only kann rules, take those
                    if options == ["","","",""]:
                        for j in range(len(comma_types[i])):
                            if Rule.objects.get(code=comma_types[i][j]).mode == 1:
                                solution_index = random.choice(non_taken_positions)
                                # Save the description of a comma
                                options[solution_index] = Rule.objects.get(code=comma_types[i][j]).description
                                # Save the index of a correct solution
                                answers.append(solution_index)
                                # "Mark" the index as "taken"
                                non_taken_positions.remove(solution_index)
                    # If there are only must-not commas
                    if options == ["","","",""]:
                        print("Only must-nots")
                        continue
                    # Save an array of answers in index array
                    index_arr.append(sorted(answers))
                    # Get neighboring explanations to the first comma (can be optimized)
                    rest_options, ignore_index = sentence.get_explanations(comma_types[i][0], user)
                    k = 0
                    # Array of indexes of rest_options
                    positions_in_rest_options = [0, 1, 2, 3]
                    # ... without the index of a correct solution
                    positions_in_rest_options.remove(ignore_index)
                    # Do until all positions are taken
                    while len(non_taken_positions) != 0:
                        random_sol_index = random.choice(non_taken_positions)
                        random_rest_option = random.choice(positions_in_rest_options)
                        options[random_sol_index] = rest_options[random_rest_option]
                        non_taken_positions.remove(random_sol_index)
                        positions_in_rest_options.remove(random_rest_option)
                    explanations.append(options)
        if index == 1:
            return render(request, 'trainer/AllKommaErklärenI.html', locals())
        else:
            return render(request, 'trainer/AllKommaSetzenUndErklären.html', locals())

    # for KannKommaSetzen.html + KannKommaLöschen.html
    elif index >= 3 and index < 5:
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
        if index == 3:
            return render(request, 'trainer/KannKommaSetzen.html', locals())
        else:
            return render(request, 'trainer/KannKommaLöschen.html', locals())

def profile(request):
    """
        Receives request for a profile page

        :param request: Django request
        :return: response
    """
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
    user = User.objects.get(user_id="testuser00")
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


def delete_user(request):
    """Remove a user."""

    # get user from URL or session or default
    user_id = request.GET.get('user_id', request.session.get('user_id', "testuser00"))

    u = User.get(user_id=user_id)
    u.delete()
    u.save()
    return "Deleted"