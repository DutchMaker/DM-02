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
P 11450 10850
F 0 "H3" H 11550 10850 50  0001 L CNN
F 1 "MountingHole" H 11550 10805 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 11450 10850 50  0001 C CNN
F 3 "~" H 11450 10850 50  0001 C CNN
	1    11450 10850
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H4
U 1 1 5D77B482
P 11650 10850
F 0 "H4" H 11750 10850 50  0001 L CNN
F 1 "MountingHole" H 11750 10805 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 11650 10850 50  0001 C CNN
F 3 "~" H 11650 10850 50  0001 C CNN
	1    11650 10850
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H2
U 1 1 5E971701
P 11650 11050
F 0 "H2" H 11750 11050 50  0001 L CNN
F 1 "MountingHole" H 11750 11005 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 11650 11050 50  0001 C CNN
F 3 "~" H 11650 11050 50  0001 C CNN
	1    11650 11050
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H1
U 1 1 5E9716FF
P 11450 11050
F 0 "H1" H 11550 11050 50  0001 L CNN
F 1 "MountingHole" H 11550 11005 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 11450 11050 50  0001 C CNN
F 3 "~" H 11450 11050 50  0001 C CNN
	1    11450 11050
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H1
U 1 1 5EAAC8FF
P 11450 11050
F 0 "H1" H 11550 11050 50  0001 L CNN
F 1 "MountingHole" H 11550 11005 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 11450 11050 50  0001 C CNN
F 3 "~" H 11450 11050 50  0001 C CNN
	1    11450 11050
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H3
U 1 1 5EAAC900
P 11450 10850
F 0 "H3" H 11550 10850 50  0001 L CNN
F 1 "MountingHole" H 11550 10805 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 11450 10850 50  0001 C CNN
F 3 "~" H 11450 10850 50  0001 C CNN
	1    11450 10850
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H2
U 1 1 5EAAC901
P 11650 11050
F 0 "H2" H 11750 11050 50  0001 L CNN
F 1 "MountingHole" H 11750 11005 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 11650 11050 50  0001 C CNN
F 3 "~" H 11650 11050 50  0001 C CNN
	1    11650 11050
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H4
U 1 1 5EAAC902
P 11650 10850
F 0 "H4" H 11750 10850 50  0001 L CNN
F 1 "MountingHole" H 11750 10805 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 11650 10850 50  0001 C CNN
F 3 "~" H 11650 10850 50  0001 C CNN
	1    11650 10850
	1    0    0    -1  
$EndComp
Text GLabel 2950 800  0    39   Input ~ 0
HALT
Text GLabel 2950 900  0    39   Input ~ 0
CONTINUE
$Comp
L power:GND #PWR01
U 1 1 5D77B846
P 1350 800
F 0 "#PWR01" H 1350 550 50  0001 C CNN
F 1 "GND" H 1355 627 50  0000 C CNN
F 2 "" H 1350 800 50  0001 C CNN
F 3 "" H 1350 800 50  0001 C CNN
	1    1350 800 
	-1   0    0    1   
$EndComp
$Comp
L Connector_Generic:Conn_02x20_Odd_Even J1
U 1 1 5D77B919
P 1550 1700
F 0 "J1" H 1600 2817 50  0000 C CNN
F 1 "BUS1" H 1600 2726 50  0000 C CNN
F 2 "Connector_PinSocket_2.54mm:PinSocket_2x20_P2.54mm_Vertical" H 1550 1700 50  0001 C CNN
F 3 "~" H 1550 1700 50  0001 C CNN
	1    1550 1700
	1    0    0    -1  
$EndComp
$Comp
L Connector_Generic:Conn_02x20_Odd_Even J2
U 1 1 5D77BA10
P 3150 1700
F 0 "J2" H 3200 2817 50  0000 C CNN
F 1 "BUS2" H 3200 2726 50  0000 C CNN
F 2 "Connector_PinSocket_2.54mm:PinSocket_2x20_P2.54mm_Vertical" H 3150 1700 50  0001 C CNN
F 3 "~" H 3150 1700 50  0001 C CNN
	1    3150 1700
	1    0    0    -1  
$EndComp
$Comp
L power:+5V #PWR04
U 1 1 5D77BAB5
P 2050 800
F 0 "#PWR04" H 2050 650 50  0001 C CNN
F 1 "+5V" H 2000 950 50  0000 L CNN
F 2 "" H 2050 800 50  0001 C CNN
F 3 "" H 2050 800 50  0001 C CNN
	1    2050 800 
	1    0    0    -1  
$EndComp
$Comp
L power:PWR_FLAG #FLG02
U 1 1 5D77BB66
P 1850 800
F 0 "#FLG02" H 1850 875 50  0001 C CNN
F 1 "PWR_FLAG" H 1850 974 50  0001 C CNN
F 2 "" H 1850 800 50  0001 C CNN
F 3 "~" H 1850 800 50  0001 C CNN
	1    1850 800 
	1    0    0    -1  
$EndComp
Wire Wire Line
	1850 800  1950 800 
