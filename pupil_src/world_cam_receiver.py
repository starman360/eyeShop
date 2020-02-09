import zmq
from msgpack import unpackb, packb
import numpy as np
import cv2
from pyzbar import pyzbar
from queue import Queue
import zbar
import socketio
import time

class PupilWorldStream(object):
    def __init__(self, q):
        super().__init__()
        self.q = q
        context = zmq.Context()
        # open a req port to talk to pupil
        addr = '127.0.0.1'  # remote ip or localhost
        req_port = "50020"  # same as in the pupil remote gui

        self.sio = socketio.Client()
        self.sio.connect("http://10.2.6.170:3000")

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

        # set subscriptions to topics
        # recv just pupil/gaze/notifications/frame
        self.sub_frame.setsockopt_string(zmq.SUBSCRIBE, 'frame.world')

        self.recent_world = None
        self.key = ""
        self.state = "Looking for Key QR Code!"

    def send(self, key, data):
        self.sio.emit(key, data)

    def start(self):
        '''
        This will start streaming from pupil headset
        '''
        try:
            pos = [10, 10]
            start_time = time.time()
            while True:
                topic, msg = self.recv_from_sub()
                if topic == 'frame.world':
                    self.recent_world = np.frombuffer(msg['__raw_data__'][0], dtype=np.uint8).reshape(msg['height'], msg['width'], 3)
                
                if self.recent_world is not None:  

                    text = "Mode # {}".format(self.state)
                    cv2.putText(self.recent_world, text, (400, 40), cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0, 0, 255), 2)

                    upos= []
                    while not self.q.empty():
                        info = self.q.get()
                        upos = info["norm_pos"]
                        # 1280x768 pupil is based on bottom_left and opencv is top left, transformation is required
                        upos[0] = (upos[0])*1280
                        upos[1] = (1 - upos[1])*720     
                        self.q.task_done()
                    
                    if len(upos) != 0:
                        pos = upos

                    x = int(pos[0])
                    y = int(pos[1])

                    paddig = 200
                    x0 = 2 if x-paddig <= 0 else x-paddig
                    x1 = 1280 if x+paddig > 1280 else x+paddig
                    y0 = 2 if y-paddig <= 0 else y-paddig
                    y1 = 768 if y+paddig > 768 else y+paddig

                    # print(x0, x1, y0, y1)
                    image = self.recent_world[x0:x1, y0:y1, :]
                    barcodes = self.check_for_qr(image)
                    cv2.rectangle(self.recent_world, (x0, y0), (x1, y1), (0, 0, 255), 2)
                    cv2.circle(self.recent_world,(x, y), 25, (0,255,0), -1)
                    
                    for barcode in barcodes:
                        # extract the bounding box location of the barcode and draw the
                        # bounding box surrounding the barcode on the image
                        (x, y, w, h) = barcode.rect
                        cv2.rectangle(self.recent_world, (x, y), (x + w, y + h), (0, 0, 255), 2)
                        barcodeData = barcode.data.decode("utf-8")
                        barcodeType = barcode.type
                        text = "{} ({})".format(barcodeData, barcodeType)
                        cv2.putText(self.recent_world, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (0, 0, 255), 2)
                        # print the barcode type and data to the terminal
                        print("[INFO] Found {} barcode: {}".format(barcodeType, barcodeData))
                        if 'key#' in barcodeData:
                            self.key = barcodeData.replace("key#", "")
                            self.state = "Key is # " + self.key
                            print("Send", self.key)
                            self.send("sync", {'key' : self.key, 'payload': 1})
                        else:
                            try:
                                elapsed_time = time.time() - start_time
                                print(elapsed_time)
                                if elapsed_time >= 2:
                                    self.send("barcode", {'key' : self.key, 'payload': barcodeData})
                                    start_time = time.time()

                            except TypeError:
                                print("Failed", barcodeData)
                                pass

                    # if image.shape[0] != 0 and image.shape[1] != 0: 
                    cv2.imshow("world", self.recent_world)
                    cv2.waitKey(1)

        except KeyboardInterrupt:
            pass
        finally:
            print("finish")
            cv2.destroyAllWindows()

    def check_for_qr(self, frame):
        barcodes = []
        try:
            barcodes = pyzbar.decode(frame)
        except ZeroDivisionError:
            pass
        
        return barcodes

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
        topic = self.sub_frame.recv_string()
        payload = unpackb(self.sub_frame.recv(), encoding='utf-8')
        extra_frames = []
        while self.sub_frame.get(zmq.RCVMORE):
            extra_frames.append(self.sub_frame.recv())
        if extra_frames:
            payload['__raw_data__'] = extra_frames
        return topic, payload