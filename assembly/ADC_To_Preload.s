#include <xc.inc>

global  ADC_To_Preloads_12bit
extrn   pre_hi_h, pre_hi_l, pre_lo_h, pre_lo_l

; Maps ADRESH (0-255) to Timer1 servo preloads.
; high_ticks = 2000 + (ADRESH * 16)  -> range 2000 to 6080 ticks
; pre_hi = 65536 - high_ticks
; pre_lo = 25536 + high_ticks  (sum = 40000 ticks = 20ms period)
; Timer1 tick = 0.5us  (Fosc=64MHz, prescaler 1:8)

psect   udata_acs
ht_l:   ds 1
ht_h:   ds 1

psect   adc_map_code, class=CODE

ADC_To_Preloads_12bit:

    ; ADRESH * 16 using mulwf
    ; PRODH:PRODL = ADRESH * 0x10
    movlw   0x10
    mulwf   ADRESH, A

    ; high_ticks = 2000 + PRODH:PRODL  (0x07D0 + product)
    movlw   0xD0
    addwf   PRODL, W, A
    movwf   ht_l, A
    movlw   0x07
    addwfc  PRODH, W, A
    movwf   ht_h, A

    ; disable interrupts before updating shared preload registers
    bcf     GIE

    ; pre_hi = 65536 - high_ticks  (two's complement negate)
    comf    ht_l, W, A
    movwf   pre_hi_l, A
    comf    ht_h, W, A
    movwf   pre_hi_h, A
    incf    pre_hi_l, F, A
    btfsc   STATUS, STATUS_Z_POSN, A
    incf    pre_hi_h, F, A

    ; pre_lo = 25536 + high_ticks  (0x63C0 + high_ticks)
    movlw   0xC0
    addwf   ht_l, W, A
    movwf   pre_lo_l, A
    movlw   0x63
    addwfc  ht_h, W, A
    movwf   pre_lo_h, A

    bsf     GIE
    return

    end
