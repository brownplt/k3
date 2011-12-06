import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import contwinue.generate as g

if __name__ == '__main__':
  g.simple_generate()
