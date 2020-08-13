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
L 74xx:74LS245 U?
U 1 1 5F5A661D
P 1550 6000
F 0 "U?" H 1550 6150 50  0000 C CNN
F 1 "74HCT245" H 1550 5700 50  0000 C CNN
F 2 "" H 1550 6000 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS245" H 1550 6000 50  0001 C CNN
	1    1550 6000
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS245 U?
U 1 1 5F5A783D
P 1550 7950
F 0 "U?" H 1550 8100 50  0000 C CNN
F 1 "74HCT245" H 1550 7650 50  0000 C CNN
F 2 "" H 1550 7950 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS245" H 1550 7950 50  0001 C CNN
	1    1550 7950
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS245 U?
U 1 1 5F5A8C71
P 11400 1600
F 0 "U?" H 11400 1750 50  0000 C CNN
F 1 "74HCT245" H 11400 1300 50  0000 C CNN
F 2 "" H 11400 1600 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS245" H 11400 1600 50  0001 C CNN
	1    11400 1600
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS191 U?
U 1 1 5F5AA130
P 5400 5900
F 0 "U?" H 5400 5950 50  0000 C CNN
F 1 "74HCT191" H 5400 5850 39  0000 C CNN
F 2 "" H 5400 5900 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS191" H 5400 5900 50  0001 C CNN
F 4 "0 - 3" H 5400 5600 50  0000 C CNN "Bits"
	1    5400 5900
	1    0    0    -1  
$EndComp
$Comp
L Memory_EPROM:27C256 U?
U 1 1 5F5AD161
P 8550 2000
F 0 "U?" H 8550 1950 50  0000 C CNN
F 1 "27C256" H 8550 3190 50  0000 C CNN
F 2 "Package_DIP:DIP-28_W15.24mm" H 8550 2000 50  0001 C CNN
F 3 "http://ww1.microchip.com/downloads/en/DeviceDoc/doc0014.pdf" H 8550 2000 50  0001 C CNN
	1    8550 2000
	1    0    0    -1  
$EndComp
$Comp
L 74xx-Computer-Symbols:UM61512AK-15 U?
U 1 1 5F5AEABC
P 8650 4700
F 0 "U?" H 8650 4850 50  0000 C CNN
F 1 "UM61512AK-15" H 8650 5810 50  0000 C CNN
F 2 "DIP32" H 8650 4850 50  0001 C CIN
F 3 "" H 8650 4700 50  0001 C CNN
	1    8650 4700
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS32 U?
U 1 1 5F5AFCCB
P 3400 9600
F 0 "U?" H 3400 9600 50  0000 C CNN
F 1 "74HCT32" H 3400 9834 50  0000 C CNN
F 2 "" H 3400 9600 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS32" H 3400 9600 50  0001 C CNN
	1    3400 9600
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS08 U?
U 1 1 5F5B30F4
P 2300 9500
F 0 "U?" H 2300 9500 50  0000 C CNN
F 1 "74HCT08" H 2300 9734 50  0000 C CNN
F 2 "" H 2300 9500 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS08" H 2300 9500 50  0001 C CNN
	1    2300 9500
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS00 U?
U 1 1 5F5B5820
P 8650 7950
F 0 "U?" H 8650 7950 50  0000 C CNN
F 1 "74HCT00" H 8650 8184 50  0000 C CNN
F 2 "" H 8650 7950 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74ls00" H 8650 7950 50  0001 C CNN
	1    8650 7950
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS04 U?
U 1 1 5F5B7D3B
P 14700 9200
F 0 "U?" H 14700 9517 50  0000 C CNN
F 1 "74HCT04" H 14700 9426 50  0000 C CNN
F 2 "" H 14700 9200 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS04" H 14700 9200 50  0001 C CNN
	1    14700 9200
	1    0    0    -1  
