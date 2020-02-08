import zmq
from msgpack import unpackb, packb
import numpy as np
import cv2
from pyzbar import pyzbar

class PupilStream(object):
    def __init__(self):
        super().__init__()
        context = zmq.Context()
        # open a req port to talk to pupil
        addr = '127.0.0.1'  # remote ip or localhost
        req_port = "50020"  # same as in the pupil remote gui

        self.req = context.socket(zmq.REQ)
        self.req.connect("tcp://{}:{}".format(addr, req_port))

        # Start frame publisher with format BGR
        self.notify({'subject': 'start_plugin', 'name': 'Frame_Publisher', 'args': {'format': 'bgr'}})

        # ask for the sub port
        self.req.send_string('SUB_PORT')
        sub_port = self.req.recv_string()

        # open a sub port to listen to pupil
        self.sub_frame = context.socket(zmq.SUB)
        self.sub_frame.connect("tcp://{}:{}".format(addr, sub_port))

        self.sub = context.socket(zmq.SUB)
        self.sub.connect("tcp://{}:{}".format(addr, sub_port))

        # set subscriptions to topics
        # recv just pupil/gaze/notifications/frame
        self.sub_frame.setsockopt_string(zmq.SUBSCRIBE, 'pupil.')

        self.recent_world = None

    def start(self):
        '''
        This will start streaming from pupil headset
        '''
        try:
            while True:
                topic, msg = self.recv_from_sub()
                print(topic)
                if topic == 'frame.world':
                    self.recent_world = np.frombuffer(msg['__raw_data__'][0], dtype=np.uint8).reshape(msg['height'], msg['width'], 3)
                # if self.recent_world is not None:
                #     cv2.imshow("world", self.recent_world)
                #     cv2.waitKey(1)

                if self.recent_world is not None:
                    self.check_for_qr(self.recent_world)
        except KeyboardInterrupt:
            pass
        finally:
            cv2.destroyAllWindows()

    def check_for_qr(self, frame):
        barcodes = pyzbar.decode(frame)
        
        if len(barcodes) == 0:
            return

        print(barcodes)


    # send notification:
    def notify(self, notification):
        """Sends ``notification`` to Pupil Remote"""
        topic = 'notify.' + notification['subject']
        payload = packb(notification, use_bin_type=True)
        self.req.send_string(topic, flags=zmq.SNDMORE)
        self.req.send(payload)
        return self.req.recv_string()

    def recv_from_sub(self):
        '''Recv a message with topic, payload.
        Topic is a utf-8 encoded string. Returned as unicode object.
        Payload is a msgpack serialized dict. Returned as a python dict.

        Any additional message frames will be added as a list
        in the payload dict with key: '__raw_data__' .
        '''
        topic = self.sub.recv_string()
        payload = unpackb(self.sub.recv(), encoding='utf-8')
        extra_frames = []
        while self.sub.get(zmq.RCVMORE):
            extra_frames.append(self.sub.recv())
        if extra_frames:
            payload['__raw_data__'] = extra_frames
        return topic, payload

 
