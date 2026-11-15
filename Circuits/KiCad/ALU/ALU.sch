EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A3 16535 11693
encoding utf-8
Sheet 1 1
Title ""
Date ""
Rev ""
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Comp
L Mechanical:MountingHole H3
U 1 1 5E971700
P 11500 11050
F 0 "H3" H 11600 11050 50  0001 L CNN
F 1 "MountingHole" H 11600 11005 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 11500 11050 50  0001 C CNN
F 3 "~" H 11500 11050 50  0001 C CNN
	1    11500 11050
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H4
U 1 1 5D77B482
P 11700 11050
F 0 "H4" H 11800 11050 50  0001 L CNN
F 1 "MountingHole" H 11800 11005 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 11700 11050 50  0001 C CNN
F 3 "~" H 11700 11050 50  0001 C CNN
	1    11700 11050
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H2
U 1 1 5E971701
P 11300 11050
F 0 "H2" H 11400 11050 50  0001 L CNN
F 1 "MountingHole" H 11400 11005 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 11300 11050 50  0001 C CNN
F 3 "~" H 11300 11050 50  0001 C CNN
	1    11300 11050
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H1
U 1 1 5E9716FF
P 11100 11050
F 0 "H1" H 11200 11050 50  0001 L CNN
F 1 "MountingHole" H 11200 11005 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 11100 11050 50  0001 C CNN
F 3 "~" H 11100 11050 50  0001 C CNN
	1    11100 11050
	1    0    0    -1  
$EndComp
$Comp
L Connector_Generic:Conn_02x32_Odd_Even BUS2
U 1 1 5EC6B636
P 4100 2250
F 0 "BUS2" H 4150 3875 50  0000 C CNN
F 1 "Conn_02x32_Odd_Even" H 4150 3876 50  0001 C CNN
F 2 "Connector_PinSocket_2.54mm:PinSocket_2x32_P2.54mm_Vertical" H 4100 2250 50  0001 C CNN
F 3 "~" H 4100 2250 50  0001 C CNN
	1    4100 2250
	-1   0    0    -1  
$EndComp
$Comp
L Connector_Generic:Conn_02x32_Odd_Even BUS1
U 1 1 5EC3909D
P 2000 2250
F 0 "BUS1" H 2050 3875 50  0000 C CNN
F 1 "Conn_02x32_Odd_Even" H 2050 3876 50  0001 C CNN
F 2 "Connector_PinSocket_2.54mm:PinSocket_2x32_P2.54mm_Vertical" H 2000 2250 50  0001 C CNN
F 3 "~" H 2000 2250 50  0001 C CNN
	1    2000 2250
	-1   0    0    -1  
$EndComp
Text GLabel 1150 750  0    39   Input ~ 0
GND
Text GLabel 1150 850  0    39   Input ~ 0
CLOCK_PH0
Text GLabel 1150 950  0    39   Input ~ 0
CLOCK_PH2
Text GLabel 1150 1050 0    39   Input ~ 0
CLOCK_ENABLE
Text GLabel 1150 1150 0    39   Input ~ 0
BTN_STEP_ENABLE
Text GLabel 1150 1250 0    39   Input ~ 0
BTN_STEP
Text GLabel 1150 1350 0    39   Input ~ 0
BTN_CONTINUE
Text GLabel 1150 1450 0    39   Input ~ 0
RESET
Text GLabel 1150 1550 0    39   Input ~ 0
IO_load
Text GLabel 1150 1950 0    39   Input ~ 0
~A_load
Text GLabel 1150 2050 0    39   Input ~ 0
~B_load
Text GLabel 1150 2150 0    39   Input ~ 0
~C_load
Text GLabel 1150 2250 0    39   Input ~ 0
~H_load
Text GLabel 1150 2350 0    39   Input ~ 0
~L_load
Text GLabel 1150 2450 0    39   Input ~ 0
~F_load
Text GLabel 1150 2550 0    39   Input ~ 0
~ALU_load
Text GLabel 1150 2650 0    39   Input ~ 0
~MEM_load
Text GLabel 1150 2750 0    39   Input ~ 0
~PC_H_load
Text GLabel 1150 2850 0    39   Input ~ 0
~PC_L_load
Text GLabel 1150 2950 0    39   Input ~ 0
~STK_H_load
Text GLabel 1150 3050 0    39   Input ~ 0
~STK_L_load
Text GLabel 1150 3150 0    39   Input ~ 0
~MAR_H_load
Text GLabel 1150 3250 0    39   Input ~ 0
~MAR_L_load
Text GLabel 1150 3350 0    39   Input ~ 0
~IR_load
Text GLabel 1150 3450 0    39   Input ~ 0
~PC_MAR_transfer
Text GLabel 1150 3550 0    39   Input ~ 0
~STK_MAR_transfer
Text GLabel 1150 3650 0    39   Input ~ 0
PC_inc
Text GLabel 1150 3750 0    39   Input ~ 0
~MAR_inc
Text GLabel 1150 3850 0    39   Input ~ 0
FETCH_done
Text GLabel 2650 3850 2    39   Input ~ 0
STK_dec
Text GLabel 2650 3750 2    39   Input ~ 0
STK_inc
Text GLabel 2650 3650 2    39   Input ~ 0
HALT
Text GLabel 2650 3550 2    39   Input ~ 0
TSTATE_reset
Text GLabel 2650 3450 2    39   Input ~ 0
~FCLR_z
Text GLabel 2650 3350 2    39   Input ~ 0
~FCLR_c
Text GLabel 2650 3250 2    39   Input ~ 0
~FSET_z
Text GLabel 2650 3150 2    39   Input ~ 0
~FSET_c
Text GLabel 2650 3050 2    39   Input ~ 0
~STK_L_out
Text GLabel 2650 2950 2    39   Input ~ 0
~STK_H_out
Text GLabel 2650 2850 2    39   Input ~ 0
~PC_L_out
Text GLabel 2650 2750 2    39   Input ~ 0
~PC_H_out
Text GLabel 2650 2650 2    39   Input ~ 0
~MEM_out
Text GLabel 2650 2550 2    39   Input ~ 0
~ALU_out
Text GLabel 2650 2450 2    39   Input ~ 0
~F_out
Text GLabel 2650 2350 2    39   Input ~ 0
~L_out
Text GLabel 2650 2250 2    39   Input ~ 0
~H_out
Text GLabel 2650 2150 2    39   Input ~ 0
~C_out
Text GLabel 2650 2050 2    39   Input ~ 0
~B_out
Text GLabel 2650 1950 2    39   Input ~ 0
~A_out
Text GLabel 2650 1550 2    39   Input ~ 0
IO_out
Text GLabel 2650 950  2    39   Input ~ 0
CLOCK_PH3
Text GLabel 2650 850  2    39   Input ~ 0
CLOCK_PH1
Text GLabel 2650 750  2    39   Input ~ 0
5V
Text GLabel 3450 750  0    39   Input ~ 0
DATA0
Text GLabel 3450 850  0    39   Input ~ 0
DATA1
Text GLabel 3450 950  0    39   Input ~ 0
DATA2
Text GLabel 3450 1050 0    39   Input ~ 0
DATA3
Text GLabel 3450 1150 0    39   Input ~ 0
DATA4
Text GLabel 3450 1250 0    39   Input ~ 0
DATA5
Text GLabel 3450 1350 0    39   Input ~ 0
DATA6
Text GLabel 3450 1450 0    39   Input ~ 0
DATA7
Text GLabel 3450 1550 0    39   Input ~ 0
INSTR0
Text GLabel 3450 1650 0    39   Input ~ 0
INSTR1
Text GLabel 3450 1750 0    39   Input ~ 0
INSTR2
Text GLabel 3450 1850 0    39   Input ~ 0
INSTR3
Text GLabel 3450 1950 0    39   Input ~ 0
INSTR4
Text GLabel 3450 2050 0    39   Input ~ 0
INSTR5
Text GLabel 3450 2150 0    39   Input ~ 0
INSTR6
Text GLabel 3450 2250 0    39   Input ~ 0
INSTR7
Text GLabel 3450 2350 0    39   Input ~ 0
ALUFUNC0
Text GLabel 3450 2450 0    39   Input ~ 0
ALUFUNC1
Text GLabel 3450 2550 0    39   Input ~ 0
ALUFUNC2
Text GLabel 3450 2650 0    39   Input ~ 0
ALUFUNC3
Text GLabel 3450 2750 0    39   Input ~ 0
ALUFUNC4
Text GLabel 4600 2750 2    39   Input ~ 0
TSTATE0
Text GLabel 4600 2650 2    39   Input ~ 0
FLAGS3
Text GLabel 4600 2550 2    39   Input ~ 0
FLAGS2
Text GLabel 4600 2450 2    39   Input ~ 0
FLAGS1
Text GLabel 4600 2350 2    39   Input ~ 0
FLAGS0
Text GLabel 4600 2250 2    39   Input ~ 0
A15
Text GLabel 4600 2150 2    39   Input ~ 0
A14
Text GLabel 4600 2050 2    39   Input ~ 0
A13
Text GLabel 4600 1950 2    39   Input ~ 0
A12
Text GLabel 4600 1850 2    39   Input ~ 0
A11
Text GLabel 4600 1750 2    39   Input ~ 0
A10
Text GLabel 4600 1650 2    39   Input ~ 0
A9
Text GLabel 4600 1550 2    39   Input ~ 0
A8
Text GLabel 4600 1450 2    39   Input ~ 0
A7
Text GLabel 4600 1350 2    39   Input ~ 0
A6
Text GLabel 4600 1250 2    39   Input ~ 0
A5
Text GLabel 4600 1150 2    39   Input ~ 0
A4
Text GLabel 4600 1050 2    39   Input ~ 0
A3
Text GLabel 4600 950  2    39   Input ~ 0
A2
Text GLabel 4600 850  2    39   Input ~ 0
A1
Text GLabel 4600 750  2    39   Input ~ 0
A0
Text GLabel 4600 3050 2    39   Input ~ 0
TSTATE3
Text GLabel 4600 2950 2    39   Input ~ 0
TSTATE2
Text GLabel 4600 2850 2    39   Input ~ 0
TSTATE1
Wire Wire Line
	4300 750  4600 750 
