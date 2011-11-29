import random
from datetime import date

def rand_bool():
  if random.random() > 0.5:
    return True
  return False

def rand_str(n):
  return ''.join([chr(random.randint(48, 90)) for x in range(n)])

def rand_email():
  nm = ''.join([chr(random.randint(97, 122)) for x in range(5)])
  dom = ''.join([chr(random.randint(97, 122)) for x in range(5)])
  return nm + '@' + dom

def rand_date():
  return date.fromtimestamp(random.randint(0, 1318790434))
