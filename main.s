#include <xc.inc>

extrn   PWM_Setup, PWM_Int_Hi
extrn   ADC_Read
extrn   pre_hi_h, pre_hi_l, pre_lo_h, pre_lo_l
extrn	ADC_Setup
extrn	ADC_To_Preloads_12bit

psect   udata_acs
mode:   ds 1            ; 0 = MANUAL, 1 = AUTO

psect   code, abs

rst:    org     0x0000
        goto    start

int_hi: org     0x0008
        goto    PWM_Int_Hi

start:
        call    PWM_Setup
	call	ADC_Setup  
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
        ; TODO: UART read/parse later
        ; force servo to centre (~1.5ms high) while in AUTO
        bcf     GIE

        movlw   0xF4
        movwf   pre_hi_h, A
        movlw   0x48
        movwf   pre_hi_l, A

        movlw   0x6F
        movwf   pre_lo_h, A
        movlw   0x78
        movwf   pre_lo_l, A

        bsf     GIE
        goto    main_loop