Wire Wire Line
	4600 850  4300 850 
Wire Wire Line
	4300 950  4600 950 
Wire Wire Line
	4600 1050 4300 1050
Wire Wire Line
	4300 1150 4600 1150
Wire Wire Line
	4600 1250 4300 1250
Wire Wire Line
	4300 1350 4600 1350
Wire Wire Line
	4600 1450 4300 1450
Wire Wire Line
	4300 1550 4600 1550
Wire Wire Line
	4600 1650 4300 1650
Wire Wire Line
	4300 1750 4600 1750
Wire Wire Line
	4600 1850 4300 1850
Wire Wire Line
	4300 1950 4600 1950
Wire Wire Line
	4600 2050 4300 2050
Wire Wire Line
	4300 2150 4600 2150
Wire Wire Line
	4600 2250 4300 2250
Wire Wire Line
	4300 2350 4600 2350
Wire Wire Line
	4600 2450 4300 2450
Wire Wire Line
	4300 2550 4600 2550
Wire Wire Line
	4600 2650 4300 2650
Wire Wire Line
	4300 2750 4600 2750
Wire Wire Line
	4600 2850 4300 2850
Wire Wire Line
	4300 2950 4600 2950
Wire Wire Line
	4600 3050 4300 3050
NoConn ~ 4600 3150
NoConn ~ 4600 3250
NoConn ~ 4600 3350
NoConn ~ 4600 3450
NoConn ~ 4600 3550
NoConn ~ 4600 3650
NoConn ~ 4600 3750
NoConn ~ 4600 3850
Wire Wire Line
	4600 3850 4300 3850
Wire Wire Line
	4300 3750 4600 3750
Wire Wire Line
	4600 3650 4300 3650
Wire Wire Line
	4300 3550 4600 3550
Wire Wire Line
	4600 3450 4300 3450
Wire Wire Line
	4600 3350 4300 3350
Wire Wire Line
	4600 3250 4300 3250
Wire Wire Line
	4600 3150 4300 3150
Text Label 4300 750  0    39   ~ 0
A0
Text Label 4300 850  0    39   ~ 0
A1
Text Label 4300 950  0    39   ~ 0
A2
Text Label 4300 1050 0    39   ~ 0
A3
Text Label 4300 1150 0    39   ~ 0
A4
Text Label 4300 1250 0    39   ~ 0
A5
Text Label 4300 1350 0    39   ~ 0
A6
Text Label 4300 1450 0    39   ~ 0
A7
Text Label 4300 1550 0    39   ~ 0
A8
Text Label 4300 1650 0    39   ~ 0
A9
Text Label 4300 1750 0    39   ~ 0
A10
Text Label 4300 1850 0    39   ~ 0
A11
Text Label 4300 1950 0    39   ~ 0
A12
Text Label 4300 2050 0    39   ~ 0
A13
Text Label 4300 2150 0    39   ~ 0
A14
Text Label 4300 2250 0    39   ~ 0
A15
Text Label 4300 2350 0    39   ~ 0
FLAGS0
Text Label 4300 2450 0    39   ~ 0
FLAGS1
Text Label 4300 2550 0    39   ~ 0
FLAGS2
Text Label 4300 2650 0    39   ~ 0
FLAGS3
Text Label 4300 2750 0    39   ~ 0
TSTATE0
Text Label 4300 2850 0    39   ~ 0
TSTATE1
Text Label 4300 2950 0    39   ~ 0
TSTATE2
Text Label 4300 3050 0    39   ~ 0
TSTATE3
Text Label 4300 3150 0    39   ~ 0
B2NC18
Text Label 4300 3250 0    39   ~ 0
B2NC17
Text Label 4300 3350 0    39   ~ 0
B2NC16
Text Label 4300 3450 0    39   ~ 0
B2NC15
Text Label 4300 3550 0    39   ~ 0
B2NC14
Text Label 4300 3650 0    39   ~ 0
B2NC13
Text Label 4300 3750 0    39   ~ 0
B2NC12
Text Label 4300 3850 0    39   ~ 0
B2NC11
Wire Wire Line
	3800 3850 3450 3850
Wire Wire Line
	3450 3750 3800 3750
Wire Wire Line
	3800 3650 3450 3650
Wire Wire Line
	3450 3550 3800 3550
Wire Wire Line
	3800 3450 3450 3450
Wire Wire Line
	3450 3350 3800 3350
Wire Wire Line
	3800 3250 3450 3250
Wire Wire Line
	3450 3150 3800 3150
Wire Wire Line
	3800 3050 3450 3050
Wire Wire Line
	3450 2950 3800 2950
Wire Wire Line
	3800 2850 3450 2850
Wire Wire Line
	3450 2750 3800 2750
Wire Wire Line
	3800 2650 3450 2650
Wire Wire Line
	3450 2550 3800 2550
Wire Wire Line
	3800 2450 3450 2450
Wire Wire Line
	3450 2350 3800 2350
Wire Wire Line
	3800 2250 3450 2250
Wire Wire Line
	3450 2150 3800 2150
Wire Wire Line
	3800 2050 3450 2050
Wire Wire Line
	3450 1950 3800 1950
Wire Wire Line
	3800 1850 3450 1850
Wire Wire Line
	3450 1750 3800 1750
Wire Wire Line
	3800 1650 3450 1650
Wire Wire Line
	3450 1550 3800 1550
Wire Wire Line
	3450 750  3800 750 
Wire Wire Line
	3800 850  3450 850 
Wire Wire Line
	3450 950  3800 950 
Wire Wire Line
	3800 1050 3450 1050
Wire Wire Line
	3450 1150 3800 1150
Wire Wire Line
	3450 1250 3800 1250
Wire Wire Line
	3450 1350 3800 1350
Wire Wire Line
	3450 1450 3800 1450
