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

        clrf    mode, A        ; default MANUAL (0)

main_loop:
        movf    mode, W, A
        bnz     auto_mode      ; if mode != 0 -> AUTO

manual_mode:
        call    ADC_Read       ; updates ADRESH:ADRESL (AN0 as currently set)
	
	call    ADC_To_Preloads_12bit

        goto    main_loop

auto_mode:
        ; TODO: UART read/parse later
        goto    main_loop

        end     rst