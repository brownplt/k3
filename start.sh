#!/bin/bash

# Adapted from http://code.google.com/p/google-belay/source/browse/run.sh

PIDS="/tmp/k3/pids"

mkdir -p $PIDS

usage() {
  cat <<END
Usage:
  $0 <application>|all start|stop|restart port

Arguments:

  <application>: Currently, one of dj-apply, dj-resume, dj-belay, or
  dj-station.  If instead all is provided, each of these applications will be
  started.

  start:   Starts the selected application(s)
  stop:    Stops the selected applications(s)
  restart: Restarts the selected application(s)

  port:    If a single application is selected, the port to run it on
END
}

startapp() {
  local appdir=$1
  local port=$2
  
  if [[ (-e $PIDS/$appdir.pid) ]]; then
    echo "PID exists for $appdir in $PIDS/$appdir, refusing to start"
    echo "try stop first, or use restart"
    exit 1
  fi

  cd $appdir
  /usr/bin/python manage.py runserver --noreload $port &
  echo $! > $PIDS/$appdir.pid
  cd ..
  echo "Started $appdir, pid in $PIDS/$appdir.pid"
}

stopapp() {
  local app=$1

  if [[ ! (-e $PIDS/$app.pid) ]]; then
    echo "WARNING: No pid file for $app in $PIDS/$app"
  else 
    echo "Stopping $app..."
    kill -2 `cat $PIDS/$app.pid`
    rm $PIDS/$app.pid
  fi 
}

startall() {
  startapp dj-plt-belay 8000
  startapp dj-apply 8001
  startapp dj-station 8002
  startapp dj-resume 8003
}

stopall() {
  stopapp dj-plt-belay
  stopapp dj-apply
  stopapp dj-station
  stopapp dj-resume
}

go() {
  local app=$1
  local op=$2
  local port=$3
  if [[ $app == 'all' ]]; then
    if [[ $op == 'start' ]]; then
      startall
    elif [[ $op == 'stop' ]]; then
      stopall
    elif [[ $op == 'restart' ]]; then
      stopall
      startall
    fi  
  else
    if [[ $op == 'start' ]]; then
      startapp $app $port
    elif [[ $op == 'stop' ]]; then
      stopapp $app $port
    elif [[ $op == 'restart' ]]; then
      stopapp $app $port
      startapp $app $port
    fi  
  fi
}

go $1 $2 $3

