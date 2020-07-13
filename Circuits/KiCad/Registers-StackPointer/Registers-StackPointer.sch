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
Text GLabel 1050 7450 0    39   Input ~ 0
~A_load
Text GLabel 1050 7550 0    39   Input ~ 0
~B_load
Text GLabel 1050 7650 0    39   Input ~ 0
~C_load
Text GLabel 1050 7750 0    39   Input ~ 0
~H_load
Text GLabel 1050 7850 0    39   Input ~ 0
~L_load
Text GLabel 2050 7450 2    39   Input ~ 0
A_clock
Text GLabel 2050 7550 2    39   Input ~ 0
B_clock
Text GLabel 2050 7650 2    39   Input ~ 0
C_clock
Text GLabel 2050 7750 2    39   Input ~ 0
H_clock
Text GLabel 2050 7850 2    39   Input ~ 0
L_clock
NoConn ~ 1050 8050
NoConn ~ 1050 8150
NoConn ~ 2050 8150
NoConn ~ 2050 8050
Text GLabel 2600 7450 0    50   Input ~ 0
D0
Text GLabel 2600 7550 0    50   Input ~ 0
D1
Text GLabel 2600 7650 0    50   Input ~ 0
D2
Text GLabel 2600 7750 0    50   Input ~ 0
D3
Text GLabel 2600 7850 0    50   Input ~ 0
D4
Text GLabel 2600 7950 0    50   Input ~ 0
D5
Text GLabel 2600 8050 0    50   Input ~ 0
D6
Text GLabel 2600 8150 0    50   Input ~ 0
D7
Text GLabel 3600 7450 2    50   Input ~ 0
D0
Text GLabel 3600 8150 2    50   Input ~ 0
D7
Text GLabel 3600 8050 2    50   Input ~ 0
D6
Text GLabel 3600 7950 2    50   Input ~ 0
D5
Text GLabel 3600 7850 2    50   Input ~ 0
D4
Text GLabel 3600 7750 2    50   Input ~ 0
D3
Text GLabel 3600 7650 2    50   Input ~ 0
D2
Text GLabel 3600 7550 2    50   Input ~ 0
D1
Text GLabel 2600 8450 0    39   Input ~ 0
~A_out
Text GLabel 2600 8350 0    39   Input ~ 0
A_clock
$Comp
L 74xx:74HCT574 U5
U 1 1 5EB0F68E
P 4550 7950
F 0 "U5" H 4650 8650 50  0000 C CNN
F 1 "74HCT574" V 4550 7950 50  0000 C CNN
F 2 "Package_DIP:DIP-20_W7.62mm" H 4550 7950 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74HCT574" H 4550 7950 50  0001 C CNN
F 4 "B" H 4750 7450 61  0000 C CNN "Register"
	1    4550 7950
	1    0    0    -1  
$EndComp
Text GLabel 4050 7450 0    50   Input ~ 0
D0
Text GLabel 4050 7550 0    50   Input ~ 0
D1
Text GLabel 4050 7650 0    50   Input ~ 0
D2
Text GLabel 4050 7750 0    50   Input ~ 0
D3
Text GLabel 4050 7850 0    50   Input ~ 0
D4
Text GLabel 4050 7950 0    50   Input ~ 0
D5
Text GLabel 4050 8050 0    50   Input ~ 0
D6
Text GLabel 4050 8150 0    50   Input ~ 0
D7
Text GLabel 5050 7450 2    50   Input ~ 0
D0
Text GLabel 5050 8150 2    50   Input ~ 0
D7
Text GLabel 5050 8050 2    50   Input ~ 0
D6
Text GLabel 5050 7950 2    50   Input ~ 0
D5
Text GLabel 5050 7850 2    50   Input ~ 0
D4
Text GLabel 5050 7750 2    50   Input ~ 0
D3
Text GLabel 5050 7650 2    50   Input ~ 0
D2
Text GLabel 5050 7550 2    50   Input ~ 0
D1
Text GLabel 4050 8450 0    39   Input ~ 0
~B_out
Text GLabel 4050 8350 0    39   Input ~ 0
B_clock
$Comp
L 74xx:74HCT574 U6
U 1 1 5EB11422
P 6000 7950
F 0 "U6" H 6100 8650 50  0000 C CNN
F 1 "74HCT574" V 6000 7950 50  0000 C CNN
F 2 "Package_DIP:DIP-20_W7.62mm" H 6000 7950 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74HCT574" H 6000 7950 50  0001 C CNN
F 4 "C" H 6200 7450 61  0000 C CNN "Register"
	1    6000 7950
	1    0    0    -1  
$EndComp
Text GLabel 5500 7450 0    50   Input ~ 0
D0
Text GLabel 5500 7550 0    50   Input ~ 0
D1
Text GLabel 5500 7650 0    50   Input ~ 0
D2
Text GLabel 5500 7750 0    50   Input ~ 0
D3
Text GLabel 5500 7850 0    50   Input ~ 0
D4
Text GLabel 5500 7950 0    50   Input ~ 0
D5
Text GLabel 5500 8050 0    50   Input ~ 0
D6
Text GLabel 5500 8150 0    50   Input ~ 0
D7
Text GLabel 6500 7450 2    50   Input ~ 0
D0
Text GLabel 6500 8150 2    50   Input ~ 0
D7
Text GLabel 6500 8050 2    50   Input ~ 0
D6
Text GLabel 6500 7950 2    50   Input ~ 0
D5
Text GLabel 6500 7850 2    50   Input ~ 0
D4
Text GLabel 6500 7750 2    50   Input ~ 0
D3
Text GLabel 6500 7650 2    50   Input ~ 0
D2
Text GLabel 6500 7550 2    50   Input ~ 0
D1
Text GLabel 5500 8450 0    39   Input ~ 0
~C_out
Text GLabel 5500 8350 0    39   Input ~ 0
C_clock
$Comp
L 74xx:74HCT574 U9
U 1 1 5EB1143E
P 7450 7950
F 0 "U9" H 7550 8650 50  0000 C CNN
F 1 "74HCT574" V 7450 7950 50  0000 C CNN
F 2 "Package_DIP:DIP-20_W7.62mm" H 7450 7950 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74HCT574" H 7450 7950 50  0001 C CNN
F 4 "H" H 7650 7450 61  0000 C CNN "Register"
	1    7450 7950
	1    0    0    -1  
$EndComp
Text GLabel 6950 7450 0    50   Input ~ 0
D0
Text GLabel 6950 7550 0    50   Input ~ 0
D1
Text GLabel 6950 7650 0    50   Input ~ 0
D2
Text GLabel 6950 7750 0    50   Input ~ 0
D3
Text GLabel 6950 7850 0    50   Input ~ 0
D4
Text GLabel 6950 7950 0    50   Input ~ 0
D5
Text GLabel 6950 8050 0    50   Input ~ 0
D6
Text GLabel 6950 8150 0    50   Input ~ 0
D7
Text GLabel 7950 7450 2    50   Input ~ 0
D0
Text GLabel 7950 8150 2    50   Input ~ 0
D7
Text GLabel 7950 8050 2    50   Input ~ 0
D6
Text GLabel 7950 7950 2    50   Input ~ 0
D5
Text GLabel 7950 7850 2    50   Input ~ 0
D4
Text GLabel 7950 7750 2    50   Input ~ 0
D3
Text GLabel 7950 7650 2    50   Input ~ 0
D2
Text GLabel 7950 7550 2    50   Input ~ 0
D1
Text GLabel 6950 8450 0    39   Input ~ 0
~H_out
Text GLabel 6950 8350 0    39   Input ~ 0
H_clock
$Comp
L 74xx:74HCT574 U11
U 1 1 5EB14221
P 8900 7950
F 0 "U11" H 9000 8650 50  0000 C CNN
F 1 "74HCT574" V 8900 7950 50  0000 C CNN
F 2 "Package_DIP:DIP-20_W7.62mm" H 8900 7950 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74HCT574" H 8900 7950 50  0001 C CNN
F 4 "L" H 9100 7450 61  0000 C CNN "Register"
	1    8900 7950
	1    0    0    -1  