$EndComp
Text GLabel 1050 5500 0    39   Input ~ 0
DATA0
Text GLabel 1050 5600 0    39   Input ~ 0
DATA1
Text GLabel 1050 5700 0    39   Input ~ 0
DATA2
Text GLabel 1050 5800 0    39   Input ~ 0
DATA3
Text GLabel 1050 5900 0    39   Input ~ 0
DATA4
Text GLabel 1050 6000 0    39   Input ~ 0
DATA5
Text GLabel 1050 6100 0    39   Input ~ 0
DATA6
Text GLabel 1050 6200 0    39   Input ~ 0
DATA7
Text GLabel 1050 7450 0    39   Input ~ 0
DATA0
Text GLabel 1050 7550 0    39   Input ~ 0
DATA1
Text GLabel 1050 7650 0    39   Input ~ 0
DATA2
Text GLabel 1050 7750 0    39   Input ~ 0
DATA3
Text GLabel 1050 7850 0    39   Input ~ 0
DATA4
Text GLabel 1050 7950 0    39   Input ~ 0
DATA5
Text GLabel 1050 8050 0    39   Input ~ 0
DATA6
Text GLabel 1050 8150 0    39   Input ~ 0
DATA7
Text GLabel 1050 6400 0    39   Input ~ 0
5V
Text GLabel 1050 8350 0    39   Input ~ 0
5V
Text GLabel 1050 8450 0    39   Input ~ 0
~MAR_H_load
Text GLabel 1050 6500 0    39   Input ~ 0
~MAR_L_load
$Comp
L 74xx:74LS191 U?
U 1 1 5F4414B0
P 3450 5900
F 0 "U?" H 3450 5950 50  0000 C CNN
F 1 "74HCT191" H 3450 5850 39  0000 C CNN
F 2 "" H 3450 5900 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS191" H 3450 5900 50  0001 C CNN
F 4 "4 - 7" H 3450 5600 50  0000 C CNN "Bits"
	1    3450 5900
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS191 U?
U 1 1 5F44204B
P 5400 7850
F 0 "U?" H 5400 7900 50  0000 C CNN
F 1 "74HCT191" H 5400 7800 39  0000 C CNN
F 2 "" H 5400 7850 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS191" H 5400 7850 50  0001 C CNN
F 4 "8 - 11" H 5400 7550 50  0000 C CNN "Bits"
	1    5400 7850
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS191 U?
U 1 1 5F442A46
P 3450 7850
F 0 "U?" H 3450 7900 50  0000 C CNN
F 1 "74HCT191" H 3450 7800 39  0000 C CNN
F 2 "" H 3450 7850 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS191" H 3450 7850 50  0001 C CNN
F 4 "12 - 15" H 3450 7550 50  0000 C CNN "Bits"
	1    3450 7850
	1    0    0    -1  
$EndComp
Text GLabel 2950 6000 0    39   Input ~ 0
~L_load_CLOCK
Text GLabel 2950 7950 0    39   Input ~ 0
~H_load_CLOCK
$Comp
L 74xx:74LS08 U?
U 1 1 5F61560B
P 2300 10100
F 0 "U?" H 2300 10100 50  0000 C CNN
F 1 "74HCT08" H 2300 10334 50  0000 C CNN
F 2 "" H 2300 10100 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS08" H 2300 10100 50  0001 C CNN
	1    2300 10100
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS08 U?
U 1 1 5F617420
P 1600 9800
F 0 "U?" H 1600 9800 50  0000 C CNN
F 1 "74HCT08" H 1600 10034 50  0000 C CNN
F 2 "" H 1600 9800 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS08" H 1600 9800 50  0001 C CNN
	1    1600 9800
	1    0    0    -1  
$EndComp
Wire Wire Line
	2000 9600 2000 9800
Wire Wire Line
	1900 9800 2000 9800
Connection ~ 2000 9800
Wire Wire Line
	2000 9800 2000 10000
