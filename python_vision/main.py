import cv2
import time
import csv
import threading
import queue
from tracking import find_red_target_x
from UART import UartLink

# Thread-safe queue for terminal input
input_queue = queue.Queue()

def get_input():
    while True:
        val = input("Enter SCOPE Pulse (us) to START: ")
        input_queue.put(val)

def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x

def main():
    PORT = "COM4"
    BAUD = 9600
    US_MIN, US_MAX, US_CENTER = 1000, 3000, 1500
    US_PER_DEGREE = 11.11 

    K_P = 0.12            
    current_pan_us = US_CENTER
    zero_reference_us = US_CENTER 
    last_send_time = 0

    is_auto = False  # Start in IDLE
    is_measuring = False
    test_start_time = None
    test_results = []

    uart = UartLink(PORT, BAUD)
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("Camera failed to open.")
        return

    # Start the input thread so it doesn't freeze the camera
    threading.Thread(target=get_input, daemon=True).start()

    print("\n--- READY ---")
    print("1. Move Pot until Angle is 30.0 (or whatever you need).")
    print("2. Type the Scope pulse width in this console and hit ENTER.")

    while True:
        ret, frame = cap.read()
        if not ret: break

        h, w = frame.shape[:2]
        center_x = w // 2
        target_x, mask = find_red_target_x(frame)

        # Check if the user typed something in the terminal
        if not input_queue.empty():
            val = input_queue.get()
            try:
                current_pan_us = clamp(int(val), US_MIN, US_MAX)
                is_auto = True
                is_measuring = True
                test_start_time = time.time()
                print(f"TEST STARTED at {current_pan_us}us. Flip PIC to AUTO now!")
            except ValueError:
                print("Invalid number. Type an integer pulse width.")

        if target_x is not None:
            error = target_x - center_x
            
            if is_auto:
                # 1. AUTO: Tracking and Sending
                current_pan_us -= int(error * K_P)
                current_pan_us = clamp(current_pan_us, US_MIN, US_MAX)

                if (time.time() - last_send_time) > 0.05:
                    uart.send_preloads_us(current_pan_us)
                    last_send_time = time.time()
                
                # 2. MEASURE: Stop timer when error is low
                if is_measuring and abs(error) < 8:
                    duration = time.time() - test_start_time
                    print(f"LOCKED: {duration:.3f}s")
                    test_results.append([K_P, duration])
                    is_measuring = False
                    is_auto = False # Go back to IDLE for next run
            else:
                # 3. IDLE: Calculate angle from pixels so you can line up the shot
                # We assume physical center is 1500 while you're holding it
                current_pan_us = US_CENTER - int(error * 1.1)

            cv2.circle(frame, (target_x, h // 2), 10, (0, 255, 0), 2)
        
        current_angle = (current_pan_us - zero_reference_us) / US_PER_DEGREE

        # OSD
        color = (0, 255, 0) if is_auto else (0, 0, 255)
        status = "AUTO - TRACKING" if is_auto else "IDLE - SET POT"
        
        cv2.putText(frame, status, (20, 40), 1, 1.5, color, 2)
        cv2.putText(frame, f"ANGLE: {current_angle:+.1f} deg", (20, 80), 1, 1.2, (255, 255, 0), 2)
        
        if is_measuring:
            cv2.putText(frame, "RECORDING...", (20, 120), 1, 1.0, (0, 255, 255), 2)

        cv2.line(frame, (center_x, 0), (center_x, h), (255, 255, 255), 1)
        cv2.imshow("Red Target Tracking", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 27: break
        elif key == ord('r'):
            zero_reference_us = current_pan_us
            print("Zero Reset.")

    if test_results:
        with open('latency_data.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["KP", "Seconds"])
            writer.writerows(test_results)

    cap.release()
    uart.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()