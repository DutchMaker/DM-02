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
L Arduino_Mega2560_Shield:Arduino_Mega2560_Shield XA1
U 1 1 5D7791B9
P 7500 3400
F 0 "XA1" H 7500 1020 60  0000 C CNN
F 1 "Arduino Mega2560" H 7500 914 60  0000 C CNN
F 2 "DM-02_8-Bit_Computer:Arduino_Mega2560_Shield" H 8200 6150 60  0001 C CNN
F 3 "" H 8200 6150 60  0001 C CNN
	1    7500 3400
	1    0    0    -1  
$EndComp
$Comp
L Switch:SW_Push SW1
U 1 1 5D77B0A8
P 4400 1250
F 0 "SW1" H 4400 1535 50  0000 C CNN
F 1 "RESET" H 4400 1444 50  0000 C CNN
F 2 "Button_Switch_THT:SW_Tactile_SKHH_Angled" H 4400 1450 50  0001 C CNN
F 3 "" H 4400 1450 50  0001 C CNN
	1    4400 1250
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H1
U 1 1 5D77B2F7
P 10500 6400
F 0 "H1" H 10600 6400 50  0001 L CNN
F 1 "MountingHole" H 10600 6355 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 10500 6400 50  0001 C CNN
F 3 "~" H 10500 6400 50  0001 C CNN
	1    10500 6400
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H2
U 1 1 5D77B464
P 10900 6400
F 0 "H2" H 11000 6400 50  0001 L CNN
F 1 "MountingHole" H 11000 6355 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 10900 6400 50  0001 C CNN
F 3 "~" H 10900 6400 50  0001 C CNN
	1    10900 6400
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H3
U 1 1 5D77B473
P 10700 6400
F 0 "H3" H 10800 6400 50  0001 L CNN
F 1 "MountingHole" H 10800 6355 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 10700 6400 50  0001 C CNN
F 3 "~" H 10700 6400 50  0001 C CNN
	1    10700 6400
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
L power:GND #PWR0101
U 1 1 5D77B846
P 1650 1200
F 0 "#PWR0101" H 1650 950 50  0001 C CNN
F 1 "GND" H 1655 1027 50  0000 C CNN
F 2 "" H 1650 1200 50  0001 C CNN
F 3 "" H 1650 1200 50  0001 C CNN
	1    1650 1200
	-1   0    0    1   
$EndComp
$Comp
L Connector_Generic:Conn_02x20_Odd_Even J1
U 1 1 5D77B919
P 1850 2100
F 0 "J1" H 1900 3217 50  0000 C CNN
F 1 "BUS1" H 1900 3126 50  0000 C CNN
F 2 "Connector_PinSocket_2.54mm:PinSocket_2x20_P2.54mm_Vertical" H 1850 2100 50  0001 C CNN
F 3 "~" H 1850 2100 50  0001 C CNN
	1    1850 2100
	1    0    0    -1  
$EndComp
$Comp
L Connector_Generic:Conn_02x20_Odd_Even J2
U 1 1 5D77BA10
P 1950 4650
F 0 "J2" H 2000 5767 50  0000 C CNN
F 1 "BUS2" H 2000 5676 50  0000 C CNN
F 2 "Connector_PinSocket_2.54mm:PinSocket_2x20_P2.54mm_Vertical" H 1950 4650 50  0001 C CNN
F 3 "~" H 1950 4650 50  0001 C CNN
	1    1950 4650
	1    0    0    -1  
$EndComp
$Comp
L power:+5V #PWR0102
U 1 1 5D77BAB5
P 2350 1200
F 0 "#PWR0102" H 2350 1050 50  0001 C CNN
F 1 "+5V" H 2300 1350 50  0000 L CNN
F 2 "" H 2350 1200 50  0001 C CNN
F 3 "" H 2350 1200 50  0001 C CNN
	1    2350 1200
	1    0    0    -1  
$EndComp
$Comp
L power:PWR_FLAG #FLG0101
U 1 1 5D77BB66
P 2150 1200
F 0 "#FLG0101" H 2150 1275 50  0001 C CNN
F 1 "PWR_FLAG" H 2150 1374 50  0001 C CNN
F 2 "" H 2150 1200 50  0001 C CNN
F 3 "~" H 2150 1200 50  0001 C CNN
	1    2150 1200
	1    0    0    -1  
$EndComp
Wire Wire Line
	2150 1200 2250 1200
