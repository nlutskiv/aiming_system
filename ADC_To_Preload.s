#include <xc.inc>

global  ADC_To_Preloads_12bit
extrn   pre_hi_h, pre_hi_l, pre_lo_h, pre_lo_l   ; from PWM module

; tick = 0.5us (Fosc=64MHz, Fosc/4=16MHz, prescale=8 => 2MHz tick)
; 1.0ms => 2000 ticks
; 2.0ms => 4000 ticks
; 20ms  => 40000 ticks

psect   udata_acs
a0:     ds 1        ; ADRESL
a1:     ds 1        ; ADRESH & 0x0F  (top 4 bits of 12-bit result)
p0:     ds 1        ; 24-bit product p2:p1:p0 = adc12 * 2000
p1:     ds 1
p2:     ds 1
sh0:    ds 1        ; shifted product (>>12)
sh1:    ds 1
sh2:    ds 1
cnt:    ds 1
sc_l:   ds 1        ; scaled 0..2000 (16-bit)
sc_h:   ds 1
ht_l:   ds 1        ; high_ticks 2000..4000 (16-bit)
ht_h:   ds 1

psect   adc_map_code, class=CODE

; ------------------------------------------------------------
; ADC_To_Preloads_12bit
; Uses 12-bit ADC (0..0x0FFF). Output:
;   HIGH pulse: 1.000ms..2.000ms exactly over full ADC range
; ------------------------------------------------------------
ADC_To_Preloads_12bit:

        ; a0 = ADRESL (D0..D7)
        movff   ADRESL, a0

        ; a1 = ADRESH & 0x0F (D8..D11)
        movf    ADRESH, W, A
        andlw   0x0F
        movwf   a1, A

        ; p = adc12 * 2000 (0x07D0), into p2:p1:p0
        ; adc12 = a1*256 + a0
        ; p = a0*0xD0 + (a0*0x07)<<8 + (a1*0xD0)<<8 + (a1*0x07)<<16

        movlw   0xD0
        mulwf   a0, A
        movff   PRODL, p0
        movff   PRODH, p1
        clrf    p2, A

        movlw   0x07
        mulwf   a0, A
        movf    PRODL, W, A
        addwf   p1, F, A
        movf    PRODH, W, A
        addwfc  p2, F, A

        movlw   0xD0
        mulwf   a1, A
        movf    PRODL, W, A
        addwf   p1, F, A
        movf    PRODH, W, A
        addwfc  p2, F, A

        movlw   0x07
        mulwf   a1, A
        movf    PRODL, W, A
        addwf   p2, F, A

        ; scaled = (p >> 12)  ~ (adc12 * 2000)/4096
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

        ; endpoint fix: if adc12 == 0x0FFF => scaled = 2000 exactly (0x07D0)
        movf    a1, W, A
        xorlw   0x0F
        bnz     not_max
        movf    a0, W, A
        xorlw   0xFF
        bnz     not_max
        movlw   0xD0
        movwf   sc_l, A
        movlw   0x07
        movwf   sc_h, A
not_max:

        ; high_ticks = 2000 + scaled  (0x07D0 + sc)
        movlw   0xD0
        addwf   sc_l, W, A
        movwf   ht_l, A
        movlw   0x07
        addwfc  sc_h, W, A
        movwf   ht_h, A

        ; atomic update
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