Text Label 3800 3850 2    39   ~ 0
B2NC10
Text Label 3800 3750 2    39   ~ 0
B2NC9
Text Label 3800 3650 2    39   ~ 0
B2NC8
Text Label 3800 3550 2    39   ~ 0
B2NC7
Text Label 3800 3450 2    39   ~ 0
B2NC6
Text Label 3800 3350 2    39   ~ 0
B2NC5
Text Label 3800 3250 2    39   ~ 0
B2NC4
Text Label 3800 3150 2    39   ~ 0
B2NC3
Text Label 3800 3050 2    39   ~ 0
B2NC2
Text Label 3800 2950 2    39   ~ 0
B2NC1
Text Label 3800 2850 2    39   ~ 0
B2NC0
Text Label 3800 2750 2    39   ~ 0
ALUFUNC4
Text Label 3800 2650 2    39   ~ 0
ALUFUNC3
Text Label 3800 2550 2    39   ~ 0
ALUFUNC2
Text Label 3800 2450 2    39   ~ 0
ALUFUNC1
Text Label 3800 2350 2    39   ~ 0
ALUFUNC0
Text Label 3800 2250 2    39   ~ 0
INSTR7
Text Label 3800 2150 2    39   ~ 0
INSTR6
Text Label 3800 2050 2    39   ~ 0
INSTR5
Text Label 3800 1950 2    39   ~ 0
INSTR4
Text Label 3800 1850 2    39   ~ 0
INSTR3
Text Label 3800 1750 2    39   ~ 0
INSTR2
Text Label 3800 1650 2    39   ~ 0
INSTR1
Text Label 3800 1550 2    39   ~ 0
INSTR0
Text Label 3800 1450 2    39   ~ 0
DATA7
Text Label 3800 1350 2    39   ~ 0
DATA6
Text Label 3800 1250 2    39   ~ 0
DATA5
Text Label 3800 1150 2    39   ~ 0
DATA4
Text Label 3800 1050 2    39   ~ 0
DATA3
Text Label 3800 950  2    39   ~ 0
DATA2
Text Label 3800 850  2    39   ~ 0
DATA1
Text Label 3800 750  2    39   ~ 0
DATA0
NoConn ~ 3450 2850
NoConn ~ 3450 2950
NoConn ~ 3450 3050
NoConn ~ 3450 3150
NoConn ~ 3450 3250
NoConn ~ 3450 3350
NoConn ~ 3450 3450
NoConn ~ 3450 3550
NoConn ~ 3450 3650
NoConn ~ 3450 3750
NoConn ~ 3450 3850
Wire Wire Line
	2650 850  2200 850 
Wire Wire Line
	2200 950  2650 950 
Wire Wire Line
	2650 1050 2200 1050
Wire Wire Line
	2200 1150 2650 1150
Wire Wire Line
	2650 1250 2200 1250
Wire Wire Line
	2200 1350 2650 1350
Wire Wire Line
	2650 1450 2200 1450
Wire Wire Line
	2200 1550 2650 1550
Wire Wire Line
	2650 1650 2200 1650
Wire Wire Line
	2200 1750 2650 1750
Wire Wire Line
	2650 1850 2200 1850
Wire Wire Line
	2200 1950 2650 1950
Wire Wire Line
	2650 2050 2200 2050
Wire Wire Line
	2200 2150 2650 2150
Wire Wire Line
	2650 2250 2200 2250
Wire Wire Line
	2200 2350 2650 2350
Wire Wire Line
	2650 2450 2200 2450
Wire Wire Line
	2200 2550 2650 2550
Wire Wire Line
	2650 2650 2200 2650
Wire Wire Line
	2200 2750 2650 2750
Wire Wire Line
	2650 2850 2200 2850
Wire Wire Line
	2200 2950 2650 2950
Wire Wire Line
	2650 3050 2200 3050
Wire Wire Line
	2650 3850 2200 3850
Wire Wire Line
	2200 3750 2650 3750
Wire Wire Line
	2650 3650 2200 3650
Wire Wire Line
	2200 3550 2650 3550
Wire Wire Line
	2650 3450 2200 3450
Wire Wire Line
	2650 3350 2200 3350
Wire Wire Line
	2650 3250 2200 3250
Wire Wire Line
	2650 3150 2200 3150
Text Label 2200 750  0    39   ~ 0
5V
Text Label 2200 850  0    39   ~ 0
CLOCK_PH1
Text Label 2200 950  0    39   ~ 0
CLOCK_PH3
Text Label 2200 1050 0    39   ~ 0
B1NC10
Text Label 2200 1150 0    39   ~ 0
B1NC9
Text Label 2200 1250 0    39   ~ 0
B1NC8
Text Label 2200 1350 0    39   ~ 0
B1NC7
Text Label 2200 1450 0    39   ~ 0
B1NC6
Text Label 2200 1550 0    39   ~ 0
IO_out
Text Label 2200 1650 0    39   ~ 0
B1NC5
Text Label 2200 1750 0    39   ~ 0
B1NC4
Text Label 2200 1850 0    39   ~ 0
B1NC3
Text Label 2200 1950 0    39   ~ 0
~A_out
Text Label 2200 2050 0    39   ~ 0
~B_out
Text Label 2200 2150 0    39   ~ 0
~C_out
Text Label 2200 2250 0    39   ~ 0
~H_out
Text Label 2200 2350 0    39   ~ 0
~L_out
Text Label 2200 2450 0    39   ~ 0
~F_out
Text Label 2200 2550 0    39   ~ 0
~ALU_out
Text Label 2200 2650 0    39   ~ 0
~MEM_out
Text Label 2200 2750 0    39   ~ 0
~PC_H_out
Text Label 2200 2850 0    39   ~ 0
~PC_L_out
Text Label 2200 2950 0    39   ~ 0
~STK_H_out
Text Label 2200 3050 0    39   ~ 0
~STK_L_out
Text Label 2200 3150 0    39   ~ 0
~FSET_c
Text Label 2200 3250 0    39   ~ 0
~FSET_z
Text Label 2200 3350 0    39   ~ 0
~FCLR_c
Text Label 2200 3450 0    39   ~ 0
~FCLR_z
Text Label 2200 3550 0    39   ~ 0
TSTATE_reset
Text Label 2200 3650 0    39   ~ 0
HALT
Text Label 2200 3750 0    39   ~ 0
STK_inc
Text Label 2200 3850 0    39   ~ 0
STK_dec
Wire Wire Line
	1700 3850 1150 3850
Wire Wire Line
	1150 3750 1700 3750
Wire Wire Line
	1700 3650 1150 3650
Wire Wire Line
	1150 3550 1700 3550
Wire Wire Line
	1700 3450 1150 3450
Wire Wire Line
	1150 3350 1700 3350
Wire Wire Line
	1700 3250 1150 3250
Wire Wire Line
	1150 3150 1700 3150
Wire Wire Line
	1700 3050 1150 3050
Wire Wire Line
	1150 2950 1700 2950
Wire Wire Line
	1700 2850 1150 2850
Wire Wire Line
	1150 2750 1700 2750
Wire Wire Line
	1700 2650 1150 2650
Wire Wire Line
	1150 2550 1700 2550
Wire Wire Line
	1700 2450 1150 2450
Wire Wire Line
	1150 2350 1700 2350
Wire Wire Line
	1700 2250 1150 2250
Wire Wire Line
	1150 2150 1700 2150
Wire Wire Line
	1700 2050 1150 2050
Wire Wire Line
	1150 1950 1700 1950
Wire Wire Line
	1700 1850 1150 1850
Wire Wire Line
	1150 1750 1700 1750
Wire Wire Line
	1700 1650 1150 1650
Wire Wire Line
	1150 1550 1700 1550
Wire Wire Line
	1700 850  1150 850 
Wire Wire Line
	1150 950  1700 950 
Wire Wire Line
	1700 1050 1150 1050
Wire Wire Line
	1150 1150 1700 1150
Wire Wire Line
	1150 1250 1700 1250
Wire Wire Line
	1150 1350 1700 1350
Wire Wire Line
	1150 1450 1700 1450
