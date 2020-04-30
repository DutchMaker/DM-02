; This program demonstrates the use of the video display.
;
; The video display is accessed using memory addresses $FF01 and $FF02.
; Sending data to one of these addresses tells the display to:
; $FF01: Set data (used for color or coordinate)
; $FF02: Execute command
;
; Supported commands are:
; $01: Set color (high byte)
; $02: Set color (low byte)
; $03: Set coordinate (if data mask is %0xxxxxxx it's coordinate X, if mask is %10000000 it's Y)
; $04: Write pixel
; $05: Clear screen

.data
*display_data : $FF01
*display_cmd  : $FF02
*x            : $4000
*y            : $4001

.include "bitmap_data.asm"   ; 64x64 pixel black&white bitmap.

.code
main:
  ; Set stack pointer.
  SP $FEFF

  ; Set pixel color to white.
  MOV A,#$FF          ; Set color data to white
  MOV *display_data,A
  MOV A,#$01          ; Execute set color (high byte) command
  MOV *display_cmd,A
  MOV A,#$02          ; Execute set color (low byte) command
  MOV *display_cmd,A

  ; Store pointer to bitmap.
  MOV BC,#bitmap

draw_bitmap:  
  CALL draw_pixel

  ; Increment pointer
  INC C
  MOV A,#0
  ADC B
  MOV B,A

  ; Increment X
  MOV A,*x
  INC A
  CMP #64       ; Check if X reached 64, then it should reset to 0
  JZ reset_x
  MOV *x,A      ; Store incremented X.
  JMP draw_bitmap

reset_x:
  MOV A,#0
  MOV *x,A

  ; Increment Y
  MOV A,*y
  INC A
  MOV *y,A

  JMP draw_bitmap

done:     
  HALT

draw_pixel:
  MOV A,(BC)    ; Get pixel color value from memory
  
  CMP #$FF      ; Check if we reached the end of the bitmap.
  JZ done

  CMP #0        ; Check if the current pixel is blank.
  RZ

  MOV A,*x            ; Set X coordinate
  MOV *display_data,A
  MOV A,#$03          ; Execute set coordinate command
  MOV *display_cmd,A

  MOV A,*y            ; Set Y coordinate
  ADD #$80            ; Most-left bit must be 1.
  MOV *display_data,A
  MOV A,#$03          ; Execute set coordinate command
  MOV *display_cmd,A

  MOV A,#$04
  MOV *display_cmd,A  ; Execute set pixel command

  RET