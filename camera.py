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

# Configure UART1
if not os.path.exists("/dev/ttyO1"):
    os.system("echo BB-UART1 > /sys/devices/bone_capemgr.8/slots")

##############################
# Global variables
device = "/dev/ttyO1"
initbauds=38400
uart = serial.Serial(device, baudrate=initbauds)
msb = None
lsb = None
size = "640x480" #size of the images to fetch from the camara (640x480,320x240,160x120)
##############################

def resetCamera():    
    """ Reset camera (SYSTEM_RESET command)
        
        @note 0x56+Serial number+0x26+0x00
    """
    uart.write(b'\x56\x00\x26\x00')
    resp = ""
    time.sleep(0.5)
    while(uart.inWaiting() > 0):
            data = uart.read()
            resp += data
            if "Init end\r\n" in resp:
                    print "Ready"
                    break

def setBaudRate(baud):
    """ Set the speed (initbauds) of the communication interface (SET_PORT command)
        
    From this point, the serial communication interface should change according to the new configured
    parameters, in order to simplify this process the function returns a newly create serial interface
    with the baudrate already configured.

    @note 0x56+Serial number+0x24+Data-length+interface type (1byte) +configuration data
    
    @warning once the baudrate has been changed to other than the default value (38400), the camera needs to be
    powered off (for now disconnecting the 5V work) in order to change it again.

    @return serial interface to use after modifying the baudrate
    """    
    available = [9600, 19200, 38400, 57600, 115200]
    if baud in available:
        global uart
        if baud == 9600:
                uart.write(b'\x56\x00\x24\x03\x01\xAE\xC8')
        elif baud == 19200:
                uart.write(b'\x56\x00\x24\x03\x01\x56\xE4')        
        elif baud == 38400: #default
                uart.write(b'\x56\x00\x24\x03\x01\x2A\xF2')
        elif baud == 57600:
                uart.write(b'\x56\x00\x24\x03\x01\x1C\x1C')
        elif baud == 115200:                
                uart.write(b'\x56\x00\x24\x03\x01\x0D\xA6')        
        resp = ""
        while (uart.inWaiting() > 0):
                data = uart.read()
                resp += data
                if b'\x76\x00\x24\x00\x00' in resp:                        
                        # overwrite the uart interface
                        break
                elif b'\x76\x00\x24\x03\x00' in resp:
                        raise Exception("Error at setBaudRate")
        uart = serial.Serial(device, baudrate=baud)
        print "Baudrate set to %s" % str(baud)
    else:
        raise Exception("Baudrate selected not available")


def setImageSize(size):
    """ Set image size controlling downsize attribute (DOWNSIZE_SIZE)

        The manual says that it's 0x53 but all the implementations point to the 0x54.
        Approximately the size of the images are:
            640x480:45164 bytes.        
            320x240:13576 bytes.
            160x120:3356 bytes.

        @note it seems that by default the camera sets the image size to 320x240
        @note 0x56+serial number+0x54+0x01+control item(1 byte)

        @warning the command manual seems to be wrong regaring the "control item"
        syntaxis. Proper values have been found out by inspection:
            0x00: 640x480
            0x01: 320x480
            0x02: 160x480
            ...
            0x06: 160x480
            0x07: 320x240
            0x08: 640x480 
            0x09: 320x480
            0x0A: 160x480
            0x0B: 320x240
            0x0C: 640x480
            0x0D: 320x480
            0x0E: 160x480
            0x0F: 320x240
            ...
            0x11: 320x240
            ...
            0x22: 160x120
            ...

    """
    if size == "640x480":
        uart.write(b'\x56\x00\x54\x01\x00')
    elif size == "320x240":
        uart.write(b'\x56\x00\x54\x01\x07')
    elif size == "160x120":
        uart.write(b'\x56\x00\x54\x01\x22')
    else:
        raise Exception("size %s not supported" % size)

    resp = ""
    time.sleep(0.1) # needed to let the camera grab the info
    while (uart.inWaiting() > 0):            
            data = uart.read()
            resp += data
            if b'\x76\x00\x54\x00\x00' in resp:
                    print "Size %s set" % size
                    break



