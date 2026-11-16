"""RR1 executable qualification specification; produces no measurement claims."""
import json
from .common import VROOT


def plan(audit):
    contract=json.loads((VROOT/'operating-contract.json').read_text())
    rows=[]
    for bus in audit['buses']:
        for scenario in bus['scenarios']:
            driver=scenario['driver'];kind=bus['bus']
            if kind=='DATA':
                controls=['U10105.19','U10105.1'];issue='dm02-57n.3.3'
                tests=['OE release from both output polarities; reset during drive; idle/HALT dwell',
                       'Re-enable and data transitions with all fitted receivers; capture at each receiving leaf',
                       'Earliest invalid DATA after each capture; input voltage and supply-current behaviour while DATA is undriven']
                acceptance=['No competing DATA driver exists in this revision.',
                    'Capture setup residual >= 10 ns; hold residual > 0 ns after device requirement and uncertainty.',
                    'Idle voltages, receiver current, re-enable settling and reset inhibition meet the eventual physical interface contract; no floating-bus value is used as valid data.']
            elif kind=='RAM':
                controls=['U9002.24','U9002.29','U9004.1','U9004.19'];issue='dm02-57n.3.4'
                tests=['Read/idle/write/idle/read with opposing and identical data, all eight DQ pins and switching patterns',
                       'Sweep old-disable to new-enable gap and command skew in both directions; include simultaneous requests as a negative control',
                       'Sweep OE/WE/address edges and reset across read and write phases; test ROM/RAM/IO boundaries 3fff/4000/feff/ff00/ffff',
                       'Halt/resume/step at the shortest legal intervals; reset abort with no retained-write assumption']
                acceptance=['R_RW = earliest writer low-Z - latest SRAM high-Z - total timing uncertainty > 0 ns.',
                    'R_WR = earliest SRAM low-Z - latest writer high-Z - total timing uncertainty > 0 ns.',
                    'WE pulse >= 9 ns, address-to-write-end >= 12 ns, write cycle >= 15 ns, data-to-write-end >= 7 ns and data hold >= 0 ns, each with positive residual margin; read captures retain >=10 ns setup reserve.',
                    'No unintended WE pulse or invalid capture; reset abort inhibits both drivers and WE before supply becomes invalid. Interrupted writes remain unspecified.']
            else:
                ref=driver.split('.')[0];controls=[ref+'.19',ref+'.1'];issue='dm02-57n.3.3'
                tests=['U9009/U8020/U8021 handovers on SOURCE3 with opposite and same data',
                       'Observe U9009 OE together with SRAM OE, source bus and BF1 U104/trunk; reset at each phase']
                acceptance=['Earliest new source drive - latest old source high-Z - uncertainty > 0 ns.',
                    'Disabling SRAM and U9009 together may propagate invalid data before U9009 releases; downstream captures must already have satisfied hold, with positive residual margin.']
            rows.append(dict(bus=kind,bit=bus['bit'],driver=driver,control_pins=controls,
                receiver_pins=scenario['receiver_pins'],other_driver_pins=scenario['other_output_pins'],
                ic_only_allocation_pf=scenario['ic_only_pf'],unknown_pin_maxima=scenario['unknown_pin_maxima'],
                actual_total_load_pf=None,actual_min_release_ns=None,actual_max_release_ns=None,
                datasheet_fixtures=scenario['screens'],unknown_parasitics=bus['unknown_parasitics'],
                tests=tests,acceptance=acceptance,issue=issue))
    return dict(revision='CP1-RR1',contract_revision=contract['revision'],candidate='CP1-MD1',
        status='measurement specification; no physical results',physical_qualification=False,
        clock=contract['clock'],supply_points_v=contract['qualification_matrix']['supply_points_v'],
        ambient_points_c=contract['qualification_matrix']['ambient_points_c'],
        qualification_points=9,driver_cases=rows,
        method=[
            'Record exact markings, lots and DIP suffixes, actual pin supply/temperature, socket/connector configuration and measured or bounded complete loads. Use assembled representative links, including inactive outputs and probe capacitance; nominal IC subtotals are not fixture totals.',
            'First reproduce the manufacturer load network and thresholds. For UM61512A use the 480-ohm/255-ohm network and 5 pF including scope/jig for low/high-Z timing, 30 pF for access; 5 ns input edges. For HCT245 follow SCLS020H Figure 7-1, 50 pF disable and 150 pF data/enable, 6 ns input edges. Record actual edges at IC pins.',
            'Then measure the actual representative loaded link independently. Sweep load around its bounded minimum/maximum, both data polarities, opposing/same-byte patterns and simultaneous switching. Do not rescale 5 pF or 50 pF table delays to the assembled load.',
            'High-Z release is cessation of drive, not a logic-threshold crossing. Use a calibrated manufacturer-style switched resistive bias, account for its DC and capacitive loading, and cross-check residual drive current with a characterized sensing fixture. De-embed probe/fixture response and report the threshold/current criterion. The SRAM 500 mV departure is a characterization method, not a receiver-valid voltage.',
            'Determine both latest release and earliest activation separately at every qualification point. Use zero earliest activation in design arithmetic until a loaded minimum is established. A same-data contention test must observe drive/current; logic voltage alone cannot detect it.',
            'At 4.75, 5.0 and 5.25 V at the pins and 0, 25 and 50 C, capture control/data/clock on a common calibrated timebase. State bandwidth, probe loading, trigger/inter-channel skew, threshold error and timing uncertainty; retain raw waveforms. Record both measured extrema and the extra engineering guard before selecting a sample-qualified design bound.',
            'The nine grid points are a test specification, not continuous-envelope or population coverage. Exact sample/lot coverage, repetition counts and acceptance of sample-qualified bounds require the work-reviewer gate; interpolate neither temperature nor lot guarantees.',
            'For command-blank budgeting use old control path maximum + qualified old-device release maximum + route/skew/measurement uncertainty + positive reserve. Confirm actual earliest new-control arrival in every mode. A slower clock alone does not supply this proof.'
        ],
        records=contract['qualification_matrix']['measurement_record']+['output_polarity','switching_pattern',
            'disable_definition','earliest_activation_ns','latest_release_ns','control_pin_gap_ns',
            'deembedded_fixture_response','sample_coverage','engineering_guard_ns','reviewed_bound_ns'],
        owners=['dm02-57n.3.3','dm02-57n.3.4'],review_required=True)