Text GLabel 1300 10200 0    39   Input ~ 0
~MAR_H_load
Text GLabel 1300 9400 0    39   Input ~ 0
~MAR_L_load
Text GLabel 1300 9700 0    39   Input ~ 0
~PC_MAR_transfer
Text GLabel 1300 9900 0    39   Input ~ 0
~STK_MAR_transfer
Wire Wire Line
	1300 9400 2000 9400
Wire Wire Line
	1300 10200 2000 10200
$Comp
L 74xx:74LS32 U?
U 1 1 5F7DB936
P 3400 10000
F 0 "U?" H 3400 10000 50  0000 C CNN
F 1 "74HCT32" H 3400 9750 50  0000 C CNN
F 2 "" H 3400 10000 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS32" H 3400 10000 50  0001 C CNN
	1    3400 10000
	1    0    0    -1  
$EndComp
Wire Wire Line
	2600 10100 3100 10100
Wire Wire Line
	2600 9500 3100 9500
Wire Wire Line
	3100 9700 3100 9800
Text GLabel 3000 9800 0    39   Input ~ 0
CLOCK_PH3
Wire Wire Line
	3000 9800 3100 9800
Connection ~ 3100 9800
Wire Wire Line
	3100 9800 3100 9900
Text GLabel 3700 10000 2    39   Input ~ 0
~H_load_CLOCK
Text GLabel 3700 9600 2    39   Input ~ 0
~L_load_CLOCK
Text GLabel 2950 6100 0    39   Input ~ 0
GND
Text GLabel 2950 8050 0    39   Input ~ 0
GND
Text GLabel 4900 8050 0    39   Input ~ 0
GND
Text GLabel 4900 6100 0    39   Input ~ 0
GND
Text GLabel 4900 6000 0    39   Input ~ 0
~L_load_CLOCK
Text GLabel 4900 7950 0    39   Input ~ 0
~H_load_CLOCK
Text GLabel 2950 6300 0    39   Input ~ 0
~MAR_inc
Text GLabel 2950 8250 0    39   Input ~ 0
~MAR_inc
Text GLabel 4900 8250 0    39   Input ~ 0
~MAR_inc
Text GLabel 4900 6300 0    39   Input ~ 0
~MAR_inc
Text GLabel 4900 6400 0    39   Input ~ 0
CLOCK_PH3
NoConn ~ 5900 6200
NoConn ~ 5900 8150
NoConn ~ 3950 8150
NoConn ~ 3950 6200
Text GLabel 5900 6000 2    39   Input ~ 0
LOW0_Rc
Text GLabel 2950 6400 0    39   Input ~ 0
LOW0_Rc
Text GLabel 3950 6000 2    39   Input ~ 0
LOW1_Rc
Text GLabel 4900 8350 0    39   Input ~ 0
LOW1_Rc
Text GLabel 5900 7950 2    39   Input ~ 0
HIGH0_Rc
Text GLabel 2950 8350 0    39   Input ~ 0
HIGH0_Rc
NoConn ~ 3950 7950
Text GLabel 1050 7150 0    39   Input ~ 0
5V
Wire Wire Line
	1050 7150 1550 7150
Connection ~ 1550 7150
Wire Wire Line
	1550 7150 3450 7150
Connection ~ 3450 7150
Wire Wire Line
	3450 7150 5400 7150
Text GLabel 1050 5200 0    39   Input ~ 0
5V
Wire Wire Line
	1050 5200 1550 5200
Connection ~ 1550 5200
Wire Wire Line
	1550 5200 3450 5200
Connection ~ 3450 5200
Wire Wire Line
	3450 5200 5400 5200
Text GLabel 1050 6800 0    39   Input ~ 0
GND
Wire Wire Line
	1050 6800 1550 6800
Wire Wire Line
	5400 6800 5400 6700
Connection ~ 1550 6800
Wire Wire Line
	1550 6800 3450 6800
Wire Wire Line
	3450 6700 3450 6800
