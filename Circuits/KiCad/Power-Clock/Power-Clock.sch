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
L Mechanical:MountingHole H1
U 1 1 5EAAC8FF
P 11050 11050
F 0 "H1" H 11150 11050 50  0001 L CNN
F 1 "MountingHole" H 11150 11005 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 11050 11050 50  0001 C CNN
F 3 "~" H 11050 11050 50  0001 C CNN
	1    11050 11050
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H3
U 1 1 5EAAC900
P 11450 11050
F 0 "H3" H 11550 11050 50  0001 L CNN
F 1 "MountingHole" H 11550 11005 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 11450 11050 50  0001 C CNN
F 3 "~" H 11450 11050 50  0001 C CNN
	1    11450 11050
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H2
U 1 1 5EAAC901
P 11250 11050
F 0 "H2" H 11350 11050 50  0001 L CNN
F 1 "MountingHole" H 11350 11005 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 11250 11050 50  0001 C CNN
F 3 "~" H 11250 11050 50  0001 C CNN
	1    11250 11050
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H4
U 1 1 5EAAC902
P 11650 11050
F 0 "H4" H 11750 11050 50  0001 L CNN
F 1 "MountingHole" H 11750 11005 50  0001 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 11650 11050 50  0001 C CNN
F 3 "~" H 11650 11050 50  0001 C CNN
	1    11650 11050
	1    0    0    -1  
$EndComp
$Comp
L Switch:SW_DPST SW2
U 1 1 5EAAC90A
P 1650 8600
F 0 "SW2" H 1700 8950 50  0000 C CNN
F 1 "Power" H 1700 8850 50  0000 C CNN
F 2 "DM-02:Switch_DPST_Angled" H 1650 8600 50  0001 C CNN
F 3 "" H 1650 8600 50  0001 C CNN
	1    1650 8600
	1    0    0    -1  
$EndComp
$Comp
L power:GND #PWR013
U 1 1 5D781541
P 5750 8750
F 0 "#PWR013" H 5750 8500 50  0001 C CNN
F 1 "GND" V 5750 8550 50  0000 C CNN
F 2 "" H 5750 8750 50  0001 C CNN
F 3 "" H 5750 8750 50  0001 C CNN
	1    5750 8750
	0    -1   -1   0   
$EndComp
$Comp
L power:+5V #PWR012
U 1 1 5D7815DA
P 5750 8450
F 0 "#PWR012" H 5750 8300 50  0001 C CNN
F 1 "+5V" V 5750 8550 50  0000 L CNN
F 2 "" H 5750 8450 50  0001 C CNN
F 3 "" H 5750 8450 50  0001 C CNN
	1    5750 8450
	0    1    1    0   
$EndComp
$Comp
L Connector:Barrel_Jack J1
U 1 1 5D784D5C
P 1150 8600
F 0 "J1" H 1150 8950 50  0000 C CNN
F 1 "Power (5V)" H 1150 8850 50  0000 C CNN
F 2 "Connector_BarrelJack:BarrelJack_Horizontal" H 1200 8560 50  0001 C CNN
F 3 "~" H 1200 8560 50  0001 C CNN
	1    1150 8600
	1    0    0    -1  
$EndComp
Text Notes 900  8950 0    50   ~ 0
Power connector and switch
$Comp
L Device:D_Zener D1
U 1 1 5D786901
P 2350 8600
F 0 "D1" V 2259 8679 50  0000 L CNN
F 1 "1N5340B" V 2350 8679 50  0000 L CNN
F 2 "Diode_THT:D_5W_P10.16mm_Horizontal" H 2350 8600 50  0001 C CNN
F 3 "~" H 2350 8600 50  0001 C CNN
F 4 "6V / 5W" V 2441 8679 50  0000 L CNN "Rating"
	1    2350 8600
	0    1    1    0   
$EndComp
$Comp
L Device:CP C3
U 1 1 5D786B78
P 2950 8600
F 0 "C3" H 3068 8646 50  0000 L CNN
F 1 "220µF" H 3068 8555 50  0000 L CNN
F 2 "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm" H 2988 8450 50  0001 C CNN
F 3 "~" H 2950 8600 50  0001 C CNN
	1    2950 8600
	1    0    0    -1  
$EndComp
Wire Wire Line
	1850 8500 1900 8500
Wire Wire Line
	1900 8500 1900 8450
Wire Wire Line
	2200 8450 2350 8450
Wire Wire Line
	1900 8750 1900 8700
Wire Wire Line
	1900 8700 1850 8700
Connection ~ 2350 8450
Connection ~ 2350 8750
Connection ~ 2950 8450
Connection ~ 2950 8750
Wire Wire Line
	2350 8450 2950 8450
Wire Wire Line
	2350 8750 2950 8750
Wire Wire Line
	2950 8450 3550 8450
Wire Wire Line
	2950 8750 3550 8750
Text GLabel 3050 3650 2    50   Input ~ 0
HALT
Text GLabel 1150 1350 0    50   Input ~ 0
CONTINUE
Text Notes 1700 6100 0    50   ~ 0
Single-step
$Comp
L 74xx-Computer-Symbols:NE555 U1
U 1 1 5ACE3F3F
P 1950 6850
F 0 "U1" H 1900 6850 50  0000 L CNN
F 1 "555" H 2050 7200 50  0000 L CNN
F 2 "Package_DIP:DIP-8_W7.62mm" H 1950 6850 50  0001 C CNN
F 3 "" H 1950 6850 50  0001 C CNN
	1    1950 6850
	1    0    0    -1  
$EndComp
$Comp
L 74xx-Computer-Symbols:R R1
U 1 1 5ACE44C8
P 1000 6450
F 0 "R1" V 1080 6450 50  0000 C CNN
F 1 "5K" V 900 6450 50  0000 C CNN
F 2 "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal" V 930 6450 50  0001 C CNN
F 3 "" H 1000 6450 50  0001 C CNN
	1    1000 6450
	-1   0    0    1   
$EndComp
$Comp
L 74xx-Computer-Symbols:R R2
U 1 1 5ACE4F86
P 2550 6450
F 0 "R2" V 2450 6450 50  0000 C CNN
F 1 "100K" V 2650 6450 50  0000 C CNN
F 2 "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal" V 2480 6450 50  0001 C CNN
F 3 "" H 2550 6450 50  0001 C CNN
	1    2550 6450
	1    0    0    -1  
$EndComp
Text GLabel 2650 6650 2    60   Output ~ 0
CLK_STEP
$Comp
L 74xx-Computer-Symbols:C C2
U 1 1 5ACE5B9E
P 2550 7350
F 0 "C2" H 2575 7450 50  0000 L CNN
F 1 "100nF" H 2575 7250 50  0000 L CNN
F 2 "Capacitor_THT:C_Rect_L4.6mm_W2.0mm_P2.50mm_MKS02_FKP02" H 2588 7200 50  0001 C CNN
F 3 "" H 2550 7350 50  0001 C CNN
	1    2550 7350
	1    0    0    -1  
$EndComp
$Comp
L 74xx-Computer-Symbols:C C1
U 1 1 5ACE61C5
P 1400 7350
F 0 "C1" H 1425 7450 50  0000 L CNN
F 1 "10nF" H 1425 7250 50  0000 L CNN
F 2 "Capacitor_THT:C_Rect_L4.6mm_W2.0mm_P2.50mm_MKS02_FKP02" H 1438 7200 50  0001 C CNN
F 3 "" H 1400 7350 50  0001 C CNN
	1    1400 7350
	1    0    0    -1  
$EndComp
Text Notes 4200 6100 0    50   ~ 0
Enable single-step mode
$Comp
L 74xx-Computer-Symbols:NE555 U3
U 1 1 5ACEAEA1
P 4550 6850
F 0 "U3" H 4500 6850 50  0000 L CNN
F 1 "555" H 4650 7200 50  0000 L CNN
F 2 "Package_DIP:DIP-8_W7.62mm" H 4550 6850 50  0001 C CNN
F 3 "" H 4550 6850 50  0001 C CNN
	1    4550 6850
	1    0    0    -1  
$EndComp
$Comp
L 74xx-Computer-Symbols:R R3
U 1 1 5ACEAEC2
P 3400 6450
F 0 "R3" V 3480 6450 50  0000 C CNN
F 1 "5K" V 3300 6450 50  0000 C CNN
F 2 "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal" V 3330 6450 50  0001 C CNN
F 3 "" H 3400 6450 50  0001 C CNN
	1    3400 6450
	-1   0    0    1   