Text Label 1700 3850 2    39   ~ 0
FETCH_done
Text Label 1700 3750 2    39   ~ 0
~MAR_inc
Text Label 1700 3650 2    39   ~ 0
PC_inc
Text Label 1700 3550 2    39   ~ 0
~STK_MAR_transfer
Text Label 1700 3450 2    39   ~ 0
~PC_MAR_transfer
Text Label 1700 3350 2    39   ~ 0
~IR_load
Text Label 1700 3250 2    39   ~ 0
~MAR_L_load
Text Label 1700 3150 2    39   ~ 0
~MAR_H_load
Text Label 1700 3050 2    39   ~ 0
~STK_L_load
Text Label 1700 2950 2    39   ~ 0
~STK_H_load
Text Label 1700 2850 2    39   ~ 0
~PC_L_load
Text Label 1700 2750 2    39   ~ 0
~PC_H_load
Text Label 1700 2650 2    39   ~ 0
~MEM_load
Text Label 1700 2550 2    39   ~ 0
~ALU_load
Text Label 1700 2450 2    39   ~ 0
~F_load
Text Label 1700 2350 2    39   ~ 0
~L_load
Text Label 1700 2250 2    39   ~ 0
~H_load
Text Label 1700 2150 2    39   ~ 0
~C_load
Text Label 1700 2050 2    39   ~ 0
~B_load
Text Label 1700 1950 2    39   ~ 0
~A_load
Text Label 1700 1850 2    39   ~ 0
B1NC2
Text Label 1700 1750 2    39   ~ 0
B1NC1
Text Label 1700 1650 2    39   ~ 0
B1NC0
Text Label 1700 1550 2    39   ~ 0
IO_load
Text Label 1700 1450 2    39   ~ 0
RESET
Text Label 1700 1350 2    39   ~ 0
BTN_CONTINUE
Text Label 1700 1250 2    39   ~ 0
BTN_STEP
Text Label 1700 1150 2    39   ~ 0
BTN_STEP_ENABLE
Text Label 1700 1050 2    39   ~ 0
CLOCK_ENABLE
Text Label 1700 950  2    39   ~ 0
CLOCK_PH2
Text Label 1700 850  2    39   ~ 0
CLOCK_PH0
Text Label 1700 750  2    39   ~ 0
GND
NoConn ~ 2650 1850
NoConn ~ 2650 1750
NoConn ~ 2650 1650
NoConn ~ 2650 1450
NoConn ~ 2650 1350
NoConn ~ 2650 1250
NoConn ~ 2650 1150
NoConn ~ 2650 1050
NoConn ~ 1150 1650
NoConn ~ 1150 1750
NoConn ~ 1150 1850
$Comp
L power:GND #PWR0101
U 1 1 5F24E0E0
P 1350 750
F 0 "#PWR0101" H 1350 500 50  0001 C CNN
F 1 "GND" H 1355 577 39  0000 C CNN
F 2 "" H 1350 750 50  0001 C CNN
F 3 "" H 1350 750 50  0001 C CNN
	1    1350 750 
	-1   0    0    1   
$EndComp
$Comp
L power:PWR_FLAG #FLG0101
U 1 1 5F24F424
P 1450 750
F 0 "#FLG0101" H 1450 825 50  0001 C CNN
F 1 "PWR_FLAG" H 1450 923 50  0001 C CNN
F 2 "" H 1450 750 50  0001 C CNN
F 3 "~" H 1450 750 50  0001 C CNN
	1    1450 750 
	1    0    0    -1  
$EndComp
$Comp
L power:+5V #PWR0102
U 1 1 5F250881
P 2500 750
F 0 "#PWR0102" H 2500 600 50  0001 C CNN
F 1 "+5V" H 2515 915 39  0000 C CNN
F 2 "" H 2500 750 50  0001 C CNN
F 3 "" H 2500 750 50  0001 C CNN
	1    2500 750 
	1    0    0    -1  
$EndComp
$Comp
L power:PWR_FLAG #FLG0102
U 1 1 5F24FE4E
P 2400 750
F 0 "#FLG0102" H 2400 825 50  0001 C CNN
F 1 "PWR_FLAG" H 2400 923 50  0001 C CNN
F 2 "" H 2400 750 50  0001 C CNN
F 3 "~" H 2400 750 50  0001 C CNN
	1    2400 750 
	1    0    0    -1  
$EndComp
Wire Wire Line
	2200 750  2400 750 
Connection ~ 2400 750 
Wire Wire Line
	2400 750  2500 750 
Connection ~ 2500 750 
Wire Wire Line
	2500 750  2650 750 
Wire Wire Line
	1150 750  1350 750 
Connection ~ 1350 750 
Wire Wire Line
	1350 750  1450 750 
Connection ~ 1450 750 
Wire Wire Line
	1450 750  1700 750 
$Comp
L 74xx:74HC74 U1
U 1 1 5F0EF992
P 9500 1350
F 0 "U1" H 9500 1831 50  0000 C CNN
F 1 "74HCT74" H 9500 1740 50  0000 C CNN
F 2 "" H 9500 1350 50  0001 C CNN
F 3 "https://www.ti.com/lit/ds/symlink/sn74hct74.pdf" H 9500 1350 50  0001 C CNN
	1    9500 1350
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74HC74 U1
U 2 1 5F0F1338
P 9500 2400
F 0 "U1" H 9500 2881 50  0000 C CNN
F 1 "74HCT74" H 9500 2790 50  0000 C CNN
F 2 "" H 9500 2400 50  0001 C CNN
F 3 "https://www.ti.com/lit/ds/symlink/sn74hct74.pdf" H 9500 2400 50  0001 C CNN
	2    9500 2400
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74HC74 U2
U 1 1 5F0FF161
P 10650 1350
F 0 "U2" H 10650 1831 50  0000 C CNN
F 1 "74HCT74" H 10650 1740 50  0000 C CNN
F 2 "" H 10650 1350 50  0001 C CNN
F 3 "https://www.ti.com/lit/ds/symlink/sn74hct74.pdf" H 10650 1350 50  0001 C CNN
	1    10650 1350
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74HC74 U2
U 2 1 5F0FF16B
P 10650 2400
F 0 "U2" H 10650 2881 50  0000 C CNN
F 1 "74HCT74" H 10650 2790 50  0000 C CNN
F 2 "" H 10650 2400 50  0001 C CNN
F 3 "https://www.ti.com/lit/ds/symlink/sn74hct74.pdf" H 10650 2400 50  0001 C CNN
	2    10650 2400
	1    0    0    -1  
$EndComp
$Comp
L 74xx-Computer-Symbols:M27C322 U3
U 1 1 5F12C1E6
P 11450 5100
F 0 "U3" H 11450 6381 50  0000 C CNN
F 1 "M27C322" H 11450 6290 50  0000 C CNN
F 2 "" H 11450 5100 50  0001 C CNN
F 3 "" H 11450 5100 50  0001 C CNN
	1    11450 5100
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74HCT240 U4
U 1 1 5F237668
P 6150 2500
F 0 "U4" H 6150 3481 50  0000 C CNN
F 1 "74HCT240" H 6150 3390 50  0000 C CNN
F 2 "" H 6150 2500 50  0001 C CNN
F 3 "" H 6150 2500 50  0001 C CNN
	1    6150 2500
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS377 U5
U 1 1 5F279A4A
P 1850 5300
F 0 "U5" H 1850 6281 50  0000 C CNN
F 1 "74HCT377" H 1850 6190 50  0000 C CNN
F 2 "" H 1850 5300 50  0001 C CNN
F 3 "" H 1850 5300 50  0001 C CNN
	1    1850 5300
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS377 U6
U 1 1 5F2AC7D4
P 3450 5300
F 0 "U6" H 3450 6281 50  0000 C CNN
F 1 "74HCT377" H 3450 6190 50  0000 C CNN
F 2 "" H 3450 5300 50  0001 C CNN
F 3 "" H 3450 5300 50  0001 C CNN
	1    3450 5300
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS377 U7
U 1 1 5F2AD4C4
P 4950 5300
F 0 "U7" H 4950 6281 50  0000 C CNN
F 1 "74HCT377" H 4950 6190 50  0000 C CNN
F 2 "" H 4950 5300 50  0001 C CNN
F 3 "" H 4950 5300 50  0001 C CNN
	1    4950 5300
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74HCT244 U8
U 1 1 5F2AE932
P 6600 4800
F 0 "U8" H 6600 5781 50  0000 C CNN
F 1 "74HCT244" H 6600 5690 50  0000 C CNN
F 2 "" H 6600 4800 50  0001 C CNN
F 3 "" H 6600 4800 50  0001 C CNN
	1    6600 4800
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS245 U9
U 1 1 5F2BC763
P 8350 5750
F 0 "U9" H 8350 6731 50  0000 C CNN
F 1 "74HCT245" H 8350 6640 50  0000 C CNN
F 2 "" H 8350 5750 50  0001 C CNN
F 3 "" H 8350 5750 50  0001 C CNN
	1    8350 5750
	1    0    0    -1  
