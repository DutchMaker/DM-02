EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
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
P 10900 6400
F 0 "H3" H 11000 6400 50  0001 L CNN
F 1 "MountingHole" H 11000 6355 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 10900 6400 50  0001 C CNN
F 3 "~" H 10900 6400 50  0001 C CNN
	1    10900 6400
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H4
U 1 1 5D77B482
P 11100 6400
F 0 "H4" H 11200 6400 50  0001 L CNN
F 1 "MountingHole" H 11200 6355 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 11100 6400 50  0001 C CNN
F 3 "~" H 11100 6400 50  0001 C CNN
	1    11100 6400
	1    0    0    -1  
$EndComp
NoConn ~ 2600 1050
NoConn ~ 2600 1150
NoConn ~ 2600 1250
NoConn ~ 2600 1350
NoConn ~ 2600 1450
NoConn ~ 2600 1550
NoConn ~ 2600 1650
NoConn ~ 2600 1750
NoConn ~ 2600 1850
$Comp
L Mechanical:MountingHole H2
U 1 1 5E971701
P 10700 6400
F 0 "H2" H 10800 6400 50  0001 L CNN
F 1 "MountingHole" H 10800 6355 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 10700 6400 50  0001 C CNN
F 3 "~" H 10700 6400 50  0001 C CNN
	1    10700 6400
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H1
U 1 1 5E9716FF
P 10500 6400
F 0 "H1" H 10600 6400 50  0001 L CNN
F 1 "MountingHole" H 10600 6355 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 10500 6400 50  0001 C CNN
F 3 "~" H 10500 6400 50  0001 C CNN
	1    10500 6400
	1    0    0    -1  
$EndComp
NoConn ~ 2600 1950
NoConn ~ 2600 2050
NoConn ~ 2600 2150
NoConn ~ 2600 2250
NoConn ~ 2600 2350
NoConn ~ 2600 2450
NoConn ~ 2600 2550
NoConn ~ 2600 2650
NoConn ~ 2600 750 
NoConn ~ 2600 850 
NoConn ~ 2600 950 
NoConn ~ 700  1050
NoConn ~ 700  2650
NoConn ~ 700  2550
NoConn ~ 700  2450
NoConn ~ 700  2350
NoConn ~ 700  2250
NoConn ~ 700  2050
NoConn ~ 700  1950
NoConn ~ 700  1850
NoConn ~ 700  1750
NoConn ~ 700  1650
NoConn ~ 700  1550
NoConn ~ 700  1450
NoConn ~ 700  1350
NoConn ~ 700  1250
NoConn ~ 700  1150
NoConn ~ 700  950 
NoConn ~ 700  850 
NoConn ~ 700  750 
NoConn ~ 2600 3050
NoConn ~ 700  3350
NoConn ~ 700  3250
NoConn ~ 700  3150
NoConn ~ 700  3050
NoConn ~ 700  2950
NoConn ~ 700  2850
NoConn ~ 700  2750
NoConn ~ 700  3450
NoConn ~ 2600 3850
NoConn ~ 2600 3750
NoConn ~ 2600 3650
NoConn ~ 2600 3550
NoConn ~ 2600 3450
NoConn ~ 2600 3350
NoConn ~ 2600 3250
NoConn ~ 2600 3150
NoConn ~ 2600 2950
NoConn ~ 2600 2850
NoConn ~ 2600 2750
NoConn ~ 700  3550
NoConn ~ 700  3650
NoConn ~ 700  3750
NoConn ~ 700  3850
$Comp
L Connector_Generic:Conn_02x32_Odd_Even BUS2
U 1 1 5EC6B636
P 3700 2250
F 0 "BUS2" H 3750 3875 50  0000 C CNN
F 1 "Conn_02x32_Odd_Even" H 3750 3876 50  0001 C CNN
F 2 "Connector_PinSocket_2.54mm:PinSocket_2x32_P2.54mm_Vertical" H 3700 2250 50  0001 C CNN
F 3 "~" H 3700 2250 50  0001 C CNN
	1    3700 2250
	-1   0    0    -1  
