import socketio
class Socket(object):
    def __init__(self):
        super().__init__()

        self.sio = socketio.Client()
        self.sio.connect("http://10.2.6.170:3000")

    def send(self, key, data):
        self.sio.emit(key, data)


if __name__ == "__main__":
    soc = Socket()
    key = ""
    while True:   
        i = input()
        if 'key#' in i:
            key = i.replace("key#", "")
            print("Send", key)
            soc.send("sync", {'key' : key, 'payload': True})
        else:
            soc.send("barcode", {'key' : key, 'payload': i})