$EndComp
Entry Wire Line
	10750 4200 10650 4100
Entry Wire Line
	10650 4200 10750 4300
Entry Wire Line
	10650 4300 10750 4400
Entry Wire Line
	10650 4400 10750 4500
Entry Wire Line
	10750 4600 10650 4500
Entry Wire Line
	10650 4600 10750 4700
Entry Wire Line
	10650 4700 10750 4800
Entry Wire Line
	10650 4800 10750 4900
Entry Wire Line
	10750 5000 10650 4900
Entry Wire Line
	10650 5000 10750 5100
Entry Wire Line
	10650 5100 10750 5200
Entry Wire Line
	10650 5200 10750 5300
Entry Wire Line
	10750 5400 10650 5300
Entry Wire Line
	10650 5400 10750 5500
Entry Wire Line
	10650 5500 10750 5600
Entry Wire Line
	10650 5600 10750 5700
Entry Wire Line
	10650 5700 10750 5800
Entry Wire Line
	10750 5900 10650 5800
Entry Wire Line
	10650 5900 10750 6000
Entry Wire Line
	10650 6000 10750 6100
Entry Wire Line
	10650 6100 10750 6200
Wire Wire Line
	11400 6400 11400 6450
Wire Wire Line
	11400 6450 11500 6450
Wire Wire Line
	11500 6450 11500 6400
Wire Wire Line
	11850 6200 11900 6200
Wire Wire Line
	11900 6200 11900 6450
Wire Wire Line
	11900 6450 11500 6450
Connection ~ 11500 6450
Wire Bus Line
	10650 4100 10600 4100
Wire Bus Line
	10650 5700 10600 5700
Wire Wire Line
	10750 4200 11050 4200
Wire Wire Line
	11050 4300 10750 4300
Wire Wire Line
	10750 4400 11050 4400
Wire Wire Line
	11050 4500 10750 4500
Wire Wire Line
	10750 4600 11050 4600
Wire Wire Line
	11050 4700 10750 4700
Wire Wire Line
	10750 4800 11050 4800
Wire Wire Line
	11050 4900 10750 4900
Wire Wire Line
	10750 5000 11050 5000
Wire Wire Line
	11050 5100 10750 5100
Wire Wire Line
	10750 5200 11050 5200
Wire Wire Line
	11050 5300 10750 5300
Wire Wire Line
	10750 5400 11050 5400
Wire Wire Line
	11050 5500 10750 5500
Wire Wire Line
	10750 5600 11050 5600
Wire Wire Line
	11050 5700 10750 5700
Wire Wire Line
	11050 5800 10750 5800
Wire Wire Line
	10750 5900 11050 5900
Wire Wire Line
	11050 6000 10750 6000
Wire Wire Line
	10750 6100 11050 6100
Wire Wire Line
	11050 6200 10750 6200
Text Label 10750 4200 0    50   ~ 0
B0
Text Label 10750 4300 0    50   ~ 0
B1
Text Label 10750 4400 0    50   ~ 0
B2
Text Label 10750 4500 0    50   ~ 0
B3
Text Label 10750 4600 0    50   ~ 0
B4
Text Label 10750 4700 0    50   ~ 0
B5
Text Label 10750 4800 0    50   ~ 0
B6
Text Label 10750 4900 0    50   ~ 0
B7
Text Label 10750 5000 0    50   ~ 0
ALU_A0
Text Label 10750 5100 0    50   ~ 0
ALU_A1
Text Label 10750 5200 0    50   ~ 0
ALU_A2
Text Label 10750 5300 0    50   ~ 0
ALU_A3
Text Label 10750 5400 0    50   ~ 0
ALU_A4
Text Label 10750 5500 0    50   ~ 0
ALU_A5
Text Label 10750 5600 0    50   ~ 0
ALU_A6
Text Label 10750 5700 0    50   ~ 0
ALU_A7
Text Label 10750 5800 0    50   ~ 0
FUNC0
Text Label 10750 5900 0    50   ~ 0
FUNC1
Text Label 10750 6000 0    50   ~ 0
FUNC2
Text Label 10750 6100 0    50   ~ 0
FUNC3
Text Label 10750 6200 0    50   ~ 0
FUNC4
Entry Wire Line
	12250 4200 12350 4100
Entry Wire Line
	12250 4300 12350 4200
Entry Wire Line
	12250 4400 12350 4300
Entry Wire Line
	12250 4500 12350 4400
Entry Wire Line
	12250 4600 12350 4500
Entry Wire Line
	12250 4700 12350 4600
Entry Wire Line
	12250 4800 12350 4700
Entry Wire Line
	12250 4900 12350 4800
Entry Wire Line
	12250 5000 12350 4900
Entry Wire Line
	12250 5100 12350 5000
Entry Wire Line
	12250 5200 12350 5100
Entry Wire Line
	12250 5300 12350 5200
Entry Wire Line
	12250 5400 12350 5300
Wire Bus Line
	12350 4100 12400 4100
Wire Bus Line
	12350 4900 12400 4900
Text GLabel 10600 4100 0    50   Input ~ 0
B
Text GLabel 10600 4900 0    50   Input ~ 0
ALU_A
Wire Bus Line
	10650 4900 10600 4900
Text GLabel 10600 5700 0    50   Input ~ 0
FUNC
Text GLabel 12400 4100 2    50   Input ~ 0
RESULT
Text GLabel 12400 4900 2    50   Input ~ 0
ALU_FLAGS
NoConn ~ 11850 5500
NoConn ~ 11850 5600
NoConn ~ 11850 5700
Wire Wire Line
	11850 4200 12250 4200
Wire Wire Line
	12250 4300 11850 4300
Wire Wire Line
	11850 4400 12250 4400
Wire Wire Line
	12250 4500 11850 4500
Wire Wire Line
	11850 4600 12250 4600
Wire Wire Line
	12250 4700 11850 4700
Wire Wire Line
	11850 4800 12250 4800
Wire Wire Line
	12250 4900 11850 4900
Wire Wire Line
	12250 5000 11850 5000
Wire Wire Line
	11850 5100 12250 5100
Wire Wire Line
	12250 5200 11850 5200
Wire Wire Line
	11850 5300 12250 5300
Wire Wire Line
	12250 5400 11850 5400
Text Label 12250 4200 2    50   ~ 0
RESULT0
Text Label 12250 4300 2    50   ~ 0
RESULT1
Text Label 12250 4400 2    50   ~ 0
RESULT2
Text Label 12250 4500 2    50   ~ 0
RESULT3
Text Label 12250 4600 2    50   ~ 0
RESULT4
Text Label 12250 4700 2    50   ~ 0
RESULT5
Text Label 12250 4800 2    50   ~ 0
RESULT6
Text Label 12250 4900 2    50   ~ 0
RESULT7
Text Label 12250 5000 2    50   ~ 0
ALU_FLAGS0
Text Label 12250 5100 2    50   ~ 0
ALU_FLAGS1
Text Label 12250 5200 2    50   ~ 0
ALU_FLAGS2
Text Label 12250 5300 2    50   ~ 0
ALU_FLAGS3
Text Label 12250 5400 2    50   ~ 0
ALU_FLAGS4
Wire Bus Line
	10650 5700 10650 6100
Wire Bus Line
	12350 4900 12350 5300
Wire Bus Line
	10650 4100 10650 4800
Wire Bus Line
	10650 4900 10650 5600
Wire Bus Line
	12350 4100 12350 4800
