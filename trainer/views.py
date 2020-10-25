from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Count, Sum, F
from django.urls import reverse
from .models import Sentence, Solution, Rule, SolutionRule, SentenceRule, User, UserSentence, UserRule, UserPretest, GroupScore
import random

import base64
from django.http import HttpResponse, HttpResponseBadRequest
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

    def check_or_create_user(username):
        try:
            user = User.objects.get(user_id=username)
        except User.DoesNotExist:  # new user: welcome!
            user = User(user_id=username)
            user.rules_activated_count = 0
            user.strategy = user.LEITNER  #  random.choice([user.BAYES, user.BAYES, user.LEITNER])
            user.gamification = random.choice([user.GAMIFICATION_CLASSIC, user.GAMIFICATION_INDIVIDUAL, user.GAMIFICATION_GROUP])
            user.prepare(request)  # create a corresponding django user and set up auth system
            user.save()
        user.login(request)
        return user

    if 'uname' in request.GET:
        # uname given from stud.ip (or elsewhere)
        #
        uname = request.GET.get('uname')
        if uname and len(uname)>8:
            check_or_create_user(uname)
            return view(request, *args, **kwargs)

    if test_func(request.user):
        # Already logged in, just return the view.
        #
        return view(request, *args, **kwargs)

    # They are not logged in. See if they provided login credentials
    #
    if 'HTTP_AUTHORIZATION' in request.META:
        auth = request.META['HTTP_AUTHORIZATION'].split()
        if len(auth) == 2:
            # NOTE: We are only support basic authentication for now.
            #
            if auth[0].lower() == "basic":
                # print(auth[1])
                auth_bytes = bytes(auth[1], 'utf8')
                uname, passwd = base64.b64decode(auth_bytes).split(b':')
                if len(uname) > 8 and uname == passwd:
                    check_or_create_user(uname.decode('utf-8'))
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
                                     lambda u: u.is_authenticated,
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

    def render_task_explain_commas(request, sent, select_rules=None, template_params={}):
        # pick one comma slot from the sentence
        # there must at least be one non-error and non-'must not' rule (ensured above)
        comma_candidates = []
        # comma candidates is a list of tuples: (position, rule list for this position)
        for pos in range(len(sent.get_words()) - 1):
            # for each position: get rules
            rules = sent.rules.filter(sentencerule__position=pos + 1).all()
            pos_rules = []  # rules at this position
            for r in rules:
                if select_rules and select_rules[0] == r:  # if we know which rule to select
                    if r not in pos_rules:
                        pos_rules.append(r)
                elif not select_rules and r.mode > 0:  # otherwise append all rules that are "may" or "must" commas
                    if r not in pos_rules:
                        pos_rules.append(r)
            if pos_rules:
                comma_candidates.append((pos, pos_rules))
        # data for template:
        # guessing_candidates: the three rules to display
        # guessing_position: the comma slot position to explain
        # print("comma_candidates:",comma_candidates)
        explanation_position = random.choice(comma_candidates)
        guessing_position = explanation_position[0]
        guessing_candidates = []  # the rules to be displayed for guessing
        correct_rules_js = "[" + ",".join(
            ['"{}"'.format(r.code) for r in explanation_position[1]]) + "]"  # javascript list of correct rules
        if len(explanation_position[1]) > 3:
            guessing_candidates = explanation_position[1][:3]
        else:
            guessing_candidates = explanation_position[1]
        # add other active rules until we have three rules as guessing candidates
        # if there aren't enough active rules (e.g. in pretest!),
        # we consider all rules
        active_rules = strategy.get_active_rules()
        rule_candidates = []
        if select_rules:  # we already know whoch rules to take
            rule_candidates = [select_rules[1], select_rules[2]]
        elif len(active_rules) < 3:  # less than 3 active rules -> not enough
            rule_candidates = list(Rule.objects.exclude(code__startswith='E').all())
        else:  # at least 3 active rules
            rule_candidates = [x.rule for x in active_rules]
        random.shuffle(rule_candidates)
        for ar in rule_candidates:
            if len(guessing_candidates) == 3:
                break
            if ar not in guessing_candidates:
                guessing_candidates.append(ar)
        random.shuffle(guessing_candidates)
        sentence=sent
        # prepare some special views for templates
        words = sentence.get_words()  # pack all words of this sentence in a list
        comma = sentence.get_commalist()  # pack all commas [0,1,2] in a list
        words_and_commas = list(zip(words, comma + [0]))  # make a combines list of both
        return render(request, 'trainer/task_explain_commas.html', {**template_params, **locals()})


    # get user from URL or session or default
    # get user from URL or session or default
    # user_id = request.GET.get('user_id', request.session.get('user_id', "testuser00"))
    user = User.objects.get(django_user=request.user)
    new_rule = None  # new level reached? (new rule to explain)
    display_rank = True  # show the rank in output? (not on welcome and rule explanation screens)
    rankimg = ""
    finished = False # default is: we're not yet finished
    in_pretest = False
    # select strategy
    strategy = user.get_strategy()
    strategy_debug = strategy.debug_output()

    # -----------------------------------------------------------------------
    # new user: show welcome page
    if not user.data:
        display_rank=False
        return render(request, 'trainer/welcome_gamification.html', locals())  # questionnaire BA Herrmann

        # return render(request, 'trainer/welcome.html', locals())  # questionnaire MA Hubert

        #user.data="No questionnaire in this run."
        #user.save()
        #strategy.init_rules() # set all knowledge about user to start
        #return render(request, 'trainer/welcome_noquestionnaire.html', locals())

    # -----------------------------------------------------------------------
    # pretest
    if not user.pretest:
        # pretest deactivated! (was used for bayesian strategy)
        if False and not request.GET.get('skip_pretest',False) and user.pretest_count < len(strategy.pretest_rules):
            rule = Rule.objects.get(code=strategy.pretest_rules[user.pretest_count][0])
            # print("Sentences for {}".format(strategy.pretest_rules[user.pretest_count]))
            # sentences = rule.find_sentences()
            sentences = Sentence.objects.filter(rules=rule, active=True) # all sentences with this rule
            if not sentences:
                error_msg="No sentence for pretest, rule {}".format(rule.code)
                return render(request, 'trainer/error.html', locals())
            # pick sentence for current pretest rule
            s = random.choice(sentences)
            in_pretest = True
            pretest_counter = user.pretest_count+1
            pretest_max = len(strategy.pretest_rules)
            display_rank=False
            rule2 = Rule.objects.get(code=strategy.pretest_rules[user.pretest_count][1])
            rule3 = Rule.objects.get(code=strategy.pretest_rules[user.pretest_count][2])
            return render_task_explain_commas(request, random.choice(sentences),
                                              select_rules=(rule,rule2,rule3), template_params=locals())
        else: # pretest finished
            strategy.init_rules()
            new_rule = strategy.process_pretest() # evaluate pretest and activate known rules, set level etc.
            user.pretest=True
            user.save()
            display_rank = 0
            return render(request, 'trainer/level_progress.html', locals())

    # -----------------------------------------------------------------------
    # pretest passed
    # user without activated rules: show first rule page
    if user.rules_activated_count == 0:
        new_rule = strategy.activate_first_rule()
        display_rank=False
        level = 0
        return render(request, 'trainer/level_progress.html', locals())

    # fetch and prepare information about level for template
    level = user.rules_activated_count  # user's current level
    activerules = strategy.get_active_rules()
    rankimg = "{}_{}.png".format(["Chaot", "Könner", "König"][int((level-1)/10)], int((level-1)%10)+1)  # construct image name
    show_ranking = False

    # ------------------------------------------------------------------------
    # adaptivity form
    # show and process form (processing will set data_adaptivity)
    # if user.rules_activated_count>18 and not user.data_adaptivity:
    #    return render(request, 'trainer/adaptivity_questionaire.html')

    # ------------------------------------------------------------------------
    # gamification questionnaire form
    if user.rules_activated_count >= 5 and not user.data_gamification_1:
        iteration=1
        return render(request, 'trainer/gamification_questionaire.html', locals())
    if user.rules_activated_count >= 15 and not user.data_gamification_2:
        iteration=2
        return render(request, 'trainer/gamification_questionaire.html', locals())
    if user.rules_activated_count >= 30 and not user.data_gamification_3:
        iteration=3
        return render(request, 'trainer/gamification_questionaire.html', locals())

    # ------------------------------------------------------------------------
    # normal task selection process
    (new_rule, finished, forgotten) = strategy.progress()  # checks if additional rule should be activated or user has finished all levels

    # level progress: show new rules instead of task
    if new_rule:
        return render(request, 'trainer/level_progress.html', locals())

    show_ranking=True

    # prepare highscore list
    if user.gamification == User.GAMIFICATION_INDIVIDUAL:
        user.update_score()
        raw_scores = User.objects.filter(gamification=User.GAMIFICATION_INDIVIDUAL).order_by('-gamification_score')

        # find user rank (same scores count as same rank)
        user_rank = 0
        last_score = -1
        counter = 1
        rank = 1
        for rsi in range(len(raw_scores)):
            if rsi > 0 and raw_scores[rsi].gamification_score != last_score:
                rank = counter
            if user == raw_scores[rsi]:
                user_rank = rank
                break
            last_score = raw_scores[rsi].gamification_score
            counter = counter + 1
        # print("Rank is: {} out of {}".format(user_rank, raw_scores))
        # build scores list
        scores=[]
        last_score = -1
        counter = 1
        rank = 1
        for rsi in range(len(raw_scores)):
            if raw_scores[rsi].gamification_score != last_score:  # only new rank if score differs (but then rank is number of people, not ranks)
                rank = counter
            if rsi < 3:  # always include first three ranks
                scores.append((rank, raw_scores[rsi]))
            elif abs(rank-user_rank) < 3:  # show people around me
                scores.append((rank, raw_scores[rsi]))
            elif rsi > 0:
                if scores[-1] != (-1,None):
                    scores.append((-1,None))
            last_score = raw_scores[rsi].gamification_score
            counter = counter + 1
        print(scores)
    elif user.gamification == User.GAMIFICATION_GROUP:
        user.update_score()
        raw_scores = GroupScore.objects.order_by('-score')
        # build scores list
        scores=[]
        last_score = -1
        counter = 1
        rank = 1
        for rsi in range(len(raw_scores)):
            if rsi > 0 and raw_scores[rsi].score != last_score:
                rank = counter
            scores.append((rank,raw_scores[rsi]))
            last_score = raw_scores[rsi].score
            counter = counter + 1


    # choose a sentence from roulette wheel (the bigger the error for
    # a certain rule, the more likely one will get a sentence with that rule)
    sentence_rule = strategy.roulette_wheel_selection()  # choose sentence and rule
    sentence = sentence_rule.sentence
    rule = sentence_rule.rule

    # prepare some special views for templates
    words = sentence.get_words()  # pack all words of this sentence in a list
    comma = sentence.get_commalist() # pack all commas [0,1,2] in a list
    words_and_commas = list(zip(words,comma+[0]))  # make a combines list of both

    # task randomizer
    # explain task only for must or may commas, usres with at least 3 active rules and non-error rules
    if rule.mode > 0 and user.rules_activated_count >= 3 and not rule.code.startswith('E'):
        index = random.randint(0, 100)
    else:  # less than 3 active rules: only set and correct tasks
        index = 0

    if index < 67:  # 1/3 chance for rule explanation
        if random.randint(0,100) > 50: # 50% chance for correct commas
            comma_types = sentence.get_commatypelist()  # pack all comma types [['A2.1'],...] of this sentence in a list
            # comma_types.append([])  # bugfix: no comma after last position
            comma_to_check = []
            for ct in comma_types:
                if ct != [] and ct[0][0] != 'E':  # rule, but no error rule
                    # at a rule position include comma with 50% probabily
                    comma_to_check.append(random.randint(0, 1))
                else:  # 1/6 prob. to set comma in no-comma position
                    comma_to_check.append(random.choice([1, 0, 0, 0, 0, 0]))
            comma_to_check.append(0)
            return render(request, 'trainer/task_correct_commas.html', locals())
        else:
            return render(request, 'trainer/task_set_commas.html', locals())
    else:
        # EXPLANATION task
        return render_task_explain_commas(request, sentence, template_params=locals())


