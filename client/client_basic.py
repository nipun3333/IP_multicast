import socket
import threading
import pyaudio
import time
import queue
import sys
import struct

host = "localhost"
port = 5432

# Global variable used as a flag to check whether we have to terminate the recieve thread
terminateRecieveThread = False


def receive(signal, multi_list, stat_int, client_socket):
    while signal:
        try:
            multi_station = multi_list[stat_int]  # station related information
            print("Information about the current station: ", multi_station)
            # this will later have to be calculated, t (taken as input) * bitrate provided by server
            BUFF_SIZE = 65536
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            p = pyaudio.PyAudio()
            CHUNK = 10240
            # multicast address of the station to be played
            MCAST_GRP = multi_station[3]
            # multicast port of the station to be playeed
            MCAST_PORT = multi_station[4]
            client_socket.bind(('', MCAST_PORT))
            group = socket.inet_aton(MCAST_GRP)
            mreq = struct.pack('4sl', group, socket.INADDR_ANY)

            # Setting socket options
            client_socket.setsockopt(
                socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1)

            stream = p.open(format=p.get_format_from_width(2),
                            channels=2,
                            rate=44100,
                            output=True,
                            frames_per_buffer=CHUNK)

            # The recieved audio data will be stored in this queue and played in the
            # later section of the function
            q = queue.Queue(maxsize=10000000)

            def getAudioData():  # function used to store data in the queue
                while True:
                    if(terminateRecieveThread):
                        return
                    try:
                        frame, _ = client_socket.recvfrom(BUFF_SIZE)
                        q.put(frame)
                    except:
                        pass
        except:
            pass
        # using t1 thread to start storing data in the queue
        t1 = threading.Thread(target=getAudioData, args=())
        t1.start()
        time.sleep(3)
        while True:
            if(terminateRecieveThread):
                return
            frame = q.get()
            stream.write(frame)  # to play the audio data from the queue
            if(q.qsize() == 0):
                break
        # Closing the client_socket
        client_socket.close()


try:
    # Connect to server through TCP protocol
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    multi_msg = sock.recv(1024).decode()
    print(multi_msg)
    # this will convert string into an ordered list
    multi_list = eval(multi_msg)
    print(multi_list)
    station = input("Enter the station you want to listen to: ")
    # stat_int is the index of the station in the list, which will be sent to recieve()
    # so as to know which station to listen to
    # further would be used for switch station feature
    stat_int = int(station)
    while(stat_int >= len(multi_list) or stat_int < 0):
        station = input("Invalid station number. Please enter a valid station number (Between 0 and %d): " % (
            len(multi_list) - 1))
        stat_int = int(station)

except:
    print("Could not make a connection to the server")
    input("Press enter to quit")
    sys.exit(0)

isPlaying = True
while True:
    terminateRecieveThread = False
    # Client socket to be used to receive audio data through UDP protocol
    client_socket = socket.socket(
        socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    receiveThread = threading.Thread(target=receive, args=(
        isPlaying, multi_list, stat_int, client_socket))
    receiveThread.start()
    time.sleep(1)

    client_msg = "Type P, R, T or S at any point you want to Pause, Restart, Terminate, or Switch respectively: "
    message = input(client_msg)

    if(message == 'P'):  # Pause
        isPlaying = False
        terminateRecieveThread = True
        receiveThread.join()
        client_socket.close()
        print("Paused")
    elif(message == 'R'):  # Restart
        if(isPlaying):
            print("The song is already playing")
        else:
            terminateRecieveThread = True
            receiveThread.join()
            client_socket.close()
            print("Restarted")
            isPlaying = True
    elif(message == 'T'):  # Terminate Radio
        terminateRecieveThread = True
        receiveThread.join()
        client_socket.close()
        exit()
    elif (message == 'S'):  # Switch Stations
        station = input("Enter the station you want to listen to: ")
        stat_int = int(station)
        while(stat_int >= len(multi_list) or stat_int < 0):
            station = input("Invalid station number. Please enter a valid station number (Between 0 and %d): " % (
                len(multi_list) - 1))
            stat_int = int(station)
        client_socket.close()
        terminateRecieveThread = True
        receiveThread.join()
        print("Switching")
