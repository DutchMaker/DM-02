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
$Comp
L Connector_Generic:Conn_02x32_Odd_Even BUS2
U 1 1 5EC6B636
P -1050 2100
F 0 "BUS2" H -1000 3725 50  0000 C CNN
F 1 "Conn_02x32_Odd_Even" H -1000 3726 50  0001 C CNN
F 2 "Connector_PinSocket_2.54mm:PinSocket_2x32_P2.54mm_Vertical" H -1050 2100 50  0001 C CNN
F 3 "~" H -1050 2100 50  0001 C CNN
	1    -1050 2100
	-1   0    0    -1  
$EndComp
$Comp
L Connector_Generic:Conn_02x32_Odd_Even BUS1
U 1 1 5EC3909D
P -3150 2100
F 0 "BUS1" H -3100 3725 50  0000 C CNN
F 1 "Conn_02x32_Odd_Even" H -3100 3726 50  0001 C CNN
F 2 "Connector_PinSocket_2.54mm:PinSocket_2x32_P2.54mm_Vertical" H -3150 2100 50  0001 C CNN
F 3 "~" H -3150 2100 50  0001 C CNN
	1    -3150 2100
	-1   0    0    -1  
$EndComp
Text GLabel -4000 600  0    39   Input ~ 0
GND
Text GLabel -4000 700  0    39   Input ~ 0
CLOCK_PH0
Text GLabel -4000 800  0    39   Input ~ 0
CLOCK_PH2
Text GLabel -4000 900  0    39   Input ~ 0
CLOCK_ENABLE
Text GLabel -4000 1000 0    39   Input ~ 0
BTN_STEP_ENABLE
Text GLabel -4000 1100 0    39   Input ~ 0
BTN_STEP
Text GLabel -4000 1200 0    39   Input ~ 0
BTN_CONTINUE
Text GLabel -4000 1300 0    39   Input ~ 0
RESET
Text GLabel -4000 1400 0    39   Input ~ 0
IO_load
Text GLabel -4000 1800 0    39   Input ~ 0
~A_load
Text GLabel -4000 1900 0    39   Input ~ 0
~B_load
Text GLabel -4000 2000 0    39   Input ~ 0
~C_load
Text GLabel -4000 2100 0    39   Input ~ 0
~H_load
Text GLabel -4000 2200 0    39   Input ~ 0
~L_load
Text GLabel -4000 2300 0    39   Input ~ 0
~F_load
Text GLabel -4000 2400 0    39   Input ~ 0
~ALU_load
Text GLabel -4000 2500 0    39   Input ~ 0
~MEM_load
Text GLabel -4000 2600 0    39   Input ~ 0
~PC_H_load
Text GLabel -4000 2700 0    39   Input ~ 0
~PC_L_load
Text GLabel -4000 2800 0    39   Input ~ 0
~STK_H_load
Text GLabel -4000 2900 0    39   Input ~ 0
~STK_L_load
Text GLabel -4000 3000 0    39   Input ~ 0
~MAR_H_load
Text GLabel -4000 3100 0    39   Input ~ 0
~MAR_L_load
Text GLabel -4000 3200 0    39   Input ~ 0
~IR_load
Text GLabel -4000 3300 0    39   Input ~ 0
~PC_MAR_transfer
Text GLabel -4000 3400 0    39   Input ~ 0
~STK_MAR_transfer
Text GLabel -4000 3500 0    39   Input ~ 0
PC_inc
Text GLabel -4000 3600 0    39   Input ~ 0
~MAR_inc
Text GLabel -4000 3700 0    39   Input ~ 0
FETCH_done
Text GLabel -2500 3700 2    39   Input ~ 0
STK_dec
Text GLabel -2500 3600 2    39   Input ~ 0
STK_inc
Text GLabel -2500 3500 2    39   Input ~ 0
HALT
Text GLabel -2500 3400 2    39   Input ~ 0
TSTATE_reset
Text GLabel -2500 3300 2    39   Input ~ 0
~FCLR_z
Text GLabel -2500 3200 2    39   Input ~ 0
~FCLR_c
Text GLabel -2500 3100 2    39   Input ~ 0
~FSET_z
Text GLabel -2500 3000 2    39   Input ~ 0
~FSET_c
Text GLabel -2500 2900 2    39   Input ~ 0
~STK_L_out
Text GLabel -2500 2800 2    39   Input ~ 0
~STK_H_out
Text GLabel -2500 2700 2    39   Input ~ 0
~PC_L_out
Text GLabel -2500 2600 2    39   Input ~ 0
~PC_H_out
Text GLabel -2500 2500 2    39   Input ~ 0
~MEM_out
Text GLabel -2500 2400 2    39   Input ~ 0
~ALU_out
Text GLabel -2500 2300 2    39   Input ~ 0
~F_out
Text GLabel -2500 2200 2    39   Input ~ 0
~L_out
Text GLabel -2500 2100 2    39   Input ~ 0
~H_out
Text GLabel -2500 2000 2    39   Input ~ 0
~C_out
Text GLabel -2500 1900 2    39   Input ~ 0
~B_out
Text GLabel -2500 1800 2    39   Input ~ 0
~A_out
Text GLabel -2500 1400 2    39   Input ~ 0
IO_out
Text GLabel -2500 800  2    39   Input ~ 0
CLOCK_PH3
Text GLabel -2500 700  2    39   Input ~ 0
CLOCK_PH1
Text GLabel -2500 600  2    39   Input ~ 0
5V
Text GLabel -1700 600  0    39   Input ~ 0
DATA0
Text GLabel -1700 700  0    39   Input ~ 0
DATA1
Text GLabel -1700 800  0    39   Input ~ 0
DATA2
Text GLabel -1700 900  0    39   Input ~ 0
DATA3
Text GLabel -1700 1000 0    39   Input ~ 0
DATA4
Text GLabel -1700 1100 0    39   Input ~ 0
DATA5
Text GLabel -1700 1200 0    39   Input ~ 0
DATA6
Text GLabel -1700 1300 0    39   Input ~ 0
DATA7
Text GLabel -1700 1400 0    39   Input ~ 0
INSTR0
Text GLabel -1700 1500 0    39   Input ~ 0
INSTR1
Text GLabel -1700 1600 0    39   Input ~ 0
INSTR2
Text GLabel -1700 1700 0    39   Input ~ 0
INSTR3
Text GLabel -1700 1800 0    39   Input ~ 0
INSTR4
Text GLabel -1700 1900 0    39   Input ~ 0
INSTR5
Text GLabel -1700 2000 0    39   Input ~ 0
INSTR6
Text GLabel -1700 2100 0    39   Input ~ 0
INSTR7
Text GLabel -1700 2200 0    39   Input ~ 0
ALUFUNC0
Text GLabel -1700 2300 0    39   Input ~ 0
ALUFUNC1
Text GLabel -1700 2400 0    39   Input ~ 0
ALUFUNC2
Text GLabel -1700 2500 0    39   Input ~ 0
ALUFUNC3
Text GLabel -1700 2600 0    39   Input ~ 0
ALUFUNC4
Text GLabel -550 2600 2    39   Input ~ 0
TSTATE0
Text GLabel -550 2500 2    39   Input ~ 0
FLAGS3
Text GLabel -550 2400 2    39   Input ~ 0
FLAGS2
Text GLabel -550 2300 2    39   Input ~ 0
FLAGS1
Text GLabel -550 2200 2    39   Input ~ 0
FLAGS0
Text GLabel -550 2100 2    39   Input ~ 0
A15
Text GLabel -550 2000 2    39   Input ~ 0
A14
Text GLabel -550 1900 2    39   Input ~ 0
A13
Text GLabel -550 1800 2    39   Input ~ 0
A12
Text GLabel -550 1700 2    39   Input ~ 0
A11
Text GLabel -550 1600 2    39   Input ~ 0
A10
Text GLabel -550 1500 2    39   Input ~ 0
A9
Text GLabel -550 1400 2    39   Input ~ 0
A8
Text GLabel -550 1300 2    39   Input ~ 0
A7
Text GLabel -550 1200 2    39   Input ~ 0
A6
Text GLabel -550 1100 2    39   Input ~ 0
A5
Text GLabel -550 1000 2    39   Input ~ 0
A4
Text GLabel -550 900  2    39   Input ~ 0
A3
Text GLabel -550 800  2    39   Input ~ 0
A2
Text GLabel -550 700  2    39   Input ~ 0
A1
Text GLabel -550 600  2    39   Input ~ 0
A0
Text GLabel -550 2900 2    39   Input ~ 0
TSTATE3
Text GLabel -550 2800 2    39   Input ~ 0
TSTATE2
Text GLabel -550 2700 2    39   Input ~ 0
TSTATE1
Wire Wire Line
	-850 600  -550 600 