$EndComp
Text Label 1500 750  2    50   ~ 0
GND
Text Label 1500 850  2    50   ~ 0
CLOCK_PH0
Text Label 1500 950  2    50   ~ 0
CLOCK_PH2
Text Label 1500 1050 2    50   ~ 0
CLOCK_ENABLE
Text Label 1500 1150 2    50   ~ 0
BTN_STEP_ENABLE
Text Label 1500 1250 2    50   ~ 0
BTN_STEP
Text Label 1500 1350 2    50   ~ 0
BTN_CONTINUE
Text Label 1500 1450 2    50   ~ 0
BTN_RESET
Text Label 1500 1550 2    50   ~ 0
IO_load
Text Label 1500 1950 2    50   ~ 0
~A_load
Text Label 1500 2050 2    50   ~ 0
~B_load
Text Label 1500 2150 2    50   ~ 0
~C_load
Text Label 1500 2250 2    50   ~ 0
~H_load
Text Label 1500 2350 2    50   ~ 0
~L_load
Text Label 1500 2450 2    50   ~ 0
~F_load
Text Label 1500 2550 2    50   ~ 0
~ALU_load
Text Label 1500 2650 2    50   ~ 0
~MEM_load
Text Label 1500 2750 2    50   ~ 0
~PC_H_load
Text Label 1500 2850 2    50   ~ 0
~PC_L_load
Text Label 1500 2950 2    50   ~ 0
~STK_H_load
Text Label 1500 3050 2    50   ~ 0
~STK_L_load
Text Label 1500 3150 2    50   ~ 0
~MAR_H_load
Text Label 1500 3250 2    50   ~ 0
~MAR_L_load
Text Label 1500 3350 2    50   ~ 0
~IR_load
Text Label 1500 3450 2    50   ~ 0
~PC_MAR_transfer
Text Label 1500 3550 2    50   ~ 0
~STK_MAR_transfer
Text Label 1500 3650 2    50   ~ 0
PC_inc
Text Label 1500 3750 2    50   ~ 0
~MAR_inc
Text Label 1500 3850 2    50   ~ 0
FETCH_done
Text Label 2000 750  0    50   ~ 0
5V
Text Label 2000 850  0    50   ~ 0
CLOCK_PH1
Text Label 2000 950  0    50   ~ 0
CLOCK_PH3
Text Label 2000 1550 0    50   ~ 0
IO_out
Text Label 2000 1950 0    50   ~ 0
~A_out
Text Label 2000 2050 0    50   ~ 0
~B_out
Text Label 2000 2150 0    50   ~ 0
~C_out
Text Label 2000 2250 0    50   ~ 0
~H_out
Text Label 2000 2350 0    50   ~ 0
~L_out
Text Label 2000 2450 0    50   ~ 0
~F_out
Text Label 2000 2550 0    50   ~ 0
~ALU_out
Text Label 2000 2650 0    50   ~ 0
~MEM_out
Text Label 2000 2750 0    50   ~ 0
~PC_H_out
Text Label 2000 2850 0    50   ~ 0
~PC_L_out
Text Label 2000 2950 0    50   ~ 0
~STK_H_out
Text Label 2000 3050 0    50   ~ 0
~STK_L_out
Text Label 2000 3150 0    50   ~ 0
~FSET_c
Text Label 2000 3250 0    50   ~ 0
~FSET_z
Text Label 2000 3350 0    50   ~ 0
~FCLR_c
Text Label 2000 3450 0    50   ~ 0
~FCLR_z
Text Label 2000 3550 0    50   ~ 0
TSTATE_reset
Text Label 2000 3650 0    50   ~ 0
HALT
Text Label 2000 3750 0    50   ~ 0
STK_inc
Text Label 2000 3850 0    50   ~ 0
STK_dec
NoConn ~ 700  2150
Wire Wire Line
	2600 750  2000 750 
Wire Wire Line
	2600 850  2000 850 
Wire Wire Line
	2600 950  2000 950 
Wire Wire Line
	2600 1050 2000 1050
Wire Wire Line
	2600 1150 2000 1150
Wire Wire Line
	2600 1250 2000 1250
Wire Wire Line
	2600 1350 2000 1350