Connection ~ 3450 6800
Wire Wire Line
	3450 6800 5400 6800
Text GLabel 1050 8750 0    39   Input ~ 0
GND
Wire Wire Line
	1050 8750 1550 8750
Wire Wire Line
	5400 8750 5400 8650
Connection ~ 1550 8750
Wire Wire Line
	1550 8750 3450 8750
Wire Wire Line
	3450 8650 3450 8750
Connection ~ 3450 8750
Wire Wire Line
	3450 8750 5400 8750
Text GLabel 2050 6200 2    39   Input ~ 0
A7
Text GLabel 2050 6100 2    39   Input ~ 0
A6
Text GLabel 2050 6000 2    39   Input ~ 0
A5
Text GLabel 2050 5900 2    39   Input ~ 0
A4
Text GLabel 2050 5800 2    39   Input ~ 0
A3
Text GLabel 2050 5700 2    39   Input ~ 0
A2
Text GLabel 2050 5600 2    39   Input ~ 0
A1
Text GLabel 2050 5500 2    39   Input ~ 0
A0
Text GLabel 2050 8150 2    39   Input ~ 0
A15
Text GLabel 2050 8050 2    39   Input ~ 0
A14
Text GLabel 2050 7950 2    39   Input ~ 0
A13
Text GLabel 2050 7850 2    39   Input ~ 0
A12
Text GLabel 2050 7750 2    39   Input ~ 0
A11
Text GLabel 2050 7650 2    39   Input ~ 0
A10
Text GLabel 2050 7550 2    39   Input ~ 0
A9
Text GLabel 2050 7450 2    39   Input ~ 0
A8
Text GLabel 4900 5800 0    39   Input ~ 0
A3
Text GLabel 4900 5700 0    39   Input ~ 0
A2
Text GLabel 4900 5600 0    39   Input ~ 0
A1
Text GLabel 4900 5500 0    39   Input ~ 0
A0
Text GLabel 2950 5800 0    39   Input ~ 0
A7
Text GLabel 2950 5700 0    39   Input ~ 0
A6
Text GLabel 2950 5600 0    39   Input ~ 0
A5
Text GLabel 2950 5500 0    39   Input ~ 0
A4
Text GLabel 4900 7750 0    39   Input ~ 0
A11
Text GLabel 4900 7650 0    39   Input ~ 0
A10
Text GLabel 4900 7550 0    39   Input ~ 0
A9
Text GLabel 4900 7450 0    39   Input ~ 0
A8
Text GLabel 2950 7750 0    39   Input ~ 0
A15
Text GLabel 2950 7650 0    39   Input ~ 0
A14
Text GLabel 2950 7550 0    39   Input ~ 0
A13
Text GLabel 2950 7450 0    39   Input ~ 0
A12
Text GLabel 3950 5500 2    39   Input ~ 0
R4
Text GLabel 3950 5600 2    39   Input ~ 0
R5
Text GLabel 3950 5700 2    39   Input ~ 0
R6
Text GLabel 3950 5800 2    39   Input ~ 0
R7
Text GLabel 5900 7450 2    39   Input ~ 0
R8
Text GLabel 5900 7550 2    39   Input ~ 0
R9
Text GLabel 5900 7650 2    39   Input ~ 0
R10
Text GLabel 5900 7750 2    39   Input ~ 0
R11
Text GLabel 3950 7450 2    39   Input ~ 0
R12
Text GLabel 3950 7550 2    39   Input ~ 0
R13
Text GLabel 3950 7650 2    39   Input ~ 0
R14
Text GLabel 3950 7750 2    39   Input ~ 0
R15
Text GLabel 5900 5800 2    39   Input ~ 0
R3
Text GLabel 5900 5700 2    39   Input ~ 0
R2
Text GLabel 5900 5600 2    39   Input ~ 0
R1
Text GLabel 5900 5500 2    39   Input ~ 0
R0
Text GLabel 8150 1400 0    39   Input ~ 0
R3
Text GLabel 8150 1300 0    39   Input ~ 0
R2
Text GLabel 8150 1200 0    39   Input ~ 0
R1
Text GLabel 8150 1100 0    39   Input ~ 0
R0
Text GLabel 8150 1500 0    39   Input ~ 0
R4
Text GLabel 8150 1600 0    39   Input ~ 0
R5
Text GLabel 8150 1700 0    39   Input ~ 0
R6
Text GLabel 8150 1800 0    39   Input ~ 0
R7
Text GLabel 8150 1900 0    39   Input ~ 0
R8
Text GLabel 8150 2000 0    39   Input ~ 0
R9
Text GLabel 8150 2100 0    39   Input ~ 0
R10
Text GLabel 8150 2200 0    39   Input ~ 0
R11
Text GLabel 8150 2300 0    39   Input ~ 0
R12
Text GLabel 8150 2400 0    39   Input ~ 0
R13
Text GLabel 8150 2500 0    39   Input ~ 0
R14
Text GLabel 7950 4100 0    39   Input ~ 0
R3
Text GLabel 7950 4000 0    39   Input ~ 0
R2
Text GLabel 7950 3900 0    39   Input ~ 0
R1
Text GLabel 7950 3800 0    39   Input ~ 0
R0
Text GLabel 7950 4200 0    39   Input ~ 0
R4
Text GLabel 7950 4300 0    39   Input ~ 0
R5
Text GLabel 7950 4400 0    39   Input ~ 0
R6
Text GLabel 7950 4500 0    39   Input ~ 0
R7
Text GLabel 7950 4600 0    39   Input ~ 0
R8
Text GLabel 7950 4700 0    39   Input ~ 0
R9
Text GLabel 7950 4800 0    39   Input ~ 0
R10
Text GLabel 7950 4900 0    39   Input ~ 0
R11
Text GLabel 7950 5000 0    39   Input ~ 0
R12
Text GLabel 7950 5100 0    39   Input ~ 0
R13
Text GLabel 7950 5200 0    39   Input ~ 0
R14
Text GLabel 7950 5300 0    39   Input ~ 0
R15
Text GLabel 11900 1100 2    39   Input ~ 0
DATA0
Text GLabel 11900 1200 2    39   Input ~ 0
DATA1
Text GLabel 11900 1300 2    39   Input ~ 0
DATA2
Text GLabel 11900 1400 2    39   Input ~ 0
DATA3
Text GLabel 11900 1500 2    39   Input ~ 0
DATA4
Text GLabel 11900 1600 2    39   Input ~ 0
DATA5
Text GLabel 11900 1700 2    39   Input ~ 0
DATA6
Text GLabel 11900 1800 2    39   Input ~ 0
DATA7
$Comp
L 74xx:74LS08 U?
U 1 1 5FD39938
P 10600 2400
F 0 "U?" H 10600 2400 50  0000 C CNN
F 1 "74HCT08" H 10600 2634 50  0000 C CNN
F 2 "" H 10600 2400 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS08" H 10600 2400 50  0001 C CNN
	1    10600 2400
	1    0    0    -1  
