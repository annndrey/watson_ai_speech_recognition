import audioop
import pyaudio
import wave
import socket

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 40

#HOST = '192.168.0.122'    # The remote host                                     
#PORT = 50007              # The same port as used by the server                 

recording = True

#s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)                          
#s.connect((HOST, PORT))                                                        

p = pyaudio.PyAudio()

for i in range(0, p.get_device_count()):
    print(i, p.get_device_info_by_index(i)['name'])

device_index = int(input('Device index: '))                                    

stream = p.open(format=FORMAT,                                                 
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                input_device_index=device_index)

print("*recording")                                                            

frames = []                                                                    

while recording:                                                               
    data  = stream.read(CHUNK)                                                 
    frames.append(data)                                                        
    print(audioop.max(data,2))
#    s.sendall(data)                                                            

print("*done recording")                                                       
                                                                               
stream.stop_stream()                                                           
stream.close()                                                                 
p.terminate()
#s.close()                                                                      

print("*closed")