@logged_in_or_basicauth("Bitte einloggen")
def start(request):
    """Store questionnaire results and redirect to task."""
    user = User.objects.get(django_user=request.user)
    vector = "{}:{}-{}:{}+{}+{}:{}:{}:{}".format(
        request.GET.get('hzb',0),
        request.GET.get('abschluss',0),
        request.GET.get('semester',0),
        request.GET.get('fach1','00'),
        request.GET.get('fach2','00'),
        request.GET.get('fach3', '00'),
        request.GET.get('sex',0),
        request.GET.get('selfest','-'),
        request.GET.get('L1','-'))
    user.data = vector # one string with al data, now obsolete TODO: remove
    user.data_study = request.GET.get('abschluss',0)
    user.data_semester = request.GET.get('semester',0)
    user.data_subject1 = request.GET.get('fach1',0)
    user.data_subject2 = request.GET.get('fach2',0)
    user.data_subject3 = request.GET.get('fach3', 0)
    user.data_study_permission = request.GET.get('hzb',0)
    user.data_sex = request.GET.get('sex',"")
    user.data_l1 = request.GET.get('L1','')
    user.data_selfestimation = request.GET.get('selfest',-1)
    user.gamification_group = request.GET.get('group', None)
    nickname = request.GET.get('nickname', None)
    if nickname: # chekc if nickname is taken, then add numbers until it's unique
        ok = False
        appendix = ''
        while not ok:
            try:
                otheruser = User.objects.get(gamification_nickname=nickname+appendix)
                if appendix == '':
                    appendix='1'
                else:
                    appendix = "{}".format(int(appendix)+1)
            except User.DoesNotExist:
                nickname = nickname+appendix
                ok = True
    user.gamification_nickname = nickname
    user.save()
    if user.gamification_group:
        group, created = GroupScore.objects.get_or_create(group=user.gamification_group)

    return redirect("task")