$EndComp
Wire Wire Line
	10900 2100 10900 2400
Text GLabel 10300 2500 0    39   Input ~ 0
~MEM_load
Text GLabel 10300 2300 0    39   Input ~ 0
~MEM_out
Text GLabel 10900 2000 0    39   Input ~ 0
~MEM_out
Wire Wire Line
	8950 1100 9350 1100
Wire Wire Line
	10900 1200 9400 1200
Wire Wire Line
	8950 1300 9450 1300
Wire Wire Line
	10900 1400 9500 1400
Wire Wire Line
	8950 1500 9550 1500
Wire Wire Line
	10900 1600 9600 1600
Wire Wire Line
	8950 1700 9650 1700
Wire Wire Line
	10900 1800 9700 1800
Wire Wire Line
	9350 3800 9350 1100
Connection ~ 9350 1100
Wire Wire Line
	9350 1100 10900 1100
Wire Wire Line
	9350 3900 9400 3900
Wire Wire Line
	9400 3900 9400 1200
Connection ~ 9400 1200
Wire Wire Line
	9400 1200 8950 1200
Wire Wire Line
	9350 4000 9450 4000
Wire Wire Line
	9450 4000 9450 1300
Connection ~ 9450 1300
Wire Wire Line
	9450 1300 10900 1300
