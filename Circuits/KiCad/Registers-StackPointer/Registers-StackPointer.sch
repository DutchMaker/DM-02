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
Text GLabel 1150 6400 0    39   Input ~ 0
~A_load
Text GLabel 1150 6500 0    39   Input ~ 0
~B_load
Text GLabel 1150 6600 0    39   Input ~ 0
~C_load
Text GLabel 1150 6700 0    39   Input ~ 0
~H_load
Text GLabel 1150 6800 0    39   Input ~ 0
~L_load
Text GLabel 2150 6400 2    39   Input ~ 0
A_clock
Text GLabel 2150 6500 2    39   Input ~ 0
B_clock
Text GLabel 2150 6600 2    39   Input ~ 0
C_clock
Text GLabel 2150 6700 2    39   Input ~ 0
H_clock
Text GLabel 2150 6800 2    39   Input ~ 0
L_clock
NoConn ~ 1150 6900
NoConn ~ 1150 7000
NoConn ~ 1150 7100
NoConn ~ 2150 7100
NoConn ~ 2150 7000
NoConn ~ 2150 6900
Text GLabel 2700 6400 0    50   Input ~ 0
D0
Text GLabel 2700 6500 0    50   Input ~ 0
D1
Text GLabel 2700 6600 0    50   Input ~ 0
D2
Text GLabel 2700 6700 0    50   Input ~ 0
D3
Text GLabel 2700 6800 0    50   Input ~ 0
D4
Text GLabel 2700 6900 0    50   Input ~ 0
D5
Text GLabel 2700 7000 0    50   Input ~ 0
D6
Text GLabel 2700 7100 0    50   Input ~ 0
D7
Text GLabel 3700 6400 2    50   Input ~ 0
D0
Text GLabel 3700 7100 2    50   Input ~ 0
D7
Text GLabel 3700 7000 2    50   Input ~ 0
D6
Text GLabel 3700 6900 2    50   Input ~ 0
D5
Text GLabel 3700 6800 2    50   Input ~ 0
D4
Text GLabel 3700 6700 2    50   Input ~ 0
D3
Text GLabel 3700 6600 2    50   Input ~ 0
D2
Text GLabel 3700 6500 2    50   Input ~ 0
D1
Text GLabel 2700 7400 0    39   Input ~ 0
~A_out
Text GLabel 2700 7300 0    39   Input ~ 0
A_clock
$Comp
L 74xx:74HCT574 U8
U 1 1 5EB0F68E
P 4650 6900
F 0 "U8" H 4750 7600 50  0000 C CNN
F 1 "74HCT574" V 4650 6900 50  0000 C CNN
F 2 "" H 4650 6900 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74HCT574" H 4650 6900 50  0001 C CNN
F 4 "B" H 4850 6400 61  0000 C CNN "Register"
	1    4650 6900
	1    0    0    -1  
$EndComp
Text GLabel 4150 6400 0    50   Input ~ 0
D0
Text GLabel 4150 6500 0    50   Input ~ 0
D1
Text GLabel 4150 6600 0    50   Input ~ 0
D2
Text GLabel 4150 6700 0    50   Input ~ 0
D3
Text GLabel 4150 6800 0    50   Input ~ 0
D4
Text GLabel 4150 6900 0    50   Input ~ 0
D5
Text GLabel 4150 7000 0    50   Input ~ 0
D6
Text GLabel 4150 7100 0    50   Input ~ 0
D7
Text GLabel 5150 6400 2    50   Input ~ 0
D0
Text GLabel 5150 7100 2    50   Input ~ 0
D7
Text GLabel 5150 7000 2    50   Input ~ 0
D6
Text GLabel 5150 6900 2    50   Input ~ 0
D5
Text GLabel 5150 6800 2    50   Input ~ 0
D4
Text GLabel 5150 6700 2    50   Input ~ 0
D3
Text GLabel 5150 6600 2    50   Input ~ 0
D2
Text GLabel 5150 6500 2    50   Input ~ 0
D1
Text GLabel 4150 7400 0    39   Input ~ 0
~B_out
Text GLabel 4150 7300 0    39   Input ~ 0
B_clock
$Comp
L 74xx:74HCT574 U11
U 1 1 5EB11422
P 6100 6900
F 0 "U11" H 6200 7600 50  0000 C CNN
F 1 "74HCT574" V 6100 6900 50  0000 C CNN
F 2 "" H 6100 6900 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74HCT574" H 6100 6900 50  0001 C CNN
F 4 "C" H 6300 6400 61  0000 C CNN "Register"
	1    6100 6900
	1    0    0    -1  