$Comp
L 74xx-Computer-Symbols:VCC #PWR03
U 1 1 5D77BC4F
P 1950 800
F 0 "#PWR03" H 1950 650 50  0001 C CNN
F 1 "VCC" H 1967 973 50  0001 C CNN
F 2 "" H 1950 800 50  0001 C CNN
F 3 "" H 1950 800 50  0001 C CNN
	1    1950 800 
	1    0    0    -1  
$EndComp
Connection ~ 1950 800 
$Comp
L power:PWR_FLAG #FLG01
U 1 1 5D77BC96
P 1250 800
F 0 "#FLG01" H 1250 875 50  0001 C CNN
F 1 "PWR_FLAG" H 1250 974 50  0001 C CNN
F 2 "" H 1250 800 50  0001 C CNN
F 3 "~" H 1250 800 50  0001 C CNN
	1    1250 800 
	1    0    0    -1  
$EndComp
Text GLabel 1350 2000 0    50   Input ~ 0
D0
Text GLabel 1350 2100 0    50   Input ~ 0
D1
Text GLabel 1350 2200 0    50   Input ~ 0
D2
Text GLabel 1350 2300 0    50   Input ~ 0
D3
Text GLabel 1350 2400 0    50   Input ~ 0
D4
Text GLabel 1350 2500 0    50   Input ~ 0
D5
Text GLabel 1350 2600 0    50   Input ~ 0
D6
Text GLabel 1350 2700 0    50   Input ~ 0
D7
Text GLabel 1850 2000 2    50   Input ~ 0
A8
Text GLabel 1850 2100 2    50   Input ~ 0
A9
Text GLabel 1850 2200 2    50   Input ~ 0
A10
Text GLabel 1850 2300 2    50   Input ~ 0
A11
Text GLabel 1850 2400 2    50   Input ~ 0
A12
Text GLabel 1850 2500 2    50   Input ~ 0
A13
Text GLabel 1850 2600 2    50   Input ~ 0
A14
Text GLabel 1850 2700 2    50   Input ~ 0
A15
Text GLabel 1850 1200 2    50   Input ~ 0
A0
Text GLabel 1850 1300 2    50   Input ~ 0
A1
Text GLabel 1850 1400 2    50   Input ~ 0
A2
Text GLabel 1850 1500 2    50   Input ~ 0
A3
Text GLabel 1850 1600 2    50   Input ~ 0
A4
Text GLabel 1850 1700 2    50   Input ~ 0
A5
Text GLabel 1850 1800 2    50   Input ~ 0
A6
Text GLabel 1850 1900 2    50   Input ~ 0
A7
Text GLabel 1200 800  0    39   Input ~ 0
COMPUTER_GND
Wire Wire Line
	1200 800  1250 800 
Connection ~ 1350 800 
Connection ~ 1250 800 
Wire Wire Line
	1250 800  1350 800 
Text GLabel 2100 800  2    39   Input ~ 0
COMPUTER_5V
Wire Wire Line
	2100 800  2050 800 
Connection ~ 2050 800 
Wire Wire Line
	2050 800  1950 800 
