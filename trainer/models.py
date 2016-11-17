import django.db
import re  # regex support


class Sentence(django.db.models.Model):
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
    text = django.db.models.CharField(max_length=2048)
    comma_list = django.db.models.CharField(max_length=255, default='')
    comma_select = django.db.models.CommaSeparatedIntegerField(max_length=255, default='0')
    total_submits = django.db.models.IntegerField(max_length=25,default='0')

    def __str__(self):
        return self.text

    def update_submits(self):
        self.total_submits += 1
        self.save()

    def set_default_commalist(self):
        """
        Set default list of comma types: amout of zeros = amount of comma-slots
        """
        self.comma_list
        for i in range(len(self.get_commalist())):
            self.comma_list.append(',0')

    def set_comma_select(self, bitfield):
        comma_select = self.get_commaselectlist()
        for i in range(len(comma_select)-1,-1,-1):
            if (bitfield - 2**i >= 0) & (i !=(len(comma_select)-1)):
                comma_select[i] = str(int(comma_select[i]) + 1) + ","
                bitfield -= 2**i
            elif bitfield - 2**i >= 0:
                comma_select[i] = str(int(comma_select[i]) + 1)
                bitfield -= 2 ** i
            elif i !=(len(comma_select)-1):
                comma_select[i] += ","

        self.comma_select = "".join(comma_select)
        self.save()

    def get_commaselectlist(self):
        """
        Get the commatype list.
        :return: List of type values split at commas
        """
        return re.split(r'[,]+',self.comma_select.strip())

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


class Solution(django.db.models.Model):
    """
    Represents one solutions to a sentence.
    Solutions are stored as bitfields for a sentence.
    """
    sentence = django.db.models.ForeignKey(Sentence, on_delete=django.db.models.CASCADE)
    # We do not use django users here because the user id is provided by the embedding system
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    user_id = django.db.models.CharField(max_length=255)
    solution = django.db.models.BigIntegerField()

class User(django.db.models.Model):
    user_id = django.db.models.CharField(max_length = 255)
    total_sentences = django.db.models.IntegerField
    # counts wrong answers for a specific comma type
    comma_type_false = django.db.models.CharField(max_length=400,default="A1:0/0, A2:0/0, A3:0/0, A4:0/0, B1.1:0/0, B1.2:0/0, B1.3:0/0, B1.4.1:0/0, B1.4.2:0/0, B1.5:0/0, B2.1:0/0, B2.2:0/0, B2.3:0/0, B2.4.1:0/0, B2.4.2:0/0, B2.5:0/0, C1:0/0, C2:0/0, C3.1:0/0, C3.2:0/0, C4.1:0/0, C4.2:0/0, C5:0/0, C6.1:0/0, C6.2:0/0, C6.3.1:0/0, C6.3.2:0/0, C6.4:0/0, C7:0/0, C8:0, D1:0/0, D2:0/0, D3:0/0, E0:0/0")
    def get_dictionary(self):
        """
        Dictionary with comma types as keys and a value tuple of erros and total amount of trials
        :return: dictionary
        """
        type_dict = {}
        tmp = re.split(r'[ ,]+', self.comma_type_false)
        for elem in tmp:
            [a,b] = re.split(r':',elem)
            type_dict[a]=b
        return type_dict

    def save_dictionary(self,update):
        """
        Save updated dictionary to the database
        :param update: updated dictionary
        """
        new_dict_str = ""
        for key in update:
            new_dict_str += key + ":" + update[key] + ","
        self.comma_type_false = new_dict_str[:-1]
        self.save()

    def count_false_types(self, user_bitfield, comma_array):
        """
        Counting false comma sets and correct comma sets save in dict
        :param user_bitfield:
        :param comma_array:
        :return:
        """
        dict = self.get_dictionary()

        for i in range(len(comma_array) - 1, 0, -1):
            # one comma too less (add false, add total)
            if ((comma_array[i] != "0") and (user_bitfield - 2 ** i < 0)):
                [a, b] = re.split(r'/', dict[comma_array[i]])
                dict[comma_array[i]] = str(int(a) + 1) + "/" + str(int(b) + 1)
            # correct comma (add to total)
            elif ((comma_array[i] != "0") and (user_bitfield - 2 ** i >= 0)):
                [a, b] = re.split(r'/', dict[comma_array[i]])
                dict[comma_array[i]] = a + "/" + str(int(b) + 1)

        self.save_dictionary(dict)