$EndComp
$Comp
L 74xx-Computer-Symbols:LED D4
U 1 1 5ACEAEE0
P 5300 7100
F 0 "D4" H 5300 7200 50  0000 C CNN
F 1 "STEP" V 5300 6950 50  0000 C CNN
F 2 "LED_THT:LED_D5.0mm_Horizontal_O1.27mm_Z3.0mm" H 5300 7100 50  0001 C CNN
F 3 "" H 5300 7100 50  0001 C CNN
	1    5300 7100
	0    -1   -1   0   
$EndComp
Text GLabel 5400 6650 2    60   Output ~ 0
STEP_EN
$Comp
L 74xx-Computer-Symbols:R R10
U 1 1 5ACEAEE9
P 5300 7500
F 0 "R10" V 5200 7500 50  0000 C CNN
F 1 "330" V 5400 7500 50  0000 C CNN
F 2 "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal" V 5230 7500 50  0001 C CNN
F 3 "" H 5300 7500 50  0001 C CNN
	1    5300 7500
	1    0    0    -1  
$EndComp
$Comp
L 74xx-Computer-Symbols:C C6
U 1 1 5ACEAEFD
P 4000 7350
F 0 "C6" H 4025 7450 50  0000 L CNN
F 1 "10nF" H 4025 7250 50  0000 L CNN
F 2 "Capacitor_THT:C_Rect_L4.6mm_W2.0mm_P2.50mm_MKS02_FKP02" H 4038 7200 50  0001 C CNN
F 3 "" H 4000 7350 50  0001 C CNN
	1    4000 7350
	1    0    0    -1  
$EndComp
$Comp
L 74xx-Computer-Symbols:R R5
U 1 1 5ACEB881
P 3850 6450
F 0 "R5" V 3930 6450 50  0000 C CNN
F 1 "5K" V 3750 6450 50  0000 C CNN
F 2 "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal" V 3780 6450 50  0001 C CNN
F 3 "" H 3850 6450 50  0001 C CNN
	1    3850 6450
	-1   0    0    1   
$EndComp
$Comp
L 74xx-Computer-Symbols:+5V #PWR09
U 1 1 5ACEE856
P 5300 6250
F 0 "#PWR09" H 5300 6100 50  0001 C CNN
F 1 "+5V" H 5300 6390 50  0000 C CNN
F 2 "" H 5300 6250 50  0001 C CNN
F 3 "" H 5300 6250 50  0001 C CNN
	1    5300 6250
	0    1    1    0   
$EndComp
$Comp
L 74xx-Computer-Symbols:Crystal_GND2 Y1
U 1 1 5ACF1834
P 6700 7200
F 0 "Y1" H 6700 7425 50  0000 C CNN
F 1 "1 MHz" H 6700 7350 50  0000 C CNN
F 2 "74xx-Computer-Footprints:Oscillator_DIP-8_v2" H 6700 7200 50  0001 C CNN
F 3 "" H 6700 7200 50  0001 C CNN
	1    6700 7200
	1    0    0    -1  
$EndComp
$Comp
L 74xx-Computer-Symbols:+5V #PWR015
U 1 1 5ACF1A93
P 6450 7200
F 0 "#PWR015" H 6450 7050 50  0001 C CNN
F 1 "+5V" H 6450 7340 50  0000 C CNN
F 2 "" H 6450 7200 50  0001 C CNN
F 3 "" H 6450 7200 50  0001 C CNN
	1    6450 7200
	0    -1   -1   0   
$EndComp
$Comp
L 74xx-Computer-Symbols:GND #PWR016
U 1 1 5ACF1AFE
P 6700 7500
F 0 "#PWR016" H 6700 7250 50  0001 C CNN
F 1 "GND" H 6700 7350 50  0000 C CNN
F 2 "" H 6700 7500 50  0001 C CNN
F 3 "" H 6700 7500 50  0001 C CNN
	1    6700 7500
	1    0    0    -1  
$EndComp
Text GLabel 6950 7200 2    60   Output ~ 0
CLK_OSC
Text Notes 6400 6850 0    50   ~ 0
Oscillator (1 MHz)
Text Notes 8750 1450 0    50   ~ 0
Clock mode toggle logic.\n\nWhen single-step mode is enabled, the clock signal is generated by the single-step push button (SW3).\nWhen single-step is disabled, the oscillator (Y1) generates the clock signal.\n\nThe signal is divided into 2 signals (CLOCK1 & CLOCK2) which are 120ns out of phase and\nboth signals are inverted as well.\n\nAll this logic is disabled when CLOCK_ENABLE is low.\nThis is used by the Debugger module to take control of the clock
Text GLabel 8600 2600 0    60   Input ~ 0
CLK_OSC
$Comp
L 74xx-Computer-Symbols:74LS08 U6
U 1 1 5AD052E2
P 9250 1850
F 0 "U6" H 9250 1900 50  0000 C CNN
F 1 "74HCT08" H 9250 1800 50  0000 C CNN
F 2 "Package_DIP:DIP-14_W7.62mm" H 9250 1850 50  0001 C CNN
F 3 "" H 9250 1850 50  0001 C CNN
	1    9250 1850
	1    0    0    -1  
$EndComp
$Comp
L 74xx-Computer-Symbols:74LS08 U6
U 2 1 5AD0533F
P 10700 2500
F 0 "U6" H 10700 2550 50  0000 C CNN
F 1 "74HCT08" H 10700 2450 50  0000 C CNN
F 2 "Package_DIP:DIP-14_W7.62mm" H 10700 2500 50  0001 C CNN
F 3 "" H 10700 2500 50  0001 C CNN
	2    10700 2500
	1    0    0    -1  
$EndComp
$Comp
L 74xx-Computer-Symbols:74LS08 U6
U 3 1 5AD05B5D
P 12150 2800
F 0 "U6" H 12150 2850 50  0000 C CNN
F 1 "74HCT08" H 12150 2750 50  0000 C CNN
F 2 "Package_DIP:DIP-14_W7.62mm" H 12150 2800 50  0001 C CNN
F 3 "" H 12150 2800 50  0001 C CNN
	3    12150 2800
	1    0    0    -1  
$EndComp
$Comp
L 74xx-Computer-Symbols:74LS32 U8
U 2 1 5AD05CC4
P 11900 1950
F 0 "U8" H 11900 2000 50  0000 C CNN
F 1 "74HCT32" H 11900 1900 50  0000 C CNN
F 2 "Package_DIP:DIP-14_W7.62mm" H 11900 1950 50  0001 C CNN
F 3 "" H 11900 1950 50  0001 C CNN
	2    11900 1950
	1    0    0    -1  
$EndComp
$Comp
L 74xx-Computer-Symbols:SW_Push SW1
U 1 1 5AD4BFF4
P 1000 7200
F 0 "SW1" H 1050 7300 50  0000 L CNN
F 1 "Single-step" H 1000 7140 50  0000 C CNN
F 2 "Button_Switch_THT:SW_Tactile_SKHH_Angled" H 1000 7400 50  0001 C CNN
F 3 "" H 1000 7400 50  0001 C CNN
	1    1000 7200
	0    -1   -1   0   
$EndComp
$Comp
L 74xx-Computer-Symbols:SW_Push_SPDT SW4
U 1 1 5AD4C08D
P 3500 7400
F 0 "SW4" H 3500 7570 50  0000 C CNN
F 1 "Single-step" H 3450 7200 50  0000 C CNN
F 2 "DM-02:Slide-switch" H 3500 7400 50  0001 C CNN
F 3 "" H 3500 7400 50  0001 C CNN
	1    3500 7400
	0    -1   -1   0   
$EndComp
NoConn ~ 5050 6850
Wire Wire Line
	1000 6650 1450 6650
Wire Wire Line
	1000 7750 1400 7750
Wire Wire Line
	1950 7250 1950 7750
Connection ~ 1950 6250
Connection ~ 1950 7750
Wire Wire Line
	2450 6850 2550 6850
Wire Wire Line
	2550 6600 2550 6850
Wire Wire Line
	2550 7050 2450 7050
Connection ~ 2550 6850
Wire Wire Line
	2550 6250 2550 6300
Wire Wire Line
	1000 6600 1000 6650
Connection ~ 1000 6650
Wire Wire Line
	1000 6250 1200 6250
Wire Wire Line
	1450 7050 1200 7050
Wire Wire Line
	1200 7050 1200 6250
Connection ~ 1200 6250
Wire Wire Line
	1450 6850 1400 6850
