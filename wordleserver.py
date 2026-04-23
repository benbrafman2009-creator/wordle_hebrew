import os

import const
import socket
import threading
import random


class HandelCommunication(threading.Thread):
    def __init__(self, cli_socket, tid):
        with open("index.dic", encoding="utf-8") as f:
            self.dictionary = [line.split("/")[0] for line in f.read().splitlines()]
        super().__init__(daemon=True)
        self.cli = cli_socket
        self.tid = tid
        self.word = ""
        self.rooms ={}
    def run(self):
        print("New Client num " + str(self.tid))
        exit_thread = False
        user_name = ""
        while not exit_thread:
            data = self.raw_recv()
            if len(data) >5 and data[0:5] == const.play_solo:
                self.gen_word(int(data.split(";")[1]))
                self.raw_send(const.start_solo_game)
            color_set = ""
            if len(data) > 4 and data[0:4] == const.word and self.word != "":
                cliword = data[4:]
                print(self.word)
                for cl,l in zip(cliword,self.word):
                    if cl == l:
                        color_set += "g"
                    elif cl in self.word:
                        color_set +="y"
                    else:
                        color_set += "b"
                self.raw_send(const.color+color_set)
            if len(data) > 3 and data[:3] == "צור":# working with hebrew in python is really hard
                parts = data.split(";")
                print(parts)
                game_type = parts[1]
                room_name = parts[0][3:]
                self.rooms[room_name] = int(game_type)
            if len(data) == 5 and data == const.ask_for_rooms:
                self.raw_send(self.rooms.keys())
    def raw_send(self, bdata, flags=0):
        if type(bdata) != bytes:
            bdata = bdata.encode()
        header_data = str(len(bdata)).zfill(const.size_header_size - 1).encode() + b"|"
        self.cli.send(header_data + bdata)
        if const.TCP_DEBUG:
            print(f"\nSent {len(bdata)})>>>{bdata[:const.LEN_TO_PRINT]}")
    def raw_recv(self, buffersize=2048, flags=0):
        size_header = b''
        while len(size_header) < const.size_header_size:
            chunk = self.cli.recv(const.size_header_size - len(size_header), flags)
            if not chunk:
                return ''
            size_header += chunk
            try:
                data_len = int(size_header[:const.size_header_size - 1])
            except ValueError:
                return ''
            data = b''
            while len(data) < data_len:
                chunk = self.cli.recv(data_len - len(data), flags)
                if not chunk:
                    return ''
                data += chunk
                if const.TCP_DEBUG:
                    print(f"\nRecv({data_len})>>>{data[:const.LEN_TO_PRINT]}")
                return data.decode()

    def gen_word(self,word_len):
        self.word = random.choice([row for row in self.dictionary if len(row) == word_len])
def main():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", const.PORT))
    s.listen(4)
    print(f"Server listening on port {const.PORT}...")

    threads = []
    i = 1

    try:
        while True:
            cli_s, addr = s.accept()
            print(f"Connection from {addr}")
            handler = HandelCommunication(cli_s, i)
            handler.start()
            threads.append(handler)
            i += 1
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        for t in threads:
            t.join(timeout=1)
        s.close()
        print("Bye ..")
if __name__ == '__main__':
    main()