$EndComp
Text GLabel 8400 7450 0    50   Input ~ 0
D0
Text GLabel 8400 7550 0    50   Input ~ 0
D1
Text GLabel 8400 7650 0    50   Input ~ 0
D2
Text GLabel 8400 7750 0    50   Input ~ 0
D3
Text GLabel 8400 7850 0    50   Input ~ 0
D4
Text GLabel 8400 7950 0    50   Input ~ 0
D5
Text GLabel 8400 8050 0    50   Input ~ 0
D6
Text GLabel 8400 8150 0    50   Input ~ 0
D7
Text GLabel 9400 7450 2    50   Input ~ 0
D0
Text GLabel 9400 8150 2    50   Input ~ 0
D7
Text GLabel 9400 8050 2    50   Input ~ 0
D6
Text GLabel 9400 7950 2    50   Input ~ 0
D5
Text GLabel 9400 7850 2    50   Input ~ 0
D4
Text GLabel 9400 7750 2    50   Input ~ 0
D3
Text GLabel 9400 7650 2    50   Input ~ 0
D2
Text GLabel 9400 7550 2    50   Input ~ 0
D1
Text GLabel 8400 8450 0    39   Input ~ 0
~L_out
Text GLabel 8400 8350 0    39   Input ~ 0
L_clock
Wire Wire Line
	1550 7150 3100 7150
Connection ~ 3100 7150
Wire Wire Line
	3100 7150 4550 7150
Connection ~ 4550 7150
Wire Wire Line
	4550 7150 6000 7150
Connection ~ 6000 7150
Wire Wire Line
	6000 7150 7450 7150
Connection ~ 7450 7150
Wire Wire Line
	7450 7150 8900 7150
Wire Wire Line
	1550 8750 3100 8750
Connection ~ 3100 8750
Wire Wire Line
	3100 8750 4550 8750
Connection ~ 4550 8750
Wire Wire Line
	4550 8750 6000 8750
Connection ~ 6000 8750
Wire Wire Line
	6000 8750 7450 8750
Connection ~ 7450 8750
Wire Wire Line
	7450 8750 8900 8750
$Comp
L 74xx:74HCT240 U2
U 1 1 5EB0A1D5
P 1550 7950
F 0 "U2" H 1550 8931 50  0000 C CNN
F 1 "74HCT240" H 1550 8840 50  0000 C CNN
F 2 "Package_DIP:DIP-20_W7.62mm" H 1550 7950 50  0001 C CNN
F 3 "https://assets.nexperia.com/documents/data-sheet/74HC_HCT240.pdf" H 1550 7950 50  0001 C CNN
	1    1550 7950
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74HCT574 U3
U 1 1 5EA2E316
P 3100 7950
F 0 "U3" H 3200 8650 50  0000 C CNN
F 1 "74HCT574" V 3100 7950 50  0000 C CNN
F 2 "Package_DIP:DIP-20_W7.62mm" H 3100 7950 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74HCT574" H 3100 7950 50  0001 C CNN
F 4 "A" H 3300 7450 61  0000 C CNN "Register"
	1    3100 7950
	1    0    0    -1  
$EndComp
Wire Wire Line
	1050 8350 1050 8450
$Comp
L 74xx:74LS191 U7
U 1 1 5EB12A22
P 6300 1500
F 0 "U7" H 6300 1550 50  0000 C CNN
F 1 "74LS191" H 6300 1450 50  0000 C CNN
F 2 "Package_DIP:DIP-16_W7.62mm" H 6300 1500 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS191" H 6300 1500 50  0001 C CNN
	1    6300 1500
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74HCT02 U1
U 2 1 5EB149A7
P 1600 5050
F 0 "U1" H 1600 5050 50  0000 C CNN
F 1 "74HCT02" H 1900 4950 50  0000 C CNN
F 2 "Package_DIP:DIP-14_W7.62mm" H 1600 5050 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74hc02" H 1600 5050 50  0001 C CNN
	2    1600 5050
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74HCT02 U1
U 3 1 5EB18026
P 1600 5500
F 0 "U1" H 1600 5500 50  0000 C CNN
F 1 "74HCT02" H 1900 5400 50  0000 C CNN
F 2 "Package_DIP:DIP-14_W7.62mm" H 1600 5500 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74hc02" H 1600 5500 50  0001 C CNN
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
L 74xx:74HCT02 U1
U 1 1 5EB1474C
P 1600 4600
F 0 "U1" H 1600 4600 50  0000 C CNN
F 1 "74HCT02" H 1900 4700 50  0000 C CNN
F 2 "Package_DIP:DIP-14_W7.62mm" H 1600 4600 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74hc02" H 1600 4600 50  0001 C CNN
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
Text GLabel 5800 1100 0    50   Input ~ 0
D0
Text GLabel 5800 1200 0    50   Input ~ 0
D1
Text GLabel 5800 1300 0    50   Input ~ 0
D2
Text GLabel 5800 1400 0    50   Input ~ 0
D3
Text GLabel 5800 2900 0    50   Input ~ 0
D4
Text GLabel 5800 3000 0    50   Input ~ 0
D5
Text GLabel 5800 3100 0    50   Input ~ 0
D6
Text GLabel 5800 3200 0    50   Input ~ 0
D7
$Comp
L 74xx:74LS191 U8
U 1 1 5EB3CFBE
P 6300 3300
F 0 "U8" H 6300 3350 50  0000 C CNN
F 1 "74LS191" H 6300 3250 50  0000 C CNN
F 2 "Package_DIP:DIP-16_W7.62mm" H 6300 3300 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS191" H 6300 3300 50  0001 C CNN
	1    6300 3300
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS32 U4
U 1 1 5EB44312
P 3500 4600
F 0 "U4" H 3500 4600 50  0000 C CNN
F 1 "74HCT32" H 3500 4800 50  0000 C CNN
F 2 "Package_DIP:DIP-14_W7.62mm" H 3500 4600 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74hc02" H 3500 4600 50  0001 C CNN
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
L 74xx:74LS191 U12
U 1 1 5EB5E750
P 10400 1500
F 0 "U12" H 10400 1550 50  0000 C CNN
F 1 "74LS191" H 10400 1450 50  0000 C CNN
F 2 "Package_DIP:DIP-16_W7.62mm" H 10400 1500 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS191" H 10400 1500 50  0001 C CNN
	1    10400 1500
	1    0    0    -1  
$EndComp
Text GLabel 9900 1100 0    50   Input ~ 0
D0
Text GLabel 9900 1200 0    50   Input ~ 0
D1
Text GLabel 9900 1300 0    50   Input ~ 0
D2
Text GLabel 9900 1400 0    50   Input ~ 0
D3
Text GLabel 9900 2900 0    50   Input ~ 0
D4
Text GLabel 9900 3000 0    50   Input ~ 0
D5
Text GLabel 9900 3100 0    50   Input ~ 0
D6
Text GLabel 9900 3200 0    50   Input ~ 0
D7
$Comp
L 74xx:74LS191 U13
U 1 1 5EB5E766
P 10400 3300
F 0 "U13" H 10400 3350 50  0000 C CNN
F 1 "74LS191" H 10400 3250 50  0000 C CNN
F 2 "Package_DIP:DIP-16_W7.62mm" H 10400 3300 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74LS191" H 10400 3300 50  0001 C CNN
	1    10400 3300
	1    0    0    -1  