Wire Wire Line
	-550 700  -850 700 
Wire Wire Line
	-850 800  -550 800 
Wire Wire Line
	-550 900  -850 900 
Wire Wire Line
	-850 1000 -550 1000
Wire Wire Line
	-550 1100 -850 1100
Wire Wire Line
	-850 1200 -550 1200
Wire Wire Line
	-550 1300 -850 1300
Wire Wire Line
	-850 1400 -550 1400
Wire Wire Line
	-550 1500 -850 1500
Wire Wire Line
	-850 1600 -550 1600
Wire Wire Line
	-550 1700 -850 1700
Wire Wire Line
	-850 1800 -550 1800
Wire Wire Line
	-550 1900 -850 1900
Wire Wire Line
	-850 2000 -550 2000
Wire Wire Line
	-550 2100 -850 2100
Wire Wire Line
	-850 2200 -550 2200
Wire Wire Line
	-550 2300 -850 2300
Wire Wire Line
	-850 2400 -550 2400
Wire Wire Line
	-550 2500 -850 2500
Wire Wire Line
	-850 2600 -550 2600
Wire Wire Line
	-550 2700 -850 2700
Wire Wire Line
	-850 2800 -550 2800
Wire Wire Line
	-550 2900 -850 2900
NoConn ~ -550 3000
NoConn ~ -550 3100
NoConn ~ -550 3200
NoConn ~ -550 3300
NoConn ~ -550 3400
NoConn ~ -550 3500
NoConn ~ -550 3600
NoConn ~ -550 3700
Wire Wire Line
	-550 3700 -850 3700