Wire Wire Line
	1400 6850 1400 7200
Wire Wire Line
	1400 7500 1400 7750
Connection ~ 1400 7750
Wire Wire Line
	1000 7400 1000 7750
Wire Wire Line
	1000 6250 1000 6300
Wire Wire Line
	3400 6650 4050 6650
Wire Wire Line
	4550 7250 4550 7750
Connection ~ 4550 7750
Wire Wire Line
	5100 7050 5050 7050
Connection ~ 3400 6650
Wire Wire Line
	3400 6250 3850 6250
Wire Wire Line
	4050 6850 4000 6850
Wire Wire Line
	4000 6850 4000 7200
Wire Wire Line
	4000 7500 4000 7750
Connection ~ 4000 7750
Wire Wire Line
	3400 6600 3400 6650
Wire Wire Line
	3850 6300 3850 6250
Connection ~ 3850 6250
Wire Wire Line
	3600 7050 3850 7050
Wire Wire Line
	3850 7050 3850 6600
Wire Wire Line
	5100 7750 5100 7050
Connection ~ 5100 7750
Wire Wire Line
	3500 7750 4000 7750
Wire Wire Line
	5050 6650 5300 6650
Wire Wire Line
	3500 7600 3500 7750
Wire Wire Line
	3600 7200 3600 7050
Connection ~ 3850 7050
Wire Wire Line
	3400 6250 3400 6300
Wire Wire Line
	6450 7200 6550 7200
Wire Wire Line
	6700 7400 6700 7500
Wire Wire Line
	6850 7200 6950 7200
Wire Wire Line
	12500 1950 12500 2250
Wire Wire Line
	12500 2250 11550 2250
Wire Wire Line
	8600 2600 10100 2600
Wire Wire Line
	1950 6250 1950 6450
Wire Wire Line
	1950 6250 2550 6250
Wire Wire Line
	2550 6850 2550 7050
Wire Wire Line
	1000 6650 1000 7000
Wire Wire Line
	1200 6250 1950 6250
Wire Wire Line
	1400 7750 1950 7750
Wire Wire Line
	4550 6250 4550 6450
Wire Wire Line
	4550 7750 5100 7750
Wire Wire Line
	3400 6650 3400 7200
Wire Wire Line
	4000 7750 4550 7750
Wire Wire Line
	3850 6250 4550 6250
Wire Wire Line
	5100 7750 5300 7750
Wire Wire Line
	3850 7050 4050 7050
Connection ~ 3500 7750
$Comp
L 74xx-Computer-Symbols:74LS04 U2
U 3 1 5AD05E2B
P 9100 2800
F 0 "U2" H 9050 2800 50  0000 C CNN
F 1 "74HCT04" H 9290 2675 50  0000 C CNN
F 2 "Package_DIP:DIP-14_W7.62mm" H 9100 2800 50  0001 C CNN
F 3 "" H 9100 2800 50  0001 C CNN
	3    9100 2800
	1    0    0    -1  
$EndComp
Wire Wire Line
	8600 2800 8650 2800
Text GLabel 8600 2800 0    60   Input ~ 0
HALT
Text GLabel 10650 3700 0    50   Output ~ 0
CLOCK_PH2
Text GLabel 8850 4250 0    50   Output ~ 0
CLOCK_PH1
Wire Wire Line
	2650 6650 2450 6650
Wire Wire Line
	2550 7050 2550 7200
Connection ~ 2550 7050
Wire Wire Line
	2550 7500 2550 7750
Wire Wire Line
	1950 7750 2550 7750
Connection ~ 2550 7750
Wire Wire Line
	2550 7750 3500 7750
Wire Wire Line
	5300 7650 5300 7750
Wire Wire Line
	5300 7250 5300 7350
Wire Wire Line
	5300 6950 5300 6650
Connection ~ 5300 6650
Wire Wire Line
	5300 6650 5400 6650
Wire Wire Line
	11300 2500 11300 2050
Wire Wire Line
	2550 6250 3400 6250
Connection ~ 2550 6250
Connection ~ 3400 6250
Connection ~ 4550 6250
$Comp
L 74xx-Computer-Symbols:74LS32 U8
U 1 1 5DB777B3
P 10150 2900
F 0 "U8" H 10150 2950 50  0000 C CNN
F 1 "74HCT32" H 10150 2850 50  0000 C CNN
F 2 "Package_DIP:DIP-14_W7.62mm" H 10150 2900 50  0001 C CNN
F 3 "" H 10150 2900 50  0001 C CNN
	1    10150 2900
	1    0    0    -1  
$EndComp
Wire Wire Line
	10750 2900 11550 2900
Wire Wire Line
	11550 2250 11550 2700
Text Notes 2000 5050 0    50   ~ 0
When HALT is active (high), pushing the CONTINUE\nbutton once will cancel out the HALT signal:\n\nHigh (active) CONTINUE signal sets flip-flop.\nLow (inactive) HALT signal resets flip-flop.
$Comp
L 74xx-Computer-Symbols:NE555 U4
U 1 1 5DBC51EF
P 5200 5250
F 0 "U4" H 5150 5250 50  0000 L CNN
F 1 "555" H 5300 5600 50  0000 L CNN
F 2 "Package_DIP:DIP-8_W7.62mm" H 5200 5250 50  0001 C CNN
F 3 "" H 5200 5250 50  0001 C CNN
	1    5200 5250
	1    0    0    -1  
$EndComp
$Comp
L 74xx-Computer-Symbols:R R6
U 1 1 5DBC51F5
P 4050 4850
F 0 "R6" V 4130 4850 50  0000 C CNN
F 1 "5K" V 3950 4850 50  0000 C CNN
F 2 "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal" V 3980 4850 50  0001 C CNN
F 3 "" H 4050 4850 50  0001 C CNN
	1    4050 4850
	-1   0    0    1   
$EndComp
$Comp
L 74xx-Computer-Symbols:C C9
U 1 1 5DBC5208
P 4650 5650
F 0 "C9" H 4675 5750 50  0000 L CNN
F 1 "10nF" H 4675 5550 50  0000 L CNN
F 2 "Capacitor_THT:C_Rect_L4.6mm_W2.0mm_P2.50mm_MKS02_FKP02" H 4688 5500 50  0001 C CNN
F 3 "" H 4650 5650 50  0001 C CNN
	1    4650 5650
	1    0    0    -1  
$EndComp
$Comp
L 74xx-Computer-Symbols:R R7
U 1 1 5DBC520E
P 4500 4850
F 0 "R7" V 4580 4850 50  0000 C CNN
F 1 "5K" V 4400 4850 50  0000 C CNN
F 2 "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal" V 4430 4850 50  0001 C CNN
F 3 "" H 4500 4850 50  0001 C CNN
	1    4500 4850
	-1   0    0    1   
$EndComp
NoConn ~ 5700 5250
Wire Wire Line
	4050 5050 4700 5050
Wire Wire Line
	5200 5650 5200 5800
Connection ~ 5200 5800
Connection ~ 4050 5050
Wire Wire Line
	4050 4650 4500 4650
Wire Wire Line
	4700 5250 4650 5250
Wire Wire Line
	4650 5250 4650 5500
Wire Wire Line
	4050 5000 4050 5050
Wire Wire Line
	4500 4700 4500 4650
Connection ~ 4500 4650
Wire Wire Line
	4500 5450 4500 5000
Wire Wire Line
	5700 5800 5700 5450
Connection ~ 5700 5800
Wire Wire Line
	4050 4650 4050 4700
Wire Wire Line
	5200 4650 5200 4850
Wire Wire Line
	5200 5800 5700 5800
Wire Wire Line
	4050 5050 4050 5250
Wire Wire Line
	4650 5800 5200 5800
Wire Wire Line
	4500 4650 5200 4650
Wire Wire Line
	4500 5450 4700 5450
$Comp
L 74xx-Computer-Symbols:+5V #PWR08
U 1 1 5DBEABD3
P 5300 4650
F 0 "#PWR08" H 5300 4500 50  0001 C CNN
F 1 "+5V" H 5300 4790 50  0000 C CNN
F 2 "" H 5300 4650 50  0001 C CNN
F 3 "" H 5300 4650 50  0001 C CNN
	1    5300 4650
	0    1    1    0   
$EndComp
Connection ~ 5200 4650
$Comp
L 74xx-Computer-Symbols:GND #PWR010
U 1 1 5DBEAC5C
P 5700 5800
F 0 "#PWR010" H 5700 5550 50  0001 C CNN
F 1 "GND" H 5700 5650 50  0000 C CNN
F 2 "" H 5700 5800 50  0001 C CNN
F 3 "" H 5700 5800 50  0001 C CNN
	1    5700 5800
	1    0    0    -1  