Text GLabel 3450 1500 2    39   Input ~ 0
~ALU_out
Text GLabel 2950 1000 0    39   Input ~ 0
~A_load
Text GLabel 2950 1100 0    39   Input ~ 0
~B_load
Text GLabel 2950 1200 0    39   Input ~ 0
~C_load
Text GLabel 2950 1300 0    39   Input ~ 0
~H_load
Text GLabel 2950 1400 0    39   Input ~ 0
~L_load
Text GLabel 2950 1500 0    39   Input ~ 0
~ALU_load
Text GLabel 2950 1600 0    39   Input ~ 0
~F_load
Text GLabel 2950 1700 0    39   Input ~ 0
~MAR_H_load
Text GLabel 2950 1800 0    39   Input ~ 0
~MAR_L_load
Text GLabel 2950 1900 0    39   Input ~ 0
~MEM_load
Text GLabel 2950 2000 0    39   Input ~ 0
~PC_H_load
Text GLabel 2950 2100 0    39   Input ~ 0
~PC_L_load
Text GLabel 3450 1000 2    39   Input ~ 0
~A_out
Text GLabel 3450 1100 2    39   Input ~ 0
~B_out
Text GLabel 3450 1200 2    39   Input ~ 0
~C_out
Text GLabel 3450 1300 2    39   Input ~ 0
~H_out
Text GLabel 3450 1400 2    39   Input ~ 0
~L_out
Text GLabel 3450 1600 2    39   Input ~ 0
~F_out
Text GLabel 1350 1500 0    39   Input ~ 0
ALU_OP0
Text GLabel 1350 1600 0    39   Input ~ 0
ALU_OP1
Text GLabel 2950 2400 0    39   Input ~ 0
IR_load
Text GLabel 3450 800  2    39   Input ~ 0
TSTATE_reset
Text GLabel 3450 1800 2    39   Input ~ 0
STK_dec
Text GLabel 3450 1700 2    39   Input ~ 0
STK_inc
Text GLabel 3450 900  2    39   Input ~ 0
PC_inc
Text GLabel 2950 2500 0    39   Input ~ 0
PC_MAR_transfer
Text GLabel 3450 2500 2    39   Input ~ 0
STK_MAR_transfer
Text GLabel 3450 2400 2    39   Input ~ 0
MAR_inc
Text GLabel 2950 2600 0    39   Input ~ 0
FSET_c
Text GLabel 2950 2700 0    39   Input ~ 0
FSET_z
Text GLabel 3450 2600 2    39   Input ~ 0
FCLR_c
Text GLabel 3450 2700 2    39   Input ~ 0
FCLR_z
Text GLabel 3450 2300 2    39   Input ~ 0
~STK_L_out
Text GLabel 3450 2100 2    39   Input ~ 0
~PC_L_out
Text GLabel 3450 2000 2    39   Input ~ 0
~PC_H_out
Text GLabel 3450 1900 2    39   Input ~ 0
~MEM_out
Connection ~ 1850 800 
NoConn ~ 1850 1100
NoConn ~ 1350 1400
Text GLabel 1350 900  0    39   Input ~ 0
CLOCK_PH0
Text GLabel 1350 1000 0    39   Input ~ 0
CLOCK_PH1
Text GLabel 1350 1700 0    39   Input ~ 0
ALU_OP2
Text GLabel 1350 1800 0    39   Input ~ 0
ALU_OP4
Text GLabel 1350 1900 0    39   Input ~ 0
ALU_OP5
Text GLabel 1350 1100 0    39   Input ~ 0
CLOCK_PH2
Text GLabel 1350 1200 0    39   Input ~ 0
CLOCK_PH3
Text GLabel 1350 1300 0    39   Input ~ 0
CLOCK_ENABLE
Text GLabel 1000 5100 0    39   Input ~ 0
~A_load
Text GLabel 1000 5200 0    39   Input ~ 0
~B_load
Text GLabel 1000 5300 0    39   Input ~ 0
~C_load
Text GLabel 1000 5400 0    39   Input ~ 0
~H_load
Text GLabel 1000 5500 0    39   Input ~ 0
~L_load
Text GLabel 2000 5100 2    39   Input ~ 0
A_clock
Text GLabel 2000 5200 2    39   Input ~ 0
B_clock
Text GLabel 2000 5300 2    39   Input ~ 0
C_clock
Text GLabel 2000 5400 2    39   Input ~ 0
H_clock
Text GLabel 2000 5500 2    39   Input ~ 0
L_clock
NoConn ~ 1000 5600
NoConn ~ 1000 5700
NoConn ~ 1000 5800
NoConn ~ 2000 5800
NoConn ~ 2000 5700
NoConn ~ 2000 5600
Text GLabel 2550 5100 0    50   Input ~ 0
D0
Text GLabel 2550 5200 0    50   Input ~ 0
D1
Text GLabel 2550 5300 0    50   Input ~ 0
D2
Text GLabel 2550 5400 0    50   Input ~ 0
D3
Text GLabel 2550 5500 0    50   Input ~ 0
D4
Text GLabel 2550 5600 0    50   Input ~ 0
D5
Text GLabel 2550 5700 0    50   Input ~ 0
D6
Text GLabel 2550 5800 0    50   Input ~ 0
D7
Text GLabel 3550 5100 2    50   Input ~ 0
D0
Text GLabel 3550 5800 2    50   Input ~ 0
D7
Text GLabel 3550 5700 2    50   Input ~ 0
D6
Text GLabel 3550 5600 2    50   Input ~ 0
D5
Text GLabel 3550 5500 2    50   Input ~ 0
D4
Text GLabel 3550 5400 2    50   Input ~ 0
D3
Text GLabel 3550 5300 2    50   Input ~ 0
D2
Text GLabel 3550 5200 2    50   Input ~ 0
D1
Text GLabel 2550 6100 0    39   Input ~ 0
~A_out
Text GLabel 2550 6000 0    39   Input ~ 0
A_clock
$Comp
L 74xx:74HCT574 U?
U 1 1 5EB0F68E
P 4500 5600
F 0 "U?" H 4600 6300 50  0000 C CNN
F 1 "74HCT574" V 4500 5600 50  0000 C CNN
F 2 "" H 4500 5600 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74HCT574" H 4500 5600 50  0001 C CNN
F 4 "B" H 4700 5100 61  0000 C CNN "Register"
	1    4500 5600
	1    0    0    -1  
