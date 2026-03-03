#include <xc.inc>

; Externs: these live in your PWM module and must be declared `global` there
extrn   pre_hi_h, pre_hi_l, pre_lo_h, pre_lo_l

global  ADC_To_Preloads
    

; tick = 0.5us
; 20ms frame  => 40000 ticks = 0x9C40
; 1.0ms high  =>  2000 ticks = 0x07D0
; Map (approx): high_ticks = 2000 + 8*ADRESH  (ADRESH=0..255 => +0..2040)
; So high_ticks ? 2000..4040 (~1.00ms..2.02ms)

psect   udata_acs
var_l:      ds 1    ; low byte of (8*ADRESH)
var_h:      ds 1    ; high byte of (8*ADRESH)
hi_l:       ds 1    ; high_ticks low byte
hi_h:       ds 1    ; high_ticks high byte
lo_l:       ds 1    ; low_ticks low byte
lo_h:       ds 1    ; low_ticks high byte
tmp_l:      ds 1
tmp_h:      ds 1

psect   adc_map_code, class=CODE

; ------------------------------------------------------------
; ADC_To_Preloads
; Inputs : ADRESH:ADRESL already updated (call ADC_Read first)
; Output : pre_hi_h/l and pre_lo_h/l updated for Timer1 ISR
; ------------------------------------------------------------
ADC_To_Preloads:

        ; ---- var = 8*ADRESH (16-bit) ----
        clrf    var_h, A
        movf    ADRESH, W, A
        movwf   var_l, A

        ; left shift by 3: var_l/var_h <<= 3
        rlcf    var_l, F, A
        rlcf    var_h, F, A
        rlcf    var_l, F, A
        rlcf    var_h, F, A
        rlcf    var_l, F, A
        rlcf    var_h, F, A

        ; ---- high_ticks = 0x07D0 + var ----
        movlw   0xD0
        addwf   var_l, W, A      ; W = 0xD0 + var_l
        movwf   hi_l, A
        movlw   0x07
        addwfc  var_h, W, A      ; W = 0x07 + var_h + carry
        movwf   hi_h, A

        ; ---- low_ticks = 0x9C40 - high_ticks ----
        ; lo = 0x9C40 - hi
        movlw   0x40
        subwf   hi_l, W, A       ; W = 0x40 - hi_l
        movwf   lo_l, A
        movlw   0x9C
        subwfb  hi_h, W, A       ; W = 0x9C - hi_h - borrow
        movwf   lo_h, A

        ; ---- pre_hi = 0x10000 - high_ticks = (~high_ticks)+1 ----
        movf    hi_l, W, A
        comf    WREG, W, A
        movwf   tmp_l, A
        movf    hi_h, W, A
        comf    WREG, W, A
        movwf   tmp_h, A
        incf    tmp_l, F, A
        btfsc   STATUS, 2, A
        incf    tmp_h, F, A      ; add carry if low wrapped

        ; ---- pre_lo = 0x10000 - low_ticks = (~low_ticks)+1 ----
        movf    lo_l, W, A
        comf    WREG, W, A
        movwf   lo_l, A          ; reuse lo_l/lo_h as preload storage
        movf    lo_h, W, A
        comf    WREG, W, A
        movwf   lo_h, A
        incf    lo_l, F, A
	btfsc   STATUS, 2, A
        incf    lo_h, F, A

        ; ---- atomic update of the 4 bytes used by ISR ----
        bcf     GIE

        ; HIGH preload bytes from tmp_h:tmp_l
        movff   tmp_h, pre_hi_h
        movff   tmp_l, pre_hi_l

        ; LOW preload bytes from lo_h:lo_l (now hold preload)
        movff   lo_h,  pre_lo_h
        movff   lo_l,  pre_lo_l

        bsf     GIE

        return

        end


