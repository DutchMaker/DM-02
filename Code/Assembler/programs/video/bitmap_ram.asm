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

.offset $4000

.data
*display_data : $FF01
*display_cmd  : $FF02
*x            : $FE00
*y            : $FE01

~CMD_SETCOLOR_H   : #$01
~CMD_SETCOLOR_L   : #$02
~CMD_SETCOORD_X   : #$04
~CMD_SETCOORD_Y   : #$08
~CMD_WRITE_PIXEL  : #$10
~CMD_CLEAR_SCREEN : #$20

.include "bitmap_ram_data.asm"   ; 128x128 pixel black&white bitmap.

.code
main:
  ; Set stack pointer.
  SP $FEFF

  MOV A,#0
  MOV *x,A
  MOV *y,A

  ; Set pixel color to white.
  MOV A,#$FF              ; Set color data to white
  MOV *display_data,A

  MOV A,~CMD_SETCOLOR_H   
  MOV *display_cmd,A      ; Execute set color (high byte) command
  MOV A,~CMD_SETCOLOR_L 
  MOV *display_cmd,A      ; Execute set color (low byte) command

  ; Store pointer to bitmap.
  MOV BC,#bitmap

draw_bitmap:  
  CALL draw_pixel

  ; Increment pointer
  INC C
  CZ inc_b
  
  ; Increment X
  MOV A,*x
  INC A
  CMP #128       ; Check if X reached 128, then it should reset to 0
  JZ reset_x
  MOV *x,A      ; Store incremented X.
  JMP draw_bitmap

inc_b:
  INC B
  RET

reset_x:
  MOV A,#0
  MOV *x,A

  ; Increment Y
  MOV A,*y
  INC A
  MOV *y,A

  MOV A,*y            ; Set Y coordinate
  MOV *display_data,A
  MOV A,~CMD_SETCOORD_Y
  MOV *display_cmd,A  ; Execute set coordinate command

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
  MOV A,~CMD_SETCOORD_X
  MOV *display_cmd,A  ; Execute set coordinate command

  MOV A,~CMD_WRITE_PIXEL
  MOV *display_cmd,A  ; Execute set pixel command

  RET