$EndComp
Text GLabel 4000 5100 0    50   Input ~ 0
D0
Text GLabel 4000 5200 0    50   Input ~ 0
D1
Text GLabel 4000 5300 0    50   Input ~ 0
D2
Text GLabel 4000 5400 0    50   Input ~ 0
D3
Text GLabel 4000 5500 0    50   Input ~ 0
D4
Text GLabel 4000 5600 0    50   Input ~ 0
D5
Text GLabel 4000 5700 0    50   Input ~ 0
D6
Text GLabel 4000 5800 0    50   Input ~ 0
D7
Text GLabel 5000 5100 2    50   Input ~ 0
D0
Text GLabel 5000 5800 2    50   Input ~ 0
D7
Text GLabel 5000 5700 2    50   Input ~ 0
D6
Text GLabel 5000 5600 2    50   Input ~ 0
D5
Text GLabel 5000 5500 2    50   Input ~ 0
D4
Text GLabel 5000 5400 2    50   Input ~ 0
D3
Text GLabel 5000 5300 2    50   Input ~ 0
D2
Text GLabel 5000 5200 2    50   Input ~ 0
D1
Text GLabel 4000 6100 0    39   Input ~ 0
~B_out
Text GLabel 4000 6000 0    39   Input ~ 0
B_clock
$Comp
L 74xx:74HCT574 U?
U 1 1 5EB11422
P 5950 5600
F 0 "U?" H 6050 6300 50  0000 C CNN
F 1 "74HCT574" V 5950 5600 50  0000 C CNN
F 2 "" H 5950 5600 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74HCT574" H 5950 5600 50  0001 C CNN
F 4 "C" H 6150 5100 61  0000 C CNN "Register"
	1    5950 5600
	1    0    0    -1  
$EndComp
Text GLabel 5450 5100 0    50   Input ~ 0
D0
Text GLabel 5450 5200 0    50   Input ~ 0
D1
Text GLabel 5450 5300 0    50   Input ~ 0
D2
Text GLabel 5450 5400 0    50   Input ~ 0
D3
Text GLabel 5450 5500 0    50   Input ~ 0
D4
Text GLabel 5450 5600 0    50   Input ~ 0
D5
Text GLabel 5450 5700 0    50   Input ~ 0
D6
Text GLabel 5450 5800 0    50   Input ~ 0
D7
Text GLabel 6450 5100 2    50   Input ~ 0
D0
Text GLabel 6450 5800 2    50   Input ~ 0
D7
Text GLabel 6450 5700 2    50   Input ~ 0
D6
Text GLabel 6450 5600 2    50   Input ~ 0
D5
Text GLabel 6450 5500 2    50   Input ~ 0
D4
Text GLabel 6450 5400 2    50   Input ~ 0
D3
Text GLabel 6450 5300 2    50   Input ~ 0
D2
Text GLabel 6450 5200 2    50   Input ~ 0
D1
Text GLabel 5450 6100 0    39   Input ~ 0
~C_out
Text GLabel 5450 6000 0    39   Input ~ 0
C_clock
$Comp
L 74xx:74HCT574 U?
U 1 1 5EB1143E
P 7400 5600
F 0 "U?" H 7500 6300 50  0000 C CNN
F 1 "74HCT574" V 7400 5600 50  0000 C CNN
F 2 "" H 7400 5600 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74HCT574" H 7400 5600 50  0001 C CNN
F 4 "H" H 7600 5100 61  0000 C CNN "Register"
	1    7400 5600
	1    0    0    -1  
$EndComp
Text GLabel 6900 5100 0    50   Input ~ 0
D0
Text GLabel 6900 5200 0    50   Input ~ 0
D1
Text GLabel 6900 5300 0    50   Input ~ 0
D2
Text GLabel 6900 5400 0    50   Input ~ 0
D3
Text GLabel 6900 5500 0    50   Input ~ 0
D4
Text GLabel 6900 5600 0    50   Input ~ 0
D5
Text GLabel 6900 5700 0    50   Input ~ 0
D6
Text GLabel 6900 5800 0    50   Input ~ 0
D7
Text GLabel 7900 5100 2    50   Input ~ 0
D0
Text GLabel 7900 5800 2    50   Input ~ 0
D7
Text GLabel 7900 5700 2    50   Input ~ 0
D6
Text GLabel 7900 5600 2    50   Input ~ 0
D5
Text GLabel 7900 5500 2    50   Input ~ 0
D4
Text GLabel 7900 5400 2    50   Input ~ 0
D3
Text GLabel 7900 5300 2    50   Input ~ 0
D2
Text GLabel 7900 5200 2    50   Input ~ 0
D1
Text GLabel 6900 6100 0    39   Input ~ 0
~H_out
Text GLabel 6900 6000 0    39   Input ~ 0
H_clock
$Comp
L 74xx:74HCT574 U?
U 1 1 5EB14221
P 8850 5600
F 0 "U?" H 8950 6300 50  0000 C CNN
F 1 "74HCT574" V 8850 5600 50  0000 C CNN
F 2 "" H 8850 5600 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74HCT574" H 8850 5600 50  0001 C CNN
F 4 "L" H 9050 5100 61  0000 C CNN "Register"
	1    8850 5600
	1    0    0    -1  
