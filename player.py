#!/usr/bin/env python3

#######################################
## Video player mark II
#######################################

from omxplayer.player import OMXPlayer
from pathlib import Path

VIDEO_PATH = Path("/opt/vc/src/hello_pi/hello_video/test.h264")
player = OMXPlayer(VIDEO_PATH)
