"""BL1 complete ROM boot through the normal FD1 simulation assembly."""
from designs.distribution_candidate import SOURCE
from .common import BUILD,evidence,write_json
from .bootloader import fixtures
from .distribution_run import profile
from .hardware_programs import render


def run():
    folder=BUILD/'boot';fixture=folder/'fixtures';coverage=fixtures(fixture,full_demo=True)
    simulation=profile(SOURCE,folder/'graphics',fixture,demo=True,boot=True)
    output=render(folder/'graphics','emulator_demo') if simulation['passed'] else dict(passed=False)
    passed=(simulation['passed'] and output['passed'] and output.get('io_events')==coverage['io_events'] and
            output.get('pixel_sha256')==coverage['output']['pixel_sha256'] and not coverage['boot_injected'])
    write_json(folder/'summary.json',dict(passed=passed,simulation=simulation,coverage=coverage,output=output))
    return evidence('boot','BL1 ROM boot on the FD1 flash machine','limited' if passed else 'fail',
        f'{coverage["microcycles"]:,} cycles; {coverage["io_events"]:,} IO events; '
        f'{coverage["image"]["payload_bytes"]:,} payload bytes reconstructed from ROM into poisoned SRAM; '
        f'{output.get("pixels_checked",0):,} pixels checked.',
        limitation='Separate boot ROM and SRAM power-on files; CPU initializes loader workspace and enters at 4000. '
                   'Maximum modeled delays at the conditional 4 MHz target; all seven receiver guards are required. '
                   'Reset/oscillator remain qualified fixture inputs. Physical programming/readback, SRAM turnaround '
                   'and display electronics remain open.',
        artifacts=['boot/summary.json','boot/fixtures/image.json','boot/fixtures/coverage.json','boot/fixtures/boot-rom.bin',
                   'boot/fixtures/loader.lst','boot/graphics/profile.json','boot/graphics/alu.log',
                   'boot/graphics/io-observed.txt','boot/graphics/display.pgm','boot/graphics/images.json']+
                  [f'boot/graphics/bank{bank}-{lane}.bin' for bank in range(4) for lane in ('low','high')])