$EndComp
Text GLabel 8350 5100 0    50   Input ~ 0
D0
Text GLabel 8350 5200 0    50   Input ~ 0
D1
Text GLabel 8350 5300 0    50   Input ~ 0
D2
Text GLabel 8350 5400 0    50   Input ~ 0
D3
Text GLabel 8350 5500 0    50   Input ~ 0
D4
Text GLabel 8350 5600 0    50   Input ~ 0
D5
Text GLabel 8350 5700 0    50   Input ~ 0
D6
Text GLabel 8350 5800 0    50   Input ~ 0
D7
Text GLabel 9350 5100 2    50   Input ~ 0
D0
Text GLabel 9350 5800 2    50   Input ~ 0
D7
Text GLabel 9350 5700 2    50   Input ~ 0
D6
Text GLabel 9350 5600 2    50   Input ~ 0
D5
Text GLabel 9350 5500 2    50   Input ~ 0
D4
Text GLabel 9350 5400 2    50   Input ~ 0
D3
Text GLabel 9350 5300 2    50   Input ~ 0
D2
Text GLabel 9350 5200 2    50   Input ~ 0
D1
Text GLabel 8350 6100 0    39   Input ~ 0
~L_out
Text GLabel 8350 6000 0    39   Input ~ 0
L_clock
Wire Wire Line
	1500 4800 3050 4800
Connection ~ 3050 4800
Wire Wire Line
	3050 4800 4500 4800
Connection ~ 4500 4800
Wire Wire Line
	4500 4800 5950 4800
Connection ~ 5950 4800
Wire Wire Line
	5950 4800 7400 4800
Connection ~ 7400 4800
Wire Wire Line
	7400 4800 8850 4800
Wire Wire Line
	1500 6400 3050 6400
Connection ~ 3050 6400
Wire Wire Line
	3050 6400 4500 6400
Connection ~ 4500 6400
Wire Wire Line
	4500 6400 5950 6400
Connection ~ 5950 6400
Wire Wire Line
	5950 6400 7400 6400
Connection ~ 7400 6400
Wire Wire Line
	7400 6400 8850 6400
$Comp
L 74xx:74HC240 U?
U 1 1 5EB0A1D5
P 1500 5600
F 0 "U?" H 1500 6581 50  0000 C CNN
F 1 "74HC240" H 1500 6490 50  0000 C CNN
F 2 "" H 1500 5600 50  0001 C CNN
F 3 "https://assets.nexperia.com/documents/data-sheet/74HC_HCT240.pdf" H 1500 5600 50  0001 C CNN
	1    1500 5600
	1    0    0    -1  
$EndComp
$Comp
L power:+5V #PWR?
U 1 1 5EB1A53C
P 8850 4800
F 0 "#PWR?" H 8850 4650 50  0001 C CNN
F 1 "+5V" H 8800 4950 50  0000 L CNN
F 2 "" H 8850 4800 50  0001 C CNN
F 3 "" H 8850 4800 50  0001 C CNN
	1    8850 4800
	0    1    1    0   
$EndComp
$Comp
L 74xx:74HCT574 U?
U 1 1 5EA2E316
P 3050 5600
F 0 "U?" H 3150 6300 50  0000 C CNN
F 1 "74HCT574" V 3050 5600 50  0000 C CNN
F 2 "" H 3050 5600 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74HCT574" H 3050 5600 50  0001 C CNN
F 4 "A" H 3250 5100 61  0000 C CNN "Register"
	1    3050 5600
	1    0    0    -1  
$EndComp
Wire Wire Line
	1000 6000 1000 6100
Connection ~ 8850 4800
$Comp
L power:GND #PWR?
U 1 1 5EB19E55
P 8850 6400
F 0 "#PWR?" H 8850 6150 50  0001 C CNN
F 1 "GND" H 8855 6227 50  0000 C CNN
F 2 "" H 8850 6400 50  0001 C CNN
F 3 "" H 8850 6400 50  0001 C CNN
	1    8850 6400
	0    -1   -1   0   
$EndComp
Connection ~ 8850 6400
$Comp
L 74xx:74LS191 U?
U 1 1 5EB12A22
P 5700 1500
F 0 "U?" H 5700 1550 50  0000 C CNN
F 1 "74LS191" H 5700 1450 50  0000 C CNN
F 2 "" H 5700 1500 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS191" H 5700 1500 50  0001 C CNN
	1    5700 1500
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74HCT02 U?
U 2 1 5EB149A7
P 1450 3750
F 0 "U?" H 1450 3750 50  0000 C CNN
F 1 "74HCT02" H 1750 3650 50  0000 C CNN
F 2 "" H 1450 3750 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74hct02" H 1450 3750 50  0001 C CNN
	2    1450 3750
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74HCT02 U?
U 3 1 5EB18026
P 1450 4200
F 0 "U?" H 1450 4200 50  0000 C CNN
F 1 "74HCT02" H 1750 4100 50  0000 C CNN
F 2 "" H 1450 4200 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74hct02" H 1450 4200 50  0001 C CNN
	3    1450 4200
	1    0    0    -1  
$EndComp
Wire Wire Line
	1150 3400 1150 3500
Wire Wire Line
	1150 3500 1750 3500
Wire Wire Line
	1750 3500 1750 3750
Wire Wire Line
	1750 3300 1750 3450
Wire Wire Line
	1750 3450 1550 3450
Wire Wire Line
	1550 3450 1550 3550
Wire Wire Line
	1550 3550 1150 3550
Wire Wire Line
	1150 3550 1150 3650
