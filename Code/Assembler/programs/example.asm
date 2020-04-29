; This source file demonstrates all the DM-02 assembly language features.

.data
message   : "Hello\0DWorld"           ; Store string data (terminated with 0x0 by the assembler).
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

;main:
  MOV BC,#message ; Load 16-bit address to the 'message' string into BC register pair.
          
nextchar: 
  MOV A,(BC)      ; Transfer value from memory location BC into A.

  ; Check if we reached the end of the string:
  MOV H,#0        ; Load immediate value 0 into H.
  CMP H           ; Compare A and H.
  JZ done         ; If A==H then we reached the string terminator.

  MOV *serialout,A ; Transfer value from A to #FF00 (I/O address).

  ; Incrementing a 16-bit register pair:
  INC C           ; First increment the lower byte value.
  MOV A,#0        ; Load immediate value 0 into A.
  ADC B           ; Add A to B with carry, 
                  ; this increments the higher byte if needed.
  MOV B,A         ; Copy A into B.
  
  JMP nextchar

done:     
  HALT


.data
example:  "Data may also be stored after the .code block" _
          "Special characters in strings are expressed by their hexadecimal code" _
          "This is a carriage return \0D and this is a tab \09"