from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Count
from django.urls import reverse
from .models import Sentence, Solution, Rule, SolutionRule, SentenceRule, User, UserSentence, UserRule
import random
import hashlib
import base64
from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.auth import logout
from django.contrib import messages


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
            user.strategy = user.LEITNER  # random.choice([user.BAYES, user.BAYES, user.LEITNER])
            user.gamification = user.GAMIFICATION_CLASSIC
            user.prepare(request)  # create a corresponding django user and set up auth system
            user.save()
        user.login(request)
        return user

    if 'uname' in request.GET:
        # uname given from stud.ip (or elsewhere)
        #
        uname = request.GET.get('uname')
        if uname and len(uname) > 8:
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

def view_or_welcome(view, request, test_func, realm="", *args, **kwargs):
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
            # user.gamification = random.choice([user.GAMIFICATION_CLASSIC, user.GAMIFICATION_INDIVIDUAL, user.GAMIFICATION_GROUP])
            user.gamification = user.GAMIFICATION_CLASSIC
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

    return code_start(request)


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
            return view_or_welcome(func, request,
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
            return view_or_welcome(func, request,
                                     lambda u: u.has_perm(perm),
                                     realm, *args, **kwargs)

        return wrapper

    return view_decorator


def code_start(request):
    nologo = True
    return render(request, 'trainer/start.html', locals())


def start_new(request):
    if 'code' in request.POST and request.POST['code'] != '':
        return start_continue(request)

    from trainer.genpasswd import generate_passphrase
    while True:
        code = generate_passphrase()
        hash_code = hashlib.sha224(code.encode('utf-8')).hexdigest()
        try:  # check if code already exists
            sess = User.objects.get(user_id=hash_code)
        except User.DoesNotExist:
            break  # go on if code is fresh

    user = User(user_id=hash_code)
    user.rules_activated_count = 0
    user.strategy = user.LEITNER
    user.code = code
    user.gamification = user.GAMIFICATION_CLASSIC
    user.prepare(request)  # create a corresponding django user and set up auth system
    user.data="No questionnaire in this run."
    user.save()
    return render(request, 'trainer/start_new.html', locals())


def start_continue(request):
    if 'code' in request.POST:
        try:
            u = User.objects.get(code=request.POST.get('code'))
        except User.DoesNotExist:
            messages.error(request, "Der eingegebene Code ist ungültig. Bitte erneut probieren.")
            return render(request, 'trainer/start.html', locals())

        u.login(request)
        messages.success(request, "Der eingegebene Code ist gültig. Du kannst jetzt weiter üben.")
        return redirect(reverse('task'))


@logged_in_or_basicauth("Bitte einloggen")
def task(request):
    """
    Pick a task and show it.

    :param request: Django request
    :return: nothing
    """

    active='task'

    def render_task_explain_commas(request, sent, select_rules=None, template_params=None):

        if not template_params:
            template_params = {}

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
    try:
        user = User.objects.get(django_user=request.user)
    except User.DoesNotExist:
        # destroy session and redirect to start page
        logout(request)
        messages.error(request, "Die vorhandene Sitzung ist ungültig geworden, weil die Regeln vereinfacht und z.T. neu formuliert worden und neue Beispielsätze erstellt wurden. Bitte neu beginnen.")
        return redirect(reverse('task'))

    new_rule = None  # new level reached? (new rule to explain)
    display_rank = True  # show the rank in output? (not on welcome and rule explanation screens)
    rankimg = ""
    finished = False # default is: we're not yet finished
    # select strategy
    strategy = user.get_strategy()
    strategy_debug = strategy.debug_output()

    # -----------------------------------------------------------------------
    # new user: show welcome page
    if not user.data:
        display_rank=False
        user.data="No questionnaire in this run."
        user.code = None
        user.save()
        return render(request, 'trainer/welcome_noquestionnaire.html', locals())

    # -----------------------------------------------------------------------
    # user without activated rules: show first rule page
    if user.rules_activated_count == 0:
        new_rule = strategy.activate_first_rule()
        display_rank=False
        level = 1
        return render(request, 'trainer/level_progress.html', locals())

    # fetch and prepare information about level for template
    level = user.rules_activated_count  # user's current level
    activerules = strategy.get_active_rules()
    rankimg = "{}_{}.png".format(["Chaot", "Könner", "König"][int((level-1)/10)], int((level-1)%10)+1)  # construct image name
    show_ranking = False

    # ------------------------------------------------------------------------
    # normal task selection process
    (new_rule, finished, forgotten) = strategy.progress()  # checks if additional rule should be activated or user has finished all levels

    # level progress: show new rules instead of task
    if new_rule:
        level = user.rules_activated_count  # user's current level
        return render(request, 'trainer/level_progress.html', locals())

    show_ranking=True

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
        # update strategy model (3=COMMA_EXPLAIN)
        user.get_strategy().update(r, 3, (correct == chosen))
        if not r.code.startswith('E'):  # only count non-error rules
            ur = UserRule.objects.get(user=user, rule=r)
            ur.count((correct == chosen))  # count rule application as correct if correct rule was chosen and vice versa
            if correct != chosen:
                error_rules.append(r)

    # recalculate individual or group score
    # user.update_score(resp)

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
def logout_view(request):
    u = User.objects.get(django_user=request.user)
    code = u.code
    logout(request)
    messages.add_message(request, messages.SUCCESS, 'Du hast Dich ausgeloggt und kannst einen neuen Durchlauf beginnen, oder Dich mit Deinem bisherigen Code "{}" wieder einloggen.'.format(code))
    return redirect('task')


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
    active = 'help'
    additional_heading = 'Anleitung'
    user = User.objects.get(django_user=request.user.id)
    return render(request, 'trainer/help.html', locals())


def rules(request):
    """Shows user rules and all rules"""
    all_rules = Rule.objects.all()
    user_rules = UserRule.objects.filter(user__django_user=request.user.id, active=True)
    active = 'rules'
    additional_heading = 'Alle Regeln'
    user = User.objects.get(django_user=request.user.id)
    return render(request, 'trainer/rules.html', locals())


def code(request):
    """Renders code and link explanation template"""
    active = 'code'
    additional_heading = 'Dein Code'
    user = User.objects.get(django_user=request.user)
    return render(request, 'trainer/code.html', locals())


def impressum(request):
    """Renders help template"""
    active = 'Impressum'
    # additional_heading = 'Anleitung'
    try:
        user = User.objects.get(django_user=request.user.id)
    except User.DoesNotExist:
        user = None
    nologo = True
    return render(request, 'trainer/impressum.html', locals())


def nocookies(request):
    """Renders information page if cookies could not be set."""
    active = ''
    additional_heading = "Cookie-Problem"
    display_rank = False  # show the rank in output? (not on welcome and rule explanation screens)
    uname = request.GET.get('uname','')
    return render(request, 'trainer/nocookies.html', locals())


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
        .annotate(the_count=Count('rule'))

    return render(request, 'trainer/stats.html', locals())

def solutions_for_user(u):
    u_txt = []
    for s in Solution.objects.filter(user=u):
        if SolutionRule.objects.filter(solution=s, error=True).count() > 0:
            u_txt.append("0")
        else:
            u_txt.append("1")
    return ",".join(u_txt)


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

    rankimg = "{}_{}.png".format(["Chaot", "Könner", "König"][int((level-1)/10)], int((level-1) % 10)+1)

    error_rules = sorted(UserRule.objects.filter(user=user, active=True), key=lambda t: t.incorrect)
    return render(request, 'trainer/mystats.html', locals())


@logged_in_or_basicauth("Bitte einloggen")
def mystats_rule(request):
    rule_id = request.GET.get('rule', False)
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
    sentence_id = int(request.GET.get('sentence_id', False))
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
    sentence_id = int(request.GET.get('sentence_id', False))
    if sentence_id:
        sentence = get_object_or_404(Sentence, pk=sentence_id)
        return render(request, 'trainer/partials/allstats_correct_sentence.html', locals())
    else:
        return HttpResponseBadRequest("No rule_id given.")