$EndComp
Text GLabel 5600 6400 0    50   Input ~ 0
D0
Text GLabel 5600 6500 0    50   Input ~ 0
D1
Text GLabel 5600 6600 0    50   Input ~ 0
D2
Text GLabel 5600 6700 0    50   Input ~ 0
D3
Text GLabel 5600 6800 0    50   Input ~ 0
D4
Text GLabel 5600 6900 0    50   Input ~ 0
D5
Text GLabel 5600 7000 0    50   Input ~ 0
D6
Text GLabel 5600 7100 0    50   Input ~ 0
D7
Text GLabel 6600 6400 2    50   Input ~ 0
D0
Text GLabel 6600 7100 2    50   Input ~ 0
D7
Text GLabel 6600 7000 2    50   Input ~ 0
D6
Text GLabel 6600 6900 2    50   Input ~ 0
D5
Text GLabel 6600 6800 2    50   Input ~ 0
D4
Text GLabel 6600 6700 2    50   Input ~ 0
D3
Text GLabel 6600 6600 2    50   Input ~ 0
D2
Text GLabel 6600 6500 2    50   Input ~ 0
D1
Text GLabel 5600 7400 0    39   Input ~ 0
~C_out
Text GLabel 5600 7300 0    39   Input ~ 0
C_clock
$Comp
L 74xx:74HCT574 U13
U 1 1 5EB1143E
P 7550 6900
F 0 "U13" H 7650 7600 50  0000 C CNN
F 1 "74HCT574" V 7550 6900 50  0000 C CNN
F 2 "" H 7550 6900 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74HCT574" H 7550 6900 50  0001 C CNN
F 4 "H" H 7750 6400 61  0000 C CNN "Register"
	1    7550 6900
	1    0    0    -1  
$EndComp
Text GLabel 7050 6400 0    50   Input ~ 0
D0
Text GLabel 7050 6500 0    50   Input ~ 0
D1
Text GLabel 7050 6600 0    50   Input ~ 0
D2
Text GLabel 7050 6700 0    50   Input ~ 0
D3
Text GLabel 7050 6800 0    50   Input ~ 0
D4
Text GLabel 7050 6900 0    50   Input ~ 0
D5
Text GLabel 7050 7000 0    50   Input ~ 0
D6
Text GLabel 7050 7100 0    50   Input ~ 0
D7
Text GLabel 8050 6400 2    50   Input ~ 0
D0
Text GLabel 8050 7100 2    50   Input ~ 0
D7
Text GLabel 8050 7000 2    50   Input ~ 0
D6
Text GLabel 8050 6900 2    50   Input ~ 0
D5
Text GLabel 8050 6800 2    50   Input ~ 0
D4
Text GLabel 8050 6700 2    50   Input ~ 0
D3
Text GLabel 8050 6600 2    50   Input ~ 0
D2
Text GLabel 8050 6500 2    50   Input ~ 0
D1
Text GLabel 7050 7400 0    39   Input ~ 0
~H_out
Text GLabel 7050 7300 0    39   Input ~ 0
H_clock
$Comp
L 74xx:74HCT574 U16
U 1 1 5EB14221
P 9000 6900
F 0 "U16" H 9100 7600 50  0000 C CNN
F 1 "74HCT574" V 9000 6900 50  0000 C CNN
F 2 "" H 9000 6900 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74HCT574" H 9000 6900 50  0001 C CNN
F 4 "L" H 9200 6400 61  0000 C CNN "Register"
	1    9000 6900
	1    0    0    -1  
$EndComp
Text GLabel 8500 6400 0    50   Input ~ 0
D0
Text GLabel 8500 6500 0    50   Input ~ 0
D1
Text GLabel 8500 6600 0    50   Input ~ 0
D2
Text GLabel 8500 6700 0    50   Input ~ 0
D3
Text GLabel 8500 6800 0    50   Input ~ 0
D4
Text GLabel 8500 6900 0    50   Input ~ 0
D5
Text GLabel 8500 7000 0    50   Input ~ 0
D6
Text GLabel 8500 7100 0    50   Input ~ 0
D7
Text GLabel 9500 6400 2    50   Input ~ 0
D0
Text GLabel 9500 7100 2    50   Input ~ 0
D7
Text GLabel 9500 7000 2    50   Input ~ 0
D6
Text GLabel 9500 6900 2    50   Input ~ 0
D5
Text GLabel 9500 6800 2    50   Input ~ 0
D4
Text GLabel 9500 6700 2    50   Input ~ 0
D3
Text GLabel 9500 6600 2    50   Input ~ 0
D2
Text GLabel 9500 6500 2    50   Input ~ 0
D1
Text GLabel 8500 7400 0    39   Input ~ 0
~L_out
Text GLabel 8500 7300 0    39   Input ~ 0
L_clock
Wire Wire Line
	1650 6100 3200 6100
Connection ~ 3200 6100
Wire Wire Line
	3200 6100 4650 6100
Connection ~ 4650 6100
Wire Wire Line
	4650 6100 6100 6100
Connection ~ 6100 6100
Wire Wire Line
	6100 6100 7550 6100
Connection ~ 7550 6100
Wire Wire Line
	7550 6100 9000 6100
Wire Wire Line
	1650 7700 3200 7700
Connection ~ 3200 7700
Wire Wire Line
	3200 7700 4650 7700
Connection ~ 4650 7700
Wire Wire Line
	4650 7700 6100 7700
