import zmq
from msgpack import unpackb, packb
import numpy as np
from pyzbar import pyzbar
import threading
from queue import Queue
import time

class PupilInfoStream(threading.Thread):
    def __init__(self, q):
        super(PupilInfoStream, self).__init__()
        context = zmq.Context()
        self.q = q
        # open a req port to talk to pupil
        addr = '127.0.0.1'  # remote ip or localhost
        req_port = "50020"  # same as in the pupil remote gui

        self.req = context.socket(zmq.REQ)
        self.req.connect("tcp://{}:{}".format(addr, req_port))

        # ask for the sub port
        self.req.send_string('SUB_PORT')
        sub_port = self.req.recv_string()

        self.sub_info = context.socket(zmq.SUB)
        self.sub_info.connect("tcp://{}:{}".format(addr, sub_port))

        # recv just pupil/gaze/notifications/frame/fixations/blinks
        self.sub_info.setsockopt_string(zmq.SUBSCRIBE, 'fixations')

    def run(self):
        try:
            last_timestamp = 0
            while True:
                topic, msg = self.recv_from_sub_info()                
                if msg['timestamp'] - last_timestamp > 0.1:
                    last_timestamp = msg['timestamp']
                self.q.put(msg)             
                
        except KeyboardInterrupt:
            print("keyboard interrupt....")
        finally:
            print("Finished....")

    def recv_from_sub_info(self):
        topic = self.sub_info.recv_string()
        payload = unpackb(self.sub_info.recv(), encoding='utf-8')
        extra_frames = []
        while self.sub_info.get(zmq.RCVMORE):
            extra_frames.append(self.sub_info.recv())
        if extra_frames:
            payload['__raw_data__'] = extra_frames
        return topic, payload

 