$Comp
L 74xx-Computer-Symbols:VCC #PWR0103
U 1 1 5D77BC4F
P 2250 1200
F 0 "#PWR0103" H 2250 1050 50  0001 C CNN
F 1 "VCC" H 2267 1373 50  0001 C CNN
F 2 "" H 2250 1200 50  0001 C CNN
F 3 "" H 2250 1200 50  0001 C CNN
	1    2250 1200
	1    0    0    -1  
$EndComp
Connection ~ 2250 1200
$Comp
L power:PWR_FLAG #FLG0102
U 1 1 5D77BC96
P 1550 1200
F 0 "#FLG0102" H 1550 1275 50  0001 C CNN
F 1 "PWR_FLAG" H 1550 1374 50  0001 C CNN
F 2 "" H 1550 1200 50  0001 C CNN
F 3 "~" H 1550 1200 50  0001 C CNN
	1    1550 1200
	1    0    0    -1  
$EndComp
Text GLabel 4600 1250 2    50   Input ~ 0
~DEBUG_RESET
Text GLabel 6200 4350 0    50   Input ~ 0
~DEBUG_RESET
Text GLabel 2150 1300 2    31   Input ~ 0
~DEBUG_RESET
Text GLabel 1650 2400 0    50   Input ~ 0
D0
Text GLabel 1650 2500 0    50   Input ~ 0
D1
Text GLabel 1650 2600 0    50   Input ~ 0
D2
Text GLabel 1650 2700 0    50   Input ~ 0
D3
Text GLabel 1650 2800 0    50   Input ~ 0
D4
Text GLabel 1650 2900 0    50   Input ~ 0
D5
Text GLabel 1650 3000 0    50   Input ~ 0
D6
Text GLabel 1650 3100 0    50   Input ~ 0
D7
Text GLabel 2150 2400 2    50   Input ~ 0
A8
Text GLabel 2150 2500 2    50   Input ~ 0
A9
Text GLabel 2150 2600 2    50   Input ~ 0
A10
Text GLabel 2150 2700 2    50   Input ~ 0
A11
Text GLabel 2150 2800 2    50   Input ~ 0
A12
Text GLabel 2150 2900 2    50   Input ~ 0
A13
Text GLabel 2150 3000 2    50   Input ~ 0
A14
Text GLabel 2150 3100 2    50   Input ~ 0
A15
Text GLabel 2150 1600 2    50   Input ~ 0
A0
Text GLabel 2150 1700 2    50   Input ~ 0
A1
Text GLabel 2150 1800 2    50   Input ~ 0
A2
Text GLabel 2150 1900 2    50   Input ~ 0
A3
Text GLabel 2150 2000 2    50   Input ~ 0
A4
Text GLabel 2150 2100 2    50   Input ~ 0
A5
Text GLabel 2150 2200 2    50   Input ~ 0
A6
Text GLabel 2150 2300 2    50   Input ~ 0
A7
$Comp
L 74xx-Computer-Symbols:SW_DPST SW2
U 1 1 5D77E85C
P 4400 1900
F 0 "SW2" H 4400 2225 50  0000 C CNN
F 1 "POWER" H 4400 2134 50  0000 C CNN
F 2 "DM-02:Switch_DPST_Angled" H 4400 1900 50  0001 C CNN
F 3 "" H 4400 1900 50  0001 C CNN
	1    4400 1900
	1    0    0    -1  
$EndComp
Text GLabel 4600 1800 2    50   Input ~ 0
ARDUINO_GND
Text GLabel 4600 2000 2    50   Input ~ 0
ARDUINO_5V
Text GLabel 4200 1800 0    50   Input ~ 0
COMPUTER_GND
Text GLabel 4200 2000 0    50   Input ~ 0
COMPUTER_5V
Text GLabel 4200 1250 0    50   Input ~ 0
ARDUINO_GND
Text GLabel 1500 1200 0    50   Input ~ 0
COMPUTER_GND
Wire Wire Line
	1500 1200 1550 1200
Connection ~ 1650 1200
Connection ~ 1550 1200
Wire Wire Line
	1550 1200 1650 1200
Text GLabel 2400 1200 2    50   Input ~ 0
COMPUTER_5V
Wire Wire Line
	2400 1200 2350 1200
Connection ~ 2350 1200
Wire Wire Line
	2350 1200 2250 1200