Connection ~ 6100 7700
Wire Wire Line
	6100 7700 7550 7700
Connection ~ 7550 7700
Wire Wire Line
	7550 7700 9000 7700
$Comp
L 74xx:74HC240 U3
U 1 1 5EB0A1D5
P 1650 6900
F 0 "U3" H 1650 7881 50  0000 C CNN
F 1 "74HC240" H 1650 7790 50  0000 C CNN
F 2 "" H 1650 6900 50  0001 C CNN
F 3 "https://assets.nexperia.com/documents/data-sheet/74HC_HCT240.pdf" H 1650 6900 50  0001 C CNN
	1    1650 6900
	1    0    0    -1  
$EndComp
$Comp
L power:+5V #PWR0101
U 1 1 5EB1A53C
P 9000 6100
F 0 "#PWR0101" H 9000 5950 50  0001 C CNN
F 1 "+5V" H 8950 6250 50  0000 L CNN
F 2 "" H 9000 6100 50  0001 C CNN
F 3 "" H 9000 6100 50  0001 C CNN
	1    9000 6100
	0    1    1    0   
$EndComp
$Comp
L 74xx:74HCT574 U4
U 1 1 5EA2E316
P 3200 6900
F 0 "U4" H 3300 7600 50  0000 C CNN
F 1 "74HCT574" V 3200 6900 50  0000 C CNN
F 2 "" H 3200 6900 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74HCT574" H 3200 6900 50  0001 C CNN
F 4 "A" H 3400 6400 61  0000 C CNN "Register"
	1    3200 6900
	1    0    0    -1  
$EndComp
Wire Wire Line
	1150 7300 1150 7400
Connection ~ 9000 6100
$Comp
L power:GND #PWR0102
U 1 1 5EB19E55
P 9000 7700
F 0 "#PWR0102" H 9000 7450 50  0001 C CNN
F 1 "GND" H 9005 7527 50  0000 C CNN
F 2 "" H 9000 7700 50  0001 C CNN
F 3 "" H 9000 7700 50  0001 C CNN
	1    9000 7700
	0    -1   -1   0   
$EndComp
Connection ~ 9000 7700
$Comp
L 74xx:74LS191 U9
U 1 1 5EB12A22
P 5150 1550
F 0 "U9" H 5150 1600 50  0000 C CNN
F 1 "74LS191" H 5150 1500 50  0000 C CNN
F 2 "" H 5150 1550 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS191" H 5150 1550 50  0001 C CNN
	1    5150 1550
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74HCT02 U2
U 2 1 5EB149A7
P 1600 5050
F 0 "U2" H 1600 5050 50  0000 C CNN
F 1 "74HCT02" H 1900 4950 50  0000 C CNN
F 2 "" H 1600 5050 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74hct02" H 1600 5050 50  0001 C CNN
	2    1600 5050
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74HCT02 U2
U 3 1 5EB18026
P 1600 5500
F 0 "U2" H 1600 5500 50  0000 C CNN
F 1 "74HCT02" H 1900 5400 50  0000 C CNN
F 2 "" H 1600 5500 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74hct02" H 1600 5500 50  0001 C CNN
	3    1600 5500
	1    0    0    -1  
$EndComp
Wire Wire Line
	1300 4700 1300 4800
Wire Wire Line
	1300 4800 1900 4800
Wire Wire Line
	1900 4800 1900 5050
Wire Wire Line
	1900 4600 1900 4750
Wire Wire Line
	1900 4750 1700 4750
Wire Wire Line
	1700 4750 1700 4850
Wire Wire Line
	1700 4850 1300 4850
Wire Wire Line
	1300 4850 1300 4950
Text GLabel 1150 4500 0    39   Input ~ 0
STK_inc
Text GLabel 1150 5150 0    39   Input ~ 0
STK_dec
Wire Wire Line
	1150 4500 1250 4500
Wire Wire Line
	1150 5150 1200 5150
Wire Wire Line
	1300 5400 1250 5400
Wire Wire Line
	1250 5400 1250 4500
Connection ~ 1250 4500
Wire Wire Line
	1250 4500 1300 4500
Wire Wire Line
	1200 5150 1200 5600
Wire Wire Line
	1200 5600 1300 5600
Connection ~ 1200 5150
Wire Wire Line
	1200 5150 1300 5150
$Comp
L 74xx:74HCT02 U2
U 1 1 5EB1474C
P 1600 4600
F 0 "U2" H 1600 4600 50  0000 C CNN
F 1 "74HCT02" H 1900 4700 50  0000 C CNN
F 2 "" H 1600 4600 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74hct02" H 1600 4600 50  0001 C CNN
	1    1600 4600
	1    0    0    -1  
$EndComp
Text GLabel 2000 4600 2    39   Input ~ 0
DOWN_~UP
Wire Wire Line
	1900 4600 2000 4600
Connection ~ 1900 4600
Text GLabel 2000 5500 2    39   Input ~ 0
~CLK_EN
Wire Wire Line
	2000 5500 1900 5500