$EndComp
Text GLabel 5800 1700 0    39   Input ~ 0
DOWN_~UP
Text GLabel 5800 3500 0    39   Input ~ 0
DOWN_~UP
Text GLabel 9900 1700 0    39   Input ~ 0
DOWN_~UP
Text GLabel 9900 3500 0    39   Input ~ 0
DOWN_~UP
Text GLabel 5800 3700 0    39   Input ~ 0
~CLK_EN
Text GLabel 5800 1900 0    39   Input ~ 0
~CLK_EN
Text GLabel 9900 1900 0    39   Input ~ 0
~CLK_EN
Text GLabel 9900 3700 0    39   Input ~ 0
~CLK_EN
Text GLabel 9900 2000 0    39   Input ~ 0
CLOCK_PH3
$Comp
L 74xx:74HC245 U10
U 1 1 5EB80D5C
P 8600 1600
F 0 "U10" H 8600 1400 50  0000 C CNN
F 1 "74HC245" H 8600 1300 50  0000 C CNN
F 2 "Package_DIP:DIP-20_W7.62mm" H 8600 1600 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74HC245" H 8600 1600 50  0001 C CNN
	1    8600 1600
	1    0    0    -1  
$EndComp
Text GLabel 8100 2100 0    39   Input ~ 0
~STK_H_out
Wire Wire Line
	6800 1100 7350 1100
Wire Wire Line
	6800 1200 7400 1200
Wire Wire Line
	8100 1300 7450 1300
Wire Wire Line
	6800 1400 7500 1400
Wire Wire Line
	8100 1800 7700 1800
Wire Wire Line
	7700 1800 7700 3200
Wire Wire Line
	7700 3200 6800 3200
Wire Wire Line
	6800 3100 7650 3100
Wire Wire Line
	7650 3100 7650 1700
Wire Wire Line
	7650 1700 8100 1700
Wire Wire Line
	8100 1600 7600 1600
Wire Wire Line
	7600 1600 7600 3000
Wire Wire Line
	7600 3000 6800 3000
Wire Wire Line
	6800 2900 7550 2900
Wire Wire Line
	7550 2900 7550 1500
Wire Wire Line
	7550 1500 8100 1500
NoConn ~ 6800 1800
NoConn ~ 6800 3600
NoConn ~ 10900 3600
NoConn ~ 10900 1800
Text GLabel 9100 1100 2    50   Input ~ 0
D0
Text GLabel 9100 1200 2    50   Input ~ 0
D1
Text GLabel 9100 1300 2    50   Input ~ 0
D2
Text GLabel 9100 1400 2    50   Input ~ 0
D3
Text GLabel 9100 1500 2    50   Input ~ 0
D4
Text GLabel 9100 1600 2    50   Input ~ 0
D5
Text GLabel 9100 1700 2    50   Input ~ 0
D6
Text GLabel 9100 1800 2    50   Input ~ 0
D7
Text GLabel 9900 3800 0    50   Input ~ 0
LOW0_Rc
Text GLabel 10900 3400 2    50   Input ~ 0
LOW1_Rc
Text GLabel 3800 5100 2    39   Input ~ 0
~LOW_PL
Text GLabel 5800 1600 0    39   Input ~ 0
~HIGH_PL
Text GLabel 5800 3400 0    39   Input ~ 0
~HIGH_PL
Text GLabel 9900 1600 0    39   Input ~ 0
~LOW_PL
Text GLabel 9900 3400 0    39   Input ~ 0
~LOW_PL
Text GLabel 6800 1600 2    50   Output ~ 0
HIGH0_Rc
NoConn ~ 6800 3400
Text GLabel 5800 3800 0    50   Input ~ 0
HIGH0_Rc
Text GLabel 5800 2000 0    50   Input ~ 0
LOW1_Rc
$Comp
L 74xx:74HC245 U15
U 1 1 5EBD5A44
P 12600 1600
F 0 "U15" H 12600 1400 50  0000 C CNN
F 1 "74HC245" H 12600 1300 50  0000 C CNN
F 2 "Package_DIP:DIP-20_W7.62mm" H 12600 1600 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74HC245" H 12600 1600 50  0001 C CNN
	1    12600 1600
	1    0    0    -1  
$EndComp
Text GLabel 12100 2100 0    39   Input ~ 0
~STK_L_out
Wire Wire Line
	10900 1100 11350 1100
Wire Wire Line
	10900 1200 11400 1200
Wire Wire Line
	12100 1300 11450 1300
Wire Wire Line
	10900 1400 11500 1400
Wire Wire Line
	12100 1800 11700 1800
Wire Wire Line
	11700 1800 11700 3200
Wire Wire Line
	11700 3200 10900 3200
Wire Wire Line
	10900 3100 11650 3100
Wire Wire Line
	11650 3100 11650 1700
Wire Wire Line
	11650 1700 12100 1700
Wire Wire Line
	12100 1600 11600 1600
Wire Wire Line
	11600 1600 11600 3000
Wire Wire Line
	11600 3000 10900 3000
Wire Wire Line
	10900 2900 11550 2900
Wire Wire Line
	11550 2900 11550 1500
Wire Wire Line
	11550 1500 12100 1500
Text GLabel 13100 1100 2    50   Input ~ 0
D0
Text GLabel 13100 1200 2    50   Input ~ 0
D1
Text GLabel 13100 1300 2    50   Input ~ 0
D2
Text GLabel 13100 1400 2    50   Input ~ 0
D3
Text GLabel 13100 1500 2    50   Input ~ 0
D4
Text GLabel 13100 1600 2    50   Input ~ 0
D5
Text GLabel 13100 1700 2    50   Input ~ 0
D6
Text GLabel 13100 1800 2    50   Input ~ 0
D7
Wire Wire Line
	6300 2300 6300 2400
Wire Wire Line
	10400 2400 10400 2300
Wire Wire Line
	6300 2400 8600 2400
Connection ~ 8600 2400
Wire Wire Line
	8600 2400 10400 2400
Wire Wire Line
	10400 2400 12600 2400
Connection ~ 10400 2400
Wire Wire Line
	10400 4100 12600 4100
Wire Wire Line
	12600 4100 12600 2400
Connection ~ 10400 4100
Connection ~ 12600 2400
Wire Wire Line
	5350 800  5350 2600
Wire Wire Line
	5350 2600 6300 2600
Connection ~ 6300 2600
Wire Wire Line
	6300 800  8600 800 
Connection ~ 6300 800 
Connection ~ 8600 800 
Wire Wire Line
	8600 800  10400 800 
Connection ~ 10400 800 
Wire Wire Line
	10400 800  12600 800 
Connection ~ 5350 800 
Connection ~ 6300 4100
Text GLabel 3800 4600 2    39   Input ~ 0
~HIGH_PL
$Comp
L 74xx:74HCT02 U1
U 4 1 5EB20C20
P 1400 9000
F 0 "U1" H 1400 9000 50  0000 C CNN
F 1 "74HCT02" H 1400 9200 50  0000 C CNN
F 2 "Package_DIP:DIP-14_W7.62mm" H 1400 9000 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74hc02" H 1400 9000 50  0001 C CNN
	4    1400 9000
	-1   0    0    1   