$Comp
L Device:LED D1
U 1 1 5D77F011
P 4250 2600
F 0 "D1" H 4242 2345 50  0000 C CNN
F 1 "POWER" H 4242 2436 50  0000 C CNN
F 2 "LED_THT:LED_D5.0mm_Horizontal_O1.27mm_Z3.0mm" H 4250 2600 50  0001 C CNN
F 3 "~" H 4250 2600 50  0001 C CNN
	1    4250 2600
	-1   0    0    1   
$EndComp
$Comp
L Device:R R1
U 1 1 5D77F199
P 4550 2600
F 0 "R1" V 4343 2600 50  0000 C CNN
F 1 "330" V 4434 2600 50  0000 C CNN
F 2 "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal" V 4480 2600 50  0001 C CNN
F 3 "~" H 4550 2600 50  0001 C CNN
	1    4550 2600
	0    1    1    0   
$EndComp
Text GLabel 4100 2600 0    50   Input ~ 0
ARDUINO_5V
Text GLabel 4700 2600 2    50   Input ~ 0
ARDUINO_GND
Text GLabel 6200 5550 0    50   Input ~ 0
ARDUINO_5V
Text GLabel 6200 4650 0    50   Input ~ 0
ARDUINO_GND
NoConn ~ 7350 800 
NoConn ~ 7450 800 
NoConn ~ 7550 800 
NoConn ~ 7650 800 
NoConn ~ 7750 800 
NoConn ~ 6200 4450
NoConn ~ 6200 4750
NoConn ~ 6200 4850
NoConn ~ 6200 4950
NoConn ~ 6200 5050
NoConn ~ 6200 5150
NoConn ~ 6200 5250
NoConn ~ 6200 5350
NoConn ~ 6200 5450
Text GLabel 6200 3350 0    50   Input ~ 0
A8
Text GLabel 6200 3450 0    50   Input ~ 0
A9
Text GLabel 6200 3550 0    50   Input ~ 0
A10
Text GLabel 6200 3650 0    50   Input ~ 0
A11
Text GLabel 6200 3750 0    50   Input ~ 0
A12
Text GLabel 6200 3850 0    50   Input ~ 0
A13
Text GLabel 6200 3950 0    50   Input ~ 0
A14
Text GLabel 6200 4050 0    50   Input ~ 0
A15
Text GLabel 6200 2550 0    50   Input ~ 0
A0
Text GLabel 6200 2650 0    50   Input ~ 0
A1
Text GLabel 6200 2750 0    50   Input ~ 0
A2
Text GLabel 6200 2850 0    50   Input ~ 0
A3
Text GLabel 6200 2950 0    50   Input ~ 0
A4
Text GLabel 6200 3050 0    50   Input ~ 0
A5
Text GLabel 6200 3150 0    50   Input ~ 0
A6
Text GLabel 6200 3250 0    50   Input ~ 0
A7
NoConn ~ 6200 4150
Text GLabel 8800 4850 2    50   Input ~ 0
D0
Text GLabel 8800 4950 2    50   Input ~ 0
D1
Text GLabel 8800 5050 2    50   Input ~ 0
D2
Text GLabel 8800 5150 2    50   Input ~ 0
D3
Text GLabel 8800 5250 2    50   Input ~ 0
D4
Text GLabel 8800 5350 2    50   Input ~ 0
D5
Text GLabel 8800 5450 2    50   Input ~ 0
D6
Text GLabel 8800 5550 2    50   Input ~ 0
D7
Text GLabel 1750 5650 0    50   Input ~ 0
BUS2_20
Text GLabel 1750 3750 0    50   Input ~ 0
BUS2_1
Text GLabel 1750 3850 0    50   Input ~ 0
BUS2_2
Text GLabel 1750 3950 0    50   Input ~ 0
BUS2_3
Text GLabel 1750 4050 0    50   Input ~ 0
BUS2_4
Text GLabel 1750 4150 0    50   Input ~ 0
BUS2_5
Text GLabel 1750 4250 0    50   Input ~ 0
BUS2_6
Text GLabel 1750 4350 0    50   Input ~ 0
BUS2_7
Text GLabel 1750 4450 0    50   Input ~ 0
BUS2_8
Text GLabel 1750 4550 0    50   Input ~ 0
BUS2_9
Text GLabel 1750 4650 0    50   Input ~ 0
BUS2_10
Text GLabel 1750 4750 0    50   Input ~ 0
BUS2_11
Text GLabel 1750 4850 0    50   Input ~ 0
BUS2_12
Text GLabel 1750 4950 0    50   Input ~ 0
BUS2_13
Text GLabel 1750 5050 0    50   Input ~ 0
BUS2_14
Text GLabel 1750 5150 0    50   Input ~ 0
BUS2_15
Text GLabel 1750 5250 0    50   Input ~ 0
BUS2_16
Text GLabel 1750 5350 0    50   Input ~ 0
BUS2_17
Text GLabel 1750 5450 0    50   Input ~ 0
BUS2_18
Text GLabel 1750 5550 0    50   Input ~ 0
BUS2_19
Text GLabel 2250 5650 2    50   Input ~ 0
BUS2_21
Text GLabel 2250 3750 2    50   Input ~ 0
BUS2_40
Text GLabel 2250 3850 2    50   Input ~ 0
BUS2_39
Text GLabel 2250 3950 2    50   Input ~ 0
BUS2_38
Text GLabel 2250 4050 2    50   Input ~ 0
BUS2_37
Text GLabel 2250 4150 2    50   Input ~ 0
BUS2_36
Text GLabel 2250 4250 2    50   Input ~ 0
BUS2_35
Text GLabel 2250 4350 2    50   Input ~ 0
BUS2_34
Text GLabel 2250 4450 2    50   Input ~ 0
BUS2_33
Text GLabel 2250 4550 2    50   Input ~ 0
BUS2_32
Text GLabel 2250 4650 2    50   Input ~ 0
BUS2_31
Text GLabel 2250 4750 2    50   Input ~ 0
BUS2_30
Text GLabel 2250 4850 2    50   Input ~ 0
BUS2_29
Text GLabel 2250 4950 2    50   Input ~ 0
BUS2_28
Text GLabel 2250 5050 2    50   Input ~ 0
BUS2_27
Text GLabel 2250 5150 2    50   Input ~ 0
BUS2_26
Text GLabel 2250 5250 2    50   Input ~ 0
BUS2_25
Text GLabel 2250 5350 2    50   Input ~ 0
BUS2_24
Text GLabel 2250 5450 2    50   Input ~ 0
BUS2_23
Text GLabel 2250 5550 2    50   Input ~ 0
BUS2_22
Text GLabel 6050 2150 0    50   Input ~ 0
BUS2_20
Text GLabel 9000 1250 2    50   Input ~ 0
BUS2_1
Text GLabel 9000 1350 2    50   Input ~ 0
BUS2_2
Text GLabel 9000 1450 2    50   Input ~ 0
BUS2_3
Text GLabel 9000 1550 2    50   Input ~ 0
BUS2_4
Text GLabel 9000 1650 2    50   Input ~ 0
BUS2_5
Text GLabel 9000 1750 2    50   Input ~ 0
BUS2_6
Text GLabel 9000 1850 2    50   Input ~ 0
BUS2_7
Text GLabel 9000 1950 2    50   Input ~ 0
BUS2_8
Text GLabel 9000 2050 2    50   Input ~ 0
BUS2_9
Text GLabel 9000 2150 2    50   Input ~ 0
BUS2_10
Text GLabel 9000 2250 2    50   Input ~ 0
BUS2_11
Text GLabel 9000 2350 2    50   Input ~ 0
BUS2_12
Text GLabel 6050 1950 0    50   Input ~ 0
BUS2_13
Text GLabel 6050 1850 0    50   Input ~ 0
BUS2_14
Text GLabel 6050 1750 0    50   Input ~ 0
BUS2_15
Text GLabel 6050 1650 0    50   Input ~ 0
BUS2_16
Text GLabel 6050 1550 0    50   Input ~ 0
BUS2_17
Text GLabel 6050 1450 0    50   Input ~ 0
BUS2_18
Text GLabel 6050 2050 0    50   Input ~ 0
BUS2_19
Text GLabel 9000 2450 2    50   Input ~ 0
BUS2_21
Text GLabel 9000 4350 2    50   Input ~ 0
BUS2_40
Text GLabel 9000 4250 2    50   Input ~ 0
BUS2_39
Text GLabel 9000 4150 2    50   Input ~ 0
BUS2_38
Text GLabel 9000 4050 2    50   Input ~ 0
BUS2_37
Text GLabel 9000 3950 2    50   Input ~ 0
BUS2_36
Text GLabel 9000 3850 2    50   Input ~ 0
BUS2_35
Text GLabel 9000 3750 2    50   Input ~ 0
BUS2_34
Text GLabel 9000 3650 2    50   Input ~ 0
BUS2_33
Text GLabel 9000 3550 2    50   Input ~ 0
BUS2_32
Text GLabel 9000 3450 2    50   Input ~ 0
BUS2_31
Text GLabel 9000 3350 2    50   Input ~ 0
BUS2_30
Text GLabel 9000 3250 2    50   Input ~ 0
BUS2_29
Text GLabel 9000 3150 2    50   Input ~ 0
BUS2_28
Text GLabel 9000 3050 2    50   Input ~ 0
BUS2_27
Text GLabel 9000 2950 2    50   Input ~ 0
BUS2_26
Text GLabel 9000 2850 2    50   Input ~ 0
BUS2_25
Text GLabel 9000 2750 2    50   Input ~ 0
BUS2_24
Text GLabel 9000 2650 2    50   Input ~ 0
BUS2_23
Text GLabel 9000 2550 2    50   Input ~ 0
BUS2_22
Text GLabel 2150 1400 2    31   Input ~ 0
~RESET
Text GLabel 9000 4750 2    31   Input ~ 0
~RESET
Connection ~ 2150 1200
NoConn ~ 2150 1500
NoConn ~ 1650 1800
Text GLabel 1650 1300 0    39   Input ~ 0
CLOCK1
Text GLabel 1650 1400 0    39   Input ~ 0
CLOCK2
Text GLabel 9000 4450 2    50   Input ~ 0
CLOCK1
Text GLabel 9000 4550 2    50   Input ~ 0
CLOCK2
Text GLabel 9000 4650 2    50   Input ~ 0
BUS1_5
Text GLabel 6050 2250 0    50   Input ~ 0
BUS1_3
Text GLabel 6050 2350 0    50   Input ~ 0
BUS1_4
Text GLabel 1650 2100 0    50   Input ~ 0
BUS1_3
Text GLabel 1650 2200 0    50   Input ~ 0
BUS1_4
Text GLabel 1650 2300 0    50   Input ~ 0
BUS1_5
NoConn ~ 1650 1900
NoConn ~ 1650 2000
NoConn ~ 6200 1250
NoConn ~ 6200 1350
Text GLabel 1650 1700 0    39   Input ~ 0
CLOCK_ENABLE
Text GLabel 7150 650  0    50   Input ~ 0
CLOCK_ENABLE
Wire Wire Line
	7150 650  7250 650 
