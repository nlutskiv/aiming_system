import cv2
import time
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

def get_blob_radius_and_center(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None, None, None

    # largest contour assumed to be the target
    c = max(contours, key=cv2.contourArea)
    (x, y), radius = cv2.minEnclosingCircle(c)
    return int(x), int(y), radius

def main():
    PORT = "COM4"
    BAUD = 9600
    US_MIN, US_MAX, US_CENTER = 1000, 3000, 1500
    US_PER_DEGREE = 11.11

    # --- TRACKING CONFIG ---
    K_P = 0.09
    MIN_STEP = 2
    lock_threshold = 12
    velocity_threshold = 2
    timeout_limit = 10.0

    current_pan_us = US_CENTER
    zero_reference_us = US_CENTER
    last_send_time = 0
    last_error = 0

    is_auto = False
    is_measuring = False
    test_start_time = None

    uart = UartLink(PORT, BAUD)
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("Camera failed to open.")
        uart.close()
        return

    threading.Thread(target=get_input, daemon=True).start()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        h, w = frame.shape[:2]
        center_x = w // 2

        target_x, mask = find_red_target_x(frame)
        circle_x, circle_y, radius = (None, None, None)

        if mask is not None:
            circle_x, circle_y, radius = get_blob_radius_and_center(mask)

        if not input_queue.empty():
            val = input_queue.get()
            try:
                current_pan_us = clamp(int(val), US_MIN, US_MAX)
                is_auto = True
                is_measuring = True
                test_start_time = time.time()
                last_error = 0
                print(f"RUNNING: Start @ {current_pan_us}us")
            except ValueError:
                pass

        current_error = None
        velocity = 0

        if target_x is not None and radius is not None:
            error = target_x - center_x
            current_error = error

            # velocity in px/frame
            velocity = abs(error - last_error)
            last_error = error

            if is_auto:
                # proportional control + minimum step
                p_move = int(error * K_P)

                if abs(error) > 2:
                    if p_move == 0:
                        p_move = 1 if error > 0 else -1
                    elif abs(p_move) < MIN_STEP:
                        p_move = MIN_STEP if error > 0 else -MIN_STEP

                current_pan_us -= p_move
                current_pan_us = clamp(current_pan_us, US_MIN, US_MAX)

                # UART rate limit
                if (time.time() - last_send_time) > 0.05:
                    uart.send_preloads_us(current_pan_us)
                    last_send_time = time.time()

                # lock check
                elapsed = time.time() - test_start_time
                if is_measuring:
                    if abs(error) <= lock_threshold and velocity <= velocity_threshold:
                        final_offset_px = error
                        final_abs_error_px = abs(error)

                        print(
                            f"DONE: {elapsed:.3f}s | "
                            f"Error = {final_abs_error_px} px | "
                            f"Offset = {final_offset_px:+d} px | "
                            f"Radius = {radius:.1f} px"
                        )

                        is_measuring = False
                        is_auto = False

                    elif elapsed > timeout_limit:
                        print("TIMEOUT: Oscillation too high to lock.")
                        is_measuring = False
                        is_auto = False

            else:
                # idle shadowing
                current_pan_us = US_CENTER - int(error * 1.1)

            # draw centroid marker
            cv2.circle(frame, (target_x, h // 2), 10, (0, 255, 0) if is_auto else (0, 0, 255), 2)

            # draw detected enclosing circle
            cv2.circle(frame, (circle_x, circle_y), int(radius), (255, 0, 0), 2)
            cv2.circle(frame, (circle_x, circle_y), 3, (255, 0, 0), -1)

            # lock zone lines
            cv2.line(frame, (center_x - lock_threshold, 0), (center_x - lock_threshold, h), (0, 255, 255), 1)
            cv2.line(frame, (center_x + lock_threshold, 0), (center_x + lock_threshold, h), (0, 255, 255), 1)

        # angle calculation
        current_angle = (current_pan_us - zero_reference_us) / US_PER_DEGREE

        # UI OSD
        mode_str = "AUTO" if is_auto else "IDLE"
        cv2.putText(frame, f"MODE: {mode_str}", (20, 40), 1, 1.5, (0, 255, 0), 2)
        cv2.putText(frame, f"ANG: {current_angle:+.1f} deg", (20, 80), 1, 1.2, (255, 255, 0), 2)
        cv2.putText(frame, f"PULSE: {current_pan_us} us", (20, 115), 1, 1.0, (200, 200, 200), 1)

        if current_error is not None:
            cv2.putText(frame, f"ERR: {current_error:+d} px", (20, 150), 1, 1.0, (0, 255, 255), 2)

        if radius is not None:
            cv2.putText(frame, f"RADIUS: {radius:.1f} px", (20, 185), 1, 1.0, (255, 0, 0), 2)

        cv2.imshow("Red Target Tracking", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    uart.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()