Text GLabel 1000 3200 0    39   Input ~ 0
STK_inc
Text GLabel 1000 3850 0    39   Input ~ 0
STK_dec
Wire Wire Line
	1000 3200 1100 3200
Wire Wire Line
	1000 3850 1050 3850
Wire Wire Line
	1150 4100 1100 4100
Wire Wire Line
	1100 4100 1100 3200
Connection ~ 1100 3200
Wire Wire Line
	1100 3200 1150 3200
Wire Wire Line
	1050 3850 1050 4300
Wire Wire Line
	1050 4300 1150 4300
Connection ~ 1050 3850
Wire Wire Line
	1050 3850 1150 3850
$Comp
L 74xx:74HCT02 U?
U 1 1 5EB1474C
P 1450 3300
F 0 "U?" H 1450 3300 50  0000 C CNN
F 1 "74HCT02" H 1750 3200 50  0000 C CNN
F 2 "" H 1450 3300 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74hct02" H 1450 3300 50  0001 C CNN
	1    1450 3300
	1    0    0    -1  
$EndComp
Text GLabel 1850 3300 2    39   Input ~ 0
DOWN_~UP
Wire Wire Line
	1750 3300 1850 3300
Connection ~ 1750 3300
Text GLabel 1850 4200 2    39   Input ~ 0
~CLK_EN
Wire Wire Line
	1850 4200 1750 4200
Text GLabel 5200 1100 0    50   Input ~ 0
D0
Text GLabel 5200 1200 0    50   Input ~ 0
D1
Text GLabel 5200 1300 0    50   Input ~ 0
D2
Text GLabel 5200 1400 0    50   Input ~ 0
D3
Text GLabel 5200 2900 0    50   Input ~ 0
D4
Text GLabel 5200 3000 0    50   Input ~ 0
D5
Text GLabel 5200 3100 0    50   Input ~ 0
D6
Text GLabel 5200 3200 0    50   Input ~ 0
D7
$Comp
L 74xx:74LS191 U?
U 1 1 5EB3CFBE
P 5700 3300
F 0 "U?" H 5700 3350 50  0000 C CNN
F 1 "74LS191" H 5700 3250 50  0000 C CNN
F 2 "" H 5700 3300 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS191" H 5700 3300 50  0001 C CNN
	1    5700 3300
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS32 U?
U 1 1 5EB44312
P 3350 3300
F 0 "U?" H 3350 3300 50  0000 C CNN
F 1 "74LS32" H 3600 3200 50  0000 C CNN
F 2 "" H 3350 3300 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS32" H 3350 3300 50  0001 C CNN
	1    3350 3300
	1    0    0    -1  
$EndComp
Wire Wire Line
	3050 3400 3050 3550
Text GLabel 2950 2200 0    39   Input ~ 0
~STK_H_load
Text GLabel 2950 2300 0    39   Input ~ 0
~STK_L_load
Text GLabel 3450 2200 2    39   Input ~ 0
~STK_H_out
Text GLabel 2900 3200 0    39   Input ~ 0
~STK_H_load
Text GLabel 2900 3900 0    39   Input ~ 0
~STK_L_load
Wire Wire Line
	2900 3900 3050 3900
Wire Wire Line
	3050 3200 2900 3200
Wire Wire Line
	2900 3550 3050 3550
Connection ~ 3050 3550
Wire Wire Line
	3050 3550 3050 3700
Text GLabel 1850 900  2    39   Input ~ 0
~DEBUG_RESET
Text GLabel 1850 1000 2    39   Input ~ 0
~RESET
Text GLabel 2900 3550 0    39   Input ~ 0
CLOCK_PH3
$Comp
L 74xx:74LS191 U?
U 1 1 5EB5E750
P 9500 1500
F 0 "U?" H 9500 1550 50  0000 C CNN
F 1 "74LS191" H 9500 1450 50  0000 C CNN
F 2 "" H 9500 1500 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS191" H 9500 1500 50  0001 C CNN
	1    9500 1500
	1    0    0    -1  
$EndComp
Text GLabel 9000 1100 0    50   Input ~ 0
D0
Text GLabel 9000 1200 0    50   Input ~ 0
D1
Text GLabel 9000 1300 0    50   Input ~ 0
D2
Text GLabel 9000 1400 0    50   Input ~ 0
D3
Text GLabel 9000 2900 0    50   Input ~ 0
D4
Text GLabel 9000 3000 0    50   Input ~ 0
D5
Text GLabel 9000 3100 0    50   Input ~ 0
D6
Text GLabel 9000 3200 0    50   Input ~ 0
D7
$Comp
L 74xx:74LS191 U?
U 1 1 5EB5E766
P 9500 3300
F 0 "U?" H 9500 3350 50  0000 C CNN
F 1 "74LS191" H 9500 3250 50  0000 C CNN
F 2 "" H 9500 3300 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS191" H 9500 3300 50  0001 C CNN
	1    9500 3300
	1    0    0    -1  
