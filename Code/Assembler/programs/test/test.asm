.code
main:
  MOV A,#$FF
  INC A

  HALT

  FCLR C
  FCLR Z

  MOV B,#$FF
  INC B

  HALT
  
  FCLR C
  FCLR Z

  MOV C,#$FF
  INC C

  HALT
  
  FCLR C
  FCLR Z

  MOV H,#$FF
  INC H

  HALT
  
  FCLR C
  FCLR Z

  MOV L,#$FF
  INC L

  HALT