def stopCurrentFrame():        
    """     Take the picture through FBUF_CTRL (control frame buffer register)
            
            This instruction stops the current frame.
                    
            @note 0x56+serial number+0x36+0x01+control flag(1 byte)
    """
    uart.write(b'\x56\x00\x36\x01\x00')
    resp = ""
    time.sleep(0.01)
    while(uart.inWaiting() > 0):
            data = uart.read()
            resp += data
            if b'\x76\x00\x36\x00\x00' in resp:
                    print "Picture taken"
                    break
            elif b'\x76\x00\x36\x03\x00' in resp:
                    # Error
                    raise Exception("Error at FBUF_CTRL")
    
    
def getCurrentFrameSize():    
    """ Get JPG size through GET_FBUF_LEN (get byte-lengths inFBUF)

        acquires the size of the actual frame (the next frame size can also be requested)

        @note 0x56+serial number+0x34+0x01+FBUF type(1 byte)
    """    
    uart.write(b'\x56\x00\x34\x01\x00')
    resp = ""
    time.sleep(0.01)
    while(uart.inWaiting() > 0):
            data = uart.read()
            resp += data
            if b'\x76\x00\x34\x00\x04\x00\x00' in resp:
                    global msb, lsb    # needed to specify the scope when modifying a global variable
                    msb = uart.read()
                    lsb = uart.read()
                    print "Image file size: %d bytes" % (ord(msb) << 8 | ord(lsb))                    
    

def readImageAndWriteToFile(bauds, size):
    # Write image to file
    """ This function reads the image data from FBUF and writes it to a file in the /tmp/
        directory according to the actual time.

        For that purpose it uses the READ_FBUF command reading the current frame (0x0, FBUF type). After the command
        has been sent, the camera starts sending the image. This process requires some time which depends on the
        baudrate and on the size of the image. For that purpose these two variables are taken in account when
        applying the delays (time.sleep).
             
    @note 0x56+serial number+0x32+0x0C+FBUF type(1 byte)+control mode(1 byte) +starting address(4 bytes)+data-length(4 bytes)+delay(2 bytes)
    """
    uart.write(b'\x56\x00\x32\x0C\x00\x0A\x00\x00\x00\x00\x00\x00%c%c\x00\x0A'
    % (msb,lsb))
    
    # take in account initbauds    
    if bauds == 9600:   #TODO
        if size == "640x480":
            time.sleep(2.5)
        elif size == "320x240":
            time.sleep(0.7)
        elif size == "160x120":
            time.sleep(0.000001)
        else:
            raise Exception("size %s not supported" % size)        
    elif bauds == 19200:
        if size == "640x480":
            time.sleep(15)
        elif size == "320x240":
            time.sleep(10)
        elif size == "160x120":
            time.sleep(5)
        else:
            raise Exception("size %s not supported" % size)        
    elif bauds == 38400:    # default
        if size == "640x480":
            time.sleep(2.5)
        elif size == "320x240":
            time.sleep(0.7)
        elif size == "160x120":
            time.sleep(0.000001)
        else:
            raise Exception("size %s not supported" % size)        
    elif bauds == 57600:    #TODO
        if size == "640x480":
            time.sleep(2.5)
        elif size == "320x240":
            time.sleep(0.7)
        elif size == "160x120":
            time.sleep(0.000001)
        else:
            raise Exception("size %s not supported" % size)        
    elif bauds == 115200:        
        if size == "640x480":
            time.sleep(2.5)
        elif size == "320x240":
            time.sleep(0.7)
        elif size == "160x120":
            time.sleep(0.000001)
        else:
            raise Exception("size %s not supported" % size)   

    now = datetime.datetime.now()
    filename = "%d.%02d.%02d.%02d.%02d.%02d.jpg" % \
    (now.year,now.month,now.day,now.hour,now.minute,now.second)
    resp = uart.read(size=5)
    if b'\x76\x00\x32\x00\x00' in resp:
            with open("/tmp/" + filename, 'wb') as f:
                    while(uart.inWaiting() > 0):
                            data = uart.read()
                            f.write('%c' % data)
            print "Image written to /tmp/%s" % (filename)
        
    # (OPTIONAL) send the image through ssh
    comando = "scp /tmp/%s victor@192.168.7.1:~/Desktop" % (filename)
    os.system(comando)


######################
#bauds = 9600
#bauds = 19200
bauds = 38400
#bauds = 57600
#bauds = 115200
resetCamera()
#setBaudRate(bauds)
setImageSize(size)
stopCurrentFrame()
getCurrentFrameSize()
readImageAndWriteToFile(bauds, size)
