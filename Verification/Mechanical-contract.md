# CP1-MC1 selected mechanical target

On 16 November 2026 the owner approved the four-card proposal with “Agreed, continue”. [mechanical-contract.json](mechanical-contract.json) records that decision under `dm02-57n.1.2`.

| Physical board | R2 sheets | Baseline DIP count |
| --- | --- | ---: |
| Control, 250 × 200 mm | CW1 + SQ1 | 35 |
| Compute, 250 × 200 mm | AL1 + RG1 | 38 |
| Counters, 250 × 200 mm | PC1 + SP1 | 35 |
| Memory, 250 × 200 mm | MA1 + ME1 | 58 |
| Active backplane, 270 × 270 mm | C1 + DT1 + BF1 + BP1 | 26 |

Eight vertical card positions at 30 mm pitch provide four CPU positions, one text peripheral and three spare peripheral positions. The electronics envelope is approximately 270 × 270 × 230 mm, excluding enclosure, cables and extraction space. Boards use four layers; 1.6 mm thickness is the planning target pending stackup and connector fit.

Provide 5 mm side-rail bands, 10 mm top access and a 25 mm connector strip on each CPU card. Remove cards with power off to access sockets. Guides and role-specific keys must prevent wrong-slot insertion and reversed mating. Put regulated 5 V entry and service controls on accessible backplane edges. Power connector rating, protection, supply capacity and cable gauge follow the electrical budget. No fabrication price ceiling was supplied; obtain quotes before ordering.

The [historical area screen](build/cp1-partition/screen.json) retains its original `owner_approved: false`: it records the proposal before approval. Its SHA-256 is pinned in MC1. It accounts for all 192 R2 DIP packages and estimates 45.18% memory-card planning-zone occupancy. New IO, power/reset and peripheral parts are additional. Actual sockets, mounting holes, connector bodies, insertion loads, routing and extraction clearances still require qualification. Legacy boards require explicit equivalence checks before reuse.

CP1-R2 remains the accepted digital circuit. MC1 selects the physical target; the [connector study](Connector-plan.md) develops its electrical boundaries.
