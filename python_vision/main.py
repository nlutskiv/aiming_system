# main.py
import cv2
from tracking import find_red_target_x
from UART import UartLink

def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x

def main():
    # ---- UART settings ----
    PORT = "COM4"     # change to your port
    BAUD = 9600

    # ---- Servo limits (safe range you used on PIC) ----
    US_MIN = 1000
    US_MAX = 3000
    US_CENTER = 1500

    # ---- Controller gain (tune) ----
    KP_US_PER_PIXEL = 1.0

    # ---- Smoothing (prevents jitter) ----
    alpha = 0.2
    pan_us_filt = US_CENTER

    uart = UartLink(PORT, BAUD)
    cap = cv2.VideoCapture(0)  # if Windows issues, try: cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("Camera failed to open.")
        uart.close()
        return

    print("Running. ESC to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        h, w = frame.shape[:2]
        center_x = w // 2

        target_x, mask = find_red_target_x(frame)

        if target_x is not None:
            err = target_x - center_x

            # pixel error -> microseconds
            pan_us = US_CENTER + int(KP_US_PER_PIXEL * err)
            pan_us = clamp(pan_us, US_MIN, US_MAX)

            # smooth
            pan_us_filt = int((1 - alpha) * pan_us_filt + alpha * pan_us)

            # send binary preloads packet: AA 55 hiH hiL loH loL
            uart.send_preloads_us(pan_us_filt, verbose=True)

            # debug overlay
            cv2.circle(frame, (target_x, h // 2), 8, (0, 255, 0), 2)
            cv2.putText(frame, f"err={err}  us={pan_us_filt}",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "no target",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

        # center line
        cv2.line(frame, (center_x, 0), (center_x, h), (255, 255, 255), 1)

        cv2.imshow("frame", frame)
        cv2.imshow("mask", mask)

        if (cv2.waitKey(1) & 0xFF) == 27:
            break

    cap.release()
    uart.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()