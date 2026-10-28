# Aiming System

Embedded vision and servo control project from my Year 3 microprocessors lab. A webcam and Python/OpenCV find a red target, and a PIC18 running assembly turns a servo to keep it in the centre of the frame. Commands go from the PC to the PIC over UART, and the PIC generates the 50 Hz servo signal itself with timer interrupts.

## How it works

PC side (Python):
- detects a red object in the webcam feed (HSV thresholding, morphological open/close, ignores small blobs)
- measures the horizontal error from the frame centre
- turns that error into a servo pulse width
- sends the new timer preload values to the PIC over UART, rate limited to 20 Hz

PIC18 side (assembly):
- manual mode: a potentiometer read through the ADC sets the servo position
- automatic mode: position commands come from the PC over UART
- the servo waveform is generated with Timer1 overflow interrupts instead of the PWM peripheral (20 ms period, pulse roughly 1 to 3 ms, 0.5 µs timer ticks)
- when switching into automatic mode, the PIC sends a sync packet with its current position so the PC starts from there and the servo doesn't jump
- the four timing bytes are updated with interrupts disabled, so the interrupt never uses a half-updated value

UART packets are `0xAA 0x55` followed by four preload bytes (high and low parts of the waveform).

## Controllers

- `main.py`: proportional control, plus a 10 s RMS tracking error test (press `s`)
- `main_dynamic_kp.py`: proportional control with an added velocity term to reduce lag
- `predictor_main.py`: experimental alpha-beta filter that predicts where the target is going and corrects for the camera's own movement
- `latency_measure.py`: measures how long the system takes to lock onto the target

## Results

`latency_measure.py` starts the servo from a set position and times how long it takes until the target is within 12 px of the centre and has stopped moving. I ran 57 trials over different proportional gains (`latency_data.csv`):

| K_P | runs | median lock time (s) |
|-----|------|----------------------|
| 0.03 | 1 | 2.94 |
| 0.08 | 5 | 1.07 |
| 0.09 | 5 | 0.79 |
| 0.10 | 1 | 0.69 |
| 0.105 | 5 | 1.17 |
| 0.11 | 1 | 0.69 |
| 0.12 | 7 | 1.07 |
| 0.13 | 6 | 1.07 |
| 0.14 | 6 | 1.05 |
| 0.15 | 5 | 1.42 |
| 0.16 | 5 | 1.46 |
| 0.17 | 5 | 1.46 |
| 0.25 | 5 | 2.99 |

Gains around 0.09 to 0.11 locked fastest, at about 0.7 to 0.8 s. Lower gains were slow, and higher gains overshot and oscillated before settling. One run at 0.12 took 22 s and is an outlier (the median ignores it).

## Running it

Python needs `opencv-python`, `numpy` and `pyserial`. The serial port is set at the top of each script (`COM4` by default). The firmware is an MPLAB X project (`nbproject/`, `Makefile`).

## Structure

```text
aiming_system/
├── assembly/              # PIC18 assembly firmware
│   ├── main.s             # main loop, mode switching, UART packet handling
│   ├── UART.s
│   ├── ADC.s
│   ├── ADC_To_Preload.s   # potentiometer reading to servo timing
│   ├── DAC_Interrupt.s    # Timer1 interrupt servo signal
│   └── config.s
├── python_vision/         # PC-side vision and control
│   ├── UART.py
│   ├── tracking.py        # red target detection
│   ├── main.py
│   ├── main_dynamic_kp.py
│   ├── predictor_main.py
│   └── latency_measure.py
├── latency_data.csv
├── Makefile
└── README.md
```