$Comp
L 74xx:74LS32 U10
U 1 1 5F568C57
P 2050 7100
F 0 "U10" H 2050 7425 50  0000 C CNN
F 1 "74HCT32" H 2050 7334 50  0000 C CNN
F 2 "" H 2050 7100 50  0001 C CNN
F 3 "" H 2050 7100 50  0001 C CNN
	1    2050 7100
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS32 U10
U 2 1 5F56A35D
P 3400 7100
F 0 "U10" H 3400 7425 50  0000 C CNN
F 1 "74HCT32" H 3400 7334 50  0000 C CNN
F 2 "" H 3400 7100 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS32" H 3400 7100 50  0001 C CNN
	2    3400 7100
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS32 U10
U 3 1 5F56AF7E
P 4550 7200
F 0 "U10" H 4550 7525 50  0000 C CNN
F 1 "74HCT32" H 4550 7434 50  0000 C CNN
F 2 "" H 4550 7200 50  0001 C CNN
F 3 "" H 4550 7200 50  0001 C CNN
	3    4550 7200
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS32 U10
U 4 1 5F56BFCF
P 5650 7100
F 0 "U10" H 5650 7425 50  0000 C CNN
F 1 "74HCT32" H 5650 7334 50  0000 C CNN
F 2 "" H 5650 7100 50  0001 C CNN
F 3 "" H 5650 7100 50  0001 C CNN
	4    5650 7100
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS32 U11
U 1 1 5F56D51F
P 2000 7750
F 0 "U11" H 2000 8075 50  0000 C CNN
F 1 "74HCT32" H 2000 7984 50  0000 C CNN
F 2 "" H 2000 7750 50  0001 C CNN
F 3 "" H 2000 7750 50  0001 C CNN
	1    2000 7750
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74HCT04 U12
U 1 1 5F56FBFE
P 1850 8450
F 0 "U12" H 1850 8767 50  0000 C CNN
F 1 "74HCT04" H 1850 8676 50  0000 C CNN
F 2 "" H 1850 8450 50  0001 C CNN
F 3 "https://assets.nexperia.com/documents/data-sheet/74HC_HCT04.pdf" H 1850 8450 50  0001 C CNN
	1    1850 8450
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74HCT04 U12
U 2 1 5F570E1C
P 3000 8500
F 0 "U12" H 3000 8817 50  0000 C CNN
F 1 "74HCT04" H 3000 8726 50  0000 C CNN
F 2 "" H 3000 8500 50  0001 C CNN
F 3 "https://assets.nexperia.com/documents/data-sheet/74HC_HCT04.pdf" H 3000 8500 50  0001 C CNN
	2    3000 8500
	1    0    0    -1  
$EndComp
Text GLabel 11400 6400 3    39   Input ~ 0
GND
Text GLabel 11500 6400 3    39   Input ~ 0
GND
Text GLabel 11450 4000 1    39   Input ~ 0
5V
Text GLabel 6150 3300 3    39   Input ~ 0
GND
Text GLabel 6150 1700 1    39   Input ~ 0
5V
Text GLabel 1850 6100 3    39   Input ~ 0
GND
Text GLabel 1850 4500 1    39   Input ~ 0
5V
Text GLabel 3450 6100 3    39   Input ~ 0
GND
Text GLabel 3450 4500 1    39   Input ~ 0
5V
Text GLabel 4950 6100 3    39   Input ~ 0
GND
Text GLabel 4950 4500 1    39   Input ~ 0
5V
Text GLabel 6600 5600 3    39   Input ~ 0
GND
Text GLabel 6600 4000 1    39   Input ~ 0
5V
Text GLabel 8350 6550 3    39   Input ~ 0
GND
Text GLabel 8350 4950 1    39   Input ~ 0
5V
Text Notes 12500 700 0    60   ~ 0
Gate supplies and spare-input termination
$Comp
L 74xx:74HC74 U1
U 3 1 69172001
P 13000 1600
F 0 "U1" H 13230 1646 50 0000 L CNN
F 1 "74HCT74" H 13230 1555 50 0000 L CNN
	3    13000 1600
	1    0    0    -1
$EndComp
Text GLabel 13000 1200 1    39   Input ~ 0
5V
Text GLabel 13000 2000 3    39   Input ~ 0
GND
$Comp
L 74xx:74HC74 U2
U 3 1 69172002
P 14200 1600
F 0 "U2" H 14430 1646 50 0000 L CNN
F 1 "74HCT74" H 14430 1555 50 0000 L CNN
	3    14200 1600
	1    0    0    -1
$EndComp
Text GLabel 14200 1200 1    39   Input ~ 0
5V
Text GLabel 14200 2000 3    39   Input ~ 0
GND
$Comp
L 74xx:74LS32 U10
U 5 1 69172003
P 15400 1600
F 0 "U10" H 15630 1646 50 0000 L CNN
F 1 "74HCT32" H 15630 1555 50 0000 L CNN
	5    15400 1600
	1    0    0    -1
$EndComp
Text GLabel 15400 1100 1    39   Input ~ 0
5V
Text GLabel 15400 2100 3    39   Input ~ 0
GND
$Comp
L 74xx:74LS32 U11
U 5 1 69172004
P 13000 3400
F 0 "U11" H 13230 3446 50 0000 L CNN
F 1 "74HCT32" H 13230 3355 50 0000 L CNN
	5    13000 3400
	1    0    0    -1
$EndComp
Text GLabel 13000 2900 1    39   Input ~ 0
5V
Text GLabel 13000 3900 3    39   Input ~ 0
GND
$Comp
L 74xx:74HCT04 U12
U 7 1 69172005
P 14200 3400
F 0 "U12" H 14430 3446 50 0000 L CNN
F 1 "74HCT04" H 14430 3355 50 0000 L CNN
	7    14200 3400
	1    0    0    -1
$EndComp
Text GLabel 14200 2900 1    39   Input ~ 0
5V
Text GLabel 14200 3900 3    39   Input ~ 0
GND
$Comp
L 74xx:74LS32 U11
U 2 1 69172101
P 13000 5200
F 0 "U11" H 13000 5500 50 0000 C CNN
F 1 "74HCT32" H 13000 5400 50 0000 C CNN
	2    13000 5200
	1    0    0    -1
$EndComp
Text GLabel 12700 5100 0    39   Input ~ 0
GND
Text GLabel 12700 5300 0    39   Input ~ 0
GND
NoConn ~ 13300 5200
$Comp
L 74xx:74LS32 U11
U 3 1 69172102
P 14200 5200
F 0 "U11" H 14200 5500 50 0000 C CNN
F 1 "74HCT32" H 14200 5400 50 0000 C CNN
	3    14200 5200
	1    0    0    -1
$EndComp
Text GLabel 13900 5100 0    39   Input ~ 0
GND
Text GLabel 13900 5300 0    39   Input ~ 0
GND
NoConn ~ 14500 5200
$Comp
L 74xx:74LS32 U11
U 4 1 69172103
P 15400 5200
F 0 "U11" H 15400 5500 50 0000 C CNN
F 1 "74HCT32" H 15400 5400 50 0000 C CNN
	4    15400 5200
	1    0    0    -1
$EndComp
Text GLabel 15100 5100 0    39   Input ~ 0
GND
Text GLabel 15100 5300 0    39   Input ~ 0
GND
NoConn ~ 15700 5200
$Comp
L 74xx:74HCT04 U12
U 3 1 69172104
P 13000 6000
F 0 "U12" H 13000 6300 50 0000 C CNN
F 1 "74HCT04" H 13000 6200 50 0000 C CNN
	3    13000 6000
	1    0    0    -1
$EndComp
Text GLabel 12700 6000 0    39   Input ~ 0
CLOCK_PH3
Text Label 13300 6000 0    39   ~ 0
ALU_PHASE_n
$Comp
L 74xx:74HCT04 U12
U 4 1 69172105
P 14200 6000
F 0 "U12" H 14200 6300 50 0000 C CNN
F 1 "74HCT04" H 14200 6200 50 0000 C CNN
	4    14200 6000
	1    0    0    -1
$EndComp
Text GLabel 13900 6000 0    39   Input ~ 0
GND
NoConn ~ 14500 6000
$Comp
L 74xx:74HCT04 U12
U 5 1 69172106
P 15400 6000
F 0 "U12" H 15400 6300 50 0000 C CNN
F 1 "74HCT04" H 15400 6200 50 0000 C CNN
	5    15400 6000
	1    0    0    -1
$EndComp
Text GLabel 15100 6000 0    39   Input ~ 0
GND
NoConn ~ 15700 6000
$Comp
L 74xx:74HCT04 U12
U 6 1 69172107
P 13000 6800
F 0 "U12" H 13000 7100 50 0000 C CNN
F 1 "74HCT04" H 13000 7000 50 0000 C CNN
	6    13000 6800
	1    0    0    -1
