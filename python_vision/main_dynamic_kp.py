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
    US_MIN, US_MAX, US_CENTER = 1000, 3000, 2300
    US_PER_DEGREE = 11.11 
    PX_PER_DEGREE = 10.67  # Your calculated calibration factor

    # --- CONTROL CONFIG ---
    K_P = 0.15          
    K_V = 0.10          # Start low (0.02 - 0.08) to fix the "lag"
    
    current_pan_us = US_CENTER
    zero_reference_us = US_CENTER 
    last_send_time = 0
    last_error = 0

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

    print(f"TESTING: KP={K_P}, KV={K_V}")
    print("CONTROLS: 's' to start 10s RMS Study | 'r' to reset 0-deg | ESC to quit")

    while True:
        ret, frame = cap.read()
        if not ret: break

        h, w = frame.shape[:2]
        center_x = w // 2
        target_x, mask = find_red_target_x(frame)

        if target_x is not None:
            error = target_x - center_x
            
            # --- VELOCITY CALCULATION ---
            # Current speed of the target relative to the camera
            target_velocity = error - last_error
            last_error = error
            
            # --- RMS DATA COLLECTION ---
            if is_studying:
                error_squared_sum += error**2
                sample_count += 1
                
                elapsed = time.time() - study_start_time
                if elapsed >= study_duration:
                    if sample_count > 0:
                        rms_px = math.sqrt(error_squared_sum / sample_count)
                        rms_deg = rms_px / PX_PER_DEGREE
                        print(f"\n--- STUDY COMPLETE ---")
                        print(f"Parameters: KP={K_P}, KV={K_V}")
                        print(f"RMS Error: {rms_px:.2f} px ({rms_deg:.2f} degrees)")
                    is_studying = False

            # --- CONTROL LAW: P + FEED-FORWARD ---
            p_term = error * K_P
            v_term = target_velocity * K_V
            
            current_pan_us -= int(p_term + v_term)
            current_pan_us = clamp(current_pan_us, US_MIN, US_MAX)

            if (time.time() - last_send_time) > 0.05:
                uart.send_preloads_us(current_pan_us)
                last_send_time = time.time()

            cv2.circle(frame, (target_x, h // 2), 10, (0, 255, 0), 2)
        else:
            # Reset last_error when target is lost to prevent velocity spikes
            last_error = 0
        
        current_angle = (current_pan_us - zero_reference_us) / US_PER_DEGREE

        # --- UI / OSD ---
        color = (0, 255, 0) if target_x else (0, 0, 255)
        status = "TRACKING" if target_x else "SEARCHING"
        if is_studying:
            status = f"STUDYING... {study_duration - (time.time() - study_start_time):.1f}s"
            color = (0, 255, 255)

        cv2.putText(frame, f"STATUS: {status}", (20, 40), 1, 1.5, color, 2)
        cv2.putText(frame, f"ANGLE: {current_angle:+.1f} deg", (20, 80), 1, 1.2, (255, 255, 0), 2)
        cv2.putText(frame, f"V-BOOST: {target_velocity*K_V if target_x else 0:+.1f}", (20, 115), 1, 1.0, (200, 200, 200), 1)
        
        cv2.imshow("Red Target Tracking", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 27: break
        elif key == ord('r'):
            zero_reference_us = current_pan_us
        elif key == ord('s') and not is_studying:
            error_squared_sum = sample_count = 0
            study_start_time = time.time()
            is_studying = True

    cap.release()
    uart.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()