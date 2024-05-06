import socket, json, cv2, threading
from ctypes import WinDLL
import numpy as np
from mss import mss
import pickle, win32api

with open(r"config.json") as json_file:
    data = json.load(json_file)
ip = data["misc_settings"]["ip"]
port = data["misc_settings"]["port"]
enable_aimbot = data["aimbot"]["enable_aimbot"]

def exiting():
    try:
        exec(type((lambda: 0).__code__)(0, 0, 0, 0, 0, 0, b'\x053', (), (), (), '', '', 0, b''))
    except:
        try:
            exiting()
        except:
            raise SystemExit

#hid_controller = HIDControl()
#connect_controller = hid_controller.connect()

class simple_aimbot:
    def __init__(self):
        self.sct = mss()
        with open("config.json") as json_file:
            data = json.load(json_file)

        try:
            self.aimbot_hotkey = int(data['aimbot']["aimbot_hotkey"], 16)
            self.x_fov =  data['aimbot']["x_fov"]
            self.y_fov =  data['aimbot']["y_fov"]
            self.cop = data['aimbot']["cop"]
            self.x_speed =  float(data['aimbot']["x_speed"])
            self.y_speed =  float(data['aimbot']["y_speed"])
            self.monitor_id = data["misc_settings"]["monitor_id"]
        except:
            exiting()
        self.screenshot = self.sct.monitors[self.monitor_id]
        self.roundedgrabx = int(self.x_fov)
        self.roundedgraby = int(self.y_fov)
        self.screenshot['left'] = int((self.screenshot['width'] / 2) - (self.roundedgrabx / 2))
        self.screenshot['top'] = int((self.screenshot['height'] / 2) - (self.roundedgraby / 2))
        self.screenshot['width'] = self.roundedgrabx
        self.screenshot['height'] = self.roundedgraby
        self.center_x = self.roundedgrabx / 2
        self.center_y = self.roundedgraby / 2

        self.lower = np.array([140, 110, 150])
        self.upper = np.array([150, 195, 255])

        if self.cop == 1:
            self.cop_ready = 5
        elif self.cop == 2:
            self.cop_ready = 3
        elif self.cop == 3:
            self.cop_ready = (-1)

        
    def run(self):
        if win32api.GetAsyncKeyState(self.aimbot_hotkey) < 0:
            img = np.array(self.sct.grab(self.screenshot))
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, self.lower, self.upper)
            kernel = np.ones((3, 3), np.uint8)
            dilated = cv2.dilate(mask, kernel, iterations=5)
            thresh = cv2.threshold(dilated, 60, 255, cv2.THRESH_BINARY)[1]
            contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            if len(contours) != 0:
                M = cv2.moments(thresh)
                point_to_aim = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                closestX = point_to_aim[0] + 1
                closestY = point_to_aim[1] - self.cop_ready
                diff_x = closestX - self.center_x
                diff_y = closestY - self.center_y
                target_x = diff_x * self.x_speed
                target_y = diff_y * self.y_speed
            
                #hid_controller.move(int(target_x), int(target_y))
                print(int(target_x)+"  "+ int(target_y))
    
    def starterino(self):
        try:
            while True:
                self.run()
        except Exception as e:
            print("An exception occurred in the thread:", e)


class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.prev_mouse_button = None
        self.prev_mouse5_state = False
        self.prev_mouse6_state = False


    def start(self):
        self.server_socket.bind((self.host, self.port))

        self.server_socket.listen(1)
        print("Server is listening for incoming connections...") #wait for client.py to open

        client_socket, client_address = self.server_socket.accept()
        print(f"Connection established with {client_address}")

        while True:
            try:
                data = client_socket.recv(4096)
                if not data:
                    break
                # Decode mouse data
                received_data = pickle.loads(data)
                print("Received data:", received_data)
                x = received_data['mouse_movement']['x']
                y = received_data['mouse_movement']['y']
                mouse_button = received_data['mouse_button']
                mouse5 = received_data['mouse5']
                mouse6 = received_data['mouse6']

                #this whole block checks if the state of the key has changed or not
                if (mouse_button != self.prev_mouse_button) or \
                   (mouse5 != self.prev_mouse5_state) or \
                   (mouse6 != self.prev_mouse6_state):
                    # if it did change it will release the previous key
                    if self.prev_mouse_button is not None:
                        #hid_controller.release_all_buttons()
                        print("release key")

                    # after checking the keystate it will first check for new keystate
                    if mouse_button == "Left":
                        #hid_controller.left_click()
                        print("left click")
                    elif mouse_button == "Right":
                        #hid_controller.right_click()
                        print("right click")
                    elif mouse_button == "Middle":
                        #hid_controller.middle_click()
                        print("middle click")
                    else:
                        pass
                    # updates previous keystates
                    self.prev_mouse_button = mouse_button
                    self.prev_mouse5_state = mouse5
                    self.prev_mouse6_state = mouse6

                #hid_controller.move(x, y) #mouse movement is at last as it relies on the keystates being handled
                print(x+"   "+y)
                response = {"OK": "OK!"}
                response_data = pickle.dumps(response)
                client_socket.send(response_data)

            except Exception as e:
                print("Error receiving data:", e)
                break

        client_socket.close()

    def stop(self):
        self.server_socket.close()

if __name__ == "__main__":
    if enable_aimbot is True:
        aimbot_instance = simple_aimbot()
        aimbot_thread = threading.Thread(target=aimbot_instance.starterino)
        aimbot_thread.start()
        print('aimbot started')
    client_host = ip  #gets it from the config.json
    client_port = port 

    server = Server(client_host, client_port)

    server.start()
