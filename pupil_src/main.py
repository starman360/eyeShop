from world_cam_receiver import PupilWorldStream
from pupil_info_receiver import PupilInfoStream
from pupil_blinks import PupilBlinksStream
import threading 
from queue import Queue

if __name__ == "__main__":

    q = Queue()

    pupil_info = PupilInfoStream(q)
    pupil_info.start()

    # pupil_blinks = PupilBlinksStream(q)
    # pupil_blinks.start()

    pupil = PupilWorldStream(q)
    pupil.start()

    pupil_info.join()
    # pupil_blinks.join()
