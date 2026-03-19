#include <xc.inc>

global  PWM_Setup, PWM_Int_Hi
global pre_hi_h, pre_hi_l, pre_lo_h, pre_lo_l
    
; State variable used by the interrupt routine:
; 0 -> the next phase loaded will be the low interval
; 1 -> the next phase loaded will be the high interval

STATE   equ 0x20        

; Default Timer1 preload values for a 20 ms servo period
; Timer tick = 0.5 us
   
; High pulse: 1.5 ms = 3000 ticks
; Timer preload = 65536 - 3000 = 0xF448
; The values below are the chosen defaults for the initial centred position
   
HIGH_PRE_H equ 0xF4
HIGH_PRE_L equ 0x48

; Low pulse: 18.5 ms = 37000 ticks
; Together with the high pulse this gives a total period of about 20 ms
 
LOW_PRE_H  equ 0x73
LOW_PRE_L  equ 0x60


psect   udata_acs
pre_hi_h:   ds 1        ; High-byte of Timer1 preload for the high pulse
pre_hi_l:   ds 1        ; Low-byte of Timer1 preload for the high pulse
pre_lo_h:   ds 1        ; High-byte of Timer1 preload for the low interval
pre_lo_l:   ds 1        ; Low-byte of Timer1 preload for the low interval

psect   pwm_code, class=CODE

PWM_Int_Hi:
        ; Check whether the interrupt was caused by Timer1 overflow.
        ; If not, return
        btfss   TMR1IF
        retfie  f
	; Clear the Timer1 interrupt flag before scheduling the next interval
        bcf     TMR1IF          

        movf    STATE, W, A
        bz      do_low

do_high:
         ; Start the high pulse on RJ0
        bsf     LATJ, 0, A
	; Load Timer1 so that the next overflow occurs after the required
        ; high-pulse duration
        movff   pre_hi_h, TMR1H
        movff   pre_hi_l, TMR1L
	; After finishing the high pulse, the next phase will be low
        clrf    STATE, A         
        retfie  f

do_low:
        ; End the pulse by driving RJ0 low
        bcf     LATJ, 0, A
	
	; Load Timer1 for the low interval between servo pulses
        movff   pre_lo_h, TMR1H
        movff   pre_lo_l, TMR1L
	; After the low interval, the next phase will be high
        movlw   0x01
        movwf   STATE, A         
        retfie  f


PWM_Setup:
        ; Configure RJ0 as a digital output and initialise it low
        clrf    TRISJ, A
        clrf    LATJ, A

        ; Timer1 configuration:
        ; - clock source = internal instruction clock (Fosc/4)
        ; - prescaler = 1:8
        ; - timer enabled
        clrf    T1CON, A
        bsf     T1CKPS0
        bsf     T1CKPS1          ; prescale = 1:8
        bcf     TMR1CS0          ; ensure internal clock (Fosc/4)
        bcf     TMR1CS1
        bsf     TMR1ON

        ; Load default pulse timing values into RAM.
        ; These values can later be overwritten by ADC input or UART commands.
        movlw   HIGH_PRE_H
        movwf   pre_hi_h, A
        movlw   HIGH_PRE_L
        movwf   pre_hi_l, A

        movlw   LOW_PRE_H
        movwf   pre_lo_h, A
        movlw   LOW_PRE_L
        movwf   pre_lo_l, A

        ; Begin with the output low.
        ; The first interrupt will occur after the low interval,
        ; at which point the high pulse starts.
        clrf    STATE, A
        bcf     LATJ, 0, A

        ; Load Timer1 with the initial low-interval preload
        movff   pre_lo_h, TMR1H
        movff   pre_lo_l, TMR1L

        ; Enable Timer1 interrupt and then enable peripheral/global interrupts
        bcf     TMR1IF           
        bsf     TMR1IE           
        bsf     PEIE             ; enable peripheral interrupts
        bsf     GIE              ; enable global interrupts

        return

        end