$EndComp
Text GLabel 12700 6800 0    39   Input ~ 0
GND
NoConn ~ 13300 6800
Text Notes 1100 4400 0    50   ~ 0
Operand A / operand B / operation: shared CLOCK_PH3, active-low enables
Text GLabel 1350 4800 0    39   Input ~ 0
DATA0
Text GLabel 1350 4900 0    39   Input ~ 0
DATA1
Text GLabel 1350 5000 0    39   Input ~ 0
DATA2
Text GLabel 1350 5100 0    39   Input ~ 0
DATA3
Text GLabel 1350 5200 0    39   Input ~ 0
DATA4
Text GLabel 1350 5300 0    39   Input ~ 0
DATA5
Text GLabel 1350 5400 0    39   Input ~ 0
DATA6
Text GLabel 1350 5500 0    39   Input ~ 0
DATA7
Text GLabel 1350 5800 0    39   Input ~ 0
~A_load
Text Label 2350 4800 0    39   ~ 0
ALU_A0
Text Label 2350 4900 0    39   ~ 0
ALU_A1
Text Label 2350 5000 0    39   ~ 0
ALU_A2
Text Label 2350 5100 0    39   ~ 0
ALU_A3
Text Label 2350 5200 0    39   ~ 0
ALU_A4
Text Label 2350 5300 0    39   ~ 0
ALU_A5
Text Label 2350 5400 0    39   ~ 0
ALU_A6
Text Label 2350 5500 0    39   ~ 0
ALU_A7
Text GLabel 2950 4800 0    39   Input ~ 0
DATA0
Text GLabel 2950 4900 0    39   Input ~ 0
DATA1
Text GLabel 2950 5000 0    39   Input ~ 0
DATA2
Text GLabel 2950 5100 0    39   Input ~ 0
DATA3
Text GLabel 2950 5200 0    39   Input ~ 0
DATA4
Text GLabel 2950 5300 0    39   Input ~ 0
DATA5
Text GLabel 2950 5400 0    39   Input ~ 0
DATA6
Text GLabel 2950 5500 0    39   Input ~ 0
DATA7
Text GLabel 2950 5800 0    39   Input ~ 0
~ALU_load
Text Label 3950 4800 0    39   ~ 0
B0
Text Label 3950 4900 0    39   ~ 0
B1
Text Label 3950 5000 0    39   ~ 0
B2
Text Label 3950 5100 0    39   ~ 0
B3
Text Label 3950 5200 0    39   ~ 0
B4
Text Label 3950 5300 0    39   ~ 0
B5
Text Label 3950 5400 0    39   ~ 0
B6
Text Label 3950 5500 0    39   ~ 0
B7
Text GLabel 4450 4800 0    39   Input ~ 0
ALUFUNC0
Text GLabel 4450 4900 0    39   Input ~ 0
ALUFUNC1
Text GLabel 4450 5000 0    39   Input ~ 0
ALUFUNC2
Text GLabel 4450 5100 0    39   Input ~ 0
ALUFUNC3
Text GLabel 4450 5200 0    39   Input ~ 0
ALUFUNC4
Text GLabel 4450 5300 0    39   Input ~ 0
GND
Text GLabel 4450 5400 0    39   Input ~ 0
GND
Text GLabel 4450 5500 0    39   Input ~ 0
GND
Text GLabel 4450 5800 0    39   Input ~ 0
~ALU_load
Text Label 5450 4800 0    39   ~ 0
FUNC0
Text Label 5450 4900 0    39   ~ 0
FUNC1
Text Label 5450 5000 0    39   ~ 0
FUNC2
Text Label 5450 5100 0    39   ~ 0
FUNC3
Text Label 5450 5200 0    39   ~ 0
FUNC4
NoConn ~ 5450 5300
NoConn ~ 5450 5400
NoConn ~ 5450 5500
Text GLabel 11850 6100 2    39   Input ~ 0
GND
Text Notes 6000 3850 0    50   ~ 0
Flags C/O/Z/N: result, bus or feedback; shared CLOCK_PH3 capture
Text Label 6100 4300 2    39   ~ 0
ALU_FLAGS0
Text Label 6100 4400 2    39   ~ 0
ALU_FLAGS1
Text Label 6100 4500 2    39   ~ 0
ALU_FLAGS2
Text Label 6100 4600 2    39   ~ 0
ALU_FLAGS3
Text GLabel 6100 4700 0    39   Input ~ 0
DATA0
Text GLabel 6100 4800 0    39   Input ~ 0
DATA1
Text GLabel 6100 4900 0    39   Input ~ 0
DATA2
Text GLabel 6100 5000 0    39   Input ~ 0
DATA3
Text GLabel 6100 5200 0    39   Input ~ 0
~ALU_out
Text GLabel 6100 5300 0    39   Input ~ 0
~F_load
Text Label 7100 4300 0    39   ~ 0
FLAG_D0
Text Label 7100 4400 0    39   ~ 0
FLAG_D1
Text Label 7100 4500 0    39   ~ 0
FLAG_D2
Text Label 7100 4600 0    39   ~ 0
FLAG_D3
Text Label 7100 4700 0    39   ~ 0
FLAG_D0
Text Label 7100 4800 0    39   ~ 0
FLAG_D1
Text Label 7100 4900 0    39   ~ 0
FLAG_D2
Text Label 7100 5000 0    39   ~ 0
FLAG_D3
Text Label 9200 1250 2    39   ~ 0
FLAG_D0
Text Label 9200 2300 2    39   ~ 0
FLAG_D2
Text Label 10350 1250 2    39   ~ 0
FLAG_D1
Text Label 10350 2300 2    39   ~ 0
FLAG_D3
Text GLabel 9800 1250 2    39   Output ~ 0
FLAGS0
Text GLabel 9800 2300 2    39   Output ~ 0
FLAGS2
Text GLabel 10950 1250 2    39   Output ~ 0
FLAGS1
Text GLabel 10950 2300 2    39   Output ~ 0
FLAGS3
NoConn ~ 9800 1450
NoConn ~ 9800 2500
NoConn ~ 10950 1450
NoConn ~ 10950 2500
Text GLabel 10650 1050 1    39   Input ~ 0
5V
Text GLabel 10650 1650 3    39   Input ~ 0
5V
Text GLabel 10650 2100 1    39   Input ~ 0
5V
Text GLabel 10650 2700 3    39   Input ~ 0
5V
Text GLabel 7850 5250 0    39   Input ~ 0
FLAGS0
Text GLabel 7850 5350 0    39   Input ~ 0
FLAGS1
Text GLabel 7850 5450 0    39   Input ~ 0
FLAGS2
Text GLabel 7850 5550 0    39   Input ~ 0
FLAGS3
Text GLabel 7850 5650 0    39   Input ~ 0
GND
Text GLabel 7850 5750 0    39   Input ~ 0
GND
Text GLabel 7850 5850 0    39   Input ~ 0
GND
Text GLabel 7850 5950 0    39   Input ~ 0
GND
Text GLabel 7850 6150 0    39   Input ~ 0
5V
Text GLabel 7850 6250 0    39   Input ~ 0
~F_out
Text GLabel 8850 5250 2    39   BiDi ~ 0
DATA0
Text GLabel 8850 5350 2    39   BiDi ~ 0
DATA1
Text GLabel 8850 5450 2    39   BiDi ~ 0
DATA2
Text GLabel 8850 5550 2    39   BiDi ~ 0
DATA3
Text GLabel 8850 5650 2    39   BiDi ~ 0
DATA4
Text GLabel 8850 5750 2    39   BiDi ~ 0
DATA5
Text GLabel 8850 5850 2    39   BiDi ~ 0
DATA6
Text GLabel 8850 5950 2    39   BiDi ~ 0
DATA7
Text Notes 7400 6800 0    50   ~ 0
ALU result bus driver
$Comp
L 74xx:74LS245 U13
U 1 1 69175001
P 8350 7900
F 0 "U13" H 8350 8881 50 0000 C CNN
F 1 "74HCT245" H 8350 8790 50 0000 C CNN
F 2 "Package_DIP:DIP-20_W7.62mm" H 8350 7900 50 0001 C CNN
	1    8350 7900
	1    0    0    -1
