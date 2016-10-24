from django.db import models
import re  # regex support


class Sentence(models.Model):
    """
    Represents one sentence.
    Database representation has to include correct commas.
    The sentence is stored as a string in the database,
    words are separated by blanks and commas.

    IMPORTANT: The list of words of a sentence must never change!
               Solutions store a bool value for each gap, so gap
               positions must stay fixed.

    Example: Wir essen, Opa.
    """
    text = models.CharField(max_length=2048)
    comma_list = models.CommaSeparatedIntegerField(max_length=255, default='0')
    
    def __str__(self):
        return self.text
    
    def set_default_commalist(self):
        """
        Set default list of comma types: amout of zeros = amount of comma-slots
        """
        self.comma_list
        for i in range(len(self.get_commalist())):
            self.comma_list.append(',0')
        
    def get_commatypelist(self):
        """
        Get the commatype list.
        :return: List of type values split at commas
        """
        return re.split(r'[,]+',self.comma_list.strip())
    
    def get_words(self):
        """
        Get the word list.
        :return: List of words split at blanks or commas
        """
        return re.split(r'[ ,]+', self.text.strip())

    def get_commalist(self):
        """
        Where do the commas go?
        :return: List of boolean values indicating comma/no comma at that position.
        """
        return list(map(lambda x: ',' in x, re.split(r'\w+', self.text.strip())[1:-1]))

    def get_commaval(self):
        """
        Where do the commas go?
        :return: Bitfield (integer) indicating comma/no comma at that position.
        """
        val = 0
        commas = self.get_commalist()
        for i in range(len(commas)):
            if commas[i]:
                val += 2**i
        return val


class Solution(models.Model):
    """
    Represents one solutions to a sentence.
    Solutions are stored as bitfields for a sentence.
    """
    sentence = models.ForeignKey(Sentence, on_delete=models.CASCADE)
    # We do not use django users here because the user id is provided by the embedding system
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    user_id = models.CharField(max_length=255)
    solution = models.BigIntegerField()