$EndComp
Wire Wire Line
	1700 8900 1700 9000
Wire Wire Line
	1800 9000 1700 9000
Connection ~ 1700 9000
Wire Wire Line
	1700 9000 1700 9100
Text GLabel 1800 9000 2    39   Input ~ 0
CLOCK_PH3
Wire Wire Line
	1050 8450 1050 9000
Wire Wire Line
	1050 9000 1100 9000
Connection ~ 1050 8450
$Comp
L 74xx:74LS32 U4
U 2 1 5EB3A9E5
P 3500 5100
F 0 "U4" H 3500 5100 50  0000 C CNN
F 1 "74HCT32" H 3500 4850 50  0000 C CNN
F 2 "Package_DIP:DIP-14_W7.62mm" H 3500 5100 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74hc02" H 3500 5100 50  0001 C CNN
	2    3500 5100
	1    0    0    -1  
$EndComp
Text GLabel 10900 1600 2    50   Input ~ 0
LOW0_Rc
Text GLabel 6150 4100 0    39   Input ~ 0
GND
Wire Wire Line
	6150 4100 6300 4100
Text GLabel 5250 800  0    39   Input ~ 0
5V
Wire Wire Line
	5250 800  5350 800 
$Comp
L Mechanical:MountingHole H3
U 1 1 5F0D560B
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
U 1 1 5F0D5609
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
U 1 1 5F0D560C
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
$Comp
L Connector_Generic:Conn_02x32_Odd_Even BUS2
U 1 1 5EC6B636
P 4100 2300
F 0 "BUS2" H 4150 3925 50  0000 C CNN
F 1 "Conn_02x32_Odd_Even" H 4150 3926 50  0001 C CNN
F 2 "Connector_PinSocket_2.54mm:PinSocket_2x32_P2.54mm_Vertical" H 4100 2300 50  0001 C CNN
F 3 "~" H 4100 2300 50  0001 C CNN
	1    4100 2300
	-1   0    0    -1  
$EndComp
$Comp
L Connector_Generic:Conn_02x32_Odd_Even BUS1
U 1 1 5EC3909D
P 2000 2300
F 0 "BUS1" H 2050 3925 50  0000 C CNN
F 1 "Conn_02x32_Odd_Even" H 2050 3926 50  0001 C CNN
F 2 "Connector_PinSocket_2.54mm:PinSocket_2x32_P2.54mm_Vertical" H 2000 2300 50  0001 C CNN
F 3 "~" H 2000 2300 50  0001 C CNN
	1    2000 2300
	-1   0    0    -1  
$EndComp
Text GLabel 1150 800  0    39   Input ~ 0
GND
Text GLabel 1150 900  0    39   Input ~ 0
CLOCK_PH0
Text GLabel 1150 1000 0    39   Input ~ 0
CLOCK_PH2
Text GLabel 1150 1100 0    39   Input ~ 0
CLOCK_ENABLE
Text GLabel 1150 1200 0    39   Input ~ 0
BTN_STEP_ENABLE
Text GLabel 1150 1300 0    39   Input ~ 0
BTN_STEP
Text GLabel 1150 1400 0    39   Input ~ 0
BTN_CONTINUE
Text GLabel 1150 1500 0    39   Input ~ 0
RESET
Text GLabel 1150 1600 0    39   Input ~ 0
IO_load
Text GLabel 1150 2000 0    39   Input ~ 0
~A_load
Text GLabel 1150 2100 0    39   Input ~ 0
~B_load
Text GLabel 1150 2200 0    39   Input ~ 0
~C_load
Text GLabel 1150 2300 0    39   Input ~ 0
~H_load
Text GLabel 1150 2400 0    39   Input ~ 0
~L_load
Text GLabel 1150 2500 0    39   Input ~ 0
~F_load
Text GLabel 1150 2600 0    39   Input ~ 0
~ALU_load
Text GLabel 1150 2700 0    39   Input ~ 0
~MEM_load
Text GLabel 1150 2800 0    39   Input ~ 0
~PC_H_load
Text GLabel 1150 2900 0    39   Input ~ 0
~PC_L_load
Text GLabel 1150 3000 0    39   Input ~ 0
~STK_H_load
Text GLabel 1150 3100 0    39   Input ~ 0
~STK_L_load
Text GLabel 1150 3200 0    39   Input ~ 0
~MAR_H_load
Text GLabel 1150 3300 0    39   Input ~ 0
~MAR_L_load
Text GLabel 1150 3400 0    39   Input ~ 0
~IR_load
Text GLabel 1150 3500 0    39   Input ~ 0
~PC_MAR_transfer
Text GLabel 1150 3600 0    39   Input ~ 0
~STK_MAR_transfer
Text GLabel 1150 3700 0    39   Input ~ 0
PC_inc
Text GLabel 1150 3800 0    39   Input ~ 0
~MAR_inc
Text GLabel 1150 3900 0    39   Input ~ 0
FETCH_done
Text GLabel 2650 3900 2    39   Input ~ 0
STK_dec
Text GLabel 2650 3800 2    39   Input ~ 0
STK_inc
Text GLabel 2650 3700 2    39   Input ~ 0
HALT
Text GLabel 2650 3600 2    39   Input ~ 0
TSTATE_reset
Text GLabel 2650 3500 2    39   Input ~ 0
~FCLR_z
Text GLabel 2650 3400 2    39   Input ~ 0
~FCLR_c
Text GLabel 2650 3300 2    39   Input ~ 0
~FSET_z
Text GLabel 2650 3200 2    39   Input ~ 0
~FSET_c
Text GLabel 2650 3100 2    39   Input ~ 0
~STK_L_out
Text GLabel 2650 3000 2    39   Input ~ 0
~STK_H_out
Text GLabel 2650 2900 2    39   Input ~ 0
~PC_L_out
Text GLabel 2650 2800 2    39   Input ~ 0
~PC_H_out
Text GLabel 2650 2700 2    39   Input ~ 0
~MEM_out
Text GLabel 2650 2600 2    39   Input ~ 0
~ALU_out
Text GLabel 2650 2500 2    39   Input ~ 0
~F_out
Text GLabel 2650 2400 2    39   Input ~ 0
~L_out
Text GLabel 2650 2300 2    39   Input ~ 0
~H_out
Text GLabel 2650 2200 2    39   Input ~ 0
~C_out
Text GLabel 2650 2100 2    39   Input ~ 0
~B_out
Text GLabel 2650 2000 2    39   Input ~ 0
~A_out
Text GLabel 2650 1600 2    39   Input ~ 0
IO_out
Text GLabel 2650 1000 2    39   Input ~ 0
CLOCK_PH3
Text GLabel 2650 900  2    39   Input ~ 0
CLOCK_PH1
Text GLabel 2650 800  2    39   Input ~ 0
5V
Text GLabel 3450 800  0    39   Input ~ 0
DATA0
Text GLabel 3450 900  0    39   Input ~ 0
DATA1
Text GLabel 3450 1000 0    39   Input ~ 0
DATA2
Text GLabel 3450 1100 0    39   Input ~ 0
DATA3
Text GLabel 3450 1200 0    39   Input ~ 0
DATA4
Text GLabel 3450 1300 0    39   Input ~ 0
DATA5
Text GLabel 3450 1400 0    39   Input ~ 0
DATA6
Text GLabel 3450 1500 0    39   Input ~ 0
DATA7
Text GLabel 3450 1600 0    39   Input ~ 0
INSTR0
Text GLabel 3450 1700 0    39   Input ~ 0
INSTR1
Text GLabel 3450 1800 0    39   Input ~ 0
INSTR2
Text GLabel 3450 1900 0    39   Input ~ 0
INSTR3
Text GLabel 3450 2000 0    39   Input ~ 0
INSTR4
Text GLabel 3450 2100 0    39   Input ~ 0
INSTR5
Text GLabel 3450 2200 0    39   Input ~ 0
INSTR6
Text GLabel 3450 2300 0    39   Input ~ 0
INSTR7
Text GLabel 3450 2400 0    39   Input ~ 0
ALUFUNC0
Text GLabel 3450 2500 0    39   Input ~ 0
ALUFUNC1
Text GLabel 3450 2600 0    39   Input ~ 0
ALUFUNC2
Text GLabel 3450 2700 0    39   Input ~ 0
ALUFUNC3
Text GLabel 3450 2800 0    39   Input ~ 0
ALUFUNC4
Text GLabel 4600 2800 2    39   Input ~ 0
TSTATE0
Text GLabel 4600 2700 2    39   Input ~ 0
FLAGS3
Text GLabel 4600 2600 2    39   Input ~ 0
FLAGS2
Text GLabel 4600 2500 2    39   Input ~ 0
FLAGS1
Text GLabel 4600 2400 2    39   Input ~ 0
FLAGS0
Text GLabel 4600 2300 2    39   Input ~ 0
A15
Text GLabel 4600 2200 2    39   Input ~ 0
A14
Text GLabel 4600 2100 2    39   Input ~ 0
A13
Text GLabel 4600 2000 2    39   Input ~ 0
A12
Text GLabel 4600 1900 2    39   Input ~ 0
A11
Text GLabel 4600 1800 2    39   Input ~ 0
A10
Text GLabel 4600 1700 2    39   Input ~ 0
A9
Text GLabel 4600 1600 2    39   Input ~ 0
A8
Text GLabel 4600 1500 2    39   Input ~ 0
A7
Text GLabel 4600 1400 2    39   Input ~ 0
A6
Text GLabel 4600 1300 2    39   Input ~ 0
A5
Text GLabel 4600 1200 2    39   Input ~ 0
A4
Text GLabel 4600 1100 2    39   Input ~ 0
A3
Text GLabel 4600 1000 2    39   Input ~ 0
A2
Text GLabel 4600 900  2    39   Input ~ 0
A1
Text GLabel 4600 800  2    39   Input ~ 0
A0
Text GLabel 4600 3100 2    39   Input ~ 0
TSTATE3
Text GLabel 4600 3000 2    39   Input ~ 0
TSTATE2
Text GLabel 4600 2900 2    39   Input ~ 0
TSTATE1
Wire Wire Line
	4300 800  4600 800 