@logged_in_or_basicauth("Bitte einloggen")
def submit_adaptivity_questionnaire(request):
    """Receive adaptivity questionnaire answers and save to data_study field"""
    user = User.objects.get(django_user=request.user)
    user.data_adaptivity = "{}:{}:{}:{}:{}:{}:{}".format(
        request.GET.get('q1',0),
        request.GET.get('q2',0),
        request.GET.get('q3',0),
        request.GET.get('q4',0),
        request.GET.get('q5',0),
        request.GET.get('q6',0),
        request.GET.get('q7',0))
    user.save()

    return redirect("task")  # go on with tasks

@logged_in_or_basicauth("Bitte einloggen")
def submit_gamification_questionnaire(request):
    """Receive gamification questionnaire answers and save to data_gamification_{1,2,3} field"""
    user = User.objects.get(django_user=request.user)
    data = "{}:{}:{}:{}:{}".format(
        request.GET.get('q1',0),
        request.GET.get('q2',0),
        request.GET.get('q3',0),
        request.GET.get('q4',0),
        request.GET.get('q5',0),
    )
    if request.GET.get('iteration', None) == '1':
        user.data_gamification_1 = data
    elif request.GET.get('iteration', None) == '2':
        user.data_gamification_2 = data
    elif request.GET.get('iteration', None) == '3':
        user.data_gamification_3 = data
    user.save()

    return redirect("task")  # go on with tasks

