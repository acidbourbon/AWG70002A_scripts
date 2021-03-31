#!/usr/bin/env python3

from AWG70002A import send_ltspice

import sys


if __name__=='__main__':
  send_ltspice( **dict(arg.split('=') for arg in sys.argv[1:])) # kwargs
