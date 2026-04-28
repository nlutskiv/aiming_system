# Aiming System

A hybrid **embedded vision + servo control** project built for a Year 3 microprocessors lab. The system tracks a **red target** using Python/OpenCV on a PC and sends position commands over **UART** to a **PIC18-based assembly program**, which generates a stable **50 Hz servo control signal** using timer-driven interrupts.

## Overview

This project is split into two parts:

- **PC-side vision and control** in Python:
  - detects a red object from a webcam feed
  - estimates horizontal image error relative to the frame centre
  - converts that error into servo pulse commands
  - sends updated PWM preload values to the microcontroller over UART
- **PIC18-side embedded firmware** in assembly:
  - supports **manual mode** using a potentiometer through the ADC
  - supports **automatic mode** using UART commands from the PC
  - generates the servo waveform using a custom interrupt-driven timing routine rather than a dedicated PWM peripheral. 

The repository also includes several experimental Python controllers for testing different tracking strategies, including proportional control, dynamic gain, prediction, and latency measurement. 

## Features

- **Manual / automatic mode switching**
  - manual mode reads a potentiometer via ADC
  - automatic mode receives position commands over UART. 
- **Red target detection**
  - HSV thresholding for red
  - contour filtering and centroid extraction. 
- **Custom servo timing**
  - interrupt-driven pulse generation
  - pulse range mapped approximately from **1.0 ms to 3.0 ms**
  - total frame period of **20 ms**. 
- **UART packet protocol**
  - command header + preload bytes for high and low portions of the waveform
  - sync packet sent from the microcontroller when entering automatic mode. 
- **Test scripts**
  - RMS tracking study
  - latency measurement
  - dynamic gain tuning
  - predictive control experiments. 

## Repository Structure

```text
aiming_system/
├── assembly/              # PIC18 assembly firmware
│   ├── main.s
│   ├── UART.s
│   ├── ADC.s
│   ├── ADC_To_Preload.s
│   ├── DAC_Interrupt.s
│   └── config.s
├── python_vision/         # PC-side vision + control scripts
│   ├── UART.py
│   ├── tracking.py
│   ├── main.py            # Baseline control loop      
│   ├── main_dynamic_kp.py # implemented control loop with tuned/dynamic K_p
│   ├── predictor_main.py  # experimental, predictive control loop
│   └── latency_measure.py
├── analysis/
├── latency_data.csv
├── Makefile
└── README.md
