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
    US_CENTER = 2200 # Kept your center
    
    # --- CALIBRATION ---
    PX_PER_US = 1

    # --- HYPERPARAMETERS (UNCHANGED) ---
    ALPHA = 0.2      
    BETA  = 0.15      
    LEAD_FACTOR = 2.0 

    K_P = 0.12        
    K_V = 0.30        

    # State variables
    est_pos = 0.0
    est_vel = 0.0
    last_error = 0.0
    current_pan_us = US_CENTER
    last_sent_us = US_CENTER
    last_send_time = 0

    # --- RMS STUDY VARIABLES ---
    is_studying = False
    study_start_time = 0
    study_duration = 10.0
    error_squared_sum = 0
    sample_count = 0

    uart = UartLink(PORT, BAUD)
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened(): return

    print("--- EGO-COMPENSATED PREDICTOR ACTIVE ---")
    print("Press 'S' to start 10s RMS Study")

    while True:
        ret, frame = cap.read()
        if not ret: break

        h, w = frame.shape[:2]
        center_x = w // 2
        target_x, _ = find_red_target_x(frame)

        if target_x is not None:
            raw_error = target_x - center_x
            
            # 1. EGO-MOTION COMPENSATION
            camera_induced_motion = (current_pan_us - last_sent_us) * PX_PER_US
            
            # 2. CALCULATE 'TRUE' TARGET VELOCITY
            apparent_vel = raw_error - last_error
            true_vel = apparent_vel + camera_induced_motion
            
            # 3. ALPHA-BETA FILTER
            residual = raw_error - est_pos
            est_pos = est_pos + (ALPHA * residual)
            est_vel = (BETA * true_vel) + ((1 - BETA) * est_vel)
            
            # 4. PREDICTION
            predicted_error = est_pos + (est_vel * LEAD_FACTOR)

            # 5. RMS DATA COLLECTION
            if is_studying:
                error_squared_sum += raw_error**2
                sample_count += 1
                # Check if 10 seconds have passed
                if (time.time() - study_start_time) >= study_duration:
                    if sample_count > 0:
                        rms_px = math.sqrt(error_squared_sum / sample_count)
                        print(f"\n--- RMS STUDY COMPLETE ---")
                        print(f"Final RMS Error: {rms_px:.2f} px")
                    is_studying = False

            # 6. CONTROL LAW
            p_move = predicted_error * K_P
            v_move = est_vel * K_V
            
            # Save state for next frame
            last_error = raw_error
            last_sent_us = current_pan_us
            
            current_pan_us -= int(p_move + v_move)
            current_pan_us = clamp(current_pan_us, 1000, 3000)

            if (time.time() - last_send_time) > 0.05:
                uart.send_preloads_us(current_pan_us)
                last_send_time = time.time()

            # Visuals
            cv2.circle(frame, (target_x, h // 2), 10, (0, 255, 0), 2)
            pred_draw_x = int(center_x + predicted_error)
            cv2.circle(frame, (pred_draw_x, h // 2 + 40), 5, (255, 0, 255), -1)
        
        # UI Overlay
        if is_studying:
            cv2.putText(frame, "RECORDING RMS...", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        cv2.imshow("Ego-Compensated Predictor", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 27: # ESC to quit
            break
        elif key == ord('s') and not is_studying:
            print("Starting 10s study...")
            error_squared_sum = 0
            sample_count = 0
            study_start_time = time.time()
            is_studying = True

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()