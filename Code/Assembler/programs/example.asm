; This source file demonstrates all the DM-02 assembly language features.

.data
message   : "Hel\0Dlo \09Wor\\ld"           ; Store string data (terminated with 0x0 by the assembler).
multiline : "This uses multipe " _  ; An underscore is required when a string 
            "lines to define data"  ; definition spans multiple lines so the assembler knows to terminate.
bytes     : $A4 $FF $5B 'G'         ; Store multiple bytes of data.
            $BC 65 %10001001 $AA    ; data may continue on the next line.
            $AA $BB 
*serialout: $FF00                   ; Define an address pointer (must be express as 4 character hex value). 
                                    ; The * prefix tells the assembler not to apply the memory offset.

.include  "/Users/ruud/Projects/DM-02/Code/Assembler/programs/example_data.asm"        ; Include the contents of another file.

;.offset		$4000										; Define the memory offset (depends on wether the
                                    ; program will run from ROM or RAM).

.code

main:
  MOV HL,message  ; Load 16-bit address to the 'message' string into HL register pair.
          
nextchar: 
  MOV A,(HL)      ; Transfer value from memory location HL into A.

  ; Check if we reached the end of the string:
  MOV B,#0        ; Load immediate value 0 into B.
  CMP B           ; Compare A and B.
  JZ done         ; If A==B then we reached the string terminator.

  MOV *serialout,A ; Transfer value from A to #FF00 (I/O address).

  ; Incrementing a 16-bit register pair:
  INC L           ; First increment the lower byte value.
  MOV A,#0        ; Load immediate value 0 into A.
  ADC H           ; Add A to H with carry, 
                  ; this increments the higher byte if needed.
  MOV H,A         ; Copy A into H.
  
  JMP nextchar

done:     
  HALT


.data
example:  "Data may also be stored after the .code block" _
          "Special characters in strings are expressed by their hexadecimal code" _
          "This is a carriage return \0D and this is a tab \09"