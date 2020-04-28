; This source file demonstrates all the DM-02 assembly language features.

.data
message   : "Hello World"           ; Store string data (terminated with 0x0 by the assembler).
bytes     : $A4 $FF $5B 'G'         ; Store multiple bytes of data.
            $BC 65 %10001001 $AA
$4F00     : $01 $02 $03 $04         ; Store data at an explicit address.
serialout : $FF00                   ; Define an address pointer.     

.code
main:     
  MOV BC,message  ; Load 16-bit address to the 'message' string into BC register pair.
          
nextchar: 
  MOV A,(BC)      ; Transfer value from memory location BC into A.

  MOV B,#0        ; Load immediate value 0 into B.
  CMP B           ; Compare A and B.
  JZ done         ; If A==B then we reached the string terminator.

  MOV serialout,A ; Transfer value from A to #FF00 (I/O address).

  INC C           ; Increment BC value
  JNC inc_nocarry
  INC B
  inc_nocarry:
    JMP nextchar

done:     
  HALT