$EndComp
Text Notes 4050 5100 3    50   ~ 0
~SET
Text Notes 4500 5100 3    50   ~ 0
~RESET
Wire Wire Line
	5300 4650 5200 4650
Wire Wire Line
	7900 3000 8650 3000
Text Notes 5800 5050 0    50   ~ 0
CONTINUE
$Comp
L 74xx-Computer-Symbols:R R11
U 1 1 5DD01CC6
P 8650 3150
F 0 "R11" V 8730 3150 50  0000 C CNN
F 1 "5K" V 8550 3150 50  0000 C CNN
F 2 "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal" V 8580 3150 50  0001 C CNN
F 3 "" H 8650 3150 50  0001 C CNN
	1    8650 3150
	-1   0    0    1   
$EndComp
$Comp
L 74xx-Computer-Symbols:GND #PWR014
U 1 1 5DD01E72
P 8650 3300
F 0 "#PWR014" H 8650 3050 50  0001 C CNN
F 1 "GND" H 8650 3150 50  0000 C CNN
F 2 "" H 8650 3300 50  0001 C CNN
F 3 "" H 8650 3300 50  0001 C CNN
	1    8650 3300
	1    0    0    -1  
$EndComp
Connection ~ 8650 3000
Wire Wire Line
	8650 3000 9550 3000
Wire Wire Line
	4550 6250 5300 6250
$Comp
L 74xx-Computer-Symbols:74LS04 U2
U 2 1 5AD05D2F
P 9100 2400
F 0 "U2" H 9050 2400 50  0000 C CNN
F 1 "74HCT04" H 9100 2350 50  0001 C CNN
F 2 "Package_DIP:DIP-14_W7.62mm" H 9100 2400 50  0001 C CNN
F 3 "" H 9100 2400 50  0001 C CNN
	2    9100 2400
	1    0    0    -1  
$EndComp
Wire Wire Line
	9550 2400 10100 2400
Wire Wire Line
	9850 1850 11300 1850
Wire Wire Line
	8650 1950 8650 2400
$Comp
L Device:C_Small C11
U 1 1 5E9AEE4F
P 10650 4500
F 0 "C11" H 10500 4500 50  0000 C CNN
F 1 "1nF" H 10500 4400 50  0000 C CNN
F 2 "Capacitor_THT:C_Rect_L4.6mm_W3.0mm_P2.50mm_MKS02_FKP02" H 10650 4500 50  0001 C CNN
F 3 "~" H 10650 4500 50  0001 C CNN
	1    10650 4500
	-1   0    0    1   
$EndComp
$Comp
L power:GND #PWR017
U 1 1 5E9B5AEB
P 10650 4600
F 0 "#PWR017" H 10650 4350 50  0001 C CNN
F 1 "GND" H 10650 4450 50  0000 C CNN
F 2 "" H 10650 4600 50  0001 C CNN
F 3 "" H 10650 4600 50  0001 C CNN
	1    10650 4600
	1    0    0    -1  
$EndComp
Text GLabel 8850 4050 0    50   Output ~ 0
CLOCK_PH3
Wire Wire Line
	11550 3700 11550 3900
Text GLabel 10650 3900 0    50   Output ~ 0
CLOCK_PH0
$Comp
L Device:Polyfuse F1
U 1 1 5EA0A4D1
P 2050 8450
F 0 "F1" V 1735 8450 50  0000 C CNN
F 1 "Polyfuse" V 1826 8450 50  0000 C CNN
F 2 "Capacitor_THT:C_Disc_D9.0mm_W2.5mm_P5.00mm" H 2100 8250 50  0001 L CNN
F 3 "~" H 2050 8450 50  0001 C CNN
F 4 "750mA" V 1917 8450 50  0000 C CNN "Rating"
	1    2050 8450
	0    1    1    0   
$EndComp
Wire Wire Line
	1900 8750 2350 8750
$Comp
L 74xx-Computer-Symbols:74LS08 U6
U 4 1 5EA24F80
P 12150 3700
F 0 "U6" H 12150 3750 50  0000 C CNN
F 1 "74HCT08" H 12150 3650 50  0000 C CNN
F 2 "Package_DIP:DIP-14_W7.62mm" H 12150 3700 50  0001 C CNN
F 3 "" H 12150 3700 50  0001 C CNN
	4    12150 3700
	-1   0    0    1   
$EndComp
Text GLabel 12800 3800 2    50   Input ~ 0
CLOCK_ENABLE
$Comp
L Device:R R12
U 1 1 5EA37418
P 12750 4100
F 0 "R12" H 12600 4150 50  0000 C CNN
F 1 "5K" H 12600 4050 50  0000 C CNN
F 2 "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal" V 12680 4100 50  0001 C CNN
F 3 "~" H 12750 4100 50  0001 C CNN
	1    12750 4100
	-1   0    0    1   
$EndComp
$Comp
L power:+5V #PWR018
U 1 1 5EA3E422
P 12750 4250
F 0 "#PWR018" H 12750 4100 50  0001 C CNN
F 1 "+5V" H 12700 4400 50  0000 L CNN
F 2 "" H 12750 4250 50  0001 C CNN
F 3 "" H 12750 4250 50  0001 C CNN
	1    12750 4250
	-1   0    0    1   
$EndComp
Wire Wire Line
	12750 3800 12800 3800
Wire Wire Line
	12750 3950 12750 3800
Connection ~ 12750 3800
$Comp
L 74xx-Computer-Symbols:74HC14 U7
U 2 1 5E9B8AA4
P 11100 4250
F 0 "U7" H 11050 4250 50  0000 C CNN
F 1 "74HCT14" H 10750 4350 50  0000 C CNN
F 2 "Package_DIP:DIP-14_W7.62mm" H 11100 4250 50  0001 C CNN
F 3 "" H 11100 4250 50  0001 C CNN
	2    11100 4250
	-1   0    0    1   
$EndComp
Connection ~ 10650 4250
Wire Wire Line
	10650 4250 10650 4400
$Comp
L 74xx-Computer-Symbols:74HC14 U7
U 3 1 5E9B9CEF
P 10200 4250
F 0 "U7" H 10150 4250 50  0000 C CNN
F 1 "74HCT14" H 10400 4350 50  0000 C CNN
F 2 "Package_DIP:DIP-14_W7.62mm" H 10200 4250 50  0001 C CNN
F 3 "" H 10200 4250 50  0001 C CNN
	3    10200 4250
	-1   0    0    1   
$EndComp
$Comp
L 74xx-Computer-Symbols:74HC14 U7
U 4 1 5E9C721B
P 9300 4050
F 0 "U7" H 9250 4050 50  0000 C CNN
F 1 "74HCT14" H 9500 4150 50  0000 C CNN
F 2 "Package_DIP:DIP-14_W7.62mm" H 9300 4050 50  0001 C CNN
F 3 "" H 9300 4050 50  0001 C CNN
	4    9300 4050
	-1   0    0    1   
$EndComp
Wire Wire Line
	8850 4250 9750 4250
Wire Wire Line
	9750 4250 9750 4050
Connection ~ 9750 4250
Wire Wire Line
	10650 3900 11550 3900
Connection ~ 11550 3900
Wire Wire Line
	11550 3900 11550 4250
Connection ~ 11550 3700
$Comp
L 74xx-Computer-Symbols:74HC14 U7
U 1 1 5E9B7892
P 11100 3700
F 0 "U7" H 11050 3700 50  0000 C CNN
F 1 "74HCT14" H 11300 3800 50  0000 C CNN
F 2 "Package_DIP:DIP-14_W7.62mm" H 11100 3700 50  0001 C CNN
F 3 "" H 11100 3700 50  0001 C CNN
	1    11100 3700
	-1   0    0    1   
$EndComp
Connection ~ 4500 5450
Wire Wire Line
	3150 5450 3450 5450
$Comp
L 74xx-Computer-Symbols:+5V #PWR02
U 1 1 5DD319DB
P 1500 5250
F 0 "#PWR02" H 1500 5100 50  0001 C CNN
F 1 "+5V" H 1500 5390 50  0000 C CNN
F 2 "" H 1500 5250 50  0001 C CNN
F 3 "" H 1500 5250 50  0001 C CNN
	1    1500 5250
	0    -1   -1   0   