Wire Wire Line
	4600 900  4300 900 
Wire Wire Line
	4300 1000 4600 1000
Wire Wire Line
	4600 1100 4300 1100
Wire Wire Line
	4300 1200 4600 1200
Wire Wire Line
	4600 1300 4300 1300
Wire Wire Line
	4300 1400 4600 1400
Wire Wire Line
	4600 1500 4300 1500
Wire Wire Line
	4300 1600 4600 1600
Wire Wire Line
	4600 1700 4300 1700
Wire Wire Line
	4300 1800 4600 1800
Wire Wire Line
	4600 1900 4300 1900
Wire Wire Line
	4300 2000 4600 2000
Wire Wire Line
	4600 2100 4300 2100
Wire Wire Line
	4300 2200 4600 2200
Wire Wire Line
	4600 2300 4300 2300
Wire Wire Line
	4300 2400 4600 2400
Wire Wire Line
	4600 2500 4300 2500
Wire Wire Line
	4300 2600 4600 2600
Wire Wire Line
	4600 2700 4300 2700
Wire Wire Line
	4300 2800 4600 2800
Wire Wire Line
	4600 2900 4300 2900
Wire Wire Line
	4300 3000 4600 3000
Wire Wire Line
	4600 3100 4300 3100
NoConn ~ 4600 3200
NoConn ~ 4600 3300
NoConn ~ 4600 3400
NoConn ~ 4600 3500
NoConn ~ 4600 3600
NoConn ~ 4600 3700
NoConn ~ 4600 3800
NoConn ~ 4600 3900
Wire Wire Line
	4600 3900 4300 3900
Wire Wire Line
	4300 3800 4600 3800
Wire Wire Line
	4600 3700 4300 3700
Wire Wire Line
	4300 3600 4600 3600
Wire Wire Line
	4600 3500 4300 3500
Wire Wire Line
	4600 3400 4300 3400
Wire Wire Line
	4600 3300 4300 3300
Wire Wire Line
	4600 3200 4300 3200
Text Label 4300 800  0    39   ~ 0
A0
Text Label 4300 900  0    39   ~ 0
A1
Text Label 4300 1000 0    39   ~ 0
A2
Text Label 4300 1100 0    39   ~ 0
A3
Text Label 4300 1200 0    39   ~ 0
A4
Text Label 4300 1300 0    39   ~ 0
A5
Text Label 4300 1400 0    39   ~ 0
A6
Text Label 4300 1500 0    39   ~ 0
A7
Text Label 4300 1600 0    39   ~ 0
A8
Text Label 4300 1700 0    39   ~ 0
A9
Text Label 4300 1800 0    39   ~ 0
A10
Text Label 4300 1900 0    39   ~ 0
A11
Text Label 4300 2000 0    39   ~ 0
A12
Text Label 4300 2100 0    39   ~ 0
A13
Text Label 4300 2200 0    39   ~ 0
A14
Text Label 4300 2300 0    39   ~ 0
A15
Text Label 4300 2400 0    39   ~ 0
FLAGS0
Text Label 4300 2500 0    39   ~ 0
FLAGS1
Text Label 4300 2600 0    39   ~ 0
FLAGS2
Text Label 4300 2700 0    39   ~ 0
FLAGS3
Text Label 4300 2800 0    39   ~ 0
TSTATE0
Text Label 4300 2900 0    39   ~ 0
TSTATE1
Text Label 4300 3000 0    39   ~ 0
TSTATE2
Text Label 4300 3100 0    39   ~ 0
TSTATE3
Text Label 4300 3200 0    39   ~ 0
B2NC18
Text Label 4300 3300 0    39   ~ 0
B2NC17
Text Label 4300 3400 0    39   ~ 0
B2NC16
Text Label 4300 3500 0    39   ~ 0
B2NC15
Text Label 4300 3600 0    39   ~ 0
B2NC14
Text Label 4300 3700 0    39   ~ 0
B2NC13
Text Label 4300 3800 0    39   ~ 0
B2NC12
Text Label 4300 3900 0    39   ~ 0
B2NC11
Wire Wire Line
	3800 3900 3450 3900
Wire Wire Line
	3450 3800 3800 3800
Wire Wire Line
	3800 3700 3450 3700
Wire Wire Line
	3450 3600 3800 3600
Wire Wire Line
	3800 3500 3450 3500
Wire Wire Line
	3450 3400 3800 3400
Wire Wire Line
	3800 3300 3450 3300
Wire Wire Line
	3450 3200 3800 3200
Wire Wire Line
	3800 3100 3450 3100
Wire Wire Line
	3450 3000 3800 3000
Wire Wire Line
	3800 2900 3450 2900
Wire Wire Line
	3450 2800 3800 2800
