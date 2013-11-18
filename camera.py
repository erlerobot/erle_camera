import serial
import time
import datetime

# Initialize camera
serial = serial.Serial("/dev/ttyO1", baudrate=38400)
# SYSTEM_RESET command
serial.write(b'\x56\x00\x26\x00')
resp = ""
time.sleep(1)
while(serial.inWaiting() > 0):
        data = serial.read()
        resp += data
        if "Init end\r\n" in resp:
                print "Ready"
                break

# Set image size to 640 x 480
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
serial.write(b'\x56\x00\x36\x01\x00')
resp = ""
time.sleep(2)
while(serial.inWaiting() > 0):
        data = serial.read()
        resp += data
        if b'\x76\x00\x36\x00\x00' in resp:
                print "Picture taken"
                break

#Get JPG size
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