$EndComp
Connection ~ 2150 5250
Wire Wire Line
	2150 5250 3150 5250
Wire Wire Line
	2150 5250 1900 5250
Wire Wire Line
	2150 5400 2150 5250
Wire Wire Line
	1900 5400 2150 5400
$Comp
L Switch:SW_Push SW3
U 1 1 5DD0D901
P 1700 5250
F 0 "SW3" H 1700 5535 50  0000 C CNN
F 1 "CONTINUE" H 1700 5444 50  0000 C CNN
F 2 "Button_Switch_THT:SW_Tactile_SKHH_Angled" H 1700 5450 50  0001 C CNN
F 3 "" H 1700 5450 50  0001 C CNN
	1    1700 5250
	1    0    0    -1  
$EndComp
Text GLabel 3150 5450 0    60   Input ~ 0
HALT
Text GLabel 1900 5400 0    60   Input ~ 0
CONTINUE
$Comp
L 74xx-Computer-Symbols:74LS04 U2
U 1 1 5DBD1E43
P 3600 5250
F 0 "U2" H 3550 5250 50  0000 C CNN
F 1 "74HCT04" H 3790 5125 50  0000 C CNN
F 2 "Package_DIP:DIP-14_W7.62mm" H 3600 5250 50  0001 C CNN
F 3 "" H 3600 5250 50  0001 C CNN
	1    3600 5250
	1    0    0    -1  
$EndComp
$Comp
L power:GND #PWR01
U 1 1 5D77B846
P 1150 750
F 0 "#PWR01" H 1150 500 50  0001 C CNN
F 1 "GND" H 1155 577 50  0000 C CNN
F 2 "" H 1150 750 50  0001 C CNN
F 3 "" H 1150 750 50  0001 C CNN
	1    1150 750 
	-1   0    0    1   
$EndComp
$Comp
L power:+5V #PWR04
U 1 1 5D77BAB5
P 3050 750
F 0 "#PWR04" H 3050 600 50  0001 C CNN
F 1 "+5V" H 3000 900 50  0000 L CNN
F 2 "" H 3050 750 50  0001 C CNN
F 3 "" H 3050 750 50  0001 C CNN
	1    3050 750 
	1    0    0    -1  
$EndComp
$Comp
L power:PWR_FLAG #FLG02
U 1 1 5D77BB66
P 2900 750
F 0 "#FLG02" H 2900 825 50  0001 C CNN
F 1 "PWR_FLAG" H 2900 924 50  0001 C CNN
F 2 "" H 2900 750 50  0001 C CNN
F 3 "~" H 2900 750 50  0001 C CNN
	1    2900 750 
	1    0    0    -1  
$EndComp
$Comp
L 74xx-Computer-Symbols:VCC #PWR03
U 1 1 5D77BC4F
P 2800 750
F 0 "#PWR03" H 2800 600 50  0001 C CNN
F 1 "VCC" H 2817 923 50  0001 C CNN
F 2 "" H 2800 750 50  0001 C CNN
F 3 "" H 2800 750 50  0001 C CNN
	1    2800 750 
	1    0    0    -1  
$EndComp
$Comp
L power:PWR_FLAG #FLG01
U 1 1 5D77BC96
P 1300 750
F 0 "#FLG01" H 1300 825 50  0001 C CNN
F 1 "PWR_FLAG" H 1300 924 50  0001 C CNN
F 2 "" H 1300 750 50  0001 C CNN
F 3 "~" H 1300 750 50  0001 C CNN
	1    1300 750 
	1    0    0    -1  
$EndComp
Text GLabel 1150 1450 0    39   Input ~ 0
~RESET
Text GLabel 1150 850  0    50   Input ~ 0
CLOCK_PH0
Text GLabel 3050 850  2    50   Input ~ 0
CLOCK_PH1
Text GLabel 1150 950  0    50   Input ~ 0
CLOCK_PH2
Text GLabel 3050 950  2    50   Input ~ 0
CLOCK_PH3
Text GLabel 1150 1050 0    50   Input ~ 0
CLOCK_ENABLE
$Comp
L 74xx-Computer-Symbols:LED D2
U 1 1 5E9B81E8
P 3450 5600
F 0 "D2" H 3450 5700 50  0000 C CNN
F 1 "HALT" V 3450 5450 50  0000 C CNN
F 2 "LED_THT:LED_D5.0mm_Horizontal_O1.27mm_Z3.0mm" H 3450 5600 50  0001 C CNN
F 3 "" H 3450 5600 50  0001 C CNN
	1    3450 5600
	0    -1   -1   0   
$EndComp
$Comp
L 74xx-Computer-Symbols:R R4
U 1 1 5E9B81F2
P 3450 5900
F 0 "R4" V 3350 5900 50  0000 C CNN
F 1 "330" V 3550 5900 50  0000 C CNN
F 2 "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal" V 3380 5900 50  0001 C CNN
F 3 "" H 3450 5900 50  0001 C CNN
	1    3450 5900
	1    0    0    -1  
$EndComp
Connection ~ 3450 5450
Wire Wire Line
	3450 5450 4500 5450
$Comp
L power:GND #PWR05
U 1 1 5E9CD855
P 3250 6050
F 0 "#PWR05" H 3250 5800 50  0001 C CNN
F 1 "GND" H 3250 5900 50  0000 C CNN
F 2 "" H 3250 6050 50  0001 C CNN
F 3 "" H 3250 6050 50  0001 C CNN
	1    3250 6050
	0    1    1    0   
$EndComp
Wire Wire Line
	3250 6050 3450 6050
$Comp
L 74xx-Computer-Symbols:C C4
U 1 1 5E9C08A0
P 3550 8600
F 0 "C4" H 3575 8700 50  0000 L CNN
F 1 "100nF" H 3575 8500 50  0000 L CNN
F 2 "Capacitor_THT:C_Rect_L4.6mm_W2.0mm_P2.50mm_MKS02_FKP02" H 3588 8450 50  0001 C CNN
F 3 "" H 3550 8600 50  0001 C CNN
	1    3550 8600
	1    0    0    -1  
$EndComp
Connection ~ 3550 8450
Wire Wire Line
	3550 8450 3900 8450
Connection ~ 3550 8750
Wire Wire Line
	3550 8750 3900 8750
$Comp
L 74xx-Computer-Symbols:C C5
U 1 1 5E9C0EDD
P 3900 8600
F 0 "C5" H 3925 8700 50  0000 L CNN
F 1 "100nF" H 3925 8500 50  0000 L CNN
F 2 "Capacitor_THT:C_Rect_L4.6mm_W2.0mm_P2.50mm_MKS02_FKP02" H 3938 8450 50  0001 C CNN
F 3 "" H 3900 8600 50  0001 C CNN
	1    3900 8600
	1    0    0    -1  
$EndComp
Connection ~ 3900 8450
Wire Wire Line
	3900 8450 4250 8450
Connection ~ 3900 8750
Wire Wire Line
	3900 8750 4250 8750
$Comp
L 74xx-Computer-Symbols:C C7
U 1 1 5E9C1247
P 4250 8600
F 0 "C7" H 4275 8700 50  0000 L CNN
F 1 "100nF" H 4275 8500 50  0000 L CNN
F 2 "Capacitor_THT:C_Rect_L4.6mm_W2.0mm_P2.50mm_MKS02_FKP02" H 4288 8450 50  0001 C CNN
F 3 "" H 4250 8600 50  0001 C CNN
	1    4250 8600
	1    0    0    -1  
$EndComp
Connection ~ 4250 8450
Wire Wire Line
	4250 8450 4600 8450
Connection ~ 4250 8750
Wire Wire Line
	4250 8750 4600 8750
$Comp
L 74xx-Computer-Symbols:C C8
U 1 1 5E9C1770
P 4600 8600
F 0 "C8" H 4625 8700 50  0000 L CNN
F 1 "100nF" H 4625 8500 50  0000 L CNN
F 2 "Capacitor_THT:C_Rect_L4.6mm_W2.0mm_P2.50mm_MKS02_FKP02" H 4638 8450 50  0001 C CNN
F 3 "" H 4600 8600 50  0001 C CNN
	1    4600 8600
	1    0    0    -1  
$EndComp
Connection ~ 4600 8450
Wire Wire Line
	4600 8450 5750 8450
Connection ~ 4600 8750
Wire Wire Line
	4600 8750 5750 8750