Wire Wire Line
	3800 2700 3450 2700
Wire Wire Line
	3450 2600 3800 2600
Wire Wire Line
	3800 2500 3450 2500
Wire Wire Line
	3450 2400 3800 2400
Wire Wire Line
	3800 2300 3450 2300
Wire Wire Line
	3450 2200 3800 2200
Wire Wire Line
	3800 2100 3450 2100
Wire Wire Line
	3450 2000 3800 2000
Wire Wire Line
	3800 1900 3450 1900
Wire Wire Line
	3450 1800 3800 1800
Wire Wire Line
	3800 1700 3450 1700
Wire Wire Line
	3450 1600 3800 1600
Wire Wire Line
	3450 800  3800 800 
Wire Wire Line
	3800 900  3450 900 
Wire Wire Line
	3450 1000 3800 1000
Wire Wire Line
	3800 1100 3450 1100
Wire Wire Line
	3450 1200 3800 1200
Wire Wire Line
	3450 1300 3800 1300
Wire Wire Line
	3450 1400 3800 1400
Wire Wire Line
	3450 1500 3800 1500
Text Label 3800 3900 2    39   ~ 0
B2NC10
Text Label 3800 3800 2    39   ~ 0
B2NC9
Text Label 3800 3700 2    39   ~ 0
B2NC8
Text Label 3800 3600 2    39   ~ 0
B2NC7
Text Label 3800 3500 2    39   ~ 0
B2NC6
Text Label 3800 3400 2    39   ~ 0
B2NC5
Text Label 3800 3300 2    39   ~ 0
B2NC4
Text Label 3800 3200 2    39   ~ 0
B2NC3
Text Label 3800 3100 2    39   ~ 0
B2NC2
Text Label 3800 3000 2    39   ~ 0
B2NC1
Text Label 3800 2900 2    39   ~ 0
B2NC0
Text Label 3800 2800 2    39   ~ 0
ALUFUNC4
Text Label 3800 2700 2    39   ~ 0
ALUFUNC3
Text Label 3800 2600 2    39   ~ 0
ALUFUNC2
Text Label 3800 2500 2    39   ~ 0
ALUFUNC1
Text Label 3800 2400 2    39   ~ 0
ALUFUNC0
Text Label 3800 2300 2    39   ~ 0
INSTR7
Text Label 3800 2200 2    39   ~ 0
INSTR6
Text Label 3800 2100 2    39   ~ 0
INSTR5
Text Label 3800 2000 2    39   ~ 0
INSTR4
Text Label 3800 1900 2    39   ~ 0
INSTR3
Text Label 3800 1800 2    39   ~ 0
INSTR2
Text Label 3800 1700 2    39   ~ 0
INSTR1
Text Label 3800 1600 2    39   ~ 0
INSTR0
Text Label 3800 1500 2    39   ~ 0
DATA7
Text Label 3800 1400 2    39   ~ 0
DATA6
Text Label 3800 1300 2    39   ~ 0
DATA5
Text Label 3800 1200 2    39   ~ 0
DATA4
Text Label 3800 1100 2    39   ~ 0
DATA3
Text Label 3800 1000 2    39   ~ 0
DATA2
Text Label 3800 900  2    39   ~ 0
DATA1
Text Label 3800 800  2    39   ~ 0
DATA0
NoConn ~ 3450 2900
NoConn ~ 3450 3000
NoConn ~ 3450 3100
NoConn ~ 3450 3200
NoConn ~ 3450 3300
NoConn ~ 3450 3400
NoConn ~ 3450 3500
NoConn ~ 3450 3600
NoConn ~ 3450 3700
NoConn ~ 3450 3800
NoConn ~ 3450 3900
Wire Wire Line
	2650 900  2200 900 
Wire Wire Line
	2200 1000 2650 1000
Wire Wire Line
	2650 1100 2200 1100
Wire Wire Line
	2200 1200 2650 1200
Wire Wire Line
	2650 1300 2200 1300
Wire Wire Line
	2200 1400 2650 1400
Wire Wire Line
	2650 1500 2200 1500
Wire Wire Line
	2200 1600 2650 1600
Wire Wire Line
	2650 1700 2200 1700
Wire Wire Line
	2200 1800 2650 1800
Wire Wire Line
	2650 1900 2200 1900
Wire Wire Line
	2200 2000 2650 2000
Wire Wire Line
	2650 2100 2200 2100
Wire Wire Line
	2200 2200 2650 2200
Wire Wire Line
	2650 2300 2200 2300
Wire Wire Line
	2200 2400 2650 2400
Wire Wire Line
	2650 2500 2200 2500
Wire Wire Line
	2200 2600 2650 2600
Wire Wire Line
	2650 2700 2200 2700
Wire Wire Line
	2200 2800 2650 2800
Wire Wire Line
	2650 2900 2200 2900
Wire Wire Line
	2200 3000 2650 3000
Wire Wire Line
	2650 3100 2200 3100
Wire Wire Line
	2650 3900 2200 3900
Wire Wire Line
	2200 3800 2650 3800
Wire Wire Line
	2650 3700 2200 3700
Wire Wire Line
	2200 3600 2650 3600
Wire Wire Line
	2650 3500 2200 3500
Wire Wire Line
	2650 3400 2200 3400
Wire Wire Line
	2650 3300 2200 3300
Wire Wire Line
	2650 3200 2200 3200
Text Label 2200 800  0    39   ~ 0
5V
Text Label 2200 900  0    39   ~ 0
CLOCK_PH1
Text Label 2200 1000 0    39   ~ 0
CLOCK_PH3
Text Label 2200 1100 0    39   ~ 0
B1NC10
Text Label 2200 1200 0    39   ~ 0
B1NC9
Text Label 2200 1300 0    39   ~ 0
B1NC8
Text Label 2200 1400 0    39   ~ 0
B1NC7
Text Label 2200 1500 0    39   ~ 0
B1NC6
Text Label 2200 1600 0    39   ~ 0
IO_out
Text Label 2200 1700 0    39   ~ 0
B1NC5
Text Label 2200 1800 0    39   ~ 0
B1NC4
Text Label 2200 1900 0    39   ~ 0
B1NC3
Text Label 2200 2000 0    39   ~ 0
~A_out
Text Label 2200 2100 0    39   ~ 0
~B_out
Text Label 2200 2200 0    39   ~ 0
~C_out
Text Label 2200 2300 0    39   ~ 0
~H_out
Text Label 2200 2400 0    39   ~ 0
~L_out
Text Label 2200 2500 0    39   ~ 0
~F_out
Text Label 2200 2600 0    39   ~ 0
~ALU_out
Text Label 2200 2700 0    39   ~ 0
~MEM_out
Text Label 2200 2800 0    39   ~ 0
~PC_H_out
Text Label 2200 2900 0    39   ~ 0
~PC_L_out
Text Label 2200 3000 0    39   ~ 0
~STK_H_out
Text Label 2200 3100 0    39   ~ 0
~STK_L_out
Text Label 2200 3200 0    39   ~ 0
~FSET_c
Text Label 2200 3300 0    39   ~ 0
~FSET_z
Text Label 2200 3400 0    39   ~ 0
~FCLR_c
Text Label 2200 3500 0    39   ~ 0
~FCLR_z
Text Label 2200 3600 0    39   ~ 0
TSTATE_reset
Text Label 2200 3700 0    39   ~ 0
HALT
Text Label 2200 3800 0    39   ~ 0
STK_inc
Text Label 2200 3900 0    39   ~ 0
STK_dec
Wire Wire Line
	1700 3900 1150 3900
