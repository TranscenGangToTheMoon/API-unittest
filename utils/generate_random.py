import string
import random


def rnstr(length=6):
    return ''.join(random.choices(string.ascii_letters, k=length))