Text Notes 3750 8350 0    50   ~ 0
Decoupling caps
$Comp
L 74xx-Computer-Symbols:GND #PWR0101
U 1 1 5E9C6EFB
P 5300 7750
F 0 "#PWR0101" H 5300 7500 50  0001 C CNN
F 1 "GND" H 5300 7600 50  0000 C CNN
F 2 "" H 5300 7750 50  0001 C CNN
F 3 "" H 5300 7750 50  0001 C CNN
	1    5300 7750
	1    0    0    -1  
$EndComp
Connection ~ 5300 7750
NoConn ~ 3050 1050
NoConn ~ 3050 1150
NoConn ~ 3050 1250
NoConn ~ 3050 1350
NoConn ~ 3050 1450
NoConn ~ 3050 1550
NoConn ~ 3050 1650
NoConn ~ 3050 1750
NoConn ~ 3050 1850
NoConn ~ 3050 1950
NoConn ~ 3050 2050
NoConn ~ 3050 2150
NoConn ~ 3050 2250
NoConn ~ 3050 2350
NoConn ~ 3050 2450
NoConn ~ 3050 2550
NoConn ~ 3050 2650
NoConn ~ 1150 2650
NoConn ~ 1150 2550
NoConn ~ 1150 2450
NoConn ~ 1150 2350
NoConn ~ 1150 2250
NoConn ~ 1150 2050
NoConn ~ 1150 1950
NoConn ~ 1150 1850
NoConn ~ 1150 1750
NoConn ~ 1150 1650
NoConn ~ 1150 1550
NoConn ~ 1150 1250
NoConn ~ 1150 1150
NoConn ~ 3050 3050
NoConn ~ 1150 3350
NoConn ~ 1150 3250
NoConn ~ 1150 3150
NoConn ~ 1150 3050
NoConn ~ 1150 2950
NoConn ~ 1150 2850
NoConn ~ 1150 2750
NoConn ~ 1150 3450
NoConn ~ 3050 3850
NoConn ~ 3050 3750
NoConn ~ 3050 3550
NoConn ~ 3050 3450
NoConn ~ 3050 3350
NoConn ~ 3050 3250
NoConn ~ 3050 3150
NoConn ~ 3050 2950
NoConn ~ 3050 2850
NoConn ~ 3050 2750
NoConn ~ 1150 3550
NoConn ~ 1150 3650
NoConn ~ 1150 3750
NoConn ~ 1150 3850
Text Label 1950 750  2    50   ~ 0
GND
Text Label 1950 850  2    50   ~ 0
CLOCK_PH0
Text Label 1950 950  2    50   ~ 0
CLOCK_PH2
Text Label 1950 1050 2    50   ~ 0
CLOCK_ENABLE
Text Label 1950 1150 2    50   ~ 0
BTN_STEP_ENABLE
Text Label 1950 1250 2    50   ~ 0
BTN_STEP
Text Label 1950 1350 2    50   ~ 0
BTN_CONTINUE
Text Label 1950 1450 2    50   ~ 0
BTN_RESET
Text Label 1950 1550 2    50   ~ 0
IO_load
Text Label 1950 1950 2    50   ~ 0
~A_load
Text Label 1950 2050 2    50   ~ 0
~B_load
Text Label 1950 2150 2    50   ~ 0
~C_load
Text Label 1950 2250 2    50   ~ 0
~H_load
Text Label 1950 2350 2    50   ~ 0
~L_load
Text Label 1950 2450 2    50   ~ 0
~F_load
Text Label 1950 2550 2    50   ~ 0
~ALU_load
Text Label 1950 2650 2    50   ~ 0
~MEM_load
Text Label 1950 2750 2    50   ~ 0
~PC_H_load
Text Label 1950 2850 2    50   ~ 0
~PC_L_load
Text Label 1950 2950 2    50   ~ 0
~STK_H_load
Text Label 1950 3050 2    50   ~ 0
~STK_L_load
Text Label 1950 3150 2    50   ~ 0
~MAR_H_load
Text Label 1950 3250 2    50   ~ 0
~MAR_L_load
Text Label 1950 3350 2    50   ~ 0
~IR_load
Text Label 1950 3450 2    50   ~ 0
~PC_MAR_transfer
Text Label 1950 3550 2    50   ~ 0
~STK_MAR_transfer
Text Label 1950 3650 2    50   ~ 0
PC_inc
Text Label 1950 3750 2    50   ~ 0
~MAR_inc
Text Label 1950 3850 2    50   ~ 0
FETCH_done
Text Label 2450 750  0    50   ~ 0
5V
Text Label 2450 850  0    50   ~ 0
CLOCK_PH1
Text Label 2450 950  0    50   ~ 0
CLOCK_PH3
Text Label 2450 1550 0    50   ~ 0
IO_out
Text Label 2450 1950 0    50   ~ 0
~A_out
Text Label 2450 2050 0    50   ~ 0
~B_out
Text Label 2450 2150 0    50   ~ 0
~C_out
Text Label 2450 2250 0    50   ~ 0
~H_out
Text Label 2450 2350 0    50   ~ 0
~L_out
Text Label 2450 2450 0    50   ~ 0
~F_out
Text Label 2450 2550 0    50   ~ 0
~ALU_out
Text Label 2450 2650 0    50   ~ 0
~MEM_out
Text Label 2450 2750 0    50   ~ 0
~PC_H_out
Text Label 2450 2850 0    50   ~ 0
~PC_L_out
Text Label 2450 2950 0    50   ~ 0
~STK_H_out
Text Label 2450 3050 0    50   ~ 0
~STK_L_out
Text Label 2450 3150 0    50   ~ 0
~FSET_c
Text Label 2450 3250 0    50   ~ 0
~FSET_z
Text Label 2450 3350 0    50   ~ 0
~FCLR_c
Text Label 2450 3450 0    50   ~ 0
~FCLR_z
Text Label 2450 3550 0    50   ~ 0
TSTATE_reset
Text Label 2450 3650 0    50   ~ 0
HALT
Text Label 2450 3750 0    50   ~ 0
STK_inc
Text Label 2450 3850 0    50   ~ 0
STK_dec
NoConn ~ 1150 2150
Wire Wire Line
	3050 750  2900 750 
Wire Wire Line
	3050 850  2450 850 
Wire Wire Line
	3050 950  2450 950 
Wire Wire Line
	3050 1050 2450 1050
Wire Wire Line
	3050 1150 2450 1150
Wire Wire Line
	3050 1250 2450 1250
Wire Wire Line
	3050 1350 2450 1350
Wire Wire Line
	3050 1450 2450 1450
Wire Wire Line
	3050 1550 2450 1550
Wire Wire Line
	3050 1650 2450 1650
Wire Wire Line
	3050 1750 2450 1750
Wire Wire Line
	3050 1850 2450 1850
Wire Wire Line
	3050 1950 2450 1950
Wire Wire Line
	3050 2050 2450 2050
Wire Wire Line
	3050 2150 2450 2150
Wire Wire Line
	3050 2250 2450 2250
Wire Wire Line
	3050 2350 2450 2350
Wire Wire Line
	3050 2450 2450 2450
Wire Wire Line
	3050 2550 2450 2550
Wire Wire Line
	3050 2650 2450 2650
Wire Wire Line
	3050 2750 2450 2750
Wire Wire Line
	3050 2850 2450 2850
Wire Wire Line
	3050 2950 2450 2950
Wire Wire Line
	3050 3050 2450 3050
Wire Wire Line
	3050 3150 2450 3150
Wire Wire Line
	3050 3250 2450 3250
Wire Wire Line
	3050 3350 2450 3350
Wire Wire Line
	3050 3450 2450 3450
Wire Wire Line
	3050 3550 2450 3550
Wire Wire Line
	3050 3650 2450 3650
Wire Wire Line
	3050 3750 2450 3750
Wire Wire Line
	3050 3850 2450 3850
Wire Wire Line
	1150 1050 1950 1050
Wire Wire Line
	1150 3850 1950 3850
Wire Wire Line
	1150 3750 1950 3750
Wire Wire Line
	1150 3650 1950 3650
Wire Wire Line
	1150 950  1950 950 
Wire Wire Line
	1150 3550 1950 3550
Wire Wire Line
	1150 3450 1950 3450
Wire Wire Line
	1150 3350 1950 3350
Wire Wire Line
	1150 3250 1950 3250
Wire Wire Line
	1150 3150 1950 3150
Wire Wire Line
	1150 3050 1950 3050
Wire Wire Line
	1150 2950 1950 2950
Wire Wire Line
	1150 2850 1950 2850
Wire Wire Line
	1150 2750 1950 2750