Wire Wire Line
	2600 1450 2000 1450
Wire Wire Line
	2600 1550 2000 1550
Wire Wire Line
	2600 1650 2000 1650
Wire Wire Line
	2600 1750 2000 1750
Wire Wire Line
	2600 1850 2000 1850
Wire Wire Line
	2600 1950 2000 1950
Wire Wire Line
	2600 2050 2000 2050
Wire Wire Line
	2600 2150 2000 2150
Wire Wire Line
	2600 2250 2000 2250
Wire Wire Line
	2600 2350 2000 2350
Wire Wire Line
	2600 2450 2000 2450
Wire Wire Line
	2600 2550 2000 2550
Wire Wire Line
	2600 2650 2000 2650
Wire Wire Line
	2600 2750 2000 2750
Wire Wire Line
	2600 2850 2000 2850
Wire Wire Line
	2600 2950 2000 2950
Wire Wire Line
	2600 3050 2000 3050
Wire Wire Line
	2600 3150 2000 3150
Wire Wire Line
	2600 3250 2000 3250
Wire Wire Line
	2600 3350 2000 3350
Wire Wire Line
	2600 3450 2000 3450
Wire Wire Line
	2600 3550 2000 3550
Wire Wire Line
	2600 3650 2000 3650
Wire Wire Line
	2600 3750 2000 3750
Wire Wire Line
	2600 3850 2000 3850
Text Label 3400 750  2    50   ~ 0
DATA0
Text Label 3400 850  2    50   ~ 0
DATA1
Text Label 3400 950  2    50   ~ 0
DATA2
Text Label 3400 1050 2    50   ~ 0
DATA3
Text Label 3400 1150 2    50   ~ 0
DATA4
Text Label 3400 1250 2    50   ~ 0
DATA5
Text Label 3400 1350 2    50   ~ 0
DATA6
Text Label 3400 1450 2    50   ~ 0
DATA7
Text Label 3400 1550 2    50   ~ 0
INSTR0
Text Label 3400 1650 2    50   ~ 0
INSTR1
Text Label 3400 1750 2    50   ~ 0
INSTR2
Text Label 3400 1850 2    50   ~ 0
INSTR3
Text Label 3400 1950 2    50   ~ 0
INSTR4
Text Label 3400 2050 2    50   ~ 0
INSTR5
Text Label 3400 2150 2    50   ~ 0
INSTR6
Text Label 3400 2250 2    50   ~ 0
INSTR7
Text Label 3400 2350 2    50   ~ 0
ALUFUNC0
Text Label 3400 2450 2    50   ~ 0
ALUFUNC1
Text Label 3400 2550 2    50   ~ 0
ALUFUNC2
Text Label 3400 2650 2    50   ~ 0
ALUFUNC3
Text Label 3400 2750 2    50   ~ 0
ALUFUNC4
Text Label 3900 750  0    50   ~ 0
A0
Text Label 3900 850  0    50   ~ 0
A1
Text Label 3900 950  0    50   ~ 0
A2
Text Label 3900 1050 0    50   ~ 0
A3
Text Label 3900 1150 0    50   ~ 0
A4
Text Label 3900 1250 0    50   ~ 0
A5
Text Label 3900 1350 0    50   ~ 0
A6
Text Label 3900 1450 0    50   ~ 0
A7
Text Label 3900 1550 0    50   ~ 0
A8
Text Label 3900 1650 0    50   ~ 0
A9
Text Label 3900 1750 0    50   ~ 0
A10
Text Label 3900 1850 0    50   ~ 0
A11
Text Label 3900 1950 0    50   ~ 0
A12
Text Label 3900 2050 0    50   ~ 0
A13
Text Label 3900 2150 0    50   ~ 0
A14
Text Label 3900 2250 0    50   ~ 0
A15
Text Label 3900 2350 0    50   ~ 0
FLAGS0
Text Label 3900 2450 0    50   ~ 0
FLAGS1
Text Label 3900 2550 0    50   ~ 0
FLAGS2
Text Label 3900 2650 0    50   ~ 0
FLAGS3
Text Label 3900 2750 0    50   ~ 0
TSTATE0
Text Label 3900 2850 0    50   ~ 0
TSTATE1
Text Label 3900 2950 0    50   ~ 0
TSTATE2
Text Label 3900 3050 0    50   ~ 0
TSTATE3
NoConn ~ 4350 1050
NoConn ~ 4350 1150
NoConn ~ 4350 1250
NoConn ~ 4350 1350
NoConn ~ 4350 1450
NoConn ~ 4350 1550
NoConn ~ 4350 1650
NoConn ~ 4350 1750
NoConn ~ 4350 1850
NoConn ~ 4350 1950
NoConn ~ 4350 2050
NoConn ~ 4350 2150
NoConn ~ 4350 2250
NoConn ~ 4350 2350
NoConn ~ 4350 2450
NoConn ~ 4350 2550
NoConn ~ 4350 2650
NoConn ~ 4350 750 
NoConn ~ 4350 850 
NoConn ~ 4350 950 
NoConn ~ 4350 3050
NoConn ~ 4350 3850
NoConn ~ 4350 3750
NoConn ~ 4350 3650
NoConn ~ 4350 3550
NoConn ~ 4350 3450
NoConn ~ 4350 3350
NoConn ~ 4350 3250
NoConn ~ 4350 3150
NoConn ~ 4350 2950
NoConn ~ 4350 2850
NoConn ~ 4350 2750
Wire Wire Line
	4350 750  3900 750 
