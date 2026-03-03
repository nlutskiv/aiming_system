#include <xc.inc>

global  ADC_Setup, ADC_Read    
    
psect	adc_code, class=CODE
    
ADC_Setup:
        ; RA0 input + analog
        bsf     TRISA, PORTA_RA0_POSN, A
        movlb   0x0F
        bsf     ANSEL0
        movlb   0x00

        ; Use AVDD/AVSS as references (no 4.096V cap)
        clrf    ADCON1, A

        ; Select AN0, turn ADC on
        movlw   0x01
        movwf   ADCON0, A

        ; ADCON2: set ADFM=1 (RIGHT justified) + your timing bits
        ; If you want to keep your old 0xF6, force bit7 anyway:
        movlw   0xF6
        iorlw   0x80            ; ensure bit7=1 (ADFM)
        movwf   ADCON2, A
        return

ADC_Read:
	bsf	GO	    ; Start conversion by setting GO bit in ADCON0
adc_loop:
	btfsc   GO	    ; check to see if finished
	bra	adc_loop
	return

end