Wire Wire Line
	1150 2650 1950 2650
Wire Wire Line
	1150 850  1950 850 
Wire Wire Line
	1150 2550 1950 2550
Wire Wire Line
	1150 2450 1950 2450
Wire Wire Line
	1150 2350 1950 2350
Wire Wire Line
	1150 2250 1950 2250
Wire Wire Line
	1150 2150 1950 2150
Wire Wire Line
	1150 2050 1950 2050
Wire Wire Line
	1150 1950 1950 1950
Wire Wire Line
	1150 1850 1950 1850
Wire Wire Line
	1150 1750 1950 1750
Wire Wire Line
	1150 1650 1950 1650
Wire Wire Line
	1150 1550 1950 1550
Wire Wire Line
	1150 1350 1950 1350
Wire Wire Line
	1150 1250 1950 1250
Wire Wire Line
	1150 1150 1950 1150
$Comp
L Connector_Generic:Conn_02x32_Odd_Even BUS1
U 1 1 5EC3909D
P 2250 2250
F 0 "BUS1" H 2300 3875 50  0000 C CNN
F 1 "Conn_02x32_Odd_Even" H 2300 3876 50  0001 C CNN
F 2 "Connector_PinSocket_2.54mm:PinSocket_2x32_P2.54mm_Vertical" H 2250 2250 50  0001 C CNN
F 3 "~" H 2250 2250 50  0001 C CNN
	1    2250 2250
	-1   0    0    -1  
$EndComp
Wire Wire Line
	1950 750  1300 750 
Connection ~ 1300 750 
Wire Wire Line
	1300 750  1150 750 
Connection ~ 2900 750 
Wire Wire Line
	2900 750  2800 750 
Connection ~ 2800 750 
Wire Wire Line
	2800 750  2450 750 
Wire Wire Line
	1150 1450 1950 1450
Connection ~ 8650 1950
Wire Wire Line
	3750 3850 4300 3850
Wire Wire Line
	3750 3750 4300 3750
Wire Wire Line
	3750 3650 4300 3650
Wire Wire Line
	3750 3550 4300 3550
Wire Wire Line
	3750 3450 4300 3450
Wire Wire Line
	3750 3350 4300 3350
Wire Wire Line
	3750 3250 4300 3250
Wire Wire Line
	3750 3150 4300 3150
Wire Wire Line
	3750 3050 4300 3050
Wire Wire Line
	3750 2950 4300 2950
Wire Wire Line
	3750 2850 4300 2850
Wire Wire Line
	3750 2750 4300 2750
Wire Wire Line
	3750 2650 4300 2650
Wire Wire Line
	3750 2550 4300 2550
Wire Wire Line
	3750 2450 4300 2450
Wire Wire Line
	3750 2350 4300 2350
Wire Wire Line
	3750 2250 4300 2250
Wire Wire Line
	3750 2150 4300 2150
NoConn ~ 3750 2150
Wire Wire Line
	3750 2050 4300 2050
Wire Wire Line
	3750 1950 4300 1950
Wire Wire Line
	3750 1850 4300 1850
Wire Wire Line
	3750 1750 4300 1750
Wire Wire Line
	3750 1650 4300 1650
Wire Wire Line
	3750 1550 4300 1550
Wire Wire Line
	3750 1450 4300 1450
Wire Wire Line
	3750 1350 4300 1350
Wire Wire Line
	3750 1250 4300 1250
Wire Wire Line
	3750 1150 4300 1150
Wire Wire Line
	3750 1050 4300 1050
Wire Wire Line
	3750 950  4300 950 
Wire Wire Line
	3750 850  4300 850 
Wire Wire Line
	4300 750  3750 750 
NoConn ~ 3750 3850
NoConn ~ 3750 3750
NoConn ~ 3750 3650
NoConn ~ 3750 3550
NoConn ~ 3750 3450
NoConn ~ 3750 2750
NoConn ~ 3750 2850
NoConn ~ 3750 2950
NoConn ~ 3750 3050
NoConn ~ 3750 3150
NoConn ~ 3750 3250
NoConn ~ 3750 3350
NoConn ~ 3750 750 
NoConn ~ 3750 850 
NoConn ~ 3750 950 
NoConn ~ 3750 1150
NoConn ~ 3750 1250
NoConn ~ 3750 1350
NoConn ~ 3750 1450
NoConn ~ 3750 1550
NoConn ~ 3750 1650
NoConn ~ 3750 1750
NoConn ~ 3750 1850
NoConn ~ 3750 1950
NoConn ~ 3750 2050
NoConn ~ 3750 2250
NoConn ~ 3750 2350
NoConn ~ 3750 2450
NoConn ~ 3750 2550
NoConn ~ 3750 2650
NoConn ~ 3750 1050
Wire Wire Line
	5250 3850 4800 3850
Wire Wire Line
	5250 3750 4800 3750
Wire Wire Line
	5250 3650 4800 3650
Wire Wire Line
	5250 3550 4800 3550
Wire Wire Line
	5250 3450 4800 3450
Wire Wire Line
	5250 3350 4800 3350
Wire Wire Line
	5250 3250 4800 3250
Wire Wire Line
	5250 3150 4800 3150
Wire Wire Line
	5250 3050 4800 3050
Wire Wire Line
	5250 2950 4800 2950
Wire Wire Line
	5250 2850 4800 2850
Wire Wire Line
	5250 2750 4800 2750
Wire Wire Line
	5250 2650 4800 2650
Wire Wire Line
	5250 2550 4800 2550
Wire Wire Line
	5250 2450 4800 2450
Wire Wire Line
	5250 2350 4800 2350
Wire Wire Line
	5250 2250 4800 2250
Wire Wire Line
	5250 2150 4800 2150
Wire Wire Line
	5250 2050 4800 2050
Wire Wire Line
	5250 1950 4800 1950
Wire Wire Line
	5250 1850 4800 1850
Wire Wire Line
	5250 1750 4800 1750
Wire Wire Line
	5250 1650 4800 1650
Wire Wire Line
	5250 1550 4800 1550
Wire Wire Line
	5250 1450 4800 1450
Wire Wire Line
	5250 1350 4800 1350
Wire Wire Line
	5250 1250 4800 1250
Wire Wire Line
	5250 1150 4800 1150
Wire Wire Line
	5250 1050 4800 1050
Wire Wire Line
	5250 950  4800 950 
Wire Wire Line
	5250 850  4800 850 
Wire Wire Line
	5250 750  4800 750 
