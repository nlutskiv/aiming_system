#include <xc.inc>
    
global  UART_Setup, UART_Transmit_Message, UART_Read_Byte

psect	udata_acs   ; reserve data space in access ram
UART_counter: ds    1	    ; reserve 1 byte for variable UART_counter

psect	uart_code,class=CODE
UART_Setup:
    bsf     SPEN            ; enable serial port
    bcf     SYNC            ; async
    bcf     BRGH            ; low speed
    bsf     TXEN            ; enable transmit
    bsf     CREN            ; *** ENABLE RECEIVE (THIS WAS MISSING) ***
    bcf     BRG16           ; 8-bit generator

    movlw   103
    movwf   SPBRG1, A

    bsf     TRISC, PORTC_TX1_POSN, A    ; RC6
    bsf     TRISC, PORTC_RX1_POSN, A    ; *** RC7 input for RX (THIS WAS MISSING) ***

    return

UART_Transmit_Message:	    ; Message stored at FSR2, length stored in W
    movwf   UART_counter, A
UART_Loop_message:
    movf    POSTINC2, W, A
    call    UART_Transmit_Byte
    decfsz  UART_counter, A
    bra	    UART_Loop_message
    return

UART_Transmit_Byte:	    ; Transmits byte stored in W
    btfss   TX1IF	    ; TX1IF is set when TXREG1 is empty
    bra	    UART_Transmit_Byte
    movwf   TXREG1, A
    return
    
UART_Read_Byte:
        ; If overrun error (OERR), reset receiver by toggling CREN
        btfsc   RCSTA1, RCSTA1_OERR_POSN, A
        bra     uart_rx_reset

uart_rx_wait:
        btfss   PIR1, PIR1_RC1IF_POSN, A     ; wait for byte
        bra     uart_rx_wait
        movf    RCREG1, W, A                 ; read received byte
        return

uart_rx_reset:
        bcf     RCSTA1, RCSTA1_CREN_POSN, A
        bsf     RCSTA1, RCSTA1_CREN_POSN, A
        bra     uart_rx_wait