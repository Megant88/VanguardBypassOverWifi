import tkinter as tk
import ctypes, json
import time
import threading
import win32api
import socket
import pickle

with open(r"config.json") as json_file:
    data = json.load(json_file)
ip = data["misc_settings"]["ip"]
port = data["misc_settings"]["port"]
tcp_sleep = data["misc_settings"]["tcp_sleep"]

class FullScreenApp:
    def __init__(self, host, port):
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.configure(background='white')
        self.root.bind('<Motion>', self.on_mouse_motion)
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.center_x = self.screen_width // 2
        self.center_y = self.screen_height // 2
        self.prev_x = self.center_x
        self.prev_y = self.center_y
        self.mouse_movement = {"x": 0, "y": 0}
        self.mouse_button = None
        self.mouse5_state = False
        self.mouse6_state = False
        self.running = True
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

    def on_mouse_motion(self, event):
        rel_x = event.x - self.prev_x
        rel_y = event.y - self.prev_y

        max_movement = 256 #limits the value
        rel_x = max(min(rel_x, max_movement), -max_movement)
        rel_y = max(min(rel_y, max_movement), -max_movement)

        if event.x == self.center_x and event.y == self.center_y:
            rel_x = rel_y = 0  # resets mouse_movement (just in case)
        self.mouse_movement = {"x": rel_x, "y": rel_y}

    
    def get_button_state(self): #records all button states except 5/6 they have their own thread as we handle them seperately for the cheese :) (driver doesnt support these)
        while self.running:
            current_key = None
            if win32api.GetAsyncKeyState(0x01) < 0:
                current_key = "Left"
            elif win32api.GetAsyncKeyState(0x02) < 0:
                current_key = "Right"
            elif win32api.GetAsyncKeyState(0x04) < 0:
                current_key = "Middle"
                
            if current_key:
                self.mouse_button = current_key
            elif current_key == None:
                self.mouse_button = current_key
            time.sleep(0.0001)

    def check_mouse5(self):
        while self.running:
            if win32api.GetAsyncKeyState(0x05) < 0:
                self.mouse5_state = True
            else:
                self.mouse5_state = False
            time.sleep(0.001)

    def check_mouse6(self):
        while self.running:
            if win32api.GetAsyncKeyState(0x06) < 0:
                self.mouse6_state = True
            else:
                self.mouse6_state = False
            time.sleep(0.001)

    def reset_mouse_position(self):
        ctypes.windll.user32.SetCursorPos(self.center_x, self.center_y)
    
    def data_received_handler(self):
        while self.running:
            data = self.socket.recv(1024)
            if data:
                received_data = pickle.loads(data)  # Deserialize data and reset the position
                print("Received data:", received_data)
                self.reset_mouse_position()

    def run(self):
        mouse5_thread = threading.Thread(target=self.check_mouse5)
        mouse6_thread = threading.Thread(target=self.check_mouse6)
        data_received_thread = threading.Thread(target=self.data_received_handler)
        left_click_thread = threading.Thread(target=self.get_button_state)
        mouse5_thread.start()
        mouse6_thread.start()
        left_click_thread.start()

        print_thread = threading.Thread(target=self.print_state)
        print_thread.start()
        data_received_thread.start()

        self.root.mainloop()
        self.running = False

    def print_state(self): 
        last_state = None
        while self.running:
            state = {
                "mouse_movement": self.mouse_movement,
                "mouse_button": self.mouse_button,
                "mouse5": self.mouse5_state,
                "mouse6": self.mouse6_state
            }

            # this basically checks for any active movements (holding is considered active)
            if (state != last_state) or (self.mouse_movement["x"] != 0) or (self.mouse_movement["y"] != 0) or \
            (self.mouse_button is not None) or self.mouse5_state or self.mouse6_state:
                print(state)
                # send it to the server.py (main pc)
                self.socket.send(pickle.dumps(state))
                last_state = state

            self.mouse_movement = {"x": 0, "y": 0}
            time.sleep(tcp_sleep) #a sleep to stabilize
    
    


if __name__ == "__main__":

    remote_host = ip  
    remote_port = port  

    app = FullScreenApp(remote_host, remote_port)
    app.run()