Text GLabel 4650 1150 0    50   Input ~ 0
D0
Text GLabel 4650 1250 0    50   Input ~ 0
D1
Text GLabel 4650 1350 0    50   Input ~ 0
D2
Text GLabel 4650 1450 0    50   Input ~ 0
D3
Text GLabel 4650 2950 0    50   Input ~ 0
D4
Text GLabel 4650 3050 0    50   Input ~ 0
D5
Text GLabel 4650 3150 0    50   Input ~ 0
D6
Text GLabel 4650 3250 0    50   Input ~ 0
D7
$Comp
L 74xx:74LS191 U10
U 1 1 5EB3CFBE
P 5150 3350
F 0 "U10" H 5150 3400 50  0000 C CNN
F 1 "74LS191" H 5150 3300 50  0000 C CNN
F 2 "" H 5150 3350 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS191" H 5150 3350 50  0001 C CNN
	1    5150 3350
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS32 U5
U 1 1 5EB44312
P 3500 4600
F 0 "U5" H 3500 4600 50  0000 C CNN
F 1 "74LS32" H 3750 4500 50  0000 C CNN
F 2 "" H 3500 4600 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS32" H 3500 4600 50  0001 C CNN
	1    3500 4600
	1    0    0    -1  
$EndComp
Wire Wire Line
	3200 4700 3200 4850
Text GLabel 3050 4500 0    39   Input ~ 0
~STK_H_load
Text GLabel 3050 5200 0    39   Input ~ 0
~STK_L_load
Wire Wire Line
	3050 5200 3200 5200
Wire Wire Line
	3200 4500 3050 4500
Wire Wire Line
	3050 4850 3200 4850
Connection ~ 3200 4850
Wire Wire Line
	3200 4850 3200 5000
Text GLabel 3050 4850 0    39   Input ~ 0
CLOCK_PH3
$Comp
L 74xx:74LS191 U14
U 1 1 5EB5E750
P 8950 1550
F 0 "U14" H 8950 1600 50  0000 C CNN
F 1 "74LS191" H 8950 1500 50  0000 C CNN
F 2 "" H 8950 1550 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS191" H 8950 1550 50  0001 C CNN
	1    8950 1550
	1    0    0    -1  
$EndComp
Text GLabel 8450 1150 0    50   Input ~ 0
D0
Text GLabel 8450 1250 0    50   Input ~ 0
D1
Text GLabel 8450 1350 0    50   Input ~ 0
D2
Text GLabel 8450 1450 0    50   Input ~ 0
D3
Text GLabel 8450 2950 0    50   Input ~ 0
D4
Text GLabel 8450 3050 0    50   Input ~ 0
D5
Text GLabel 8450 3150 0    50   Input ~ 0
D6
Text GLabel 8450 3250 0    50   Input ~ 0
D7
$Comp
L 74xx:74LS191 U15
U 1 1 5EB5E766
P 8950 3350
F 0 "U15" H 8950 3400 50  0000 C CNN
F 1 "74LS191" H 8950 3300 50  0000 C CNN
F 2 "" H 8950 3350 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS191" H 8950 3350 50  0001 C CNN
	1    8950 3350
	1    0    0    -1  
$EndComp
Text GLabel 4650 1750 0    39   Input ~ 0
DOWN_~UP
Text GLabel 4650 3550 0    39   Input ~ 0
DOWN_~UP
Text GLabel 8450 1750 0    39   Input ~ 0
DOWN_~UP
Text GLabel 8450 3550 0    39   Input ~ 0
DOWN_~UP
Text GLabel 4650 3750 0    39   Input ~ 0
~CLK_EN
Text GLabel 4650 1950 0    39   Input ~ 0
~CLK_EN
Text GLabel 8450 1950 0    39   Input ~ 0
~CLK_EN
Text GLabel 8450 3750 0    39   Input ~ 0
~CLK_EN
Text GLabel 8450 2050 0    39   Input ~ 0
CLOCK_PH3
$Comp
L 74xx:74HC245 U12
U 1 1 5EB80D5C
P 7150 1650
F 0 "U12" H 7150 1450 50  0000 C CNN
F 1 "74HC245" H 7150 1350 50  0000 C CNN
F 2 "" H 7150 1650 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74HC245" H 7150 1650 50  0001 C CNN
	1    7150 1650
	1    0    0    -1  
$EndComp
Text GLabel 6650 2150 0    39   Input ~ 0
~STK_H_out
$Comp
L power:GND #PWR0103
U 1 1 5EB8450C
P 6650 2050
F 0 "#PWR0103" H 6650 1800 50  0001 C CNN
F 1 "GND" V 6650 1850 50  0000 C CNN
F 2 "" H 6650 2050 50  0001 C CNN
F 3 "" H 6650 2050 50  0001 C CNN
	1    6650 2050
	0    1    1    0   
$EndComp
Wire Wire Line
	5650 1150 6650 1150
Wire Wire Line
	5650 1250 6650 1250