$EndComp
Text GLabel 8350 7100 1    39   Input ~ 0
5V
Text GLabel 8350 8700 3    39   Input ~ 0
GND
Text Label 7850 7400 2    39   ~ 0
RESULT0
Text Label 7850 7500 2    39   ~ 0
RESULT1
Text Label 7850 7600 2    39   ~ 0
RESULT2
Text Label 7850 7700 2    39   ~ 0
RESULT3
Text Label 7850 7800 2    39   ~ 0
RESULT4
Text Label 7850 7900 2    39   ~ 0
RESULT5
Text Label 7850 8000 2    39   ~ 0
RESULT6
Text Label 7850 8100 2    39   ~ 0
RESULT7
Text GLabel 7850 8300 0    39   Input ~ 0
5V
Text GLabel 7850 8400 0    39   Input ~ 0
~ALU_out
Text GLabel 8850 7400 2    39   BiDi ~ 0
DATA0
Text GLabel 8850 7500 2    39   BiDi ~ 0
DATA1
Text GLabel 8850 7600 2    39   BiDi ~ 0
DATA2
Text GLabel 8850 7700 2    39   BiDi ~ 0
DATA3
Text GLabel 8850 7800 2    39   BiDi ~ 0
DATA4
Text GLabel 8850 7900 2    39   BiDi ~ 0
DATA5
Text GLabel 8850 8000 2    39   BiDi ~ 0
DATA6
Text GLabel 8850 8100 2    39   BiDi ~ 0
DATA7
Text Notes 5600 3600 0    50   ~ 0
Former tri-state clock buffer disabled; clocks now driven directly
Text GLabel 5650 2000 0    39   Input ~ 0
GND
Text GLabel 5650 2100 0    39   Input ~ 0
GND
Text GLabel 5650 2200 0    39   Input ~ 0
GND
Text GLabel 5650 2300 0    39   Input ~ 0
GND
Text GLabel 5650 2400 0    39   Input ~ 0
GND
Text GLabel 5650 2500 0    39   Input ~ 0
GND
Text GLabel 5650 2600 0    39   Input ~ 0
GND
Text GLabel 5650 2700 0    39   Input ~ 0
GND
Text GLabel 5650 2900 0    39   Input ~ 0
5V
Text GLabel 5650 3000 0    39   Input ~ 0
5V
NoConn ~ 6650 2000
NoConn ~ 6650 2100
NoConn ~ 6650 2200
NoConn ~ 6650 2300
NoConn ~ 6650 2400
NoConn ~ 6650 2500
NoConn ~ 6650 2600
NoConn ~ 6650 2700
Text GLabel 1350 5700 0    39   Input ~ 0
CLOCK_PH3
Text GLabel 2950 5700 0    39   Input ~ 0
CLOCK_PH3
Text GLabel 4450 5700 0    39   Input ~ 0
CLOCK_PH3
Text GLabel 9200 1350 0    39   Input ~ 0
CLOCK_PH3
Text GLabel 9200 2400 0    39   Input ~ 0
CLOCK_PH3
Text GLabel 10350 1350 0    39   Input ~ 0
CLOCK_PH3
Text GLabel 10350 2400 0    39   Input ~ 0
CLOCK_PH3
Text Label 9500 1650 0    39   ~ 0
FCLR_c_PHASE_n
Text Label 9500 1050 0    39   ~ 0
FSET_c_PHASE_n
Text Label 9500 2700 0    39   ~ 0
FCLR_z_PHASE_n
Text Label 9500 2100 0    39   ~ 0
FSET_z_PHASE_n
Text GLabel 1750 7000 0    39   Input ~ 0
~FCLR_c
Text Label 1750 7200 2    39   ~ 0
ALU_PHASE_n
Text Label 2350 7100 0    39   ~ 0
FCLR_c_PHASE_n
Text GLabel 3100 7000 0    39   Input ~ 0
~FCLR_z
Text Label 3100 7200 2    39   ~ 0
ALU_PHASE_n
Text Label 3700 7100 0    39   ~ 0
FCLR_z_PHASE_n
Text GLabel 4250 7100 0    39   Input ~ 0
~FSET_c
Text Label 4250 7300 2    39   ~ 0
ALU_PHASE_n
Text Label 4850 7200 0    39   ~ 0
FSET_c_PHASE_n
Text GLabel 5350 7000 0    39   Input ~ 0
~FSET_z
Text Label 5350 7200 2    39   ~ 0
ALU_PHASE_n
Text Label 5950 7100 0    39   ~ 0
FSET_z_PHASE_n
Text GLabel 1550 8450 0    39   Input ~ 0
~ALU_out
Text Label 2150 8450 0    39   ~ 0
ALU_RESULT_SELECTED
Text GLabel 2700 8500 0    39   Input ~ 0
~F_load
Text Label 3300 8500 0    39   ~ 0
F_BUS_SELECTED
Text Label 1700 7650 2    39   ~ 0
ALU_RESULT_SELECTED
Text Label 1700 7850 2    39   ~ 0
F_BUS_SELECTED
Text Label 2300 7750 0    39   ~ 0
FLAG_NEW_DATA
Text Notes 9700 7000 0    50   ~ 0
Flag feedback enabled only while both result and bus captures are inactive
$Comp
L 74xx:74LS125 U14
U 1 1 69176001
P 10400 7400
F 0 "U14" H 10400 7700 50 0000 C CNN
F 1 "74HCT125" H 10400 7600 50 0000 C CNN
F 2 "Package_DIP:DIP-14_W7.62mm" H 10400 7400 50 0001 C CNN
	1    10400 7400
	1    0    0    -1
$EndComp
Text GLabel 10100 7400 0    39   Input ~ 0
FLAGS0
Text Label 10700 7400 0    39   ~ 0
FLAG_D0
Text Label 10400 7650 0    39   ~ 0
FLAG_NEW_DATA
$Comp
L 74xx:74LS125 U14
U 2 1 69176002
P 11800 7400
F 0 "U14" H 11800 7700 50 0000 C CNN
F 1 "74HCT125" H 11800 7600 50 0000 C CNN
F 2 "Package_DIP:DIP-14_W7.62mm" H 11800 7400 50 0001 C CNN
	2    11800 7400
	1    0    0    -1
$EndComp
Text GLabel 11500 7400 0    39   Input ~ 0
FLAGS1
Text Label 12100 7400 0    39   ~ 0
FLAG_D1
Text Label 11800 7650 0    39   ~ 0
FLAG_NEW_DATA
$Comp
L 74xx:74LS125 U14
U 3 1 69176003
P 10400 8600
F 0 "U14" H 10400 8900 50 0000 C CNN
F 1 "74HCT125" H 10400 8800 50 0000 C CNN
F 2 "Package_DIP:DIP-14_W7.62mm" H 10400 8600 50 0001 C CNN
	3    10400 8600
	1    0    0    -1
$EndComp
Text GLabel 10100 8600 0    39   Input ~ 0
FLAGS2
Text Label 10700 8600 0    39   ~ 0
FLAG_D2
Text Label 10400 8850 0    39   ~ 0
FLAG_NEW_DATA
$Comp
L 74xx:74LS125 U14
U 4 1 69176004
P 11800 8600
F 0 "U14" H 11800 8900 50 0000 C CNN
F 1 "74HCT125" H 11800 8800 50 0000 C CNN
F 2 "Package_DIP:DIP-14_W7.62mm" H 11800 8600 50 0001 C CNN
	4    11800 8600
	1    0    0    -1
$EndComp
Text GLabel 11500 8600 0    39   Input ~ 0
FLAGS3
Text Label 12100 8600 0    39   ~ 0
FLAG_D3
Text Label 11800 8850 0    39   ~ 0
FLAG_NEW_DATA
$Comp
L 74xx:74LS125 U14
U 5 1 69176005
P 15400 3400
F 0 "U14" H 15630 3446 50 0000 L CNN
F 1 "74HCT125" H 15630 3355 50 0000 L CNN
F 2 "Package_DIP:DIP-14_W7.62mm" H 15400 3400 50 0001 C CNN
	5    15400 3400
	1    0    0    -1
$EndComp
Text GLabel 15400 2900 1    39   Input ~ 0
5V
Text GLabel 15400 3900 3    39   Input ~ 0
GND
$EndSCHEMATC
