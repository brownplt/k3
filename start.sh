#!/bin/bash

gnome-terminal -x python ~/src/google_appengine/dev_appserver.py --clear_datastore plt-belay
gnome-terminal -x python ~/src/google_appengine/dev_appserver.py apply -p 8081

