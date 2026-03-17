#include <xc.inc>

extrn   PWM_Setup, PWM_Int_Hi
extrn   ADC_Read
extrn   pre_hi_h, pre_hi_l, pre_lo_h, pre_lo_l
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
last_mode: ds 1      ; NEW: To detect the flip

psect   code, abs

rst:    org     0x0000
        goto    start

int_hi: org     0x0008
        goto    PWM_Int_Hi

start:
    bcf TRISJ,0,A 
    clrf rx_state, A
    clrf rx_idx, A
    call    PWM_Setup
    call    ADC_Setup  
    call    UART_Setup
    bsf     TRISB, 0, A          
    bcf     INTCON2, 7, A        
    clrf    mode, A        
    clrf    last_mode, A     ; Start in manual

main_loop:
    btfss   PORTB, 0, A          
    bra     auto_mode
    bra     manual_mode

manual_mode:
    clrf    last_mode, A     ; Keep last_mode 0 while in manual
    call    ADC_Read       
    call    ADC_To_Preloads_12bit
    goto    main_loop

auto_mode:
    ; --- THE SYNC TRIGGER (Minimal Change) ---
    movf    last_mode, W, A
    bnz     skip_sync        ; If last_mode was already 1, we already synced.
    
    ; Send sync packet ONCE
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
    btfss   PIR1, 5, A       ; Now check if Python is sending data
    goto    main_loop

    call    UART_Read_Byte
    xorlw   0xAA
    bnz     main_loop         

wait_55:
    btfss   PIR1, 5, A
    bra     wait_55                
    call    UART_Read_Byte
    xorlw   0x55
    bnz     main_loop              

    call    Wait_And_Read
    movwf   temp_hi_h, A     
    call    Wait_And_Read
    movwf   temp_hi_l, A
    call    Wait_And_Read
    movwf   temp_lo_h, A
    call    Wait_And_Read
    movwf   temp_lo_l, A

    bcf     INTCON, 7, A     
    movff   temp_hi_h, pre_hi_h
    movff   temp_hi_l, pre_hi_l
    movff   temp_lo_h, pre_lo_h
    movff   temp_lo_l, pre_lo_l
    bsf     INTCON, 7, A     
    goto    main_loop

Wait_And_Read:
    btfss   PIR1, 5, A
    bra     Wait_And_Read
    goto    UART_Read_Byte