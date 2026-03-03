#include <xc.inc>

global  ADC_To_Preloads_Exact
extrn   pre_hi_h, pre_hi_l, pre_lo_h, pre_lo_l

psect   udata_acs
a0:     ds 1        ; ADRESL
a1:     ds 1        ; (ADRESH & 0x03)
p0:     ds 1        ; 24-bit product p2:p1:p0
p1:     ds 1
p2:     ds 1
sh0:    ds 1        ; shifted product (>>10)
sh1:    ds 1
sh2:    ds 1
cnt:    ds 1
sc_l:   ds 1        ; scaled (0..2000) 16-bit
sc_h:   ds 1
ht_l:   ds 1        ; high_ticks (2000..4000) 16-bit
ht_h:   ds 1

psect   adc_map_code, class=CODE

; Call ADC_Read first (right-justified).
ADC_To_Preloads_Exact:

        ; Build adc10 = (a1:a0) where a1 = ADRESH & 0x03
        movff   ADRESL, a0
        movf    ADRESH, W, A
        andlw   0x03
        movwf   a1, A

        ; p = adc10 * 2000 (0x07D0), 24-bit p2:p1:p0
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

        ; scaled = (p >> 10)
        movff   p0, sh0
        movff   p1, sh1
        movff   p2, sh2
        movlw   10
        movwf   cnt, A
s10:    rrcf    sh2, F, A
        rrcf    sh1, F, A
        rrcf    sh0, F, A
        decfsz  cnt, F, A
        bra     s10

        ; scaled = sh1:sh0
        movff   sh0, sc_l
        movff   sh1, sc_h

        ; If adc10 == 1023 (a1==3 and a0==0xFF), force scaled=2000 (0x07D0)
        movf    a1, W, A
        xorlw   0x03
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
        btfsc   STATUS, 2, A     ; Z flag bit
        incf    pre_hi_h, F, A

        ; pre_lo = 0x63C0 + high_ticks
        movlw   0xC0
        addwf   ht_l, W, A
        movwf   pre_lo_l, A
        movlw   0x63
        addwfc  ht_h, W, A
        movwf   pre_lo_h, A

        bsf     GIE
        return

        end