$EndComp
Text GLabel 5200 1700 0    39   Input ~ 0
DOWN_~UP
Text GLabel 5200 3500 0    39   Input ~ 0
DOWN_~UP
Text GLabel 9000 1700 0    39   Input ~ 0
DOWN_~UP
Text GLabel 9000 3500 0    39   Input ~ 0
DOWN_~UP
Text GLabel 5200 3700 0    39   Input ~ 0
~CLK_EN
Text GLabel 5200 1900 0    39   Input ~ 0
~CLK_EN
Text GLabel 9000 1900 0    39   Input ~ 0
~CLK_EN
Text GLabel 9000 3700 0    39   Input ~ 0
~CLK_EN
Text GLabel 9000 2000 0    39   Input ~ 0
CLOCK_PH3
$Comp
L 74xx:74HC245 U?
U 1 1 5EB80D5C
P 7700 1600
F 0 "U?" H 7700 1400 50  0000 C CNN
F 1 "74HC245" H 7700 1300 50  0000 C CNN
F 2 "" H 7700 1600 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74HC245" H 7700 1600 50  0001 C CNN
	1    7700 1600
	1    0    0    -1  
$EndComp
Text GLabel 7200 2100 0    39   Input ~ 0
~STK_H_out
$Comp
L power:GND #PWR?
U 1 1 5EB8450C
P 7200 2000
F 0 "#PWR?" H 7200 1750 50  0001 C CNN
F 1 "GND" V 7200 1800 50  0000 C CNN
F 2 "" H 7200 2000 50  0001 C CNN
F 3 "" H 7200 2000 50  0001 C CNN
	1    7200 2000
	0    1    1    0   
$EndComp
Wire Wire Line
	6200 1100 7200 1100
Wire Wire Line
	6200 1200 7200 1200
Wire Wire Line
	7200 1300 6200 1300
Wire Wire Line
	6200 1400 7200 1400
Wire Wire Line
	7200 1800 6800 1800
Wire Wire Line
	6800 1800 6800 3200
Wire Wire Line
	6800 3200 6200 3200
Wire Wire Line
	6200 3100 6750 3100
Wire Wire Line
	6750 3100 6750 1700
Wire Wire Line
	6750 1700 7200 1700
Wire Wire Line
	7200 1600 6700 1600
Wire Wire Line
	6700 1600 6700 3000
Wire Wire Line
	6700 3000 6200 3000
Wire Wire Line
	6200 2900 6650 2900
Wire Wire Line
	6650 2900 6650 1500
Wire Wire Line
	6650 1500 7200 1500
NoConn ~ 6200 1800
NoConn ~ 6200 3600
NoConn ~ 10000 3600
NoConn ~ 10000 1800
Text GLabel 8200 1100 2    50   Input ~ 0
D0
Text GLabel 8200 1200 2    50   Input ~ 0
D1
Text GLabel 8200 1300 2    50   Input ~ 0
D2
Text GLabel 8200 1400 2    50   Input ~ 0
D3
Text GLabel 8200 1500 2    50   Input ~ 0
D4
Text GLabel 8200 1600 2    50   Input ~ 0
D5
Text GLabel 8200 1700 2    50   Input ~ 0
D6
Text GLabel 8200 1800 2    50   Input ~ 0
D7
Text GLabel 10000 1600 2    50   Input ~ 0
LOW0_Rc
Text GLabel 9000 3800 0    50   Input ~ 0
LOW0_Rc
Text GLabel 10000 3400 2    50   Input ~ 0
LOW1_Rc
Text GLabel 4250 3800 2    39   Input ~ 0
~LOW_PL
Text GLabel 5200 1600 0    39   Input ~ 0
~HIGH_PL
Text GLabel 5200 3400 0    39   Input ~ 0
~HIGH_PL
Text GLabel 9000 1600 0    39   Input ~ 0
~LOW_PL
Text GLabel 9000 3400 0    39   Input ~ 0
~LOW_PL
Text GLabel 6200 1600 2    50   Input ~ 0
HIGH0_Rc
NoConn ~ 6200 3400
Text GLabel 5200 3800 0    50   Input ~ 0
HIGH0_Rc
Text GLabel 5200 2000 0    50   Input ~ 0
LOW1_Rc
$Comp
L 74xx:74HC245 U?
U 1 1 5EBD5A44
P 11500 1600
F 0 "U?" H 11500 1400 50  0000 C CNN
F 1 "74HC245" H 11500 1300 50  0000 C CNN
F 2 "" H 11500 1600 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74HC245" H 11500 1600 50  0001 C CNN
	1    11500 1600
	1    0    0    -1  
$EndComp
Text GLabel 11000 2100 0    39   Input ~ 0
~STK_L_out
$Comp
L power:GND #PWR?
U 1 1 5EBD5A4F
P 11000 2000
F 0 "#PWR?" H 11000 1750 50  0001 C CNN
F 1 "GND" V 11000 1800 50  0000 C CNN
F 2 "" H 11000 2000 50  0001 C CNN
F 3 "" H 11000 2000 50  0001 C CNN
	1    11000 2000
	0    1    1    0   
$EndComp
Wire Wire Line
	10000 1100 11000 1100
Wire Wire Line
	10000 1200 11000 1200
Wire Wire Line
	11000 1300 10000 1300
