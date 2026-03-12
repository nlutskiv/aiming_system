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
    US_MIN, US_MAX, US_CENTER = 1000, 3000, 1500
    US_PER_DEGREE = 11.11 
    PX_PER_DEGREE = 10.67 

    # --- ADVANCED NON-LINEAR CONFIG ---
    K_P = 0.15            
    K_V = 0.4             # Slightly lowered to help stability
    LEAD_MAX = 6.0        # Predictive look-ahead (frames)
    VEL_DEADBAND = 2.5    # Ignore movement noise below this pixel threshold
    LPF_ALPHA = 0.35      # 0.35 = 35% new data, 65% old. Smooths out sensor noise.
    
    current_pan_us = US_CENTER
    last_send_time = 0
    last_error = 0
    smooth_vel = 0        # Filtered velocity memory

    # --- RMS STUDY ---
    is_studying = False
    study_start_time = 0
    study_duration = 10.0
    error_squared_sum = 0
    sample_count = 0

    uart = UartLink(PORT, BAUD)
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened(): return

    print("--- NON-LINEAR PREDICTIVE TRACKER ACTIVE ---")

    while True:
        ret, frame = cap.read()
        if not ret: break

        h, w = frame.shape[:2]
        center_x = w // 2
        target_x, mask = find_red_target_x(frame)

        if target_x is not None:
            error = target_x - center_x
            
            # 1. LOW-PASS FILTERED VELOCITY
            # This kills the "twitch" by smoothing out frame-to-frame noise
            raw_vel = error - last_error
            smooth_vel = (LPF_ALPHA * raw_vel) + ((1.0 - LPF_ALPHA) * smooth_vel)
            last_error = error
            
            # 2. DYNAMIC LEAD (NON-LINEAR)
            # Only predict if the target is actually moving with intent
            if abs(smooth_vel) > VEL_DEADBAND:
                predicted_error = error + (smooth_vel * LEAD_MAX)
            else:
                predicted_error = error # Stationary = no prediction

            # --- RMS DATA COLLECTION ---
            if is_studying:
                error_squared_sum += error**2
                sample_count += 1
                if (time.time() - study_start_time) >= study_duration:
                    if sample_count > 0:
                        rms_px = math.sqrt(error_squared_sum / sample_count)
                        print(f"\n--- STUDY COMPLETE ---")
                        print(f"RMS: {rms_px:.2f} px | Lead Used: {LEAD_MAX}")
                    is_studying = False

            # --- CONTROL LAW ---
            p_move = predicted_error * K_P
            v_move = smooth_vel * K_V
            
            current_pan_us -= int(p_move + v_move)
            current_pan_us = clamp(current_pan_us, US_MIN, US_MAX)

            if (time.time() - last_send_time) > 0.05:
                uart.send_preloads_us(current_pan_us)
                last_send_time = time.time()

            # Target Visuals
            cv2.circle(frame, (target_x, h // 2), 10, (0, 255, 0), 2)
            if abs(smooth_vel) > VEL_DEADBAND:
                # Ghost dot showing where the computer is aiming
                cv2.circle(frame, (int(center_x + predicted_error), h // 2 + 40), 5, (255, 0, 255), -1)
        else:
            smooth_vel = 0
            last_error = 0
        
        # --- UI ---
        status = "STUDYING" if is_studying else "STABLE-PREDICT"
        cv2.putText(frame, f"STATUS: {status}", (20, 40), 1, 1.5, (0, 255, 255), 2)
        cv2.putText(frame, f"SMOOTH_V: {smooth_vel:.1f}", (20, 80), 1, 1.0, (200, 200, 200), 1)
        
        cv2.imshow("Advanced Lead-Predictor", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 27: break
        elif key == ord('s') and not is_studying:
            error_squared_sum = sample_count = 0
            study_start_time = time.time()
            is_studying = True

    cap.release()
    uart.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()