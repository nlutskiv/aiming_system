import cv2
import time
import math
from tracking import find_red_target_x
from UART import UartLink

def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x

def main():
    PORT = "COM4"
    BAUD = 9600
    US_MIN, US_MAX, US_CENTER = 1000, 3000, 2000
    US_PER_DEGREE = 11.11 

    # --- TRACKING CONFIG ---
    K_P = 0.15            
    current_pan_us = US_CENTER
    zero_reference_us = US_CENTER 

    # INITIALIZE THESE HERE TO PREVENT UNBOUNDLOCALERROR
    last_send_time = 0.0  
    last_sent_us = US_CENTER
    last_error = 0
    est_pos = 0.0
    est_vel = 0.0

    # --- RMS STUDY VARIABLES ---
    is_studying = False
    study_start_time = 0
    study_duration = 10.0
    error_squared_sum = 0
    sample_count = 0

    uart = UartLink(PORT, BAUD)
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("Camera failed to open.")
        return

    print("CONTROLS: 's' to start 10s RMS Study | 'r' to reset 0-deg | ESC to quit")

    while True:
        while uart.ser.in_waiting >= 3:
            header = ord(uart.ser.read(1))
            #handshake -> synch the position
            if header == 0xAA:
                hi = ord(uart.ser.read(1))
                lo = ord(uart.ser.read(1))
                
                # 1. Combine to get the raw preload
                preload = (hi << 8) | lo
                
                # 2. Convert preload back to elapsed ticks
                ticks = 65535 - preload
                
                # 3. Convert ticks to microseconds (1 tick = 0.5us for 1:8 prescaler)
                # Adjust 0.5 if your clock/prescaler math is different!
                actual_us = int(ticks * 0.5) 
                
                current_pan_us = clamp(actual_us, US_MIN, US_MAX)
                
                # 4. Sync the rest of the tracking state
                last_sent_us = current_pan_us
                last_error = 0
                est_pos = 0.0
                est_vel = 0.0
                
                print(f"BUMPLESS TRANSFER: {ticks} ticks -> {current_pan_us}us")
                break
            else:
                # If it wasn't 0xAA, it's garbage. The loop continues to next byte.
                pass
        ret, frame = cap.read()
        if not ret: break
        h, w = frame.shape[:2]
        center_x = w // 2
        target_x, mask = find_red_target_x(frame)

        if target_x is not None:
            error = target_x - center_x
            
            # --- RMS DATA COLLECTION ---
            if is_studying:
                error_squared_sum += error**2
                sample_count += 1
                
                # Check if 10 seconds have passed
                elapsed = time.time() - study_start_time
                if elapsed >= study_duration:
                    # Final Calculation
                    if sample_count > 0:
                        rms_error = math.sqrt(error_squared_sum / sample_count)
                        print(f"\n--- STUDY COMPLETE ---")
                        print(f"KP: {K_P} | Samples: {sample_count} | RMS ERROR: {rms_error:.2f} px")
                    is_studying = False

            # Standard Tracking
            current_pan_us -= int(error * K_P)
            current_pan_us = clamp(current_pan_us, US_MIN, US_MAX)

            if (time.time() - last_send_time) > 0.05:
                uart.send_preloads_us(current_pan_us)
                last_send_time = time.time()

            cv2.circle(frame, (target_x, h // 2), 10, (0, 255, 0), 2)
        
        current_angle = (current_pan_us - zero_reference_us) / US_PER_DEGREE

        # --- UI / OSD ---
        color = (0, 255, 0) if target_x else (0, 0, 255)
        status = "TRACKING" if target_x else "SEARCHING"
        if is_studying:
            status = f"STUDYING... {study_duration - (time.time() - study_start_time):.1f}s"
            color = (0, 255, 255) # Yellow for active test

        cv2.putText(frame, f"STATUS: {status}", (20, 40), 1, 1.5, color, 2)
        cv2.putText(frame, f"ANGLE: {current_angle:+.1f} deg", (20, 80), 1, 1.2, (255, 255, 0), 2)
        
        cv2.imshow("Red Target Tracking", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 27: # ESC
            break
        elif key == ord('r'):
            zero_reference_us = current_pan_us
            print(f"Zero reset to {zero_reference_us} us")
        elif key == ord('s') and not is_studying:
            print("Starting 10-second RMS Study...")
            error_squared_sum = 0
            sample_count = 0
            study_start_time = time.time()
            is_studying = True

    cap.release()
    uart.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()