Wire Wire Line
	1150 3800 1700 3800
Wire Wire Line
	1700 3700 1150 3700
Wire Wire Line
	1150 3600 1700 3600
Wire Wire Line
	1700 3500 1150 3500
Wire Wire Line
	1150 3400 1700 3400
Wire Wire Line
	1700 3300 1150 3300
Wire Wire Line
	1150 3200 1700 3200
Wire Wire Line
	1700 3100 1150 3100
Wire Wire Line
	1150 3000 1700 3000
Wire Wire Line
	1700 2900 1150 2900
Wire Wire Line
	1150 2800 1700 2800
Wire Wire Line
	1700 2700 1150 2700
Wire Wire Line
	1150 2600 1700 2600
Wire Wire Line
	1700 2500 1150 2500
Wire Wire Line
	1150 2400 1700 2400
Wire Wire Line
	1700 2300 1150 2300
Wire Wire Line
	1150 2200 1700 2200
Wire Wire Line
	1700 2100 1150 2100
Wire Wire Line
	1150 2000 1700 2000
Wire Wire Line
	1700 1900 1150 1900
Wire Wire Line
	1150 1800 1700 1800
Wire Wire Line
	1700 1700 1150 1700
Wire Wire Line
	1150 1600 1700 1600
Wire Wire Line
	1700 900  1150 900 
Wire Wire Line
	1150 1000 1700 1000
Wire Wire Line
	1700 1100 1150 1100
Wire Wire Line
	1150 1200 1700 1200
Wire Wire Line
	1150 1300 1700 1300
Wire Wire Line
	1150 1400 1700 1400
Wire Wire Line
	1150 1500 1700 1500
Text Label 1700 3900 2    39   ~ 0
FETCH_done
Text Label 1700 3800 2    39   ~ 0
~MAR_inc
Text Label 1700 3700 2    39   ~ 0
PC_inc
Text Label 1700 3600 2    39   ~ 0
~STK_MAR_transfer
Text Label 1700 3500 2    39   ~ 0
~PC_MAR_transfer
Text Label 1700 3400 2    39   ~ 0
~IR_load
Text Label 1700 3300 2    39   ~ 0
~MAR_L_load
Text Label 1700 3200 2    39   ~ 0
~MAR_H_load
Text Label 1700 3100 2    39   ~ 0
~STK_L_load
Text Label 1700 3000 2    39   ~ 0
~STK_H_load
Text Label 1700 2900 2    39   ~ 0
~PC_L_load
Text Label 1700 2800 2    39   ~ 0
~PC_H_load
Text Label 1700 2700 2    39   ~ 0
~MEM_load
Text Label 1700 2600 2    39   ~ 0
~ALU_load
Text Label 1700 2500 2    39   ~ 0
~F_load
Text Label 1700 2400 2    39   ~ 0
~L_load
Text Label 1700 2300 2    39   ~ 0
~H_load
Text Label 1700 2200 2    39   ~ 0
~C_load
Text Label 1700 2100 2    39   ~ 0
~B_load
Text Label 1700 2000 2    39   ~ 0
~A_load
Text Label 1700 1900 2    39   ~ 0
B1NC2
Text Label 1700 1800 2    39   ~ 0
B1NC1
Text Label 1700 1700 2    39   ~ 0
B1NC0
Text Label 1700 1600 2    39   ~ 0
IO_load
Text Label 1700 1500 2    39   ~ 0
RESET
Text Label 1700 1400 2    39   ~ 0
BTN_CONTINUE
Text Label 1700 1300 2    39   ~ 0
BTN_STEP
Text Label 1700 1200 2    39   ~ 0
BTN_STEP_ENABLE
Text Label 1700 1100 2    39   ~ 0
CLOCK_ENABLE
Text Label 1700 1000 2    39   ~ 0
CLOCK_PH2
Text Label 1700 900  2    39   ~ 0
CLOCK_PH0
Text Label 1700 800  2    39   ~ 0
GND
NoConn ~ 2650 1900
NoConn ~ 2650 1800
NoConn ~ 2650 1700
NoConn ~ 2650 1500
NoConn ~ 2650 1400
NoConn ~ 2650 1300
NoConn ~ 2650 1200
NoConn ~ 2650 1100
NoConn ~ 1150 1700
NoConn ~ 1150 1800
NoConn ~ 1150 1900
$Comp
L power:GND #PWR01
U 1 1 5F24E0E0
P 1350 800
F 0 "#PWR01" H 1350 550 50  0001 C CNN
F 1 "GND" H 1355 627 39  0000 C CNN
F 2 "" H 1350 800 50  0001 C CNN
F 3 "" H 1350 800 50  0001 C CNN
	1    1350 800 
	-1   0    0    1   
$EndComp
$Comp
L power:PWR_FLAG #FLG01
U 1 1 5F24F424
P 1450 800
F 0 "#FLG01" H 1450 875 50  0001 C CNN
F 1 "PWR_FLAG" H 1450 973 50  0001 C CNN
F 2 "" H 1450 800 50  0001 C CNN
F 3 "~" H 1450 800 50  0001 C CNN
	1    1450 800 
	1    0    0    -1  
$EndComp
$Comp
L power:+5V #PWR02
U 1 1 5F250881
P 2500 800
F 0 "#PWR02" H 2500 650 50  0001 C CNN
F 1 "+5V" H 2515 965 39  0000 C CNN
F 2 "" H 2500 800 50  0001 C CNN
F 3 "" H 2500 800 50  0001 C CNN
	1    2500 800 
	1    0    0    -1  
$EndComp
$Comp
L power:PWR_FLAG #FLG02
U 1 1 5F24FE4E
P 2400 800
F 0 "#FLG02" H 2400 875 50  0001 C CNN
F 1 "PWR_FLAG" H 2400 973 50  0001 C CNN
F 2 "" H 2400 800 50  0001 C CNN
F 3 "~" H 2400 800 50  0001 C CNN
	1    2400 800 
	1    0    0    -1  
$EndComp
Wire Wire Line
	2200 800  2400 800 
Connection ~ 2400 800 
Wire Wire Line
	2400 800  2500 800 
Connection ~ 2500 800 
Wire Wire Line
	2500 800  2650 800 
Wire Wire Line
	1150 800  1350 800 
Connection ~ 1350 800 
Wire Wire Line
	1350 800  1450 800 
Connection ~ 1450 800 
Wire Wire Line
	1450 800  1700 800 
Wire Wire Line
	5350 800  6300 800 
Wire Wire Line
	6300 4100 10400 4100
$Comp
L 74xx:74HCT574 U14
U 1 1 5F29B767
P 10350 7950
F 0 "U14" H 10450 8650 50  0000 C CNN
F 1 "74HCT574" V 10350 7950 50  0000 C CNN
F 2 "Package_DIP:DIP-20_W7.62mm" H 10350 7950 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74HCT574" H 10350 7950 50  0001 C CNN
F 4 "L" H 10550 7450 61  0000 C CNN "Register"
	1    10350 7950
	1    0    0    -1  
