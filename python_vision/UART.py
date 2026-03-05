import serial
import time

class UartLink:
    def __init__(self, port: str, baud: int = 9600, timeout: float = 0.01):
        self.ser = serial.Serial(port, baud, timeout=timeout, write_timeout=0.5)
        time.sleep(0.5)

    @staticmethod
    def us_to_preloads(pulse_us: int):
        # tick = 0.5us => ticks = 2*us
        high_ticks = 2 * int(pulse_us)

        # safety clamp (optional, adjust)
        if high_ticks < 2000:  # 1.0ms
            high_ticks = 2000
        if high_ticks > 6000:  # 3.0ms
            high_ticks = 6000

        pre_hi = (65536 - high_ticks) & 0xFFFF
        pre_lo = (0x63C0 + high_ticks) & 0xFFFF  # 0x63C0 = 25536 = 65536-40000

        return pre_hi, pre_lo

    def send_preloads_us(self, pulse_us: int, verbose: bool = False):
        pre_hi, pre_lo = self.us_to_preloads(pulse_us)

        pkt = bytes([
            0xAA, 0x55,
            (pre_hi >> 8) & 0xFF, pre_hi & 0xFF,
            (pre_lo >> 8) & 0xFF, pre_lo & 0xFF,
        ])

        if verbose:
            print(f"TX us={pulse_us} pre_hi=0x{pre_hi:04X} pre_lo=0x{pre_lo:04X}")

        self.ser.write(pkt)

    def close(self):
        try:
            self.ser.close()
        except Exception:
            pass