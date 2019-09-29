# ALU ROM data generator

This script generate ALU ROM data for the M27C322 ROM chip and for the Logisim ALU component.

## Credits

This code was 99.9% copied from Warren Toomey (@DoctorWkt) his CSCvon8 project: https://github.com/DoctorWkt/CSCvon8
**All credit goes to him!** I took his ROM-based ALU idea/implementation and used it in my project.
Only thing I changed in the code is that it generates a ROM image for Logisim, instead of one for the Verilog implementation.

## Usage (on Linux or Mac OS)

- Make sure the script is executable: `chmod +x generate_alu.pl`
- Run the script: `./generate_alu.pl`
- The script will generate 8 ALU ROMS (more documentation on this later) and one image that is used for Logisim
