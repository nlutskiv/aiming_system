#include <xc.inc>

global  PWM_Setup, PWM_Int_Hi
global pre_hi_h, pre_hi_l, pre_lo_h, pre_lo_l

STATE   equ 0x20        ; 0 => next set LOW phase, 1 => next set HIGH phase

; Preloads for Timer1 overflow (tick = 0.5us)
; HIGH duration 1.5ms => 3000 ticks => preload 0xF060 (example defaults you used)
HIGH_PRE_H equ 0xF0
HIGH_PRE_L equ 0x60

; LOW duration 18.5ms => 37000 ticks => preload 0x7360 (example defaults you used)
LOW_PRE_H  equ 0x73
LOW_PRE_L  equ 0x60

; ---- NEW: 4 bytes in RAM for variable preloads ----
psect   udata_acs
pre_hi_h:   ds 1        ; HIGH phase preload high byte
pre_hi_l:   ds 1        ; HIGH phase preload low byte
pre_lo_h:   ds 1        ; LOW  phase preload high byte
pre_lo_l:   ds 1        ; LOW  phase preload low byte

psect   pwm_code, class=CODE

PWM_Int_Hi:
        ; Was it Timer1 overflow?
        btfss   TMR1IF
        retfie  f

        bcf     TMR1IF           ; clear flag

        movf    STATE, W, A
        bz      do_low

do_high:
        ; Drive RJ0 HIGH, schedule HIGH duration (variable)
        bsf     LATJ, 0, A

        movff   pre_hi_h, TMR1H
        movff   pre_hi_l, TMR1L

        clrf    STATE, A         ; next time do_low
        retfie  f

do_low:
        ; Drive RJ0 LOW, schedule LOW duration (variable)
        bcf     LATJ, 0, A

        movff   pre_lo_h, TMR1H
        movff   pre_lo_l, TMR1L

        movlw   0x01
        movwf   STATE, A         ; next time do_high
        retfie  f


PWM_Setup:
        ; RJ0 output
        clrf    TRISJ, A
        clrf    LATJ, A

        ; ---- Timer1 config: Fosc/4, prescale 1:8, enable ----
        clrf    T1CON, A
        bsf     T1CKPS0
        bsf     T1CKPS1          ; prescale = 1:8
        bcf     TMR1CS0          ; ensure internal clock (Fosc/4)
        bcf     TMR1CS1
        bsf     TMR1ON

        ; ---- NEW: initialise variable preloads to defaults ----
        movlw   HIGH_PRE_H
        movwf   pre_hi_h, A
        movlw   HIGH_PRE_L
        movwf   pre_hi_l, A

        movlw   LOW_PRE_H
        movwf   pre_lo_h, A
        movlw   LOW_PRE_L
        movwf   pre_lo_l, A

        ; Start with LOW first (RJ0 low) then go HIGH on first interrupt
        clrf    STATE, A
        bcf     LATJ, 0, A

        ; Load initial delay = LOW duration so first interrupt happens after LOW time
        movff   pre_lo_h, TMR1H
        movff   pre_lo_l, TMR1L

        ; Enable Timer1 interrupt (PIE1), and global/peripheral enables (INTCON)
        bcf     TMR1IF           ; clear any pending flag
        bsf     TMR1IE           ; enable Timer1 interrupt
        bsf     PEIE             ; enable peripheral interrupts
        bsf     GIE              ; enable global interrupts

        return

        end