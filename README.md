# AWG70002A_scripts

## Dependencies
- python3
- numpy
- scipy
- pyltspice
- python-vxi11

```
# install all dependencies

sudo pip3 install numpy scipy pyltspice python-vxi11
```

## The clients on either Windows/Linux

The below scripts have been written and tested on a Linux machine which is in the same
network as the AWG.
The scripts have also been proven to work on a windows machine with the IDLE Python3 release for Windows.

For the scripts to properly communicate with the server they need to be called with with the "ip" argument.
The given ip is the ip of the AWG:
```
./pulser.py       ip=192.168.0.123 <further arguments>
./send_csv.py     ip=192.168.0.123 <further arguments>
./send_ltspice.py ip=192.168.0.123 <further arguments>
```
If you don't want to type the ip argument all the time, you can export the ip as an environment variable once:
```
export AWG70002A_IP=192.168.0.123
```

You can also use the AWG70002 module directly in python3. The syntax is the same as the command line scripts.
Or you can directly send numpy data vectors to the AWG (see below for more detailed example).

```python
import AWG70002A as awg
# the python functions behind the individual utility .py scripts
awg.pulser(ip="192.168.0.123", trace=1, width="20n", delay="100n")
awg.send_csv(ip="192.168.0.123", trace=2, file="waveform.csv")
awg.send_ltspice(ip="192.168.0.123", trace=3, file="example.raw", signal="V(output)")

# directly send numpy vectors
awg.send_data(xdata, ydata, ip="192.168.0.123", trace=4)

```
you get the idea ...

---

