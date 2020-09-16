#!/usr/bin/env python3



import vxi11

import struct
from time import sleep
import numpy as np
import sys
import os
import datetime

from scipy import interpolate

local_objects = {}






def spice_float(argument):
   
  if( isinstance(argument,str)):
   
    expr = argument
    if("p" in expr):
      expr = expr.replace("p","e-12")
    elif("n" in expr):
      expr = expr.replace("n","e-9")
    elif("u" in expr):
      expr = expr.replace("u","e-6")
    elif("m" in expr):
      expr = expr.replace("m","e-3")
    elif("k" in expr):
      expr = expr.replace("k","e3")
    elif("Meg" in expr):
      expr = expr.replace("Meg","e6")
    elif("M" in expr):
      expr = expr.replace("M","e6")
    elif("G" in expr):
      expr = expr.replace("G","e9")
    elif("T" in expr):
      expr = expr.replace("T","e12")
      
    try:
      number = float(expr)
    except:
      raise NameError("cannot convert \"{}\" to a reasonable number".format(argument))
  else:
    number = float(argument)
  
  return number



  


def resample(target_x,data_x,data_y,**kwargs):
  fill_value = float(kwargs.get("fill_value",0.))
  f = interpolate.interp1d(data_x,data_y,bounds_error=False, fill_value=fill_value)
  out_x = target_x
  out_y = f(target_x)
  return (out_x,out_y)


def open_session(ip):
  
  # Open socket, create waveform, send data, read back and close socket
  print("connect to device ...")
  session = vxi11.Instrument('TCPIP::{}::INSTR'.format(ip))
  session.timeout = 500
  session.clear()
  #session.chunk_size = 102400
  print("*IDN?")
  idn_str = session.ask("*idn?")
  print(idn_str)
  if( "TEKTRONIX,AWG70002A,B030548" in idn_str):
    print("success!")
  else:
    session.close()
    raise NameError("could not communicate with device, or not a Tektronix AWG70002A")
  local_objects["session"] = session
  return session
  


def close_session():
  if (not("session" in local_objects.keys())):
    raise NameError("there is no running communication session with AWG!")
  session = local_objects["session"]
  
  print("close socket")
  session.close()
  
def __del__(self):
  close_session()
  
  
  
def run():
  if (not("session" in local_objects.keys())):
    raise NameError("there is no running communication session with AWG!")
  session = local_objects["session"]
 
  print("RUN!")
  session.write("AWGControl:RUN")
  session.write("OUTPUT1:STATE 1")
  session.write("OUTPUT2:STATE 1")

  
  
def stop():
  if (not("session" in local_objects.keys())):
    raise NameError("there is no running communication session with AWG!")
  session = local_objects["session"]
 
  print("STOP!")
  session.write("AWGControl:STOP")
  session.write("OUTPUT1:STATE 0")
  session.write("OUTPUT2:STATE 0")
  
 
def set_sample_rate(sample_rate):
  if (not("session" in local_objects.keys())):
    raise NameError("there is no running communication session with AWG!")
  session = local_objects["session"]
  
  
  if ((sample_rate < 1e9) or (sample_rate > 8e9)):
    raise NameError('sample rate must be >=1e9 and <= 8e9')
  
  print("attempting to set sample rate : {:e} Hz".format(sample_rate))
  session.write( "CLOCK:SRATE {:e}".format(sample_rate))
  
  print("read back sample rate (Hz):")
  read_back = session.ask("CLOCK:SRATE?")
  print(read_back)
  
  if( float(read_back) == float(sample_rate)):
    print("success!")
    return 1
  else:
    sleep(2)
    read_back = session.ask("CLOCK:SRATE?")
    print(read_back)
  
  if( float(read_back) == float(sample_rate)):
    print("success!")
    return 1
  else:
    raise NameError("could not set desired sample rate!")
  

def next_int_mult_128(n):
  return np.max([int((n)/128+1)*128,128]) # multiples of 128


def prev_int_mult_128(n):
  return np.max([int((n)/128)*128,128]) # multiples of 128

  
