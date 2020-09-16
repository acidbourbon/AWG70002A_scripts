#!/usr/bin/env python3


#import SCPI_socket as sock


import vxi11

import struct
from time import sleep
import numpy as np
import sys
import os
import datetime

from scipy import interpolate

local_objects = {}

waveformName = 'ExtWaveform2400'




def reverse_8bits(n):
        result = 0
        for i in range(8):
            result <<= 1
            result |= n & 1
            n >>= 1
        return result
      
def reverse_32bits(n):
        result = 0
        for i in range(32):
            result <<= 1
            result |= n & 1
            n >>= 1
        return result


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




# Method to convert a 32bit float to a HEX number
def float_to_hex(f):
    if f == 0:
        return '0x00000000'
    else:
        return hex(struct.unpack('<I', struct.pack('<f', f))[0])


  


def resample(target_x,data_x,data_y,**kwargs):
  fill_value = float(kwargs.get("fill_value",0.))
  f = interpolate.interp1d(data_x,data_y,bounds_error=False, fill_value=fill_value)
  out_x = target_x
  out_y = f(target_x)
  return (out_x,out_y)


def open_session(ip):
  
  # Open socket, create waveform, send data, read back and close socket
  print("connect to device ...")
  #session = sock.SCPI_sock_connect(ip)
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
  session.write("SOURCE1:CASSET:WAVEFORM \"{}\"".format(waveformName))
  session.write("SOURCE2:CASSET:WAVEFORM \"{}\"".format(waveformName))
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
  

  #if( np.max(np.abs(target_y)) > 0.5):
    #print("############################################")
    #print("## WARNING: Waveform on ch {:d} will clip!!! ##".format(trace))
    #print("############################################")

  # clip to allowed value range
  #target_y[target_y > 0.5] = 0.5
  #target_y[target_y < -0.5] = -0.5
  target_y[target_y > 1] = 1
  target_y[target_y < -1] = -1


  ##volt        = float(kwargs.get("volt",0.5))
  #offset = 0
  #volt = np.max(np.abs(target_y))
  #idle_val = idle_val/volt
  #target_y = target_y*127./volt
  #volt = volt*2
  
  offset = 0
  volt = np.max(np.abs(target_y))
  volt = volt*2


  if(invert):
    idle_val = -idle_val
    target_y = -target_y



  #n_delay = int(delay*sample_rate) 
  #n_offset = int(offset*sample_rate) 
  n = int(len(target_x))
  
  # sample len must be a multiple of 128
  #sample_len = next_int_mult_128(n)
  #sample_len = np.min([sample_len,mem_size])
  #print("sample len :{:d}".format(sample_len))
  
  #dataList = [-100 for i in range(sample_len)]
  
  sample_len = np.max([MIN_SAMPLE_LEN,n])
  
  dataList = idle_val*np.ones(sample_len)
  
  n_ = np.min([n,sample_len])
  
  dataList[0:n_] = target_y[0:n_]
  #dataList = dataList.astype(np.int).tolist()
  #dataList = dataList.tolist()
  #dataList = dataList.astype('float32')
  
  #dataString = ",".join(map(str,dataList))
  #cmdString = ":TRAC{:d}:DATA 1,{:d},{}".format(trace,n_offset,dataString)
  
  
  
  #print(session.ask(":TRAC{:d}:CAT?".format(trace)))
  #session.write(":TRAC{:d}:DEL:ALL".format(trace))
  #session.write(":TRAC{:d}:DEF 1,{:d},{:d}".format(trace,mem_size,idle_val_dac))
  
  ##delete all traces with wrong mem_size
  #for i in range(1,5):
    #cat_answer = session.ask(":TRAC{:d}:CAT?".format(i))
    #cat_answer.replace("\n","")
    #cat_answer.replace("\r","")
    #cat_answer.replace(" ","")
    ##print(cat_answer)
    #if( (cat_answer != "1,{:d}".format(mem_size))  and (cat_answer != "0,0" )): 
      #print("delete trace {:d}, because wrong mem size / wrong period".format(i))
      #session.write(":TRAC{:d}:DEL:ALL".format(i))
  
  
  #send data
  print("sending data ...")
  #session.write(cmdString)
  #print(session.ask(":TRAC1:DATA? 1,0,512"))
  
  substring = ""
  datastring = ""
  #recordLength = 2400    # [samples] (min. 2400 samples required)
  #data = []
  
  #leadingZeroes = 5      # [samples]
  maxWaveformLength = sample_len

  for i in range(maxWaveformLength):
      hexval = float_to_hex(dataList[i]) # float to HEX
      hexstring = hexval[2:] # discard HEX prefix
        
      for j in range(3,-1,-1): # split into 4 times 8 bit and convert to char
      #for j in range(0,4): # split into 4 times 8 bit and convert to char
          substring = hexstring[j*2:j*2+2]
          datastring += chr(int(substring,16)) # add chars to data string
          #data  += [int(substring,16)] # add chars to data string
      #datastring += chr(reverse_8bits(int(dataList[i]*127)))
          
  
  # Assemble command (send waveform data)
  #commandString = "WLIST:WAVEFORM:DATA \"{}\",0,{},#{}{}{}".format(waveformName, maxWaveformLength, len(str(4*maxWaveformLength)), str(4*maxWaveformLength), datastring)
  commandString = "WLIST:WAVEFORM:DATA \"{}\",0,{},#{}{}".format(waveformName, maxWaveformLength, len(str(4*maxWaveformLength)), str(4*maxWaveformLength))# + datastring

  print(commandString)
  
  # Open socket, create waveform, send data, read back, start playing waveform and close socket
  session.write("WLIST:WAVEFORM:DELETE ALL")
  session.write("WLIST:WAVEFORM:NEW \"{}\" ,{}".format(waveformName, sample_len))
  session.write_raw( str.encode(commandString+datastring))
  #session.write_raw( str.encode(datastring) )
  
  if(0):
    print("read back:")
    print("WLIST:WAVEFORM:DATA? \"{}\" ,0 ,{}".format(waveformName, maxWaveformLength))
    print(session.ask("WLIST:WAVEFORM:DATA? \"{}\" ,0 ,{}".format(waveformName, maxWaveformLength)))

  

  #print("set output voltage ...")
  #session.write(":VOLT{:d} {:3.3f}".format(trace,volt))

  #print("Output {:d} on ...".format(trace))
  #session.write(":OUTP{:d} ON".format(trace))
  
  
