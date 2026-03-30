#include <xc.inc>

;external routines and shared variables
extrn   PWM_Setup, PWM_Int_Hi
extrn   ADC_Read
extrn   pre_hi_h, pre_hi_l, pre_lo_h, pre_lo_l ; control the servo position via weird clock1 math
extrn   ADC_Setup
extrn   ADC_To_Preloads_12bit
extrn   UART_Read_Byte, UART_Setup, UART_Transmit_Byte

psect   udata_acs
rx_state:  ds 1      
rx_idx:    ds 1      
temp_hi_h: ds 1
temp_hi_l: ds 1
temp_lo_h: ds 1
temp_lo_l: ds 1
mode:      ds 1      
last_mode: ds 1      ; Stores previous operating mode so mode changes can be detected

psect   code, abs

rst:    org     0x0000
        goto    start
; High-priority interrupt vector
; Servo PWM timing is handled in the interrupt routine
int_hi: org     0x0008  
        goto    PWM_Int_Hi

start:
    ; Set RJ0 as an output (PMW outupt for servo control)
    bcf TRISJ,0,A 
    ; Clear software state variables
    clrf rx_state, A
    clrf rx_idx, A
    ; Initialise peripherals
    call    PWM_Setup
    call    ADC_Setup  
    call    UART_Setup
    ; RB0 is used as the mode-select input:
    ; RB0 = 1 -> manual mode
    ; RB0 = 0 -> automatic mode
    bsf     TRISB, 0, A 
    ; Enable PORTB internal pull-ups
    bcf     INTCON2, 7, A     
    ; Start in manual mode by default
    clrf    mode, A        
    clrf    last_mode, A     ; Start in manual

main_loop:
    ; Check the mode-select switch on RB0
    ; If RB0 is low, enter automatic mode
    ; If RB0 is high, stay in manual mode
    btfss   PORTB, 0, A          
    bra     auto_mode
    bra     manual_mode

manual_mode:
    ; In manual mode the ADC potentiometer directly controls servo position.
    ; last_mode is cleared so that if the user switches into automatic
    clrf    last_mode, A     ; Keep last_mode 0 while in manual
    
    ; Read the analogue input and convert it into servo preload values
    call    ADC_Read       
    call    ADC_To_Preloads_12bit
    goto    main_loop

auto_mode:
    ; On first entry into automatic mode, send one sync packet to Python.
    ; This allows the PC side to initialise its commanded position using
    ; the current servo state, avoiding a sudden jump when auto mode starts.
    movf    last_mode, W, A
    bnz     skip_sync        ; If last_mode was already 1, we already synced.
    
    ; Sync packet format:
    ;   0xAA, pre_hi_h, pre_hi_l
    ; Only the high pulse preload is sent here, which is enough for the
    ; PC side to recover the current commanded servo position (cuz full width is 20ms)
    movlw   0xAA
    call    UART_Transmit_Byte
    movf    pre_hi_h, W, A
    call    UART_Transmit_Byte
    movf    pre_hi_l, W, A
    call    UART_Transmit_Byte
    
    movlw   1
    movwf   last_mode, A     ; Mark that sync is DONE
    ; -----------------------------------------

skip_sync:
     ; Check whether a UART byte has arrived from the PC.
    ; If not, return to the top of the loop.
    btfss   PIR1, 5, A       
    goto    main_loop
    
    ; First byte of the incoming command packet must be 0xAA
    call    UART_Read_Byte
    xorlw   0xAA
    bnz     main_loop         

wait_55:
    ; Second byte of the packet must be 0x55
    ; Wait here until another byte arrives
    btfss   PIR1, 5, A
    bra     wait_55                
    call    UART_Read_Byte
    xorlw   0x55
    bnz     main_loop              

    ; Read four payload bytes:
    ; temp_hi_h, temp_hi_l, temp_lo_h, temp_lo_l
    ; These represent the new PWM preload values for the servo timing.
    
    call    Wait_And_Read
    movwf   temp_hi_h, A     
    call    Wait_And_Read
    movwf   temp_hi_l, A
    call    Wait_And_Read
    movwf   temp_lo_h, A
    call    Wait_And_Read
    movwf   temp_lo_l, A

    ; Copy the received preload values into the active PWM registers.
    ; Global interrupts are briefly disabled so the interrupt routine
    ; cannot read a partially updated set of bytes.
    
    bcf     INTCON, 7, A     
    movff   temp_hi_h, pre_hi_h
    movff   temp_hi_l, pre_hi_l
    movff   temp_lo_h, pre_lo_h
    movff   temp_lo_l, pre_lo_l
    bsf     INTCON, 7, A     
    goto    main_loop

Wait_And_Read:
    ; Wait until a UART byte has been received, then return it in W
    btfss   PIR1, 5, A
    bra     Wait_And_Read
    goto    UART_Read_Byte