Wire Wire Line
	9350 4100 9500 4100
Wire Wire Line
	9500 4100 9500 1400
Connection ~ 9500 1400
Wire Wire Line
	9500 1400 8950 1400
Wire Wire Line
	9350 4200 9550 4200
Wire Wire Line
	9550 4200 9550 1500
Connection ~ 9550 1500
Wire Wire Line
	9550 1500 10900 1500
Wire Wire Line
	9350 4300 9600 4300
Wire Wire Line
	9600 4300 9600 1600
Connection ~ 9600 1600
Wire Wire Line
	9600 1600 8950 1600
Wire Wire Line
	9350 4400 9650 4400
Wire Wire Line
	9650 4400 9650 1700
Connection ~ 9650 1700
Wire Wire Line
	9650 1700 10900 1700
Wire Wire Line
	9350 4500 9700 4500
Wire Wire Line
	9700 4500 9700 1800
Connection ~ 9700 1800
Wire Wire Line
	9700 1800 8950 1800
Text GLabel 7400 6900 0    39   Input ~ 0
A15
Text GLabel 7400 6800 0    39   Input ~ 0
A14
Text GLabel 7400 6700 0    39   Input ~ 0
A13
Text GLabel 7400 6600 0    39   Input ~ 0
A12
Text GLabel 7400 6500 0    39   Input ~ 0
A11
Text GLabel 7400 6400 0    39   Input ~ 0
A10
Text GLabel 7400 6300 0    39   Input ~ 0
A9
Text GLabel 7400 6200 0    39   Input ~ 0
A8
Text GLabel 9350 5300 2    39   Input ~ 0
5V
Text GLabel 8150 2800 0    39   Input ~ 0
GND
$Comp
L 74xx:74LS08 U?
U 1 1 5FEF36D4
P 8300 6550
F 0 "U?" H 8300 6550 50  0000 C CNN
F 1 "74HCT08" H 8300 6784 50  0000 C CNN
F 2 "" H 8300 6550 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS08" H 8300 6550 50  0001 C CNN
	1    8300 6550
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS21 U?
U 1 1 5FEF5707
P 7700 6350
F 0 "U?" H 7700 6350 50  0000 C CNN
F 1 "74LS21" H 7700 6600 50  0000 C CNN
F 2 "" H 7700 6350 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS21" H 7700 6350 50  0001 C CNN
	1    7700 6350
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS21 U?
U 1 1 5FEF9971
P 7700 6750
F 0 "U?" H 7700 6750 50  0000 C CNN
F 1 "74LS21" H 7700 6500 50  0000 C CNN
F 2 "" H 7700 6750 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS21" H 7700 6750 50  0001 C CNN
	1    7700 6750
	1    0    0    -1  
$EndComp
Wire Wire Line
	8000 6350 8000 6450
Wire Wire Line
	8000 6650 8000 6750
Text GLabel 7700 8350 0    39   Input ~ 0
IO_enable
$Comp
L 74xx:74LS08 U?
U 1 1 5FF23E1B
P 8700 7000
F 0 "U?" H 8700 7000 50  0000 C CNN
F 1 "74HCT08" H 8700 7234 50  0000 C CNN
F 2 "" H 8700 7000 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS08" H 8700 7000 50  0001 C CNN
	1    8700 7000
	1    0    0    -1  