LTspice, a Windows application,
runs perfectly fine on Linux via WINE. 
(http://ltspice.analog.com/software/LTspiceXVII.exe)

***



## pulser.py

- generate square pulses with arbitrary "idle" and "on" levels (-0.25 to 0.25V)


example usage:

![Photo](https://github.com/acidbourbon/AWG70002A_scripts/blob/master/pics/pulser.png)

```
./pulser.py width=50e-9 trace=1 on_val=0.25 idle_val=0
./pulser.py width=30n trace=2 on_val=-150m idle_val=50m delay=10n

```


![Photo](https://github.com/acidbourbon/AWG70002A_scripts/blob/master/pics/pulser2.png)

```
./pulser.py trace=2 width=10n leading_edge=2n trailing_edge=10n delay=5n on_val=250m
./pulser.py trace=3 width=10n leading_edge=2.5n trailing_edge=1n delay=15n on_val=-200m
```

![Photo](https://github.com/acidbourbon/AWG70002A_scripts/blob/master/pics/pulser_period.png)

```
./pulser.py trace=1 width=10n period=50n
```

example usage (python module):

```python
#!/usr/bin/env python3

from AWG70002A import pulser

pulser(
    ip="192.168.0.208",
    trace=1,
    period="2u",
    width="20n",
    leading_edge="1n",
    trailing_edge="5n",
    on_val="150m",
    idle_val="-20m",
    delay="10n",
    invert=0
)

```


optional parameters/standard values:
```
sample_rate=8e9
period=0
invert=0
on_val=0.5
idle_val=0
trace=1
width=50n
delay=0n
ip=192.168.0.198
xscale=1
yscale=1
```

- if leading and trailing edge are set to macroscopic values, the width is defined between the 50% points
- time and voltage definitions can be given with numeric postfixes, i.e. n=1e-9 p=1e-12 m=1e-3, etc ...

## send_csv.py

- read in two column csv file and send it to the AWG
- first column is time in seconds
- second column is voltage in volts
- standard delimiter is "," but can be adjusted (see below)
- waveform is resampled/interpolated, so time steps can be arbitrary


example usage:

![Photo](https://github.com/acidbourbon/AWG70002A_scripts/blob/master/pics/send_csv.png)

```
./send_csv.py file=waveform.csv trace=1 
./send_csv.py file=waveform.csv trace=2 delay=10n invert=1 yscale=0.5 xscale=0.3

```

![Photo](https://github.com/acidbourbon/AWG70002A_scripts/blob/master/pics/csv_period.png)
```
./send_csv.py file=waveform.csv trace=1 period=80n
```


```
# get trace data from another column of CSV file
./send_csv.py file=waveform.csv trace=1 tcol=2 ycol=5

# program multiple channels from different columns in same CSV file, watch csv file for changes
./send_csv.py file=waveform.csv \
  tcol=0 \
  ch1col=1 \
  ch2col=2 \
  ch3col=3 \
  ch4col=4 \
  watch_changes=1
```
optional parameters/standard values:
```
file=<none>
delimiter=","
sample_rate=8e9
period=0
invert=0
idle_val=0
trace=1
delay=0
xscale=1
yscale=1
ip=192.168.0.198
watch_changes=0
tcol=0
ycol=1
ch1col=""
ch2col=""
ch3col=""
ch4col=""
```

- If watch_changes is set to 1, then script will not terminate but continue watching the CSV file for changes.
If a change is detected, the AWG will be re-programmed automatically.



## send_ltspice.py

### single channel example

- read in LTSpice .raw file (binary simulation output file, containing all voltages and currents)
- waveform is resampled/interpolated and then sent to AWG

example circuit - models a typical PMT signal

![Photo](https://github.com/acidbourbon/AWG70002A_scripts/blob/master/pics/spice_asc.png)

example circuit - simulated waveform

![Photo](https://github.com/acidbourbon/AWG70002A_scripts/blob/master/pics/spice_raw.png)

measured waveform from AWG

![Photo](https://github.com/acidbourbon/AWG70002A_scripts/blob/master/pics/spice_scope.png)

example usage:
```
./send_ltspice.py trace=1 file=ltspice_example/example.raw signal="V(output)"
```
optional parameters/standard values:
```
file=<none>
sample_rate=8e9
period=0
signal="V(output)"
invert=0
idle_val=0
trace=1
delay=0e-9
xscale=1
yscale=1
ip=192.168.0.198
watch_changes=0
```

### multi channel example

example circuit - four different uses of the LTSpice voltage source

![Photo](https://github.com/acidbourbon/AWG70002A_scripts/blob/master/pics/multichan_asc.png)

example circuit simulated waveforms

![Photo](https://github.com/acidbourbon/AWG70002A_scripts/blob/master/pics/multichan_raw.png)

measured waveforms from AWG

![Photo](https://github.com/acidbourbon/AWG70002A_scripts/blob/master/pics/multichan_scope_zoom.png)

example usage:
```
./send_ltspice.py file=ltspice_example/example_multichan.raw \
  signal1="V(out1)" \
  signal2="V(out2)" \
  signal3="V(out3)" \
  signal4="V(out4)" \
  watch_changes=1
```

- If watch_changes is set to 1, then script will not terminate but continue watching the .raw file for changes.
If a change is detected, the AWG will be re-programmed automatically.

![Photo](https://github.com/acidbourbon/AWG70002A_scripts/blob/master/pics/watch_changes.png)

## send python/numpy data directly

![Photo](https://github.com/acidbourbon/AWG70002A_scripts/blob/master/pics/gauss_scope.png)

Recorded waveform was generated with the following python code:

```python
#!/usr/bin/env python3

import numpy as np
from matplotlib import pyplot as plt

import AWG20007A as awg
awg_ip = "192.168.0.208"

##################################################
##                 gauss pulse                  ##
##################################################


def gauss(x, **kwargs):
  mu = kwargs.get("mu",0)
  sigma = kwargs.get("sigma",1)
  ## default amplitude A generates bell curve with area = 1
  A = kwargs.get("A",1./(sigma*(2.*np.pi)**0.5)) 
  return A*np.exp(-(x-mu)**2/(2.*sigma**2))



period = 1e-6

x=np.arange(0,period,0.1e-9)

y=gauss(x,sigma=20e-9,mu=300e-9,A=200e-3)

plt.plot(x*1e9,y)
plt.xlabel("time (ns)")
plt.ylabel("voltage (V)")
plt.show()

awg.send_data(x,y,
              trace=1,
              ip=awg_ip,
              period=period)

```
![Photo](https://github.com/acidbourbon/AWG70002A_scripts/blob/master/pics/gauss_plot.png)

## Acknowledgements

Thanks to Nuno Brum for the beautiful LTSpice RawReader module!
https://pypi.org/project/PyLTSpice/