Wire Wire Line
	-850 3600 -550 3600
Wire Wire Line
	-550 3500 -850 3500
Wire Wire Line
	-850 3400 -550 3400
Wire Wire Line
	-550 3300 -850 3300
Wire Wire Line
	-550 3200 -850 3200
Wire Wire Line
	-550 3100 -850 3100
Wire Wire Line
	-550 3000 -850 3000
Text Label -850 600  0    39   ~ 0
A0
Text Label -850 700  0    39   ~ 0
A1
Text Label -850 800  0    39   ~ 0
A2
Text Label -850 900  0    39   ~ 0
A3
Text Label -850 1000 0    39   ~ 0
A4
Text Label -850 1100 0    39   ~ 0
A5
Text Label -850 1200 0    39   ~ 0
A6
Text Label -850 1300 0    39   ~ 0
A7
Text Label -850 1400 0    39   ~ 0
A8
Text Label -850 1500 0    39   ~ 0
A9
Text Label -850 1600 0    39   ~ 0
A10
Text Label -850 1700 0    39   ~ 0
A11
Text Label -850 1800 0    39   ~ 0
A12
Text Label -850 1900 0    39   ~ 0
A13
Text Label -850 2000 0    39   ~ 0
A14
Text Label -850 2100 0    39   ~ 0
A15
Text Label -850 2200 0    39   ~ 0
FLAGS0
Text Label -850 2300 0    39   ~ 0
FLAGS1
Text Label -850 2400 0    39   ~ 0
FLAGS2
Text Label -850 2500 0    39   ~ 0
FLAGS3
Text Label -850 2600 0    39   ~ 0
TSTATE0
Text Label -850 2700 0    39   ~ 0
TSTATE1
Text Label -850 2800 0    39   ~ 0
TSTATE2
Text Label -850 2900 0    39   ~ 0
TSTATE3
Text Label -850 3000 0    39   ~ 0
B2NC18
Text Label -850 3100 0    39   ~ 0
B2NC17
Text Label -850 3200 0    39   ~ 0
B2NC16
Text Label -850 3300 0    39   ~ 0
B2NC15
Text Label -850 3400 0    39   ~ 0
B2NC14
Text Label -850 3500 0    39   ~ 0
B2NC13
Text Label -850 3600 0    39   ~ 0
B2NC12
Text Label -850 3700 0    39   ~ 0
B2NC11
Wire Wire Line
	-1350 3700 -1700 3700
