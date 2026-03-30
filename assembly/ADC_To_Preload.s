#include <xc.inc>

global  ADC_To_Preloads_12bit
extrn   pre_hi_h, pre_hi_l, pre_lo_h, pre_lo_l   ; from PWM module

; -------------------------------------------------------------------------
; ADC_To_Preloads_12bit
;
; Purpose:
;   Converts the 12-bit ADC reading from the potentiometer into the Timer1
;   preload values used by the PWM interrupt routine for servo control.
;
; Behaviour:
;   - ADC input range:      0 to 4095
;   - Servo high pulse:     1.0 ms to 3.0 ms
;   - Total PWM period:     20 ms
;
; Method:
;   1. Read the 12-bit ADC result from ADRESH:ADRESL
;   2. Scale it into the range 0 to 4000 timer ticks
;   3. Add 2000 ticks so the final high pulse is 2000 to 6000 ticks
;      which corresponds to 1.0 ms to 3.0 ms
;   4. Convert the pulse widths into Timer1 preload values
;   5. Update the shared PWM preload registers safely with interrupts disabled
;
; Timer1 timing:
;   Fosc = 64 MHz
;   Instruction clock = Fosc/4 = 16 MHz
;   Timer1 prescaler = 1:8
;   Timer1 tick = 0.5 us
;
; Therefore:
;   1.0 ms  = 2000 ticks
;   3.0 ms  = 6000 ticks
;   20.0 ms = 40000 ticks
;
; The PWM module expects preload values rather than raw tick counts, so:
;   preload = 65536 - required_ticks
;
; -------------------------------------------------------------------------

psect   udata_acs
a0:     ds 1        ; Lower 8 bits of ADC result (ADRESL)
a1:     ds 1        ; Upper 4 bits of ADC result (ADRESH & 0x0F)

p0:     ds 1        ; 24-bit product p2:p1:p0 = adc12 * 4000
p1:     ds 1
p2:     ds 1

sh0:    ds 1        ; Temporary copy of product for right-shifting by 12 bits
sh1:    ds 1
sh2:    ds 1

cnt:    ds 1        ; Shift counter

sc_l:   ds 1        ; 16-bit scaled value in range 0 to 4000
sc_h:   ds 1

ht_l:   ds 1        ; 16-bit high pulse width in ticks: 2000 to 6000
ht_h:   ds 1

psect   adc_map_code, class=CODE


ADC_To_Preloads_12bit:


        ; Read the 12-bit ADC result.
        ; ADRESL contains bits D0-D7
        ; ADRESH contains bits D8-D11 in its lower nibble
        movff   ADRESL, a0
        movf    ADRESH, W, A
        andlw   0x0F
        movwf   a1, A

        ; p = adc12 * 4000 (0x0FA0), into p2:p1:p0
        ; 0x0FA0 => m1=0x0F, m0=0xA0
        ; p = a0*0xA0 + (a0*0x0F)<<8 + (a1*0xA0)<<8 + (a1*0x0F)<<16

        movlw   0xA0
        mulwf   a0, A
        movff   PRODL, p0
        movff   PRODH, p1
        clrf    p2, A

        movlw   0x0F
        mulwf   a0, A
        movf    PRODL, W, A
        addwf   p1, F, A
        movf    PRODH, W, A
        addwfc  p2, F, A

        movlw   0xA0
        mulwf   a1, A
        movf    PRODL, W, A
        addwf   p1, F, A
        movf    PRODH, W, A
        addwfc  p2, F, A

        movlw   0x0F
        mulwf   a1, A
        movf    PRODL, W, A
        addwf   p2, F, A

        ; scaled = (p >> 12)  ~ (adc12 * 4000)/4096
        movff   p0, sh0
        movff   p1, sh1
        movff   p2, sh2
        movlw   12
        movwf   cnt, A
s12:    rrcf    sh2, F, A
        rrcf    sh1, F, A
        rrcf    sh0, F, A
        decfsz  cnt, F, A
        bra     s12

        movff   sh0, sc_l
        movff   sh1, sc_h

        ; endpoint fix: if adc12 == 0x0FFF => scaled = 4000 exactly (0x0FA0)
        movf    a1, W, A
        xorlw   0x0F
        bnz     not_max
        movf    a0, W, A
        xorlw   0xFF
        bnz     not_max
        movlw   0xA0
        movwf   sc_l, A
        movlw   0x0F
        movwf   sc_h, A
not_max:

        ; high_ticks = 2000 + scaled  (0x07D0 + sc)
        movlw   0xD0
        addwf   sc_l, W, A
        movwf   ht_l, A
        movlw   0x07
        addwfc  sc_h, W, A
        movwf   ht_h, A

        bcf     GIE

        ; pre_hi = 0x10000 - high_ticks = (~high)+1
        movf    ht_l, W, A
        comf    WREG, W, A
        movwf   pre_hi_l, A
        movf    ht_h, W, A
        comf    WREG, W, A
        movwf   pre_hi_h, A
        incf    pre_hi_l, F, A
        btfsc   STATUS, 2, A          ; Z flag bit2
        incf    pre_hi_h, F, A

        ; pre_lo = 0x63C0 + high_ticks  (keeps 20ms frame)
        movlw   0xC0
        addwf   ht_l, W, A
        movwf   pre_lo_l, A
        movlw   0x63
        addwfc  ht_h, W, A
        movwf   pre_lo_h, A

        bsf     GIE
        return

        end