def index(request):
    """Display index page."""
    return render(request, 'trainer/index.html', locals())


@logged_in_or_basicauth("Bitte einloggen")
def submit_task_set_commas(request):
    """
    Receives an AJAX GET request containing a solution bitfield for a 'set' task.
    Saves solution and user_id to database.

    :param request: Django request
    :return: nothing
    """

    # extract request parameters
    sentence = Sentence.objects.get(id=request.GET['id'])
    user_solution = request.GET['sol']
    time_elapsed = request.GET.get('tim',0)

    # save solution
    user = User.objects.get(django_user=request.user)  # current user
    solution = Solution(user=user, sentence=sentence, type="set", time_elapsed=time_elapsed, solution="".join(user_solution))
    solution.save() # save solution to db

    # calculate response
    response = user.eval_set_commas(user_solution, sentence, solution)  # list of dictionaries with keys 'correct' and 'rule'

    # update internal states for strategy according to answer
    for single_solution in response:
        if single_solution['rule']['code']:
            # print("checking " + single_solution['rule']['code'])
            user.get_strategy().update(Rule.objects.get(code=single_solution['rule']['code']), 1, single_solution['correct'])
    # update per user counter for sentence (to avoid repetition of same sentences)
    try:
        us = UserSentence.objects.get(user=user, sentence=sentence)
        us.count += 1
        us.save()
    except UserSentence.DoesNotExist:  # user did not yet encouter this sentence
        UserSentence(user=user, sentence=sentence, count=1).save()
    except UserSentence.MultipleObjectsReturned:  # somehow multiple entries existed... (should not happen)
        UserSentence.objects.filter(user=user, sentence=sentence).delete()
        UserSentence(user=user, sentence=sentence, count=1).save()

    return JsonResponse({'submit': 'ok', 'response': response}, safe=False)


@logged_in_or_basicauth("Bitte einloggen")
def submit_task_correct_commas(request):
    """
    Receives an AJAX GET request containing a solution bitfield for a sentence.
    Saves solution and user_id to database.

    :param request: Django request
    :return: nothing
    """

    # extract request parameters
    sentence = Sentence.objects.get(id=request.GET['id'])
    user_solution = request.GET['sol']
    time_elapsed = request.GET.get('tim',0)

    # save solution
    user = User.objects.get(django_user=request.user)
    solution = Solution(user=user, sentence=sentence, type="correct", time_elapsed=time_elapsed, solution="".join([str(x) for x in user_solution]))
    solution.save() # save solution to db

    # calculate response
    response = user.count_false_types_task_correct_commas(user_solution, sentence, solution)
    # print(response)

    # update internal states for strategy according to answer (2=COMMA_CORRECT)
    for single_solution in response:
        if single_solution['rule']['code']:
            # print("checking "+single_solution['rule']['code'])
            user.get_strategy().update(Rule.objects.get(code=single_solution['rule']['code']), 2, single_solution['correct'])

    # update per user counter for sentence (to avoid repetition of same sentences)
    try:
        us = UserSentence.objects.get(user=user, sentence=sentence)
        us.count += 1
        us.save()
    except UserSentence.DoesNotExist:
        UserSentence(user=user, sentence=sentence, count=1).save()
    except UserSentence.MultipleObjectsReturned:  # somehow multiple entries existed..
        UserSentence.objects.filter(user=user, sentence=sentence).delete()
        UserSentence(user=user, sentence=sentence, count=1).save()

    return JsonResponse({'submit': 'ok', 'response':response}, safe=False)


