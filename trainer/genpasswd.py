

words = [   "A",
            "B",
            "C",
            "D",
            "E",
            "F",
            "G",
            "H",
            "J",
            "K",
            "L",
            "M",
            "N",
            "P",
            "Q",
            "R",
            "S",
            "T",
            "U",
           "V",
           "W",
           "X",
           "Y",
           "Z",
           "2",
           "3",
           "4",
           "5",
           "6",
           "7",
           "8",
           "9"]

def generate_passphrase():
    import random
    password = ''.join(random.choice(words) for i in range(6))
    return password

if __name__=='__main__':
    print(generate_passphrase())