$EndComp
Text GLabel 8400 6900 0    39   Input ~ 0
~MAR_L_load
Text GLabel 8400 7100 0    39   Input ~ 0
~MAR_H_load
$Comp
L 74xx:74LS08 U?
U 1 1 5FF3B239
P 9300 6650
F 0 "U?" H 9300 6650 50  0000 C CNN
F 1 "74HCT08" H 9300 6884 50  0000 C CNN
F 2 "" H 9300 6650 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS08" H 9300 6650 50  0001 C CNN
	1    9300 6650
	1    0    0    -1  
$EndComp
Wire Wire Line
	9000 6750 9000 7000
Wire Wire Line
	9000 6550 8600 6550
$Comp
L 74xx:74LS32 U?
U 1 1 5FF7D14D
P 8050 7850
F 0 "U?" H 8050 7850 50  0000 C CNN
F 1 "74HCT32" H 8050 8084 50  0000 C CNN
F 2 "" H 8050 7850 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS32" H 8050 7850 50  0001 C CNN
	1    8050 7850
	1    0    0    -1  
$EndComp
Text GLabel 7750 7950 0    39   Input ~ 0
A15
Text GLabel 7750 7750 0    39   Input ~ 0
A14
$Comp
L 74xx:74LS00 U?
U 1 1 5FFE46A9
P 8050 8350
F 0 "U?" H 8050 8350 50  0000 C CNN
F 1 "74HCT00" H 8050 8584 50  0000 C CNN
F 2 "" H 8050 8350 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74ls00" H 8050 8350 50  0001 C CNN
	1    8050 8350
	1    0    0    -1  
$EndComp
Wire Wire Line
	7700 8350 7750 8350
Connection ~ 7750 8350
Wire Wire Line
	7750 8350 7750 8450
Wire Wire Line
	7750 8250 7750 8350
Wire Wire Line
	8350 8050 8350 8350
Text GLabel 10150 7950 2    39   Input ~ 0
~RAM_enable
Text GLabel 9350 5200 2    39   Input ~ 0
GND
Text GLabel 9350 4950 2    39   Input ~ 0
~RAM_enable
Text GLabel 8550 3100 2    39   Input ~ 0
GND
Text GLabel 8550 900  2    39   Input ~ 0
5V
Text GLabel 11400 2400 2    39   Input ~ 0
GND
Text GLabel 11400 800  2    39   Input ~ 0
5V
$Comp
L 74xx:74LS32 U?
U 1 1 600F0F45
P 9900 8600
F 0 "U?" H 9900 8600 50  0000 C CNN
F 1 "74HCT32" H 9900 8834 50  0000 C CNN
F 2 "" H 9900 8600 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS32" H 9900 8600 50  0001 C CNN
	1    9900 8600
	1    0    0    -1  
$EndComp
Text GLabel 9550 8800 0    39   Input ~ 0
IO_enable
Wire Wire Line
	10150 7950 9000 7950
$Comp
L 74xx:74LS00 U?
U 1 1 60170A74
P 9300 8500
F 0 "U?" H 9300 8500 50  0000 C CNN
F 1 "74HCT00" H 9300 8734 50  0000 C CNN
F 2 "" H 9300 8500 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74ls00" H 9300 8500 50  0001 C CNN
	1    9300 8500
	1    0    0    -1  
$EndComp
Wire Wire Line
	9000 8600 9000 8400
Connection ~ 9000 7950
Wire Wire Line
	9000 7950 8950 7950
Connection ~ 9000 8400
Wire Wire Line
	9000 8400 9000 7950
Wire Wire Line
	9550 8800 9600 8800
Wire Wire Line
	9600 8800 9600 8700
Text GLabel 10200 8600 2    39   Input ~ 0
~ROM_enable
Text GLabel 8150 2900 0    39   Input ~ 0
~ROM_enable
$EndSCHEMATC