Wire Wire Line
	-1700 3600 -1350 3600
Wire Wire Line
	-1350 3500 -1700 3500
Wire Wire Line
	-1700 3400 -1350 3400
Wire Wire Line
	-1350 3300 -1700 3300
Wire Wire Line
	-1700 3200 -1350 3200
Wire Wire Line
	-1350 3100 -1700 3100
Wire Wire Line
	-1700 3000 -1350 3000
Wire Wire Line
	-1350 2900 -1700 2900
Wire Wire Line
	-1700 2800 -1350 2800
Wire Wire Line
	-1350 2700 -1700 2700
Wire Wire Line
	-1700 2600 -1350 2600
Wire Wire Line
	-1350 2500 -1700 2500
Wire Wire Line
	-1700 2400 -1350 2400
Wire Wire Line
	-1350 2300 -1700 2300
Wire Wire Line
	-1700 2200 -1350 2200
Wire Wire Line
	-1350 2100 -1700 2100
Wire Wire Line
	-1700 2000 -1350 2000
Wire Wire Line
	-1350 1900 -1700 1900
Wire Wire Line
	-1700 1800 -1350 1800
Wire Wire Line
	-1350 1700 -1700 1700
Wire Wire Line
	-1700 1600 -1350 1600
Wire Wire Line
	-1350 1500 -1700 1500
Wire Wire Line
	-1700 1400 -1350 1400
Wire Wire Line
	-1700 600  -1350 600 
Wire Wire Line
	-1350 700  -1700 700 
Wire Wire Line
	-1700 800  -1350 800 
Wire Wire Line
	-1350 900  -1700 900 
Wire Wire Line
	-1700 1000 -1350 1000
Wire Wire Line
	-1700 1100 -1350 1100
Wire Wire Line
	-1700 1200 -1350 1200
Wire Wire Line
	-1700 1300 -1350 1300
