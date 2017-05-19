# from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Sentence, Solution, Rule, User, UserRule
import re  # regex support
import os


import base64
from django.http import HttpResponse
# from django.contrib.auth import authenticate, login

#############################################################################
#
def view_or_basicauth(view, request, test_func, realm="", *args, **kwargs):
    """
    This is a helper function used by both 'logged_in_or_basicauth' and
    'has_perm_or_basicauth' that does the nitty of determining if they
    are already logged in or if they have provided proper http-authorization
    and returning the view if all goes well, otherwise responding with a 401.
    """
    #if test_func(request.username):
        # Already logged in, just return the view.
        #
    #    return view(request, *args, **kwargs)

    # They are not logged in. See if they provided login credentials
    #
    if 'HTTP_AUTHORIZATION' in request.META:
        auth = request.META['HTTP_AUTHORIZATION'].split()
        if len(auth) == 2:
            # NOTE: We are only support basic authentication for now.
            #
            if auth[0].lower() == "basic":
                print(auth[1])
                auth_bytes=bytes(auth[1], 'utf8')
                uname, passwd = base64.b64decode(auth_bytes).split(b':')
                if uname == passwd:
                    request.username=uname
                    return view(request, *args, **kwargs)

    # Either they did not provide an authorization header or
    # something in the authorization attempt failed. Send a 401
    # back to them to ask them to authenticate.
    #
    response = HttpResponse()
    response.status_code = 401
    response['WWW-Authenticate'] = 'Basic realm="%s"' % realm
    return response


#############################################################################
#
def logged_in_or_basicauth(realm=""):
    """
    A simple decorator that requires a user to be logged in. If they are not
    logged in the request is examined for a 'authorization' header.

    If the header is present it is tested for basic authentication and
    the user is logged in with the provided credentials.

    If the header is not present a http 401 is sent back to the
    requestor to provide credentials.

    The purpose of this is that in several django projects I have needed
    several specific views that need to support basic authentication, yet the
    web site as a whole used django's provided authentication.

    The uses for this are for urls that are access programmatically such as
    by rss feed readers, yet the view requires a user to be logged in. Many rss
    readers support supplying the authentication credentials via http basic
    auth (and they do NOT support a redirect to a form where they post a
    username/password.)

    Use is simple:

    @logged_in_or_basicauth
    def your_view:
        ...

    You can provide the name of the realm to ask for authentication within.
    """

    def view_decorator(func):
        def wrapper(request, *args, **kwargs):
            return view_or_basicauth(func, request,
                                     lambda u: u.is_authenticated(),
                                     realm, *args, **kwargs)

        return wrapper

    return view_decorator


#############################################################################
#
def has_perm_or_basicauth(perm, realm=""):
    """
    This is similar to the above decorator 'logged_in_or_basicauth'
    except that it requires the logged in user to have a specific
    permission.

    Use:

    @logged_in_or_basicauth('asforums.view_forumcollection')
    def your_view:
        ...

    """

    def view_decorator(func):
        def wrapper(request, *args, **kwargs):
            return view_or_basicauth(func, request,
                                     lambda u: u.has_perm(perm),
                                     realm, *args, **kwargs)

        return wrapper

    return view_decorator

@logged_in_or_basicauth("Bitte einloggen")
def task(request):
    """
    Pick a task and show it.

    :param request: Django request
    :return: nothing
    """
    import random

    # get user from URL or session or default
    # user_id = request.GET.get('user_id', request.session.get('user_id', "testuser00"))
    uname = request.username
    new_rule = None  # new level reached? (new rule to explain)
    display_rank=True  # show the rank in output? (not on welcome and rule explanation screens)

    try:
        user = User.objects.get(user_id=uname)
    except User.DoesNotExist:  # new user: welcome!
        user = User(user_id=uname)
        user.rules_activated_count=0
        user.save()
        display_rank=False
        return render(request, 'trainer/welcome.html', locals())

    if user.rules_activated_count == 0: # new user without activated rules
        new_rule = user.init_rules()
        display_rank=False
        level = 0
        return render(request, 'trainer/level_progress.html', locals())

    # normal task selection process
    new_rule = user.progress()
    level = user.rules_activated_count
    rank = user.get_user_rank_display()
    leveldsp = user.level_display()
    rankimg = "{}_{}.png".format(["Chaot", "Könner", "König"][int((level-1)/10)], int((level-1)%10)+1)

    if new_rule:  # level progress: show new rules instead of task
        return render(request, 'trainer/level_progress.html', locals())

    # task randomizer
    if user.rules_activated_count >= 3:  # more than 3 rules: set, correct or explain task
        index = random.randint(0, 1)
    else:  # less than 3 active rules: only set and correct tasks
        index = 0
    # for AllKommaSetzen.html + AllKommaErklärenI.html
    if index < 3:
        # choose a sentence from roulette wheel (the bigger the error for
        # a certain rule, the more likely one will get a sentence with that rule)
        #TODO: fetch errors
        sentence = user.roulette_wheel_selection()
        words = sentence.get_words()  # pack all words of this sentence in a list
        comma = sentence.get_commalist() # pack all commas [0,1,2] in a list
        comma_types = sentence.get_commatypelist()  # pack all comma types [['A2.1'],...] of this sentence in a list
        comma_to_check=[]
        for ct in comma_types:
            if ct != [] and ct[0][0] != 'E': # rule, but no error rule
                # at a rule position include comma with 50% probabily
                comma_to_check.append(random.randint(0,1))
            else:  # 10% prob. to set comma in no-comma position
                comma_to_check.append(random.choice([1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]))

        comma_select = sentence.get_commaselectlist() # pack all selects in a list
        comma_select.append('0') # dirty trick to make the comma_select and comma_types the same length as words
        comma_types.append([])
        comma_to_check.append(0)
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
            # return render(request, 'trainer/task_set_commas.html', locals())
            # return render(request, 'trainer/task_correct_commas.html', locals())

            if random.randint(0,1)==0:
                return render(request, 'trainer/task_correct_commas.html', locals())
            else:
                return render(request, 'trainer/task_set_commas.html', locals())

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
            return render(request, 'trainer/task_explain_commas.html', locals())
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