Wire Wire Line
	10000 1400 11000 1400
Wire Wire Line
	11000 1800 10600 1800
Wire Wire Line
	10600 1800 10600 3200
Wire Wire Line
	10600 3200 10000 3200
Wire Wire Line
	10000 3100 10550 3100
Wire Wire Line
	10550 3100 10550 1700
Wire Wire Line
	10550 1700 11000 1700
Wire Wire Line
	11000 1600 10500 1600
Wire Wire Line
	10500 1600 10500 3000
Wire Wire Line
	10500 3000 10000 3000
Wire Wire Line
	10000 2900 10450 2900
Wire Wire Line
	10450 2900 10450 1500
Wire Wire Line
	10450 1500 11000 1500
Text GLabel 12000 1100 2    50   Input ~ 0
D0
Text GLabel 12000 1200 2    50   Input ~ 0
D1
Text GLabel 12000 1300 2    50   Input ~ 0
D2
Text GLabel 12000 1400 2    50   Input ~ 0
D3
Text GLabel 12000 1500 2    50   Input ~ 0
D4
Text GLabel 12000 1600 2    50   Input ~ 0
D5
Text GLabel 12000 1700 2    50   Input ~ 0
D6
Text GLabel 12000 1800 2    50   Input ~ 0
D7
Wire Wire Line
	5700 2300 5700 2400
Wire Wire Line
	9500 2400 9500 2300
Wire Wire Line
	5700 2400 7700 2400
Connection ~ 7700 2400
Wire Wire Line
	7700 2400 9500 2400
Wire Wire Line
	9500 2400 11500 2400
Connection ~ 9500 2400
Wire Wire Line
	5700 4100 9500 4100
Wire Wire Line
	9500 4100 11500 4100
Wire Wire Line
	11500 4100 11500 2400
Connection ~ 9500 4100
Connection ~ 11500 2400
Wire Wire Line
	9500 2600 5700 2600
Wire Wire Line
	5700 800  4750 800 
Wire Wire Line
	4750 800  4750 2600
Wire Wire Line
	4750 2600 5700 2600
Connection ~ 5700 2600
Wire Wire Line
	5700 800  7700 800 
Connection ~ 5700 800 
Connection ~ 7700 800 
Wire Wire Line
	7700 800  9500 800 
Connection ~ 9500 800 
Wire Wire Line
	9500 800  11500 800 
$Comp
L power:+5V #PWR?
U 1 1 5EBF9D81
P 4750 800
F 0 "#PWR?" H 4750 650 50  0001 C CNN
F 1 "+5V" H 4700 950 50  0000 L CNN
F 2 "" H 4750 800 50  0001 C CNN
F 3 "" H 4750 800 50  0001 C CNN
	1    4750 800 
	1    0    0    -1  
$EndComp
Connection ~ 4750 800 
$Comp
L power:GND #PWR?
U 1 1 5EBFA1E0
P 5700 4100
F 0 "#PWR?" H 5700 3850 50  0001 C CNN
F 1 "GND" H 5705 3927 50  0000 C CNN
F 2 "" H 5700 4100 50  0001 C CNN
F 3 "" H 5700 4100 50  0001 C CNN
	1    5700 4100
	1    0    0    -1  
$EndComp
Connection ~ 5700 4100
Text GLabel 3650 3300 2    39   Input ~ 0
~HIGH_PL
$Comp
L 74xx:74HC02 U?
U 1 1 5EB20C20
P 1350 6650
F 0 "U?" H 1350 6650 50  0000 C CNN
F 1 "74HC02" H 1350 6850 50  0000 C CNN
F 2 "" H 1350 6650 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74hc02" H 1350 6650 50  0001 C CNN
	1    1350 6650
	-1   0    0    1   
$EndComp
Wire Wire Line
	1650 6550 1650 6650
Wire Wire Line
	1750 6650 1650 6650
Connection ~ 1650 6650
Wire Wire Line
	1650 6650 1650 6750
Text GLabel 1750 6650 2    39   Input ~ 0
CLOCK_PH3
Wire Wire Line
	1000 6100 1000 6650
Wire Wire Line
	1000 6650 1050 6650
Connection ~ 1000 6100
$Comp
L 74xx:74HC02 U?
U 1 1 5EB3A9E5
P 3350 3800
F 0 "U?" H 3350 3800 50  0000 C CNN
F 1 "74HC02" H 3300 3550 50  0000 C CNN
F 2 "" H 3350 3800 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74hc02" H 3350 3800 50  0001 C CNN
	1    3350 3800
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74HC02 U?
U 1 1 5EB3DE91
P 3950 3800
F 0 "U?" H 3950 3800 50  0000 C CNN
F 1 "74HC02" H 3950 3550 50  0000 C CNN
F 2 "" H 3950 3800 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74hc02" H 3950 3800 50  0001 C CNN
	1    3950 3800
	1    0    0    -1  
$EndComp
Wire Wire Line
	3650 3700 3650 3800
Connection ~ 3650 3800
Wire Wire Line
	3650 3800 3650 3900
$EndSCHEMATC
