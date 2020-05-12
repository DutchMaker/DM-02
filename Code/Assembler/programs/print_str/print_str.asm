; This program sends string data to the text display.

.data
message       : "Hello world\0D\3A-)"
*txt_display  : $FF00

.code
main:
  SP $FEFF            ; Set stack pointer.

  MOV BC,#message     ; Load 16-bit address to the 'message' string into BC register pair.
  CALL print_str      ; Print the string to which BC is now pointing.

done:     
  HALT

; Prints a string to the text display.
; BC must contain the address to the string data.
print_str:
  MOV A,(BC)          ; Transfer data (current character) from memory location BC into A.
  CMP #0              ; Compare A to zero.
  RZ                  ; Return if zero (A==0).

  MOV *txt_display,A  ; Send the current character to the text display.

  INC C               ; Increment the 16-bit BC.
  MOV A,#0            ; Reset A to zero.
  ADC B               ; Add B + carry to A (increments high byte if needed).
  MOV B,A             ; Transfer A to B.

  JMP print_str       ; Repeat for next character.