Wire Wire Line
	4350 850  3900 850 
Wire Wire Line
	4350 950  3900 950 
Wire Wire Line
	4350 1050 3900 1050
Wire Wire Line
	4350 1150 3900 1150
Wire Wire Line
	4350 1250 3900 1250
Wire Wire Line
	4350 1350 3900 1350
Wire Wire Line
	4350 1450 3900 1450
Wire Wire Line
	4350 1550 3900 1550
Wire Wire Line
	4350 1650 3900 1650
Wire Wire Line
	4350 1750 3900 1750
Wire Wire Line
	4350 1850 3900 1850
Wire Wire Line
	4350 1950 3900 1950
Wire Wire Line
	4350 2050 3900 2050
Wire Wire Line
	4350 2150 3900 2150
Wire Wire Line
	4350 2250 3900 2250
Wire Wire Line
	4350 2350 3900 2350
Wire Wire Line
	4350 2450 3900 2450
Wire Wire Line
	4350 2550 3900 2550
Wire Wire Line
	4350 2650 3900 2650
Wire Wire Line
	4350 2750 3900 2750
Wire Wire Line
	4350 2850 3900 2850
Wire Wire Line
	4350 2950 3900 2950
Wire Wire Line
	4350 3050 3900 3050
Wire Wire Line
	4350 3150 3900 3150
Wire Wire Line
	4350 3250 3900 3250
Wire Wire Line
	4350 3350 3900 3350
Wire Wire Line
	4350 3450 3900 3450
Wire Wire Line
	4350 3550 3900 3550
Wire Wire Line
	4350 3650 3900 3650
Wire Wire Line
	4350 3750 3900 3750
Wire Wire Line
	4350 3850 3900 3850
NoConn ~ 2850 1050
NoConn ~ 2850 2650
NoConn ~ 2850 2550
NoConn ~ 2850 2450
NoConn ~ 2850 2350
NoConn ~ 2850 2250
NoConn ~ 2850 2050
NoConn ~ 2850 1950
NoConn ~ 2850 1850
NoConn ~ 2850 1750
NoConn ~ 2850 1650
NoConn ~ 2850 1550
NoConn ~ 2850 1450
NoConn ~ 2850 1350
NoConn ~ 2850 1250
NoConn ~ 2850 1150
NoConn ~ 2850 950 
NoConn ~ 2850 850 
NoConn ~ 2850 750 
NoConn ~ 2850 3350
NoConn ~ 2850 3250
NoConn ~ 2850 3150
NoConn ~ 2850 3050
NoConn ~ 2850 2950
NoConn ~ 2850 2850
NoConn ~ 2850 2750
NoConn ~ 2850 3450
NoConn ~ 2850 3550
NoConn ~ 2850 3650
NoConn ~ 2850 3750
NoConn ~ 2850 3850
Wire Wire Line
	3400 750  2850 750 
