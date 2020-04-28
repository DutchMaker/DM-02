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
L 74xx:74HCT574 U?
U 1 1 5EA2E316
P 6200 1700
F 0 "U?" H 6300 2400 50  0000 C CNN
F 1 "74HCT574" V 6200 1700 50  0000 C CNN
F 2 "" H 6200 1700 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74HCT574" H 6200 1700 50  0001 C CNN
	1    6200 1700
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H1
U 1 1 5EAAC8FF
P 10500 6400
F 0 "H1" H 10600 6400 50  0001 L CNN
F 1 "MountingHole" H 10600 6355 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 10500 6400 50  0001 C CNN
F 3 "~" H 10500 6400 50  0001 C CNN
	1    10500 6400
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H3
U 1 1 5EAAC900
P 10900 6400
F 0 "H3" H 11000 6400 50  0001 L CNN
F 1 "MountingHole" H 11000 6355 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 10900 6400 50  0001 C CNN
F 3 "~" H 10900 6400 50  0001 C CNN
	1    10900 6400
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H2
U 1 1 5EAAC901
P 10700 6400
F 0 "H2" H 10800 6400 50  0001 L CNN
F 1 "MountingHole" H 10800 6355 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 10700 6400 50  0001 C CNN
F 3 "~" H 10700 6400 50  0001 C CNN
	1    10700 6400
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H4
U 1 1 5EAAC902
P 11100 6400
F 0 "H4" H 11200 6400 50  0001 L CNN
F 1 "MountingHole" H 11200 6355 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 11100 6400 50  0001 C CNN
F 3 "~" H 11100 6400 50  0001 C CNN
	1    11100 6400
	1    0    0    -1  
$EndComp
Text GLabel 2950 800  0    50   Input ~ 0
HALT
Text GLabel 2950 900  0    50   Input ~ 0
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
L Connector_Generic:Conn_02x20_Odd_Even J2
U 1 1 5D77B919
P 1550 1700
F 0 "J2" H 1600 2817 50  0000 C CNN
F 1 "BUS1" H 1600 2726 50  0000 C CNN
F 2 "Connector_PinSocket_2.54mm:PinSocket_2x20_P2.54mm_Vertical" H 1550 1700 50  0001 C CNN
F 3 "~" H 1550 1700 50  0001 C CNN
	1    1550 1700
	1    0    0    -1  
$EndComp
$Comp
L Connector_Generic:Conn_02x20_Odd_Even J3
U 1 1 5D77BA10
P 3150 1700
F 0 "J3" H 3200 2817 50  0000 C CNN
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
Text GLabel 1850 900  2    31   Input ~ 0
~DEBUG_RESET
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
Text GLabel 1200 800  0    50   Input ~ 0
COMPUTER_GND
Wire Wire Line
	1200 800  1250 800 
Connection ~ 1350 800 
Connection ~ 1250 800 
Wire Wire Line
	1250 800  1350 800 
Text GLabel 2100 800  2    50   Input ~ 0
COMPUTER_5V
Wire Wire Line
	2100 800  2050 800 
Connection ~ 2050 800 
Wire Wire Line
	2050 800  1950 800 
Text GLabel 2950 2700 0    50   Input ~ 0
BUS2_20
Text GLabel 2950 1000 0    50   Input ~ 0
BUS2_3
Text GLabel 2950 1100 0    50   Input ~ 0
BUS2_4
Text GLabel 2950 1200 0    50   Input ~ 0
BUS2_5
Text GLabel 2950 1300 0    50   Input ~ 0
BUS2_6
Text GLabel 2950 1400 0    50   Input ~ 0
BUS2_7
Text GLabel 2950 1500 0    50   Input ~ 0
BUS2_8
Text GLabel 2950 1600 0    50   Input ~ 0
BUS2_9
Text GLabel 2950 1700 0    50   Input ~ 0
BUS2_10
Text GLabel 2950 1800 0    50   Input ~ 0
BUS2_11
Text GLabel 2950 1900 0    50   Input ~ 0
BUS2_12
Text GLabel 2950 2000 0    50   Input ~ 0
BUS2_13
Text GLabel 2950 2100 0    50   Input ~ 0
BUS2_14
Text GLabel 2950 2200 0    50   Input ~ 0
BUS2_15
Text GLabel 2950 2300 0    50   Input ~ 0
BUS2_16
Text GLabel 2950 2400 0    50   Input ~ 0
BUS2_17
Text GLabel 2950 2500 0    50   Input ~ 0
BUS2_18
Text GLabel 2950 2600 0    50   Input ~ 0
BUS2_19
Text GLabel 3450 2700 2    50   Input ~ 0
BUS2_21
Text GLabel 3450 800  2    50   Input ~ 0
BUS2_40
Text GLabel 3450 900  2    50   Input ~ 0
BUS2_39
Text GLabel 3450 1000 2    50   Input ~ 0
BUS2_38
Text GLabel 3450 1100 2    50   Input ~ 0
BUS2_37
Text GLabel 3450 1200 2    50   Input ~ 0
BUS2_36
Text GLabel 3450 1300 2    50   Input ~ 0
BUS2_35
Text GLabel 3450 1400 2    50   Input ~ 0
BUS2_34
Text GLabel 3450 1500 2    50   Input ~ 0
BUS2_33
Text GLabel 3450 1600 2    50   Input ~ 0
BUS2_32
Text GLabel 3450 1700 2    50   Input ~ 0
BUS2_31
Text GLabel 3450 1800 2    50   Input ~ 0
BUS2_30
Text GLabel 3450 1900 2    50   Input ~ 0
BUS2_29
Text GLabel 3450 2000 2    50   Input ~ 0
BUS2_28
Text GLabel 3450 2100 2    50   Input ~ 0
BUS2_27
Text GLabel 3450 2200 2    50   Input ~ 0
BUS2_26
Text GLabel 3450 2300 2    50   Input ~ 0
BUS2_25
Text GLabel 3450 2400 2    50   Input ~ 0
BUS2_24
Text GLabel 3450 2500 2    50   Input ~ 0
BUS2_23
Text GLabel 3450 2600 2    50   Input ~ 0
BUS2_22
Text GLabel 1850 1000 2    31   Input ~ 0
~RESET
Connection ~ 1850 800 
NoConn ~ 1850 1100
NoConn ~ 1350 1400
Text GLabel 1350 900  0    50   Input ~ 0
CLOCK1
Text GLabel 1350 1000 0    50   Input ~ 0
CLOCK2
Text GLabel 1350 1500 0    50   Input ~ 0
BUS1_1
Text GLabel 1350 1600 0    50   Input ~ 0
BUS1_2
Text GLabel 1350 1700 0    50   Input ~ 0
BUS1_3
Text GLabel 1350 1800 0    50   Input ~ 0
BUS1_4
Text GLabel 1350 1900 0    50   Input ~ 0
BUS1_5
Text GLabel 1350 1100 0    39   Input ~ 0
~CLOCK1
Text GLabel 1350 1200 0    39   Input ~ 0
~CLOCK2
Text GLabel 1350 1300 0    50   Input ~ 0
CLOCK_ENABLE
$EndSCHEMATC