Wire Wire Line
	7250 650  7250 800 
NoConn ~ 6200 1450
NoConn ~ 6200 1550
NoConn ~ 6200 1650
NoConn ~ 6200 1750
NoConn ~ 6200 1850
NoConn ~ 6200 1950
NoConn ~ 6200 2050
NoConn ~ 6200 2150
NoConn ~ 6200 2250
NoConn ~ 6200 2350
NoConn ~ 8800 4750
NoConn ~ 8800 4650
NoConn ~ 8800 4550
NoConn ~ 8800 4450
NoConn ~ 8800 4350
NoConn ~ 8800 4250
NoConn ~ 8800 4150
NoConn ~ 8800 4050
NoConn ~ 8800 3950
NoConn ~ 8800 3850
NoConn ~ 8800 3750
NoConn ~ 8800 3650
NoConn ~ 8800 3550
NoConn ~ 8800 3450
NoConn ~ 8800 3350
NoConn ~ 8800 3250
NoConn ~ 8800 3150
NoConn ~ 8800 3050
NoConn ~ 8800 2950
NoConn ~ 8800 2850
NoConn ~ 8800 2750
NoConn ~ 8800 2650
NoConn ~ 8800 2550
NoConn ~ 8800 2450
NoConn ~ 8800 2350
NoConn ~ 8800 2250
NoConn ~ 8800 2150
NoConn ~ 8800 2050
NoConn ~ 8800 1950
NoConn ~ 8800 1850
NoConn ~ 8800 1750
NoConn ~ 8800 1650
NoConn ~ 8800 1550
NoConn ~ 8800 1450
NoConn ~ 8800 1350
NoConn ~ 8800 1250
Text GLabel 1650 1500 0    39   Input ~ 0
~CLOCK1
Text GLabel 1650 1600 0    39   Input ~ 0
~CLOCK2
$EndSCHEMATC