Wire Wire Line
	6650 1350 5650 1350
Wire Wire Line
	5650 1450 6650 1450
Wire Wire Line
	6650 1850 6250 1850
Wire Wire Line
	6250 1850 6250 3250
Wire Wire Line
	6250 3250 5650 3250
Wire Wire Line
	5650 3150 6200 3150
Wire Wire Line
	6200 3150 6200 1750
Wire Wire Line
	6200 1750 6650 1750
Wire Wire Line
	6650 1650 6150 1650
Wire Wire Line
	6150 1650 6150 3050
Wire Wire Line
	6150 3050 5650 3050
Wire Wire Line
	5650 2950 6100 2950
Wire Wire Line
	6100 2950 6100 1550
Wire Wire Line
	6100 1550 6650 1550
NoConn ~ 5650 1850
NoConn ~ 5650 3650
NoConn ~ 9450 3650
NoConn ~ 9450 1850
Text GLabel 7650 1150 2    50   Input ~ 0
D0
Text GLabel 7650 1250 2    50   Input ~ 0
D1
Text GLabel 7650 1350 2    50   Input ~ 0
D2
Text GLabel 7650 1450 2    50   Input ~ 0
D3
Text GLabel 7650 1550 2    50   Input ~ 0
D4
Text GLabel 7650 1650 2    50   Input ~ 0
D5
Text GLabel 7650 1750 2    50   Input ~ 0
D6
Text GLabel 7650 1850 2    50   Input ~ 0
D7
Text GLabel 8450 3850 0    50   Input ~ 0
LOW0_Rc
Text GLabel 9450 3450 2    50   Input ~ 0
LOW1_Rc
Text GLabel 4400 5100 2    39   Input ~ 0
~LOW_PL
Text GLabel 4650 1650 0    39   Input ~ 0
~HIGH_PL
Text GLabel 4650 3450 0    39   Input ~ 0
~HIGH_PL
Text GLabel 8450 1650 0    39   Input ~ 0
~LOW_PL
Text GLabel 8450 3450 0    39   Input ~ 0
~LOW_PL
Text GLabel 5650 1650 2    50   Output ~ 0
HIGH0_Rc
NoConn ~ 5650 3450
Text GLabel 4650 3850 0    50   Input ~ 0
HIGH0_Rc
Text GLabel 4650 2050 0    50   Input ~ 0
LOW1_Rc
$Comp
L 74xx:74HC245 U17
U 1 1 5EBD5A44
P 10950 1650
F 0 "U17" H 10950 1450 50  0000 C CNN
F 1 "74HC245" H 10950 1350 50  0000 C CNN
F 2 "" H 10950 1650 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74HC245" H 10950 1650 50  0001 C CNN
	1    10950 1650
	1    0    0    -1  
$EndComp
Text GLabel 10450 2150 0    39   Input ~ 0
~STK_L_out
$Comp
L power:GND #PWR0104
U 1 1 5EBD5A4F
P 10450 2050
F 0 "#PWR0104" H 10450 1800 50  0001 C CNN
F 1 "GND" V 10450 1850 50  0000 C CNN
F 2 "" H 10450 2050 50  0001 C CNN
F 3 "" H 10450 2050 50  0001 C CNN
	1    10450 2050
	0    1    1    0   
$EndComp
Wire Wire Line
	9450 1150 10450 1150
Wire Wire Line
	9450 1250 10450 1250
Wire Wire Line
	10450 1350 9450 1350
Wire Wire Line
	9450 1450 10450 1450
Wire Wire Line
	10450 1850 10050 1850
Wire Wire Line
	10050 1850 10050 3250
Wire Wire Line
	10050 3250 9450 3250
Wire Wire Line
	9450 3150 10000 3150
Wire Wire Line
	10000 3150 10000 1750
Wire Wire Line
	10000 1750 10450 1750
Wire Wire Line
	10450 1650 9950 1650
Wire Wire Line
	9950 1650 9950 3050
Wire Wire Line
	9950 3050 9450 3050
Wire Wire Line
	9450 2950 9900 2950
Wire Wire Line
	9900 2950 9900 1550
Wire Wire Line
	9900 1550 10450 1550
Text GLabel 11450 1150 2    50   Input ~ 0
D0
Text GLabel 11450 1250 2    50   Input ~ 0
D1
Text GLabel 11450 1350 2    50   Input ~ 0
D2
Text GLabel 11450 1450 2    50   Input ~ 0
D3
Text GLabel 11450 1550 2    50   Input ~ 0
D4
Text GLabel 11450 1650 2    50   Input ~ 0
D5
Text GLabel 11450 1750 2    50   Input ~ 0
D6
Text GLabel 11450 1850 2    50   Input ~ 0
D7
Wire Wire Line
	5150 2350 5150 2450
Wire Wire Line
	8950 2450 8950 2350
Wire Wire Line
	5150 2450 7150 2450
Connection ~ 7150 2450
Wire Wire Line
	7150 2450 8950 2450