@logged_in_or_basicauth("Bitte einloggen")
def submit_task_explain_commas(request):
    """
    Receives an AJAX GET request containing a solution bitfield for a sentence.
    Saves solution and user_id to database.

    :param request: Django request
    :return: nothing
    """

    # extract request parameters
    sentence = Sentence.objects.get(id=request.POST['sentence_id'])
    rules=[]
    try:
        rules.append(Rule.objects.get(code=request.POST.getlist('rule-0')[0]))
        rules.append(Rule.objects.get(code=request.POST.getlist('rule-1')[0]))
        rules.append(Rule.objects.get(code=request.POST.getlist('rule-2')[0]))
    except Rule.DoesNotExist:
        return JsonResponse({'error': 'invalid rule', 'submit':'fail'})

    user = User.objects.get(django_user=request.user)

    solution = [] # solution is array of the form: rule_id:correct?:chosen?, rule_id:...
    resp = []  # array for score update
    error_rules = [] # all rules with errors
    pos = int(request.POST['position'])+1
    for r in rules:
        correct = 1 if SentenceRule.objects.filter(sentence=sentence, rule=r, position=pos) else 0  # correct if sentence has rule
        chosen = 1 if r.code in request.POST else 0  # chosen if box was checked
        solution.append("{}:{}:{}".format(r.id, correct, chosen))
        resp.append({'correct': (correct==chosen)})
        # are we in pretest?
        if not user.pretest:
            if user.get_strategy().pretest_rules[user.pretest_count][0] == r.code:  # do we look at the rule to test?
                # save pretest result
                up = UserPretest(user=user, rule=r, result=(correct==chosen))
                up.save()
                user.pretest_count += 1  # increase pretest counter
                user.save()
                return JsonResponse({'submit': 'ok'})
        else:  # not on pretest
            # update strategy model (3=COMMA_EXPLAIN)
            user.get_strategy().update(r, 3, (correct == chosen))
            if not r.code.startswith('E'):  # only count non-error rules
                ur = UserRule.objects.get(user=user, rule=r)
                ur.count((correct == chosen))  # count rule application as correct if correct rule was chosen and vice versa
                if correct != chosen:
                    error_rules.append(r)

    # recalculate individual or group score
    user.update_score(resp)

    # write solution to db
    time_elapsed = request.POST.get('tim', 0)
    sol = Solution(user=user, sentence=sentence, type='explain', time_elapsed=time_elapsed,
                   solution="{}|".format(pos)+",".join(solution))
    sol.save()
    for er in error_rules:
        SolutionRule(solution=sol, rule = er, error=True).save()

    # update per user counter for sentence (to avoid repetition of same sentences)
    try:  # count sentence as seen
        us = UserSentence.objects.get(user=user, sentence=sentence)
        us.count += 1
        us.save()
    except UserSentence.DoesNotExist:
        UserSentence(user=user, sentence=sentence, count=1).save()
    except UserSentence.MultipleObjectsReturned:  # somehow multiple entries existed..
        UserSentence.objects.filter(user=user, sentence=sentence).delete()
        UserSentence(user=user, sentence=sentence, count=1).save()

    return JsonResponse({'submit': 'ok'})


@logged_in_or_basicauth("Bitte einloggen")
def delete_user(request):
    """Remove a user."""

    # get user from URL or session or default
    u = User.objects.get(django_user=request.user)
    uid = request.user.username
    u.delete()

    request.user.delete()  # also delete the django user
    return redirect(reverse("task")+"?uname="+uid)


@logged_in_or_basicauth("Bitte einloggen")
def logout(request):
    return render(request, 'trainer/reset.html', locals())


def sentence(request, sentence_id):
    """Renders a partial template for a sentence including rule information."""

    # fetch sentence
    s = Sentence.objects.get(id=sentence_id)

    # extract rules to separate list
    wcr = s.get_words_commas_rules()  # Return a list of tuples: (word,commstring,rule) for a sentence.
    rules = []
    for x in wcr:
        for y in x[2]:
            rules.append(y)
    rules = list(set(rules))
    return render(request, 'trainer/partials/correct_sentence.html', locals())


def help(request):
    """Renders help template"""
    return render(request, 'trainer/help.html', locals())


def nocookies(request):
    """Renders information page if cookies could not be set."""
    display_rank = False  # show the rank in output? (not on welcome and rule explanation screens)
    uname = request.GET.get('uname','')
    return render(request, 'trainer/nocookies.html', locals())


def vanillalm(request):
    """Stud.IP Lernmodule plugin vanillalm integration."""
    return render(request, 'trainer/vanillalm.html', locals())


