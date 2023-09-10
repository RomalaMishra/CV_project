import cv2
import time
import numpy as np
import HandTrack as htm
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as sbc

class VolumeControl:
    def __init__(self):
        # Initialize camera properties
        self.wCam, self.hCam = 1280, 780
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, self.wCam)
        self.cap.set(4, self.hCam)
        self.pTime = 0

        # Initialize hand detection model
        self.detector = htm.handDetector(detectionCon=0.7)

        # Initialize audio volume control
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(interface, POINTER(IAudioEndpointVolume))

    def run(self):
        # Get volume range
        minVol, maxVol = self.volume.GetVolumeRange()
        vol = 0
        volBar = 400
        volPer = 0

        while True:
            success, img = self.cap.read()
            img = self.detector.findHands(img)
            lmList = self.detector.findPosition(img, draw=False)
            
            if len(lmList) != 0:
                # Hand gesture for volume control
                x1, y1 = lmList[4][1], lmList[4][2]
                x2, y2 = lmList[8][1], lmList[8][2]
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                # Calculate the length between fingers for volume control
                length = math.hypot(x2 - x1, y2 - y1)
                vol = np.interp(length, [50, 300], [minVol, maxVol])
                volBar = np.interp(length, [50, 300], [400, 150])
                volPer = np.interp(length, [50, 300], [0, 100])

                print(int(length), vol)
                self.volume.SetMasterVolumeLevel(vol, None)

                # Hand gesture for brightness control
                x11, y11 = lmList[4][1], lmList[4][2]
                x22, y22 = lmList[20][1], lmList[20][2]
                cxx, cyy = (x11 + x22) // 2, (y11 + y22) // 2

                # Calculate the length between fingers for brightness control
                lengthB = math.hypot(x22 - x11, y22 - y11)
                bri = np.interp(lengthB, [50, 300], [0, 100])
                briBar = np.interp(lengthB, [150, 300], [400, 150])
                briPer = np.interp(lengthB, [150, 300], [0, 100])

                # Adjust screen brightness
                sbc.set_brightness(int(lengthB), display=0)

                if length < 50:
                    cv2.circle(img, (cx, cy), 15, (0, 255, 0), cv2.FILLED)

            # Draw UI elements on the screen
            cv2.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 3)
            cv2.rectangle(img, (50, int(volBar)), (85, 400), (255, 0, 0), cv2.FILLED)
            cv2.putText(img, f'{int(volPer)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX,
                        1, (255, 0, 0), 3)

            cTime = time.time()
            fps = 1 / (cTime - self.pTime)
            self.pTime = cTime
            cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_COMPLEX,
                        1, (255, 0, 0), 3)

            # Display the image
            cv2.imshow("Img", img)
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break    

        cv2.destroyAllWindows()

if __name__ == "__main__":
    # Create an instance of the HandGestureControl class and run the application
    gesture_control = VolumeControl()
    gesture_control.run()