$EndComp
Text GLabel 9850 7450 0    50   Input ~ 0
D0
Text GLabel 9850 7550 0    50   Input ~ 0
D1
Text GLabel 9850 7650 0    50   Input ~ 0
D2
Text GLabel 9850 7750 0    50   Input ~ 0
D3
Text GLabel 9850 7850 0    50   Input ~ 0
D4
Text GLabel 9850 7950 0    50   Input ~ 0
D5
Text GLabel 9850 8050 0    50   Input ~ 0
D6
Text GLabel 9850 8150 0    50   Input ~ 0
D7
Text GLabel 10850 7450 2    50   Input ~ 0
INSTR0
Text GLabel 10850 8150 2    50   Input ~ 0
INSTR7
Text GLabel 10850 8050 2    50   Input ~ 0
INSTR6
Text GLabel 10850 7950 2    50   Input ~ 0
INSTR5
Text GLabel 10850 7850 2    50   Input ~ 0
INSTR4
Text GLabel 10850 7750 2    50   Input ~ 0
INSTR3
Text GLabel 10850 7650 2    50   Input ~ 0
INSTR2
Text GLabel 10850 7550 2    50   Input ~ 0
INSTR1
Text GLabel 9850 8350 0    39   Input ~ 0
IR_clock
Wire Wire Line
	8900 7150 10350 7150
Wire Wire Line
	8900 8750 9800 8750
Connection ~ 8900 7150
Connection ~ 8900 8750
Wire Wire Line
	9850 8450 9800 8450
Wire Wire Line
	9800 8450 9800 8750
Connection ~ 9800 8750
Wire Wire Line
	9800 8750 10350 8750
Text GLabel 1050 7950 0    39   Input ~ 0
~IR_load
Text GLabel 2050 7950 2    39   Input ~ 0
IR_clock
Text GLabel 8100 2000 0    39   Input ~ 0
GND
Text GLabel 12100 2000 0    39   Input ~ 0
GND
Text GLabel 10400 8750 2    39   Input ~ 0
GND
Connection ~ 10350 8750
Wire Wire Line
	10350 8750 10400 8750
Text GLabel 10400 7150 2    39   Input ~ 0
5V
Connection ~ 10350 7150
Wire Wire Line
	10350 7150 10400 7150
$Comp
L 74xx:74HC245 U16
U 1 1 5F599FD5
P 8600 5250
F 0 "U16" H 8600 5050 50  0000 C CNN
F 1 "74HC245" H 8600 4950 50  0000 C CNN
F 2 "Package_DIP:DIP-20_W7.62mm" H 8600 5250 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74HC245" H 8600 5250 50  0001 C CNN
	1    8600 5250
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74HC245 U17
U 1 1 5F59EE9B
P 12600 5250
F 0 "U17" H 12600 5050 50  0000 C CNN
F 1 "74HC245" H 12600 4950 50  0000 C CNN
F 2 "Package_DIP:DIP-20_W7.62mm" H 12600 5250 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74HC245" H 12600 5250 50  0001 C CNN
	1    12600 5250
	1    0    0    -1  
$EndComp
Wire Wire Line
	8500 4450 8600 4450
Wire Wire Line
	8500 6050 8600 6050
Text GLabel 8500 6050 0    39   Input ~ 0
GND
Connection ~ 8600 6050
Wire Wire Line
	8600 6050 12600 6050
Wire Wire Line
	6300 2600 10400 2600
Text GLabel 8500 4450 0    39   Input ~ 0
5V
Connection ~ 8600 4450
Wire Wire Line
	8600 4450 12600 4450
Wire Wire Line
	7700 3200 7700 5450
Wire Wire Line
	7700 5450 8100 5450
Connection ~ 7700 3200
Wire Wire Line
	7650 3100 7650 5350
Wire Wire Line
	7650 5350 8100 5350
Connection ~ 7650 3100
Wire Wire Line
	7600 3000 7600 5250
Wire Wire Line
	7600 5250 8100 5250
Connection ~ 7600 3000
Wire Wire Line
	7550 2900 7550 5150
Wire Wire Line
	7550 5150 8100 5150
Connection ~ 7550 2900
Wire Wire Line
	7500 1400 7500 5050
Wire Wire Line
	7500 5050 8100 5050
Connection ~ 7500 1400
Wire Wire Line
	7500 1400 8100 1400
Wire Wire Line
	7450 1300 7450 4950
Wire Wire Line
	7450 4950 8100 4950
Connection ~ 7450 1300
Wire Wire Line
	7450 1300 6800 1300
Wire Wire Line
	7400 1200 7400 4850
Wire Wire Line
	7400 4850 8100 4850
Connection ~ 7400 1200
Wire Wire Line
	7400 1200 8100 1200
Wire Wire Line
	7350 1100 7350 4750
Wire Wire Line
	7350 4750 8100 4750
Connection ~ 7350 1100
Wire Wire Line
	7350 1100 8100 1100
Wire Wire Line
	11700 3200 11700 5450
Wire Wire Line
	11700 5450 12100 5450
Connection ~ 11700 3200
Wire Wire Line
	11650 3100 11650 5350
Wire Wire Line
	11650 5350 12100 5350
Connection ~ 11650 3100
Wire Wire Line
	11600 3000 11600 5250
Wire Wire Line
	11600 5250 12100 5250
Connection ~ 11600 3000
Wire Wire Line
	11550 2900 11550 5150
Wire Wire Line
	11550 5150 12100 5150
Connection ~ 11550 2900
Wire Wire Line
	11500 1400 11500 5050
Wire Wire Line
	11500 5050 12100 5050
Connection ~ 11500 1400
Wire Wire Line
	11500 1400 12100 1400
Wire Wire Line
	11450 1300 11450 4950
Wire Wire Line
	11450 4950 12100 4950
Connection ~ 11450 1300
Wire Wire Line
	11450 1300 10900 1300
Wire Wire Line
	11400 1200 11400 4850
Wire Wire Line
	11400 4850 12100 4850
Connection ~ 11400 1200
Wire Wire Line
	11400 1200 12100 1200
Wire Wire Line
	11350 1100 11350 4750
Wire Wire Line
	11350 4750 12100 4750
Connection ~ 11350 1100
Wire Wire Line
	11350 1100 12100 1100
Text GLabel 8100 5650 0    39   Input ~ 0
GND
Text GLabel 12100 5650 0    39   Input ~ 0
GND
Text GLabel 8000 6200 0    39   Input ~ 0
~STK_MAR_transfer
Wire Wire Line
	8000 6200 8050 6200
Wire Wire Line
	8050 6200 8050 5750
Wire Wire Line
	8050 5750 8100 5750
Wire Wire Line
	8050 6200 12050 6200
Wire Wire Line
	12050 6200 12050 5750
Wire Wire Line
	12050 5750 12100 5750
Connection ~ 8050 6200
Text GLabel 13100 4750 2    39   Input ~ 0
A0
Text GLabel 13100 4850 2    39   Input ~ 0
A1
Text GLabel 13100 4950 2    39   Input ~ 0
A2
Text GLabel 13100 5050 2    39   Input ~ 0
A3
Text GLabel 13100 5150 2    39   Input ~ 0
A4
Text GLabel 13100 5250 2    39   Input ~ 0
A5
Text GLabel 13100 5350 2    39   Input ~ 0
A6
Text GLabel 13100 5450 2    39   Input ~ 0
A7
Text GLabel 9100 4750 2    39   Input ~ 0
A8
Text GLabel 9100 4850 2    39   Input ~ 0
A9
Text GLabel 9100 4950 2    39   Input ~ 0
A10
Text GLabel 9100 5050 2    39   Input ~ 0
A11
Text GLabel 9100 5150 2    39   Input ~ 0
A12
Text GLabel 9100 5250 2    39   Input ~ 0
A13
Text GLabel 9100 5350 2    39   Input ~ 0
A14
Text GLabel 9100 5450 2    39   Input ~ 0
A15
$EndSCHEMATC
