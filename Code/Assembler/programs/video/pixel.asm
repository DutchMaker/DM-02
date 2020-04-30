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

.code
main:
  SP $FEFF            ; Set stack pointer.

  MOV A,#$FF          ; Set color data to white
  MOV *display_data,A
  MOV A,#$01          ; Execute set color (high byte) command
  MOV *display_cmd,A
  MOV A,#$02          ; Execute set color (high byte) command
  MOV *display_cmd,A

  MOV A,#$40          ; Set X coordinate data to 64
  MOV *display_data,A
  MOV A,#$03          ; Execute set coordinate command
  MOV *display_cmd,A

  MOV A,#$C0          ; Set Y coordinate data to 64
  MOV *display_data,A
  MOV A,#$03          ; Execute set coordinate command
  MOV *display_cmd,A

  MOV A,#$04
  MOV *display_cmd,A  ; Execute set pixel command

  MOV A,#$05
  MOV *display_cmd,A  ; Execute clear screen command

done:     
  HALT