Text Label -1350 3700 2    39   ~ 0
B2NC10
Text Label -1350 3600 2    39   ~ 0
B2NC9
Text Label -1350 3500 2    39   ~ 0
B2NC8
Text Label -1350 3400 2    39   ~ 0
B2NC7
Text Label -1350 3300 2    39   ~ 0
B2NC6
Text Label -1350 3200 2    39   ~ 0
B2NC5
Text Label -1350 3100 2    39   ~ 0
B2NC4
Text Label -1350 3000 2    39   ~ 0
B2NC3
Text Label -1350 2900 2    39   ~ 0
B2NC2
Text Label -1350 2800 2    39   ~ 0
B2NC1
Text Label -1350 2700 2    39   ~ 0
B2NC0
Text Label -1350 2600 2    39   ~ 0
ALUFUNC4
Text Label -1350 2500 2    39   ~ 0
ALUFUNC3
Text Label -1350 2400 2    39   ~ 0
ALUFUNC2
Text Label -1350 2300 2    39   ~ 0
ALUFUNC1
Text Label -1350 2200 2    39   ~ 0
ALUFUNC0
Text Label -1350 2100 2    39   ~ 0
INSTR7
Text Label -1350 2000 2    39   ~ 0
INSTR6
Text Label -1350 1900 2    39   ~ 0
INSTR5
Text Label -1350 1800 2    39   ~ 0
INSTR4
Text Label -1350 1700 2    39   ~ 0
INSTR3
Text Label -1350 1600 2    39   ~ 0
INSTR2
Text Label -1350 1500 2    39   ~ 0
INSTR1
Text Label -1350 1400 2    39   ~ 0
INSTR0
Text Label -1350 1300 2    39   ~ 0
DATA7
Text Label -1350 1200 2    39   ~ 0
DATA6
Text Label -1350 1100 2    39   ~ 0
DATA5
Text Label -1350 1000 2    39   ~ 0
DATA4
Text Label -1350 900  2    39   ~ 0
DATA3
Text Label -1350 800  2    39   ~ 0
DATA2
Text Label -1350 700  2    39   ~ 0
DATA1
Text Label -1350 600  2    39   ~ 0
DATA0
NoConn ~ -1700 2700
NoConn ~ -1700 2800
NoConn ~ -1700 2900
NoConn ~ -1700 3000
NoConn ~ -1700 3100
NoConn ~ -1700 3200
NoConn ~ -1700 3300
NoConn ~ -1700 3400
NoConn ~ -1700 3500
NoConn ~ -1700 3600
NoConn ~ -1700 3700
Wire Wire Line
	-2500 700  -2950 700 
Wire Wire Line
	-2950 800  -2500 800 
Wire Wire Line
	-2500 900  -2950 900 
Wire Wire Line
	-2950 1000 -2500 1000
Wire Wire Line
	-2500 1100 -2950 1100
Wire Wire Line
	-2950 1200 -2500 1200
Wire Wire Line
	-2500 1300 -2950 1300
Wire Wire Line
	-2950 1400 -2500 1400
Wire Wire Line
	-2500 1500 -2950 1500
Wire Wire Line
	-2950 1600 -2500 1600
Wire Wire Line
	-2500 1700 -2950 1700
Wire Wire Line
	-2950 1800 -2500 1800
Wire Wire Line
	-2500 1900 -2950 1900
Wire Wire Line
	-2950 2000 -2500 2000
Wire Wire Line
	-2500 2100 -2950 2100
Wire Wire Line
	-2950 2200 -2500 2200
Wire Wire Line
	-2500 2300 -2950 2300
Wire Wire Line
	-2950 2400 -2500 2400
Wire Wire Line
	-2500 2500 -2950 2500
Wire Wire Line
	-2950 2600 -2500 2600
Wire Wire Line
	-2500 2700 -2950 2700
Wire Wire Line
	-2950 2800 -2500 2800
Wire Wire Line
	-2500 2900 -2950 2900
Wire Wire Line
	-2500 3700 -2950 3700
Wire Wire Line
	-2950 3600 -2500 3600
Wire Wire Line
	-2500 3500 -2950 3500
Wire Wire Line
	-2950 3400 -2500 3400
Wire Wire Line
	-2500 3300 -2950 3300
Wire Wire Line
	-2500 3200 -2950 3200
Wire Wire Line
	-2500 3100 -2950 3100
Wire Wire Line
	-2500 3000 -2950 3000