def stats(request):
    """Render general statistics."""

    ud = []
    count_users = User.objects.filter(rules_activated_count__gt=0).count()
    count_studip_users = User.objects.filter(rules_activated_count__gt=0, user_id__iregex=r'[0-9a-f]{32}').count()
    count_solutions = Solution.objects.count()
    count_error = SolutionRule.objects.count()
    count_error_set = SolutionRule.objects.filter(solution__type='set').count()
    count_error_correct = SolutionRule.objects.filter(solution__type='correct').count()
    count_error_explain = SolutionRule.objects.filter(solution__type='explain').count()

    users = User.objects.filter(rules_activated_count__gt=0).all()

    levels = User.objects.values('rules_activated_count')\
        .order_by('rules_activated_count')\
        .annotate(the_count = Count('rules_activated_count'))

    error_rules = SolutionRule.objects.values('rule') \
        .order_by('rule') \
        .annotate(the_count = Count('rule'))

    return render(request, 'trainer/stats.html', locals())

def stats2(request):
    """Render general statistics for leitner/bayes experiment."""

    user_from=810 # value for production system uni osnabrück # HACK
    #user_from=0  # value for test system
    ud = []
    count_users = User.objects.filter(rules_activated_count__gt=0, id__gte=user_from).count()
    count_studip_users = User.objects.filter(rules_activated_count__gt=0, user_id__iregex=r'[0-9a-f]{32}', id__gte=user_from).count()
    users = User.objects.filter(rules_activated_count__gt=0, id__gte=user_from).all()

    count_leitner = User.objects.filter(rules_activated_count__gt=0, strategy=User.LEITNER, id__gte=user_from).count()
    count_bayes = User.objects.filter(rules_activated_count__gt=0, strategy=User.BAYES, id__gte=user_from).count()
    count_leitner_finished = User.objects.filter(rules_activated_count__gt=19, strategy=User.LEITNER, id__gte=user_from).count()
    count_bayes_finished = User.objects.filter(rules_activated_count__gt=19, strategy=User.BAYES, id__gte=user_from).count()

    ql1=[]
    ql2=[]
    ql3=[]
    ql4=[]
    ql5=[]
    ql6=[]
    qb1=[]
    qb2=[]
    qb3=[]
    qb4=[]
    qb5=[]
    qb6=[]

    for u in User.objects.filter(rules_activated_count__gt=19, strategy=User.LEITNER, id__gte=user_from):
        answers = [int(x) for x in u.data_adaptivity.split(":")]
        if len(answers) >= 6:
            if answers[0] < 5: ql1.append(answers[0])
            if answers[1] < 5: ql2.append(answers[1])
            if answers[2] < 5: ql3.append(answers[2])
            if answers[3] < 5: ql4.append(answers[3])
            if answers[4] < 5: ql5.append(answers[4])
            if answers[5] < 5: ql6.append(answers[5])

    for u in User.objects.filter(rules_activated_count__gt=19, strategy=User.BAYES, id__gte=user_from):
        answers = [int(x) for x in u.data_adaptivity.split(":")]
        if len(answers) >= 6:
            if answers[0] < 5: qb1.append(answers[0])
            if answers[1] < 5: qb2.append(answers[1])
            if answers[2] < 5: qb3.append(answers[2])
            if answers[3] < 5: qb4.append(answers[3])
            if answers[4] < 5: qb5.append(answers[4])
            if answers[5] < 5: qb6.append(answers[5])

    ql1 = sum(ql1) / len(ql1)
    ql2 = sum(ql2) / len(ql2)
    ql3 = sum(ql3) / len(ql3)
    ql4 = sum(ql4) / len(ql4)
    ql5 = sum(ql5) / len(ql5)
    ql6 = sum(ql6) / len(ql6)
    qb1 = sum(qb1) / len(qb1)
    qb2 = sum(qb2) / len(qb2)
    qb3 = sum(qb3) / len(qb3)
    qb4 = sum(qb4) / len(qb4)
    qb5 = sum(qb5) / len(qb5)
    qb6 = sum(qb6) / len(qb6)
    return render(request, 'trainer/stats2.html', locals())