NoConn ~ 5250 2750
NoConn ~ 5250 2850
NoConn ~ 5250 2950
NoConn ~ 5250 3150
NoConn ~ 5250 3250
NoConn ~ 5250 3350
NoConn ~ 5250 3450
NoConn ~ 5250 3550
NoConn ~ 5250 3650
NoConn ~ 5250 3750
NoConn ~ 5250 3850
NoConn ~ 5250 3050
NoConn ~ 5250 950 
NoConn ~ 5250 850 
NoConn ~ 5250 750 
NoConn ~ 5250 2650
NoConn ~ 5250 2550
NoConn ~ 5250 2450
NoConn ~ 5250 2350
NoConn ~ 5250 2250
NoConn ~ 5250 2150
NoConn ~ 5250 2050
NoConn ~ 5250 1950
NoConn ~ 5250 1850
NoConn ~ 5250 1750
NoConn ~ 5250 1650
NoConn ~ 5250 1550
NoConn ~ 5250 1450
NoConn ~ 5250 1350
NoConn ~ 5250 1250
NoConn ~ 5250 1150
NoConn ~ 5250 1050
Text Label 4800 3050 0    50   ~ 0
TSTATE3
Text Label 4800 2950 0    50   ~ 0
TSTATE2
Text Label 4800 2850 0    50   ~ 0
TSTATE1
Text Label 4800 2750 0    50   ~ 0
TSTATE0
Text Label 4800 2650 0    50   ~ 0
FLAGS3
Text Label 4800 2550 0    50   ~ 0
FLAGS2
Text Label 4800 2450 0    50   ~ 0
FLAGS1
Text Label 4800 2350 0    50   ~ 0
FLAGS0
Text Label 4800 2250 0    50   ~ 0
A15
Text Label 4800 2150 0    50   ~ 0
A14
Text Label 4800 2050 0    50   ~ 0
A13
Text Label 4800 1950 0    50   ~ 0
A12
Text Label 4800 1850 0    50   ~ 0
A11
Text Label 4800 1750 0    50   ~ 0
A10
Text Label 4800 1650 0    50   ~ 0
A9
Text Label 4800 1550 0    50   ~ 0
A8
Text Label 4800 1450 0    50   ~ 0
A7
Text Label 4800 1350 0    50   ~ 0
A6
Text Label 4800 1250 0    50   ~ 0
A5
Text Label 4800 1150 0    50   ~ 0
A4
Text Label 4800 1050 0    50   ~ 0
A3
Text Label 4800 950  0    50   ~ 0
A2
Text Label 4800 850  0    50   ~ 0
A1
Text Label 4800 750  0    50   ~ 0
A0
Text Label 4300 2750 2    50   ~ 0
ALUFUNC4
Text Label 4300 2650 2    50   ~ 0
ALUFUNC3
Text Label 4300 2550 2    50   ~ 0
ALUFUNC2
Text Label 4300 2450 2    50   ~ 0
ALUFUNC1
Text Label 4300 2350 2    50   ~ 0
ALUFUNC0
Text Label 4300 2250 2    50   ~ 0
INSTR7
Text Label 4300 2150 2    50   ~ 0
INSTR6
Text Label 4300 2050 2    50   ~ 0
INSTR5
Text Label 4300 1950 2    50   ~ 0
INSTR4
Text Label 4300 1850 2    50   ~ 0
INSTR3
Text Label 4300 1750 2    50   ~ 0
INSTR2
Text Label 4300 1650 2    50   ~ 0
INSTR1
Text Label 4300 1550 2    50   ~ 0
INSTR0
Text Label 4300 1450 2    50   ~ 0
DATA7
Text Label 4300 1350 2    50   ~ 0
DATA6
Text Label 4300 1250 2    50   ~ 0
DATA5
Text Label 4300 1150 2    50   ~ 0
DATA4
Text Label 4300 1050 2    50   ~ 0
DATA3
Text Label 4300 950  2    50   ~ 0
DATA2
Text Label 4300 850  2    50   ~ 0
DATA1
Text Label 4300 750  2    50   ~ 0
DATA0
$Comp
L Connector_Generic:Conn_02x32_Odd_Even BUS2
U 1 1 5EC6B636
P 4600 2250
F 0 "BUS2" H 4650 3875 50  0000 C CNN
F 1 "Conn_02x32_Odd_Even" H 4650 3876 50  0001 C CNN
F 2 "Connector_PinSocket_2.54mm:PinSocket_2x32_P2.54mm_Vertical" H 4600 2250 50  0001 C CNN
F 3 "~" H 4600 2250 50  0001 C CNN
	1    4600 2250
	-1   0    0    -1  
$EndComp
Wire Wire Line
	8600 1750 8650 1750
Wire Wire Line
	8600 1950 8650 1950
Text GLabel 8600 1950 0    60   Input ~ 0
STEP_EN
Text GLabel 8600 1750 0    60   Input ~ 0
CLK_STEP
Connection ~ 5650 2750
Wire Wire Line
	5650 2750 6050 2750
Wire Wire Line
	5650 2250 5650 2750
Connection ~ 7100 1600
Wire Wire Line
	7100 1600 7150 1600
Wire Wire Line
	7100 1600 7050 1600
Wire Wire Line
	7100 1150 7100 1600
Wire Wire Line
	6750 1150 7100 1150
Wire Wire Line
	6150 1150 6150 1600
Connection ~ 6150 1150
Wire Wire Line
	6550 1150 6150 1150
$Comp
L Device:C_Small C10
U 1 1 5D785005
P 6650 1150
F 0 "C10" V 6421 1150 50  0000 C CNN
F 1 "100 nF" V 6512 1150 50  0000 C CNN
F 2 "Capacitor_THT:C_Rect_L4.6mm_W3.0mm_P2.50mm_MKS02_FKP02" H 6650 1150 50  0001 C CNN
F 3 "~" H 6650 1150 50  0001 C CNN
	1    6650 1150
	0    1    1    0   
$EndComp
Wire Wire Line
	6650 2250 6650 2750
Text Notes 6000 2950 0    50   ~ 0
Power indicator
Text Notes 5900 800  0    50   ~ 0
Supervisory circuit holds the ~RESET~\nline low for 350ms after powering up.
$Comp
L power:GND #PWR011
U 1 1 5D782444
P 7150 1600
F 0 "#PWR011" H 7150 1350 50  0001 C CNN
F 1 "GND" V 7150 1400 50  0000 C CNN
F 2 "" H 7150 1600 50  0001 C CNN
F 3 "" H 7150 1600 50  0001 C CNN
	1    7150 1600
	0    -1   -1   0   
$EndComp
Wire Wire Line
	6150 1600 6150 1900
Connection ~ 6150 1600
Wire Wire Line
	6250 1600 6150 1600
Wire Wire Line
	6150 1050 6150 1150
Wire Wire Line
	6650 2250 7100 2250
Connection ~ 6650 2250
Wire Wire Line
	6650 2000 6650 2250
Wire Wire Line
	6150 2250 6650 2250
$Comp
L Power_Supervisor:MCP100-300D U5
U 1 1 5D781C37
P 6650 1700
F 0 "U5" V 6283 1700 50  0000 C CNN
F 1 "MCP100-450D" V 6374 1700 50  0000 C CNN
F 2 "Package_TO_SOT_THT:TO-92" H 6250 1850 50  0001 C CNN
F 3 "http://ww1.microchip.com/downloads/en/DeviceDoc/11187f.pdf" H 6350 1950 50  0001 C CNN
	1    6650 1700
	0    -1   1    0   
$EndComp
$Comp
L power:+5V #PWR07
U 1 1 5D7819EB
P 6150 1050
F 0 "#PWR07" H 6150 900 50  0001 C CNN
F 1 "+5V" H 6100 1200 50  0000 L CNN
F 2 "" H 6150 1050 50  0001 C CNN
F 3 "" H 6150 1050 50  0001 C CNN
	1    6150 1050
	1    0    0    -1  
$EndComp
Connection ~ 6150 2250
Wire Wire Line
	6150 2200 6150 2250
Wire Wire Line
	6050 2250 6150 2250
$Comp
L Device:R R8
U 1 1 5D78173D
P 6150 2050
F 0 "R8" H 6000 2100 50  0000 C CNN
F 1 "5K" H 6000 2000 50  0000 C CNN
F 2 "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal" V 6080 2050 50  0001 C CNN
F 3 "~" H 6150 2050 50  0001 C CNN
	1    6150 2050
	-1   0    0    1   
$EndComp
$Comp
L power:GND #PWR06
U 1 1 5D7816DE
P 5650 2750
F 0 "#PWR06" H 5650 2500 50  0001 C CNN
F 1 "GND" V 5650 2550 50  0000 C CNN
F 2 "" H 5650 2750 50  0001 C CNN
F 3 "" H 5650 2750 50  0001 C CNN
	1    5650 2750
	1    0    0    -1  
$EndComp
$Comp
L Device:R R9
U 1 1 5D77F199
P 6200 2750
F 0 "R9" V 6350 2750 50  0000 C CNN
F 1 "330" V 6450 2750 50  0000 C CNN
F 2 "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal" V 6130 2750 50  0001 C CNN
F 3 "~" H 6200 2750 50  0001 C CNN
	1    6200 2750
	0    -1   -1   0   
$EndComp
$Comp
L Device:LED D3
U 1 1 5EAAC90B
P 6500 2750
F 0 "D3" H 6500 2900 50  0000 C CNN
F 1 "POWER" H 6500 3000 50  0000 C CNN
F 2 "LED_THT:LED_D5.0mm_Horizontal_O1.27mm_Z3.0mm" H 6500 2750 50  0001 C CNN
F 3 "~" H 6500 2750 50  0001 C CNN
	1    6500 2750
	1    0    0    -1  
$EndComp
Text GLabel 7100 2250 2    50   Input ~ 0
~RESET
$Comp
L Switch:SW_Push SW5
U 1 1 5D77B0A8
P 5850 2250
F 0 "SW5" H 5850 2535 50  0000 C CNN
F 1 "RESET" H 5850 2444 50  0000 C CNN
F 2 "Button_Switch_THT:SW_Tactile_SKHH_Angled" H 5850 2450 50  0001 C CNN
F 3 "" H 5850 2450 50  0001 C CNN
	1    5850 2250
	1    0    0    -1  
$EndComp
Wire Wire Line
	5700 5050 7900 5050
Wire Wire Line
	7900 5050 7900 3000
Wire Wire Line
	12750 2800 12750 3600
$EndSCHEMATC