Wire Wire Line
	8950 2450 10950 2450
Connection ~ 8950 2450
Wire Wire Line
	5150 4150 5500 4150
Wire Wire Line
	8950 4150 10950 4150
Wire Wire Line
	10950 4150 10950 2450
Connection ~ 8950 4150
Connection ~ 10950 2450
Wire Wire Line
	8950 2650 5150 2650
Wire Wire Line
	5150 850  4600 850 
Wire Wire Line
	4200 850  4200 2650
Wire Wire Line
	4200 2650 5150 2650
Connection ~ 5150 2650
Wire Wire Line
	5150 850  7150 850 
Connection ~ 5150 850 
Connection ~ 7150 850 
Wire Wire Line
	7150 850  8950 850 
Connection ~ 8950 850 
Wire Wire Line
	8950 850  10950 850 
$Comp
L power:+5V #PWR0105
U 1 1 5EBF9D81
P 4200 850
F 0 "#PWR0105" H 4200 700 50  0001 C CNN
F 1 "+5V" H 4150 1000 50  0000 L CNN
F 2 "" H 4200 850 50  0001 C CNN
F 3 "" H 4200 850 50  0001 C CNN
	1    4200 850 
	1    0    0    -1  
$EndComp
Connection ~ 4200 850 
$Comp
L power:GND #PWR0106
U 1 1 5EBFA1E0
P 5150 4150
F 0 "#PWR0106" H 5150 3900 50  0001 C CNN
F 1 "GND" H 5155 3977 50  0000 C CNN
F 2 "" H 5150 4150 50  0001 C CNN
F 3 "" H 5150 4150 50  0001 C CNN
	1    5150 4150
	1    0    0    -1  
$EndComp
Connection ~ 5150 4150
Text GLabel 3800 4600 2    39   Input ~ 0
~HIGH_PL
$Comp
L 74xx:74HC02 U1
U 1 1 5EB20C20
P 1500 7950
F 0 "U1" H 1500 7950 50  0000 C CNN
F 1 "74HC02" H 1500 8150 50  0000 C CNN
F 2 "" H 1500 7950 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74hc02" H 1500 7950 50  0001 C CNN
	1    1500 7950
	-1   0    0    1   
$EndComp
Wire Wire Line
	1800 7850 1800 7950
Wire Wire Line
	1900 7950 1800 7950
Connection ~ 1800 7950
Wire Wire Line
	1800 7950 1800 8050
Text GLabel 1900 7950 2    39   Input ~ 0
CLOCK_PH3
Wire Wire Line
	1150 7400 1150 7950
Wire Wire Line
	1150 7950 1200 7950
Connection ~ 1150 7400
$Comp
L 74xx:74HC02 U6
U 1 1 5EB3A9E5
P 3500 5100
F 0 "U6" H 3500 5100 50  0000 C CNN
F 1 "74HC02" H 3450 4850 50  0000 C CNN
F 2 "" H 3500 5100 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74hc02" H 3500 5100 50  0001 C CNN
	1    3500 5100
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74HC02 U7
U 1 1 5EB3DE91
P 4100 5100
F 0 "U7" H 4100 5100 50  0000 C CNN
F 1 "74HC02" H 4100 4850 50  0000 C CNN
F 2 "" H 4100 5100 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74hc02" H 4100 5100 50  0001 C CNN
	1    4100 5100
	1    0    0    -1  
$EndComp
Wire Wire Line
	3800 5000 3800 5100
Connection ~ 3800 5100
Wire Wire Line
	3800 5100 3800 5200
$Comp
L Mechanical:MountingHole H3
U 1 1 5E971700
P 11450 11050
F 0 "H3" H 11550 11050 50  0001 L CNN
F 1 "MountingHole" H 11550 11005 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 11450 11050 50  0001 C CNN
F 3 "~" H 11450 11050 50  0001 C CNN
	1    11450 11050
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H4
U 1 1 5D77B482
P 11650 11050
F 0 "H4" H 11750 11050 50  0001 L CNN
F 1 "MountingHole" H 11750 11005 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 11650 11050 50  0001 C CNN
F 3 "~" H 11650 11050 50  0001 C CNN
	1    11650 11050
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H2
U 1 1 5E971701
P 11250 11050
F 0 "H2" H 11350 11050 50  0001 L CNN
F 1 "MountingHole" H 11350 11005 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 11250 11050 50  0001 C CNN
F 3 "~" H 11250 11050 50  0001 C CNN
	1    11250 11050
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H1
U 1 1 5E9716FF
P 11050 11050
F 0 "H1" H 11150 11050 50  0001 L CNN
F 1 "MountingHole" H 11150 11005 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 11050 11050 50  0001 C CNN
F 3 "~" H 11050 11050 50  0001 C CNN
	1    11050 11050
	1    0    0    -1  