@logged_in_or_basicauth("Bitte einloggen")
def submit_task1(request):
    """
    Receives an AJAX GET request containing a solution bitfield for a sentence.
    Saves solution and user_id to database.

    :param request: Django request
    :return: nothing
    """
    uname = request.username
    sentence = Sentence.objects.get(id=request.GET['id'])
    user_solution = request.GET['sol']
    sentence.set_comma_select(user_solution)
    sentence.update_submits()
    user = User.objects.get(user_id=uname)
    user.count_false_types_task1(user_solution, sentence.get_commatypelist())
    user.update_rank()
    Solution(user=user, sentence=sentence, type="set", solution="".join(user_solution)).save() # save solution to db
    return JsonResponse({'submit': 'ok'})

@logged_in_or_basicauth("Bitte einloggen")
def submit_task_correct_commas(request):
    """
    Receives an AJAX GET request containing a solution bitfield for a sentence.
    Saves solution and user_id to database.

    :param request: Django request
    :return: nothing
    """
    uname = request.username
    sentence = Sentence.objects.get(id=request.GET['id'])
    user_solution = request.GET['sol']
    commas = request.GET['commas']
    #sentence.set_comma_select(user_solution)
    #sentence.update_submits()
    user = User.objects.get(user_id=uname)
    user.count_false_types_task_correct_commas(user_solution, commas, sentence.get_commatypelist())

    Solution(user=user, sentence=sentence, type="correct", solution="".join([str(x) for x in user_solution])).save() # save solution to db

    #user.update_rank()
    return JsonResponse({'submit': 'ok'})

@logged_in_or_basicauth("Bitte einloggen")
def submit_task_explain_commas(request):
    """
    Receives an AJAX GET request containing a solution bitfield for a sentence.
    Saves solution and user_id to database.

    :param request: Django request
    :return: nothing
    """
    uname = request.username
    sentence = Sentence.objects.get(id=request.GET['id'])
    sentence.update_submits()
    user = User.objects.get(user_id=uname)
    user.update_rank()

    chckbx_sol = request.GET['chckbx_sol']
    user_array = re.split(r'[ ,]+', chckbx_sol)  # TODO fix for explain task

    # write solution to db
    Solution(user=user, sentence=sentence, type='explain', solution="".join(user_array), ).save()

    user.count_false_types_task_explain_commas(user_array, sentence.get_commatypelist())
    return JsonResponse({'submit': 'ok'})

@logged_in_or_basicauth("Bitte einloggen")
def submit_task3(request):
    """
    Receives an AJAX GET request containing a solution bitfield for a sentence.
    Saves solution and user_id to database.

    :param request: Django request
    :return: nothing
    """
    uname = request.username
    sentence = Sentence.objects.get(id=request.GET['id'])
    user_solution = request.GET['sol']
    sentence.set_comma_select(user_solution)
    sentence.update_submits()
    user = User.objects.get(user_id=uname)
    user.count_false_types_task3(user_solution, sentence.get_commatypelist())
    user.update_rank()
    return JsonResponse({'submit': 'ok'})

@logged_in_or_basicauth("Bitte einloggen")
def submit_task4(request):
    """
    Receives an AJAX GET request containing a solution bitfield for a sentence.
    Saves solution and user_id to database.

    :param request: Django request
    :return: nothing
    """
    uname = request.username
    sentence = Sentence.objects.get(id=request.GET['id'])
    user_solution = request.GET['sol']
    sentence.set_comma_select(user_solution)
    sentence.update_submits()
    user = User.objects.get(user_id=uname)
    user.count_false_types_task4(user_solution, sentence.get_commatypelist())
    user.update_rank()
    return JsonResponse({'submit': 'ok'})


@logged_in_or_basicauth("Bitte einloggen")
def delete_user(request):
    """Remove a user."""

    # get user from URL or session or default
    u = User.objects.get(user_id=request.username)
    u.delete()
    return redirect("/")

@logged_in_or_basicauth("Bitte einloggen")
def logout(request):
    return render(request, 'trainer/reset.html', locals())