Text Label -2950 600  0    39   ~ 0
5V
Text Label -2950 700  0    39   ~ 0
CLOCK_PH1
Text Label -2950 800  0    39   ~ 0
CLOCK_PH3
Text Label -2950 900  0    39   ~ 0
B1NC10
Text Label -2950 1000 0    39   ~ 0
B1NC9
Text Label -2950 1100 0    39   ~ 0
B1NC8
Text Label -2950 1200 0    39   ~ 0
B1NC7
Text Label -2950 1300 0    39   ~ 0
B1NC6
Text Label -2950 1400 0    39   ~ 0
IO_out
Text Label -2950 1500 0    39   ~ 0
B1NC5
Text Label -2950 1600 0    39   ~ 0
B1NC4
Text Label -2950 1700 0    39   ~ 0
B1NC3
Text Label -2950 1800 0    39   ~ 0
~A_out
Text Label -2950 1900 0    39   ~ 0
~B_out
Text Label -2950 2000 0    39   ~ 0
~C_out
Text Label -2950 2100 0    39   ~ 0
~H_out
Text Label -2950 2200 0    39   ~ 0
~L_out
Text Label -2950 2300 0    39   ~ 0
~F_out
Text Label -2950 2400 0    39   ~ 0
~ALU_out
Text Label -2950 2500 0    39   ~ 0
~MEM_out
Text Label -2950 2600 0    39   ~ 0
~PC_H_out
Text Label -2950 2700 0    39   ~ 0
~PC_L_out
Text Label -2950 2800 0    39   ~ 0
~STK_H_out
Text Label -2950 2900 0    39   ~ 0
~STK_L_out
Text Label -2950 3000 0    39   ~ 0
~FSET_c
Text Label -2950 3100 0    39   ~ 0
~FSET_z
Text Label -2950 3200 0    39   ~ 0
~FCLR_c
Text Label -2950 3300 0    39   ~ 0
~FCLR_z
Text Label -2950 3400 0    39   ~ 0
TSTATE_reset
Text Label -2950 3500 0    39   ~ 0
HALT
Text Label -2950 3600 0    39   ~ 0
STK_inc
Text Label -2950 3700 0    39   ~ 0
STK_dec
Wire Wire Line
	-3450 3700 -4000 3700
Wire Wire Line
	-4000 3600 -3450 3600
Wire Wire Line
	-3450 3500 -4000 3500
Wire Wire Line
	-4000 3400 -3450 3400
Wire Wire Line
	-3450 3300 -4000 3300
Wire Wire Line
	-4000 3200 -3450 3200
Wire Wire Line
	-3450 3100 -4000 3100
Wire Wire Line
	-4000 3000 -3450 3000
Wire Wire Line
	-3450 2900 -4000 2900
Wire Wire Line
	-4000 2800 -3450 2800
Wire Wire Line
	-3450 2700 -4000 2700
Wire Wire Line
	-4000 2600 -3450 2600
Wire Wire Line
	-3450 2500 -4000 2500
Wire Wire Line
	-4000 2400 -3450 2400
Wire Wire Line
	-3450 2300 -4000 2300
Wire Wire Line
	-4000 2200 -3450 2200
Wire Wire Line
	-3450 2100 -4000 2100
Wire Wire Line
	-4000 2000 -3450 2000
Wire Wire Line
	-3450 1900 -4000 1900
Wire Wire Line
	-4000 1800 -3450 1800
Wire Wire Line
	-3450 1700 -4000 1700
Wire Wire Line
	-4000 1600 -3450 1600
Wire Wire Line
	-3450 1500 -4000 1500
Wire Wire Line
	-4000 1400 -3450 1400
Wire Wire Line
	-3450 700  -4000 700 
Wire Wire Line
	-4000 800  -3450 800 
Wire Wire Line
	-3450 900  -4000 900 
Wire Wire Line
	-4000 1000 -3450 1000
Wire Wire Line
	-4000 1100 -3450 1100
Wire Wire Line
	-4000 1200 -3450 1200
Wire Wire Line
	-4000 1300 -3450 1300