$EndComp
NoConn ~ 3100 3200
NoConn ~ 3100 3300
NoConn ~ 3100 3400
NoConn ~ 3100 3500
NoConn ~ 3100 3600
NoConn ~ 3100 3700
NoConn ~ 3100 3800
NoConn ~ 3100 3900
NoConn ~ 2600 3900
NoConn ~ 2600 3800
NoConn ~ 2600 3700
NoConn ~ 2600 3600
NoConn ~ 2600 3500
NoConn ~ 2600 3400
NoConn ~ 2600 3300
NoConn ~ 2600 3200
NoConn ~ 2600 3100
NoConn ~ 2600 3000
NoConn ~ 2600 2900
Text GLabel 2600 2800 0    39   Input ~ 0
ALUFUNC5
Text GLabel 2600 2700 0    39   Input ~ 0
ALUFUNC3
Text GLabel 2600 2600 0    39   Input ~ 0
ALUFUNC2
Text GLabel 2600 2500 0    39   Input ~ 0
ALUFUNC1
Text GLabel 2600 2400 0    39   Input ~ 0
ALUFUNC0
Text GLabel 2600 2300 0    39   Input ~ 0
INSTR7
Text GLabel 2600 2200 0    39   Input ~ 0
INSTR6
Text GLabel 2600 2100 0    39   Input ~ 0
INSTR5
Text GLabel 2600 2000 0    39   Input ~ 0
INSTR4
Text GLabel 2600 1900 0    39   Input ~ 0
INSTR3
Text GLabel 2600 1800 0    39   Input ~ 0
INSTR2
Text GLabel 2600 1700 0    39   Input ~ 0
INSTR1
Text GLabel 2600 1600 0    39   Input ~ 0
INSTR0
Text GLabel 2600 1500 0    39   Input ~ 0
DATA7
Text GLabel 2600 1400 0    39   Input ~ 0
DATA6
Text GLabel 2600 1300 0    39   Input ~ 0
DATA5
Text GLabel 2600 1200 0    39   Input ~ 0
DATA4
Text GLabel 2600 1100 0    39   Input ~ 0
DATA3
Text GLabel 2600 1000 0    39   Input ~ 0
DATA2
Text GLabel 2600 900  0    39   Input ~ 0
DATA1
Text GLabel 2600 800  0    39   Input ~ 0
DATA0
NoConn ~ 1750 1900
NoConn ~ 1750 1800
NoConn ~ 1750 1700
NoConn ~ 1750 1500
NoConn ~ 1750 1400
NoConn ~ 1750 1300
NoConn ~ 1750 1200
NoConn ~ 1750 1100
NoConn ~ 1250 1900
NoConn ~ 1250 1800
NoConn ~ 1250 1700
Text GLabel 1750 800  2    39   Input ~ 0
5V
Text GLabel 1750 900  2    39   Input ~ 0
CLOCK_PH1
Text GLabel 1750 1000 2    39   Input ~ 0
CLOCK_PH3
Text GLabel 1750 1600 2    39   Input ~ 0
IO_out
Text GLabel 1750 2000 2    39   Input ~ 0
~A_out
Text GLabel 1750 2100 2    39   Input ~ 0
~B_out
Text GLabel 1750 2200 2    39   Input ~ 0
~C_out
Text GLabel 1750 2300 2    39   Input ~ 0
~H_out
Text GLabel 1750 2400 2    39   Input ~ 0
~L_out
Text GLabel 1750 2500 2    39   Input ~ 0
~F_out
Text GLabel 1750 2600 2    39   Input ~ 0
~ALU_out
Text GLabel 1750 2700 2    39   Input ~ 0
~MEM_out
Text GLabel 1750 2800 2    39   Input ~ 0
~PC_H_out
Text GLabel 1750 2900 2    39   Input ~ 0
~PC_L_out
Text GLabel 1750 3000 2    39   Input ~ 0
~STK_H_out
Text GLabel 1750 3100 2    39   Input ~ 0
~STK_L_out
Text GLabel 1750 3200 2    39   Input ~ 0
~FSET_c
Text GLabel 1750 3300 2    39   Input ~ 0
~FSET_z
Text GLabel 1750 3400 2    39   Input ~ 0
~FCLR_c
Text GLabel 1750 3500 2    39   Input ~ 0
~FCLR_z
Text GLabel 1750 3600 2    39   Input ~ 0
TSTATE_reset
Text GLabel 1750 3700 2    39   Input ~ 0
HALT
Text GLabel 1750 3800 2    39   Input ~ 0
STK_inc
Text GLabel 1750 3900 2    39   Input ~ 0
STK_dec
Text GLabel 1250 3900 0    39   Input ~ 0
FETCH_done
Text GLabel 1250 3800 0    39   Input ~ 0
~MAR_inc
Text GLabel 1250 3700 0    39   Input ~ 0
PC_inc
Text GLabel 1250 3600 0    39   Input ~ 0
~STK_MAR_transfer
Text GLabel 1250 3500 0    39   Input ~ 0
~PC_MAR_transfer
Text GLabel 1250 3400 0    39   Input ~ 0
~IR_load
Text GLabel 1250 3300 0    39   Input ~ 0
~MAR_L_load
Text GLabel 1250 3200 0    39   Input ~ 0
~MAR_H_load
Text GLabel 1250 3100 0    39   Input ~ 0
~STK_L_load
Text GLabel 1250 3000 0    39   Input ~ 0
~STK_H_load
Text GLabel 1250 2900 0    39   Input ~ 0
~PC_L_load
Text GLabel 1250 2800 0    39   Input ~ 0
~PC_H_load
Text GLabel 1250 2700 0    39   Input ~ 0
~MEM_load
Text GLabel 1250 2600 0    39   Input ~ 0
~ALU_load
Text GLabel 1250 2500 0    39   Input ~ 0
~F_load
Text GLabel 1250 2400 0    39   Input ~ 0
~L_load
Text GLabel 1250 2300 0    39   Input ~ 0
~H_load
Text GLabel 1250 2200 0    39   Input ~ 0
~C_load
Text GLabel 1250 2100 0    39   Input ~ 0
~B_load
Text GLabel 1250 2000 0    39   Input ~ 0
~A_load
Text GLabel 1250 1600 0    39   Input ~ 0
IO_load
Text GLabel 1250 1500 0    39   Input ~ 0
BTN_RESET
Text GLabel 1250 1400 0    39   Input ~ 0
BTN_CONTINUE
Text GLabel 1250 1300 0    39   Input ~ 0
BTN_STEP
Text GLabel 1250 1200 0    39   Input ~ 0
BTN_STEP_ENABLE
Text GLabel 1250 1100 0    39   Input ~ 0
CLOCK_ENABLE
Text GLabel 1250 1000 0    39   Input ~ 0
CLOCK_PH2
Text GLabel 1250 900  0    39   Input ~ 0
CLOCK_PH0
$Comp
L Connector_Generic:Conn_02x32_Odd_Even BUS1
U 1 1 5EC3909D
P 1550 2300
F 0 "BUS1" H 1600 3925 50  0000 C CNN
F 1 "Conn_02x32_Odd_Even" H 1600 3926 50  0001 C CNN
F 2 "Connector_PinSocket_2.54mm:PinSocket_2x32_P2.54mm_Vertical" H 1550 2300 50  0001 C CNN
F 3 "~" H 1550 2300 50  0001 C CNN
	1    1550 2300
	-1   0    0    -1  
