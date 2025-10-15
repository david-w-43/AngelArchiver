#!/bin/bash

# Run the ffmpeg command to record the stream
#ffmpeg -t "24:00:00" -i https://edge.clrmedia.co.uk/angel_hb -c copy ./Recordings/$(date -d "today" +"%Y%m%d%H%M").mp3
ffmpeg -i https://edge.clrmedia.co.uk/angel_hb -c copy -f segment -segment_atclocktime 1 -segment_time 300 -segment_format mp3 -strftime 1 /app/Recordings/%Y%m%d%H%M.mp3