Wire Wire Line
	2850 850  3400 850 
Wire Wire Line
	2850 950  3400 950 
Wire Wire Line
	2850 1050 3400 1050
Wire Wire Line
	2850 1150 3400 1150
Wire Wire Line
	2850 1250 3400 1250
Wire Wire Line
	2850 1350 3400 1350
Wire Wire Line
	2850 1450 3400 1450
Wire Wire Line
	2850 1550 3400 1550
Wire Wire Line
	2850 1650 3400 1650
Wire Wire Line
	2850 1750 3400 1750
Wire Wire Line
	2850 1850 3400 1850
Wire Wire Line
	2850 1950 3400 1950
Wire Wire Line
	2850 2050 3400 2050
NoConn ~ 2850 2150
Wire Wire Line
	2850 2150 3400 2150
Wire Wire Line
	2850 2250 3400 2250
Wire Wire Line
	2850 2350 3400 2350
Wire Wire Line
	2850 2450 3400 2450
Wire Wire Line
	2850 2550 3400 2550
Wire Wire Line
	2850 2650 3400 2650
Wire Wire Line
	2850 2750 3400 2750
Wire Wire Line
	2850 2850 3400 2850
Wire Wire Line
	2850 2950 3400 2950
Wire Wire Line
	2850 3050 3400 3050
Wire Wire Line
	2850 3150 3400 3150
Wire Wire Line
	2850 3250 3400 3250
Wire Wire Line
	2850 3350 3400 3350
Wire Wire Line
	2850 3450 3400 3450
Wire Wire Line
	2850 3550 3400 3550
Wire Wire Line
	2850 3650 3400 3650
Wire Wire Line
	2850 3750 3400 3750
Wire Wire Line
	2850 3850 3400 3850
Wire Wire Line
	700  1050 1500 1050
Wire Wire Line
	700  3850 1500 3850
Wire Wire Line
	700  3750 1500 3750
Wire Wire Line
	700  3650 1500 3650
Wire Wire Line
	700  950  1500 950 
Wire Wire Line
	700  3550 1500 3550
Wire Wire Line
	700  3450 1500 3450
Wire Wire Line
	700  3350 1500 3350
Wire Wire Line
	700  3250 1500 3250
Wire Wire Line
	700  3150 1500 3150
Wire Wire Line
	700  3050 1500 3050
Wire Wire Line
	700  2950 1500 2950
Wire Wire Line
	700  2850 1500 2850
Wire Wire Line
	700  2750 1500 2750
Wire Wire Line
	700  2650 1500 2650
Wire Wire Line
	700  850  1500 850 
Wire Wire Line
	700  2550 1500 2550
Wire Wire Line
	700  2450 1500 2450
Wire Wire Line
	700  2350 1500 2350
Wire Wire Line
	700  2250 1500 2250
Wire Wire Line
	700  2150 1500 2150
Wire Wire Line
	700  2050 1500 2050
Wire Wire Line
	700  1950 1500 1950
Wire Wire Line
	700  1850 1500 1850
Wire Wire Line
	700  1750 1500 1750
Wire Wire Line
	700  1650 1500 1650
Wire Wire Line
	1500 750  700  750 
Wire Wire Line
	700  1550 1500 1550
Wire Wire Line
	700  1450 1500 1450
Wire Wire Line
	700  1350 1500 1350
Wire Wire Line
	700  1250 1500 1250
Wire Wire Line
	700  1150 1500 1150
$Comp
L Connector_Generic:Conn_02x32_Odd_Even BUS1
U 1 1 5EC3909D
P 1800 2250
F 0 "BUS1" H 1850 3875 50  0000 C CNN
F 1 "Conn_02x32_Odd_Even" H 1850 3876 50  0001 C CNN
F 2 "Connector_PinSocket_2.54mm:PinSocket_2x32_P2.54mm_Vertical" H 1800 2250 50  0001 C CNN
F 3 "~" H 1800 2250 50  0001 C CNN
	1    1800 2250
	-1   0    0    -1  
$EndComp
$EndSCHEMATC