Text Label -3450 3700 2    39   ~ 0
FETCH_done
Text Label -3450 3600 2    39   ~ 0
~MAR_inc
Text Label -3450 3500 2    39   ~ 0
PC_inc
Text Label -3450 3400 2    39   ~ 0
~STK_MAR_transfer
Text Label -3450 3300 2    39   ~ 0
~PC_MAR_transfer
Text Label -3450 3200 2    39   ~ 0
~IR_load
Text Label -3450 3100 2    39   ~ 0
~MAR_L_load
Text Label -3450 3000 2    39   ~ 0
~MAR_H_load
Text Label -3450 2900 2    39   ~ 0
~STK_L_load
Text Label -3450 2800 2    39   ~ 0
~STK_H_load
Text Label -3450 2700 2    39   ~ 0
~PC_L_load
Text Label -3450 2600 2    39   ~ 0
~PC_H_load
Text Label -3450 2500 2    39   ~ 0
~MEM_load
Text Label -3450 2400 2    39   ~ 0
~ALU_load
Text Label -3450 2300 2    39   ~ 0
~F_load
Text Label -3450 2200 2    39   ~ 0
~L_load
Text Label -3450 2100 2    39   ~ 0
~H_load
Text Label -3450 2000 2    39   ~ 0
~C_load
Text Label -3450 1900 2    39   ~ 0
~B_load
Text Label -3450 1800 2    39   ~ 0
~A_load
Text Label -3450 1700 2    39   ~ 0
B1NC2
Text Label -3450 1600 2    39   ~ 0
B1NC1
Text Label -3450 1500 2    39   ~ 0
B1NC0
Text Label -3450 1400 2    39   ~ 0
IO_load
Text Label -3450 1300 2    39   ~ 0
RESET
Text Label -3450 1200 2    39   ~ 0
BTN_CONTINUE
Text Label -3450 1100 2    39   ~ 0
BTN_STEP
Text Label -3450 1000 2    39   ~ 0
BTN_STEP_ENABLE
Text Label -3450 900  2    39   ~ 0
CLOCK_ENABLE
Text Label -3450 800  2    39   ~ 0
CLOCK_PH2
Text Label -3450 700  2    39   ~ 0
CLOCK_PH0
Text Label -3450 600  2    39   ~ 0
GND
NoConn ~ -2500 1700
NoConn ~ -2500 1600
NoConn ~ -2500 1500
NoConn ~ -2500 1300
NoConn ~ -2500 1200
NoConn ~ -2500 1100
NoConn ~ -2500 1000
NoConn ~ -2500 900 
NoConn ~ -4000 1500
NoConn ~ -4000 1600
NoConn ~ -4000 1700
$Comp
L power:GND #PWR?
U 1 1 5F24E0E0
P -3800 600
F 0 "#PWR?" H -3800 350 50  0001 C CNN
F 1 "GND" H -3795 427 39  0000 C CNN
F 2 "" H -3800 600 50  0001 C CNN
F 3 "" H -3800 600 50  0001 C CNN
	1    -3800 600 
	-1   0    0    1   
$EndComp
$Comp
L power:PWR_FLAG #FLG?
U 1 1 5F24F424
P -3700 600
F 0 "#FLG?" H -3700 675 50  0001 C CNN
F 1 "PWR_FLAG" H -3700 773 50  0001 C CNN
F 2 "" H -3700 600 50  0001 C CNN
F 3 "~" H -3700 600 50  0001 C CNN
	1    -3700 600 
	1    0    0    -1  
$EndComp
$Comp
L power:+5V #PWR?
U 1 1 5F250881
P -2650 600
F 0 "#PWR?" H -2650 450 50  0001 C CNN
F 1 "+5V" H -2635 765 39  0000 C CNN
F 2 "" H -2650 600 50  0001 C CNN
F 3 "" H -2650 600 50  0001 C CNN
	1    -2650 600 
	1    0    0    -1  
$EndComp
$Comp
L power:PWR_FLAG #FLG?
U 1 1 5F24FE4E
P -2750 600
F 0 "#FLG?" H -2750 675 50  0001 C CNN
F 1 "PWR_FLAG" H -2750 773 50  0001 C CNN
F 2 "" H -2750 600 50  0001 C CNN
F 3 "~" H -2750 600 50  0001 C CNN
	1    -2750 600 
	1    0    0    -1  
$EndComp
Wire Wire Line
	-2950 600  -2750 600 
Connection ~ -2750 600 
Wire Wire Line
	-2750 600  -2650 600 
Connection ~ -2650 600 
Wire Wire Line
	-2650 600  -2500 600 
Wire Wire Line
	-4000 600  -3800 600 
Connection ~ -3800 600 
Wire Wire Line
	-3800 600  -3700 600 
Connection ~ -3700 600 
Wire Wire Line
	-3700 600  -3450 600 
$EndSCHEMATC
