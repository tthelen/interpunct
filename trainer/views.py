# from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import JsonResponse
from .models import Sentence, Solution


def task(request):
    """
    Pick a task and show it.

    :param request: Django request
    :return: nothing
    """
    import random
    # get a random sentence
    count = Sentence.objects.all().count()
    sentence = Sentence.objects.all()[int(random.random() * count)]
    # get a corresponding solution for this sentence
    sol_sample = Solution.objects.get(sentence=sentence,user_id='mr_right')
    # pack all words of this sentence in a list
    words = sentence.get_words()
    # pack all comma types of this sentence in a list
    comma_types = sentence.get_commatypelist()
    # apply a 'dirty trick' to make it the same length as the words list
    comma_types.append('0')
    user_id = "testuser"
    return render(request, 'trainer/task.html', locals())


def submit(request):
    """
    Receives an AJAX GET request containing a solution bitfield for a sentence.
    Saves solution and user_id to database.

    :param request: Django request
    :return: nothing
    """
    #sentence = Sentence.objects.get(id=request.GET['id'])
    #s = Solution(sentence=sentence, user_id=request.GET['uid'], solution=request.GET['sol'])
    #s.save()
    return JsonResponse({'submit': 'ok'})
