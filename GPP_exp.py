#! /usr/bin/env python
# # -*- coding: UTF-8 -*-

from pyvisa import visa,visa_exceptions
from time import sleep

#GPP=visa.instrument('TCPIP0::172.16.26.103::1026::SOCKET',term_chars='\n',delay=0,timeout=10)
#GPP=visa.instrument('GPIB0::5::INSTR',term_chars='\n',delay=0)
GPP=visa.instrument('ASRL6',baud_rate=115200,timeout=1,term_chars='\n',delay=0)

print GPP.ask('*IDN?') 
GPP.write(':SOUR1:VOLT 5.0')
GPP.write(':SOUR2:VOLT 5.0')
GPP.write(':SOUR3:VOLT 5.0')
GPP.write(':SOUR4:VOLT 5.0') 
GPP.write(':SOUR1:CURR 0.2')
GPP.write(':SOUR2:CURR 0.2')
GPP.write(':SOUR3:CURR 0.2')
GPP.write(':SOUR4:CURR 0.2')
GPP.write('OUT1')
print "VOLT :",GPP.ask('MEAS:VOLT:ALL?')
print "CURR :",GPP.ask('MEAS:CURR:ALL?')
sleep(5)
GPP.write('OUT0')
GPP.close()
