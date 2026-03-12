import cv2
import time
import csv
import threading
import queue
from tracking import find_red_target_x
from UART import UartLink

input_queue = queue.Queue()

def get_input():
    while True:
        val = input("\nEnter SCOPE Pulse (us) to START: ")
        input_queue.put(val)

def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x

def main():
    PORT = "COM4"
    BAUD = 9600
    US_MIN, US_MAX, US_CENTER = 1000, 3000, 1500
    US_PER_DEGREE = 11.11 

    # --- TRACKING CONFIG ---
    K_P = 0.3      
    MIN_STEP = 2          # Prevents asymptotic stall
    lock_threshold = 12    # Position window
    velocity_threshold = 2 # Speed window (px per frame)
    timeout_limit = 10.0   # Emergency stop for infinite oscillation
    
    current_pan_us = US_CENTER
    zero_reference_us = US_CENTER 
    last_send_time = 0
    last_error = 0

    is_auto = False
    is_measuring = False
    test_start_time = None
    test_results = []

    uart = UartLink(PORT, BAUD)
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("Camera failed to open.")
        return

    threading.Thread(target=get_input, daemon=True).start()

    while True:
        ret, frame = cap.read()
        if not ret: break

        h, w = frame.shape[:2]
        center_x = w // 2
        target_x, mask = find_red_target_x(frame)

        if not input_queue.empty():
            val = input_queue.get()
            try:
                current_pan_us = clamp(int(val), US_MIN, US_MAX)
                is_auto = True
                is_measuring = True
                test_start_time = time.time()
                print(f"RUNNING: Start @ {current_pan_us}us")
            except ValueError: pass

        if target_x is not None:
            error = target_x - center_x
            
            # Calculate Velocity (pixels per frame)
            velocity = abs(error - last_error)
            last_error = error
            
            if is_auto:
                # 1. Proportional Move + Min Step Hack
                p_move = int(error * K_P)
                if abs(error) > 2:
                    if p_move == 0:
                        p_move = 1 if error > 0 else -1
                    elif abs(p_move) < MIN_STEP:
                        p_move = MIN_STEP if error > 0 else -MIN_STEP

                current_pan_us -= p_move
                current_pan_us = clamp(current_pan_us, US_MIN, US_MAX)

                # 2. UART Rate Limit
                if (time.time() - last_send_time) > 0.05:
                    uart.send_preloads_us(current_pan_us)
                    last_send_time = time.time()
                
                # 3. PURE POSITIONAL + VELOCITY LOCK
                elapsed = time.time() - test_start_time
                if is_measuring:
                    if abs(error) <= lock_threshold and velocity <= velocity_threshold:
                        print(f"DONE: {elapsed:.3f}s (Speed: {velocity})")
                        test_results.append([K_P, elapsed])
                        is_measuring = False
                        is_auto = False
                    elif elapsed > timeout_limit:
                        print("TIMEOUT: Oscillation too high to lock.")
                        is_measuring = False
                        is_auto = False
            else:
                # Idle shadowing
                current_pan_us = US_CENTER - int(error * 1.1)

            cv2.circle(frame, (target_x, h // 2), 10, (0, 255, 0) if is_auto else (0,0,255), 2)
            # Threshold lines (visual aid for the lock zone)
            cv2.line(frame, (center_x - lock_threshold, 0), (center_x - lock_threshold, h), (0, 255, 255), 1)
            cv2.line(frame, (center_x + lock_threshold, 0), (center_x + lock_threshold, h), (0, 255, 255), 1)
        
        # Angle Calculation
        current_angle = (current_pan_us - zero_reference_us) / US_PER_DEGREE
        
        # UI OSD
        mode_str = "AUTO" if is_auto else "IDLE"
        cv2.putText(frame, f"MODE: {mode_str}", (20, 40), 1, 1.5, (0, 255, 0), 2)
        cv2.putText(frame, f"ANG: {current_angle:+.1f} deg", (20, 80), 1, 1.2, (255, 255, 0), 2)
        cv2.putText(frame, f"PULSE: {current_pan_us} us", (20, 115), 1, 1.0, (200, 200, 200), 1)
        
        cv2.imshow("Red Target Tracking", frame)

        if cv2.waitKey(1) & 0xFF == 27: break

    if test_results:
        with open('latency_data.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(test_results)

    cap.release()
    uart.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()