$EndComp
$Comp
L Connector_Generic:Conn_02x32_Odd_Even BUS2
U 1 1 5EC6B636
P 2900 2300
F 0 "BUS2" H 2950 3925 50  0000 C CNN
F 1 "Conn_02x32_Odd_Even" H 2950 3926 50  0001 C CNN
F 2 "Connector_PinSocket_2.54mm:PinSocket_2x32_P2.54mm_Vertical" H 2900 2300 50  0001 C CNN
F 3 "~" H 2900 2300 50  0001 C CNN
	1    2900 2300
	-1   0    0    -1  
$EndComp
Text GLabel 9450 1650 2    50   Input ~ 0
LOW0_Rc
Text GLabel 1250 800  0    39   Input ~ 0
GND
Text GLabel 5000 4150 0    39   Input ~ 0
GND
Wire Wire Line
	5000 4150 5150 4150
$Comp
L power:PWR_FLAG #FLG0101
U 1 1 5F087432
P 5500 4150
F 0 "#FLG0101" H 5500 4225 50  0001 C CNN
F 1 "PWR_FLAG" H 5500 4323 50  0000 C CNN
F 2 "" H 5500 4150 50  0001 C CNN
F 3 "~" H 5500 4150 50  0001 C CNN
	1    5500 4150
	-1   0    0    1   
$EndComp
Connection ~ 5500 4150
Wire Wire Line
	5500 4150 8950 4150
$Comp
L power:PWR_FLAG #FLG0102
U 1 1 5F087D65
P 4600 850
F 0 "#FLG0102" H 4600 925 50  0001 C CNN
F 1 "PWR_FLAG" H 4600 1023 50  0000 C CNN
F 2 "" H 4600 850 50  0001 C CNN
F 3 "~" H 4600 850 50  0001 C CNN
	1    4600 850 
	1    0    0    -1  
$EndComp
Connection ~ 4600 850 
Wire Wire Line
	4600 850  4200 850 
Text GLabel 4100 850  0    39   Input ~ 0
5V
Wire Wire Line
	4100 850  4200 850 
NoConn ~ 3100 3100
NoConn ~ 3100 3000
NoConn ~ 3100 2900
NoConn ~ 3100 2800
NoConn ~ 3100 2700
NoConn ~ 3100 2600
NoConn ~ 3100 2500
NoConn ~ 3100 2400
NoConn ~ 3100 2300
NoConn ~ 3100 2200
NoConn ~ 3100 2100
NoConn ~ 3100 2000
NoConn ~ 3100 1900
NoConn ~ 3100 1800
NoConn ~ 3100 1700
NoConn ~ 3100 1600
NoConn ~ 700  4200
$EndSCHEMATC
