
#include <xc.inc>

global  ADC_To_Preloads_10bit

; These live in your PWM module (must be `global` there)
extrn   pre_hi_h, pre_hi_l, pre_lo_h, pre_lo_l

psect   udata_acs
a0:     ds 1            ; ADRESL
a1:     ds 1            ; ADRESH (masked to 0..3)
p0:     ds 1            ; 24-bit product p2:p1:p0 = ADC * 2000
p1:     ds 1
p2:     ds 1
sh0:    ds 1            ; shifted copy for >>10
sh1:    ds 1
sh2:    ds 1
cnt:    ds 1
ht_l:   ds 1            ; high_ticks (16-bit)
ht_h:   ds 1

psect   adc_map_code, class=CODE

; ------------------------------------------------------------
; ADC_To_Preloads_10bit
; Call ADC_Read first (ADRESH:ADRESL updated, right-justified).
; Output: pre_hi_*, pre_lo_* updated atomically.
; ------------------------------------------------------------
ADC_To_Preloads_10bit:

        ; a0 = ADRESL
        movff   ADRESL, a0
        ; a1 = ADRESH & 0x03 (10-bit result => only bits1:0 meaningful)
        movf    ADRESH, W, A
        andlw   0x03
        movwf   a1, A

        ; ---- p = ADC * 2000 (0x07D0), keep 24-bit p2:p1:p0 ----
        ; p = a0*m0 + 256*(a0*m1 + a1*m0) + 65536*(a1*m1)
        ; where m0=0xD0, m1=0x07

        ; p = a0 * 0xD0
        movlw   0xD0
        mulwf   a0, A            ; PRODH:PRODL = a0*0xD0
        movff   PRODL, p0
        movff   PRODH, p1
        clrf    p2, A

        ; add (a0 * 0x07) << 8
        movlw   0x07
        mulwf   a0, A
        movf    PRODL, W, A
        addwf   p1, F, A
        movf    PRODH, W, A
        addwfc  p2, F, A

        ; add (a1 * 0xD0) << 8
        movlw   0xD0
        mulwf   a1, A
        movf    PRODL, W, A
        addwf   p1, F, A
        movf    PRODH, W, A
        addwfc  p2, F, A

        ; add (a1 * 0x07) << 16  (only affects p2; high byte is always 0 here)
        movlw   0x07
        mulwf   a1, A
        movf    PRODL, W, A
        addwf   p2, F, A

        ; ---- scaled = (p >> 10)  (24-bit shift, take low 16 bits) ----
        movff   p0, sh0
        movff   p1, sh1
        movff   p2, sh2

        movlw   10
        movwf   cnt, A
shift10:
        rrcf    sh2, F, A
        rrcf    sh1, F, A
        rrcf    sh0, F, A
        decfsz  cnt, F, A
        bra     shift10

        ; scaled is now in sh1:sh0 (<= ~2000)
        ; high_ticks = 2000 (0x07D0) + scaled
        movlw   0xD0
        addwf   sh0, W, A
        movwf   ht_l, A
        movlw   0x07
        addwfc  sh1, W, A
        movwf   ht_h, A

        ; ---- pre_hi = 0x10000 - high_ticks = (~high_ticks)+1 ----
        movf    ht_l, W, A
        comf    WREG, W, A
        movwf   pre_hi_l, A
        movf    ht_h, W, A
        comf    WREG, W, A
        movwf   pre_hi_h, A
        incf    pre_hi_l, F, A
        btfsc   STATUS, 2, A     ; Z flag (bit2) set if low wrapped
        incf    pre_hi_h, F, A

        ; ---- pre_lo = 0x63C0 + high_ticks ----
        ; (25536 = 0x63C0 = 0x10000 - 40000)
        movlw   0xC0
        addwf   ht_l, W, A
        movwf   pre_lo_l, A
        movlw   0x63
        addwfc  ht_h, W, A
        movwf   pre_lo_h, A

        return

        end