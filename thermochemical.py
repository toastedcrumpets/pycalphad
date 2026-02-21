import matplotlib.pyplot as plt
from pycalphad import Database, variables as v
dbf = Database('C_A_S_Fe_O_M.tdb')
O2_partial_pressure = 101325*0.02  # 2% of atmospheric pressure in Pascals
# Phases from C_A_S_Fe_O_M.tdb to include
casf_phases = [
    'AC2S',
    'ACRIS',
    'APC2S',
    'AQUARTZ',
    'BC2S',
    'BCRIS',
    'BQUARTZ',
    'C12A7',
    'C2AS',
    'C2F',
    'C3A',
    'CA',
    'CA2',
    'CA6',
    'CAO',
    'CAS2',
    'GC2S',
    'MC3S',
    'MULLITE',
    'PCS',
    'RC3S',
    'RC3S2',
    'TC3S',
    'WCS',
    'FERRITE',
    'C2F', 'CF', 'CF2',
    'BCC_A2','FCC_A1','HALITE',
    'CORUNDUM',
    'SPINEL',
    'LIQUID',
    'GAS'
]
# Base composition from OPC example
solids_base = {
    "CaO": 68.2,
    "Al2O3": 5.5,
    "SiO2": 22.3,
    "Fe2O3": 3.9,
    "MgO": 0.0,
    'SO3': 0.0,
}

# Create variations: ±10% for CaO, SiO2, Al2O3 and ±5% for Fe2O3
import itertools
variations = [-0.10, 0.0, 0.10]  # -10%, 0%, +10%
fe_variations = [-0.05, 0.0, 0.05]  # -5%, 0%, +5%

# Store all composition variations
composition_set = []

for cao_var, sio2_var, al2o3_var, fe_var in itertools.product(variations, variations, variations, fe_variations):
    solids = solids_base.copy()
    solids["CaO"] = solids_base["CaO"] * (1 + cao_var)
    solids["SiO2"] = solids_base["SiO2"] * (1 + sio2_var)
    solids["Al2O3"] = solids_base["Al2O3"] * (1 + al2o3_var)
    solids["Fe2O3"] = solids_base["Fe2O3"] * (1 + fe_var)

    L = solids["CaO"] / 56.077
    A = solids["Al2O3"] / 101.96
    Q = solids["SiO2"] / 60.08
    F = solids["Fe2O3"] / 159.69
    M = solids["MgO"] / 40.3044
    S = solids['SO3'] / 80.06
    FE = 2*F
    N = 0.01  # Small amount of nitrogen (trace)
    O = 3*F + 3*S + 0.01

    total_moles = L + A + Q + FE + M + O + S + N

    X_L = L / total_moles
    X_FE = FE / total_moles
    X_A = A / total_moles
    X_Q = Q / total_moles
    X_O = O / total_moles
    X_M = M / total_moles
    X_N = N / total_moles

    composition_set.append({
        'CaO': solids["CaO"],
        'SiO2': solids["SiO2"],
        'Al2O3': solids["Al2O3"],
        'Fe2O3': solids["Fe2O3"],
        'X_L': X_L,
        'X_Q': X_Q,
        'X_A': X_A,
        'X_FE': X_FE,
        'X_O': X_O,
        'X_N': X_N,
        'cao_var': cao_var,
        'sio2_var': sio2_var,
        'al2o3_var': al2o3_var,
        'fe_var': fe_var
    })     

comps = ['L','Q','A','FE','O','N','VA']

from pycalphad import equilibrium
import numpy as np
import sys
from datetime import datetime

# Open output file for writing
output_filename = f"equilibrium_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
output_file = open(output_filename, 'w')

# Function to print to both console and file
def tee_print(*args, **kwargs):
    # Print to console
    print(*args, **kwargs)
    # Print to file
    print(*args, **kwargs, file=output_file)
    output_file.flush()  # Ensure it's written immediately

# Equilibrium calculations across temperature range and composition variations
tee_print("=" * 80)
tee_print("EQUILIBRIUM CALCULATIONS - OPC Composition Variations")
tee_print(f"Testing {len(composition_set)} compositions (±10% CaO, SiO2, Al2O3; ±5% Fe2O3)")
tee_print("Temperature range: 800K to 1800K (100K steps)")
tee_print(f"Output file: {output_filename}")
tee_print("=" * 80)

convergence_failures = 0
errors = 0
successful = 0
total_calcs = 0

for comp_idx, comp in enumerate(composition_set, 1):
    tee_print(f"\n{'='*80}")
    tee_print(f"COMPOSITION {comp_idx}/{len(composition_set)}")
    tee_print(f"  CaO:   {comp['CaO']:6.2f} ({comp['cao_var']*100:+.0f}%)")
    tee_print(f"  SiO2:  {comp['SiO2']:6.2f} ({comp['sio2_var']*100:+.0f}%)")
    tee_print(f"  Al2O3: {comp['Al2O3']:6.2f} ({comp['al2o3_var']*100:+.0f}%)")
    tee_print(f"  Fe2O3: {comp['Fe2O3']:6.2f} ({comp['fe_var']*100:+.0f}%)")
    tee_print(f"  Mole fractions: X_L={comp['X_L']:.4f}, X_Q={comp['X_Q']:.4f}, X_A={comp['X_A']:.4f}, X_FE={comp['X_FE']:.4f}, X_O={comp['X_O']:.4f}, X_N={comp['X_N']:.6f}")
    tee_print("=" * 80)

    for T in np.arange(1700.0, 2201.0, 100):
        total_calcs += 1
        tee_print(f"\nT: {T:.0f}K ({T-273.15:.0f}°C) ", end="")

        try:
            eq = equilibrium(dbf, comps, casf_phases,
                            conditions={v.X('L'): comp['X_L'], v.X('Q'): comp['X_Q'],
                                      v.X('A'): comp['X_A'], v.X('FE'): comp['X_FE'],
                                      v.X('N'): comp['X_N'],
                                      v.T: T, v.P: 101325, v.N: 1},
                            calc_opts={"pdens": 10000},
                            #_diagnostic=True, 
                            #verbose=True,
                            )

            # Filter out empty phase entries
            phase_names_unfiltered = eq['Phase'].squeeze()
            row_selector = (phase_names_unfiltered != '')
            phase_names = phase_names_unfiltered[row_selector]
            fractions = eq["NP"].squeeze()[row_selector]

            if len(phase_names) == 0:
                tee_print(f"⚠️  CONVERGENCE FAILURE", end="")
                convergence_failures += 1
            else:
                tee_print(f"✓ {len(phase_names)} phases: ", end="")
                phase_strs = [f"{p}({f*100:.1f}%)" for p, f in zip(phase_names.values, fractions.values)]
                tee_print(", ".join(phase_strs), end="")
                successful += 1
        except Exception as e:
            tee_print(f"❌ ERROR: {str(e)[:50]}")
            errors += 1

tee_print("\n" + "=" * 80)
tee_print("EQUILIBRIUM CALCULATIONS COMPLETE")
tee_print("=" * 80)
tee_print(f"Total calculations:      {total_calcs}")
tee_print(f"Successful:              {successful} ({successful/total_calcs*100:.1f}%)")
tee_print(f"Convergence failures:    {convergence_failures} ({convergence_failures/total_calcs*100:.1f}%)")
tee_print(f"Errors:                  {errors} ({errors/total_calcs*100:.1f}%)")
tee_print("=" * 80)

# Close the output file
output_file.close()
tee_print(f"\nResults saved to: {output_filename}")
