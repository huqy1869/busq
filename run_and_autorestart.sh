#!/bin/sh
while true
do
	python test2.py &
	pid=$!
	inotifywait -q -e modify test2.py
	kill $pid
done