def stats3(request):
    """Render general statistics for leitner/bayes experiment."""

    ud = []
    count_users = User.objects.filter(rules_activated_count__gt=0, gamification__gte=1).count()
    count_studip_users = User.objects.filter(rules_activated_count__gt=0, user_id__iregex=r'[0-9a-f]{32}', gamification__gte=1).count()
    users = User.objects.filter(rules_activated_count__gt=0, gamification__gte=1).all()

    count_classic = User.objects.filter(rules_activated_count__gt=0, gamification=User.GAMIFICATION_CLASSIC).count()
    count_classic_finished1 = User.objects.filter(rules_activated_count__gt=0, gamification=User.GAMIFICATION_CLASSIC).exclude(data_gamification_1='').count()
    count_classic_finished2 = User.objects.filter(rules_activated_count__gt=0, gamification=User.GAMIFICATION_CLASSIC).exclude(data_gamification_2='').count()
    count_classic_finished3 = User.objects.filter(rules_activated_count__gt=0, gamification=User.GAMIFICATION_CLASSIC).exclude(data_gamification_3='').count()

    count_individual = User.objects.filter(rules_activated_count__gt=0, gamification=User.GAMIFICATION_INDIVIDUAL).count()
    count_individual_finished1 = User.objects.filter(rules_activated_count__gt=0, gamification=User.GAMIFICATION_INDIVIDUAL).exclude(data_gamification_1='').count()
    count_individual_finished2 = User.objects.filter(rules_activated_count__gt=0, gamification=User.GAMIFICATION_INDIVIDUAL).exclude(data_gamification_2='').count()
    count_individual_finished3 = User.objects.filter(rules_activated_count__gt=0, gamification=User.GAMIFICATION_INDIVIDUAL).exclude(data_gamification_3='').count()

    count_group = User.objects.filter(rules_activated_count__gt=0, gamification=User.GAMIFICATION_GROUP).count()
    count_group_finished1 = User.objects.filter(rules_activated_count__gt=0, gamification=User.GAMIFICATION_GROUP).exclude(data_gamification_1='').count()
    count_group_finished2 = User.objects.filter(rules_activated_count__gt=0, gamification=User.GAMIFICATION_GROUP).exclude(data_gamification_2='').count()
    count_group_finished3 = User.objects.filter(rules_activated_count__gt=0, gamification=User.GAMIFICATION_GROUP).exclude(data_gamification_3='').count()

    # individuals
    individuals = User.objects.filter(rules_activated_count__gt=0, gamification=User.GAMIFICATION_INDIVIDUAL).order_by('-gamification_score')
    i_level = 0
    i_tries = 0
    i_errors = 0
    i_num = 0
    for i in individuals:
        i_num += 1
        i_level += i.rules_activated_count
        i_tries += i.tries()
        i_errors += i.errors()
        i.q = [['', '', '', ''], ['', '', '', ''], ['', '', '', '']]
        if i.data_gamification_1:
            answers = [int(x) for x in i.data_gamification_1.split(":")]
            for j in range(4):
                if answers[j] < 5: i.q[0][j] = answers[j]
        if i.data_gamification_2:
            answers = [int(x) for x in i.data_gamification_3.split(":")]
            for j in range(4):
                if answers[j] < 5: i.q[1][j] = answers[j]
        if i.data_gamification_3:
            answers = [int(x) for x in i.data_gamification_3.split(":")]
            for j in range(4):
                if answers[j] < 5: i.q[2][j] = answers[j]
    if i_num > 0:
        i_level = i_level / i_num
        i_tries = i_tries / i_num
        i_errors = i_errors / i_num

    # groups
    groups = User.objects.filter(rules_activated_count__gt=0, gamification=User.GAMIFICATION_GROUP).order_by('gamification_group')
    g_level = 0
    g_tries = 0
    g_errors = 0
    g_num = 0
    for i in groups:
        g_num += 1
        g_level += i.rules_activated_count
        g_tries += i.tries()
        g_errors += i.errors()
        i.q = [['', '', '', '', ''], ['', '', '', '', ''], ['', '', '', '', '']]
        if i.data_gamification_1:
            answers = [int(x) for x in i.data_gamification_1.split(":")]
            for j in range(5):
                if answers[j] < 5: i.q[0][j] = answers[j]
        if i.data_gamification_2:
            answers = [int(x) for x in i.data_gamification_3.split(":")]
            for j in range(5):
                if answers[j] < 5: i.q[1][j] = answers[j]
        if i.data_gamification_3:
            answers = [int(x) for x in i.data_gamification_3.split(":")]
            for j in range(5):
                if answers[j] < 5: i.q[2][j] = answers[j]
        i.groupscore=GroupScore.objects.get(group=i.gamification_group).score
    if g_num > 0:
        g_level = g_level / g_num
        g_tries = g_tries / g_num
        g_errors = g_errors / g_num

    # classics
    classics = User.objects.filter(rules_activated_count__gt=0, gamification=User.GAMIFICATION_CLASSIC)
    c_level = 0
    c_tries = 0
    c_errors = 0
    c_num = 0
    for i in classics:
        c_num += 1
        c_level += i.rules_activated_count
        c_tries += i.tries()
        c_errors += i.errors()
        i.q = [['', ''], ['', ''], ['', '']]
        if i.data_gamification_1:
            answers = [int(x) for x in i.data_gamification_1.split(":")]
            for j in range(2):
                if answers[j] < 5: i.q[0][j] = answers[j]
        if i.data_gamification_2:
            answers = [int(x) for x in i.data_gamification_3.split(":")]
            for j in range(2):
                if answers[j] < 5: i.q[1][j] = answers[j]
        if i.data_gamification_3:
            answers = [int(x) for x in i.data_gamification_3.split(":")]
            for j in range(2):
                if answers[j] < 5: i.q[2][j] = answers[j]
    if c_num > 0:
        c_level = c_level / c_num
        c_tries = c_tries / c_num
        c_errors = c_errors / c_num


    #for u in User.objects.filter(rules_activated_count__gt=19, strategy=User.LEITNER, id__gte=user_from):
    #    answers = [int(x) for x in u.data_adaptivity.split(":")]
    #    if len(answers) >= 6:
    #        if answers[0] < 5: ql1.append(answers[0])
    #        if answers[1] < 5: ql2.append(answers[1])
    #        if answers[2] < 5: ql3.append(answers[2])
    #        if answers[3] < 5: ql4.append(answers[3])
    #        if answers[4] < 5: ql5.append(answers[4])
    #        if answers[5] < 5: ql6.append(answers[5])

    #for u in User.objects.filter(rules_activated_count__gt=19, strategy=User.LEITNER, id__gte=user_from):
    #    answers = [int(x) for x in u.data_adaptivity.split(":")]
    #    if len(answers) >= 6:
    #        if answers[0] < 5: ql1.append(answers[0])
    #        if answers[1] < 5: ql2.append(answers[1])
    #        if answers[2] < 5: ql3.append(answers[2])
    #        if answers[3] < 5: ql4.append(answers[3])
    #        if answers[4] < 5: ql5.append(answers[4])
    #        if answers[5] < 5: ql6.append(answers[5])


    #ql1 = sum(ql1) / len(ql1)
    #ql2 = sum(ql2) / len(ql2)
    #ql3 = sum(ql3) / len(ql3)
    #ql4 = sum(ql4) / len(ql4)
    #ql5 = sum(ql5) / len(ql5)
    #ql6 = sum(ql6) / len(ql6)
    #qb1 = sum(qb1) / len(qb1)
    #qb2 = sum(qb2) / len(qb2)
    #qb3 = sum(qb3) / len(qb3)
    #qb4 = sum(qb4) / len(qb4)
    #qb5 = sum(qb5) / len(qb5)
    #qb6 = sum(qb6) / len(qb6)
    return render(request, 'trainer/stats3.html', locals())