def program_trace(xdata,ydata,**kwargs):
  
  stop()
  
  if (not("session" in local_objects.keys())):
    raise NameError("there is no running communication session with AWG!")
  session = local_objects["session"]
  
  
  MAX_MEM_SIZE = 262144
  
  MIN_SAMPLE_LEN = 2400
  
  mem_size     = MAX_MEM_SIZE
  
  trace       = int(kwargs.get("trace",1))
  idle_val    = float(kwargs.get("idle_val",0))
  yscale      = float(kwargs.get("yscale",1))
  xscale      = float(kwargs.get("xscale",1))
  delay       = float(kwargs.get("delay",0e-9))
  sample_rate = int(float(kwargs.get("sample_rate",8e9)))
  invert      = int(kwargs.get("invert",0))
  period      = float(kwargs.get("period",0))

  
  waveformName = "ExtWaveformCh{:d}".format(trace)

  
  if(period != 0):
    #mem_size = next_int_mult_128(int(period * sample_rate))
    #mem_size = np.min([mem_size,MAX_MEM_SIZE])
    
    print("NOTE: overriding sample rate to match desired period!")
    
    sample_rate = 8e9

    mem_size = prev_int_mult_128(int(period * sample_rate))
    mem_size = np.min([mem_size,MAX_MEM_SIZE])
    hypothetical_period = 1/sample_rate*mem_size
    rate_scaler = hypothetical_period/period
    
    sample_rate *= rate_scaler
    sample_rate = int(sample_rate)
    
    
  set_sample_rate(sample_rate)
  
  print("preparing data for channel {:d}".format(trace))
  
  
  xdata = xdata*xscale + delay

  width = xdata[-1]

  ydata = ydata*yscale


  target_x = np.arange(0,width,1./sample_rate)
  target_x , target_y = resample(target_x,xdata,ydata,fill_value=idle_val)
  

  if( np.max(np.abs(target_y)) > 0.25):
    print("############################################")
    print("## WARNING: Waveform on ch {:d} will clip!!! ##".format(trace))
    print("############################################")

  target_y[target_y > .25] = .25
  target_y[target_y < -.25] = -.25

  target_y = target_y/.25
  idle_val = idle_val/.25


  if(invert):
    idle_val = -idle_val
    target_y = -target_y



  n = int(len(target_x))
  
  
  sample_len = np.max([MIN_SAMPLE_LEN,n])
  
  dataList = idle_val*np.ones(sample_len)
  
  n_ = np.min([n,sample_len])
  
  dataList[0:n_] = target_y[0:n_]
  
  #send data
  print("sending data ...")

  
  substring = ""
  datastring = ""
  data = bytearray()
  

  maxWaveformLength = sample_len

  for i in range(maxWaveformLength):
    value =  dataList[i]
    data += bytearray(struct.pack("f", value))
    
  commandString = "WLIST:WAVEFORM:DATA \"{}\",0,{},#{}{}".format(waveformName, maxWaveformLength, len(str(4*maxWaveformLength)), str(4*maxWaveformLength))# + datastring

  #print(commandString)
  
  # Open socket, create waveform, send data, read back, start playing waveform and close socket
  session.write("WLIST:WAVEFORM:DELETE {}".format(waveformName))
  session.write("WLIST:WAVEFORM:NEW \"{}\" ,{}".format(waveformName, sample_len))
  session.write_raw( str.encode(commandString) + data )
  
  #if(0):
    #print("read back:")
    #print("WLIST:WAVEFORM:DATA? \"{}\" ,0 ,{}".format(waveformName, maxWaveformLength))
    #print(session.ask("WLIST:WAVEFORM:DATA? \"{}\" ,0 ,{}".format(waveformName, maxWaveformLength)))

  
  session.write("SOURCE{:d}:CASSET:WAVEFORM \"{}\"".format(trace,waveformName))
  #session.write("SOURCE2:CASSET:WAVEFORM \"{}\"".format(waveformName))
  
  
