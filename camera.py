# -*- encoding: utf-8 -*-
'''
                                          
 _____     _        _____     _       _   
|   __|___| |___   | __  |___| |_ ___| |_ 
|   __|  _| | -_|  |    -| . | . | . |  _|
|_____|_| |_|___|  |__|__|___|___|___|_|  
                                          
@author: Víctor Mayoral Vilches <victor@erlerobot.com>
@description: python interface with the IMU
'''

import serial
import time
import datetime
import os

# Initial configuration
device = "/dev/ttyO1"
bauds=38400
serial = serial.Serial(device, baudrate=bauds)

def resetCamera():    
    """ Reset camera (SYSTEM_RESET command)
        
        @note 0x56+Serial number+0x26+0x00
    """
    serial.write(b'\x56\x00\x26\x00')
    resp = ""
    time.sleep(1)
    while(serial.inWaiting() > 0):
            data = serial.read()
            resp += data
            if "Init end\r\n" in resp:
                    print "Ready"
                    break

def setBaudRate115200():
    """ Set the speed (bauds) of the communication interface (SET_PORT command)
        
    From this point, the serial communication interface should change according to the new configured
    parameters, in order to simplify this process the function returns a newly create serial interface
    with the baudrate already configured.

    @note 0x56+Serial number+0x24+Data-length+interface type (1byte) +configuration data
    @return serial interface to use after modifying the baudrate
    """    
    available = [9600, 19200, 38400, 38400, 115200]
    if baud in available:
        serial.write(b'\x56\x00\x24\x03\x01\x0D\xA6')
        resp = ""
        while (serial.inWaiting() > 0):
                data = serial.read()
                resp += data
                if b'\x76\x00\x24\x00\x00' in resp:
                        print "Baudrate set to 115200"
                        break
                elif b'\x76\x00\x24\x03\x00' in resp:
                        raise Exception("Error at setBaudRate")
        # return a new interface
        return serial.Serial(device, baudrate=115200)
    else:
        raise Exception("Baudrate selected not available")





    # Set image size to 640 x 480 
    """     according to the command manual 0x54 corresponds with DOWNSIZE_STATUS
            Everything looks like it might refer to DOWNSIZE_SIZE, 0x53. The return code fits
            exactly with it. PROBABLY MISTAKEN
    
            TODO inspect this more carefully.
    """     
    serial.write(b'\x56\x00\x54\x01\x00')
    resp = ""
    time.sleep(1)
    while (serial.inWaiting() > 0):
            data = serial.read()
            resp += data
            if b'\x76\x00\x54\x00\x00' in resp:
                    print "Size set"
                    break
    
    # Take picture
    """     FBUF_CTRL: control frame buffer register
            particularly this instruction stop the current frame.
                    0x56+serial number+0x36+0x01+control flag(1 byte)
    """
    serial.write(b'\x56\x00\x36\x01\x00')
    resp = ""
    time.sleep(2)
    while(serial.inWaiting() > 0):
            data = serial.read()
            resp += data
            if b'\x76\x00\x36\x00\x00' in resp:
                    print "Picture taken"
                    break
            elif b'\x76\x00\x36\x03\x00' in resp:
                    # Error
                    raise Exception("Error at FBUF_CTRL")
    
    
    #Get JPG size
    """     GET_FBUF_LEN: get byte-lengths inFBUF
                    0x56+serial number+0x34+0x01+FBUF type(1 byte)
    """
    serial.write(b'\x56\x00\x34\x01\x00')
    resp = ""
    time.sleep(1)
    while(serial.inWaiting() > 0):
            data = serial.read()
            resp += data
            if b'\x76\x00\x34\x00\x04\x00\x00' in resp:
                    msb = serial.read()
                    lsb = serial.read()
                    print "Image file size: %d bytes" % (ord(msb) << 8 | ord(lsb))
    
    # Write image to file
    """     READ_FBUF: read image data from FBUF
                    0x56+serial number+0x32+0x0C+FBUF type(1 byte)+control mode(1 byte) +starting address(4 bytes)+data-length(4 bytes)+delay(2 bytes)
    """
    serial.write(b'\x56\x00\x32\x0C\x00\x0A\x00\x00\x00\x00\x00\x00%c%c\x00\x0A'
    % (msb,lsb))
    time.sleep(5)
    now = datetime.datetime.now()
    filename = "%d.%02d.%02d.%02d.%02d.%02d.jpg" % \
    (now.year,now.month,now.day,now.hour,now.minute,now.second)
    resp = serial.read(size=5)
    if b'\x76\x00\x32\x00\x00' in resp:
            with open("/tmp/" + filename, 'wb') as f:
                    while(serial.inWaiting() > 0):
                            data = serial.read()
                            f.write('%c' % data)
            print "Image written to /tmp/%s" % (filename)
    
    
    # send the image through ssh
    comando = "scp /tmp/%s victor@192.168.7.1:~/Desktop" % (filename)
    os.system(comando)


######################
resetCamera()
serial = setBaudRate115200()
