#include <xc.inc>

extrn   PWM_Setup, PWM_Int_Hi
extrn   ADC_Read
extrn   pre_hi_h, pre_hi_l, pre_lo_h, pre_lo_l
extrn	ADC_Setup
extrn	ADC_To_Preloads_12bit
extrn	UART_Read_Byte, UART_Setup

psect   udata_acs
rx_state:  ds 1      ; 0=waitAA, 1=wait55, 2=data
rx_idx:    ds 1      ; 0..3
temp_hi_h: ds 1
temp_hi_l: ds 1
temp_lo_h: ds 1
temp_lo_l: ds 1
mode:   ds 1            ; 0 = MANUAL, 1 = AUTO

psect   code, abs

rst:    org     0x0000
        goto    start

int_hi: org     0x0008
        goto    PWM_Int_Hi

start:
	bcf TRISJ,0,A ;useless
	clrf rx_state, A
	clrf rx_idx, A
        call    PWM_Setup
	call	ADC_Setup  
	call	UART_Setup
	; delay if does not work
	bsf     TRISB, 0, A          ; RB0 input
        bcf     INTCON2, 7, A        ; enable PORTB pull-ups (RBPU=0)

        clrf    mode, A        ; default MANUAL (0)

main_loop:
        btfss   PORTB, 0, A          ; if RB0==0 -> AUTO
        bra     auto_mode
        bra     manual_mode

manual_mode:
        call    ADC_Read       ; updates ADRESH:ADRESL (AN0 as currently set)
	
	call    ADC_To_Preloads_12bit

        goto    main_loop

auto_mode:
    ; 1. Check if a byte is even there. If not, go back to main loop
    btfss   PIR1, 5, A            
    goto    main_loop

    ; 2. Look for Header 0xAA
    call    UART_Read_Byte
    xorlw   0xAA
    bnz     main_loop             ; Not our header? Exit and try again

wait_55:
    ; 3. Wait (block briefly) for the 0x55. 
    ; Using a "Wait" instead of "Exit" ensures we don't lose sync.
    btfss   PIR1, 5, A
    bra     wait_55               
    call    UART_Read_Byte
    xorlw   0x55
    bnz     main_loop             ; If 2nd byte isn't 0x55, packet is corrupt

    ; 4. Collect the 4 data bytes. 
    ; Once we have 0xAA 0x55, we MUST read the next 4 bytes.
    
    call    Wait_And_Read
    movwf   temp_hi_h, A     ; Save to temp
    call    Wait_And_Read
    movwf   temp_hi_l, A
    call    Wait_And_Read
    movwf   temp_lo_h, A
    call    Wait_And_Read
    movwf   temp_lo_l, A

    ; NOW copy all at once (Atomic-ish)
    bcf     INTCON, 7, A     ; Disable Global Interrupts (GIE is bit 7)
    movff   temp_hi_h, pre_hi_h
    movff   temp_hi_l, pre_hi_l
    movff   temp_lo_h, pre_lo_h
    movff   temp_lo_l, pre_lo_l
    bsf     INTCON, 7, A     ; Re-enable Global Interrupts
    goto    main_loop

; Helper to avoid code duplication
Wait_And_Read:
    btfss   PIR1, 5, A
    bra     Wait_And_Read
    goto    UART_Read_Byte