def ustats(request):
    users = User.objects.all()
    return render(request, 'trainer/ustats.html', locals())


@logged_in_or_basicauth("Bitte einloggen")
def mystats(request):
    user = User.objects.get(django_user=request.user)
    display_rank = False
    level = user.rules_activated_count
    rank = user.get_user_rank_display()

    num_solutions = Solution.objects.filter(user=user).count()
    num_errors = SolutionRule.objects.filter(solution__user=user, error=True).count()

    rankimg = "{}_{}.png".format(["Chaot", "Könner", "König"][int((level-1)/10)], int((level-1)%10)+1)

    error_rules = sorted(UserRule.objects.filter(user=user, active=True), key=lambda t: t.incorrect)
    return render(request, 'trainer/mystats.html', locals())


@logged_in_or_basicauth("Bitte einloggen")
def mystats_rule(request):
    rule_id = request.GET.get('rule',False)
    if rule_id:
        user = User.objects.get(django_user=request.user)
        userrule = UserRule.objects.get(user=user, rule__id=rule_id)
        solutions = SolutionRule.objects.filter(solution__user=user, rule=rule_id, error=True)
        return render(request, 'trainer/partials/mystats_rule.html', locals())
    else:
        return HttpResponseBadRequest("No rule_id given.")


def allstats(request):

    # id = int(request.GET.get('sid',1))
    sentences = Sentence.objects.all()

    return render(request, 'trainer/allstats.html', locals())


def allstats_sentence(request):
    sentence_id = int(request.GET.get('sentence_id',False))
    if sentence_id:
        sentence = get_object_or_404(Sentence, pk=sentence_id)
        return render(request, 'trainer/partials/allstats_sentence.html', locals())
    else:
        return HttpResponseBadRequest("No rule_id given.")


def allstats_correct(request):

    # id = int(request.GET.get('sid',1))
    sentences = Sentence.objects.all()

    return render(request, 'trainer/allstats_correct.html', locals())


def allstats_correct_sentence(request):
    sentence_id = int(request.GET.get('sentence_id',False))
    if sentence_id:
        sentence = get_object_or_404(Sentence, pk=sentence_id)
        return render(request, 'trainer/partials/allstats_correct_sentence.html', locals())
    else:
        return HttpResponseBadRequest("No rule_id given.")
