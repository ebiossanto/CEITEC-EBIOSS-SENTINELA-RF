SENTINELA-RF DEVELOPMENT ENVIRONMENT SETUP
============================================

This document lists all tools and packages needed to develop the SENTINELA-RF project,
which involves RFID chip health monitoring using BCH error-correcting codes and PUF techniques.

INSTALLED TOOLS
---------------

1. Python 3.15.2
   - Location: C:\Python315\
   - Status: ✅ Installed and working

2. Git 2.56.0 (Windows)
   - Status: ✅ Installed and working
   - Used for version control and repository management

3. Lean 4.15.0 (Lean Prover)
   - Location: D:\Redes adaptativas\repositorio-github\redes-adaptativas-fluxo-energetico\lean_project\
   - With Mathlib4 at C:\Users\Euzebio\.lean\mathlib4\
   - Status: ✅ Installed and verifiable
   - Version: leanprover/lean4:4.15.0

4. galois Python library (version 0.4.11)
   - Used for GF(32) arithmetic and BCD code construction
   - Status: ✅ Installed and verified
   - Verification: GF(32) = GF(2^5, primitive_element='x', irreducible_poly='x^5 + x^2 + 1')

5. sympy Python library (version 1.14.0)
   - Used for symbolic mathematics
   - Status: ✅ Installed

ESSENTIAL PYTHON PACKAGES
-------------------------
- numpy: 2.5.4 (matrix operations)
- galois: 0.4.11 (GF(32) field operations)
- sympy: 1.14.0 (symbolic math)
- matplotlib: 3.11.2 (data visualization)
- networkx: 3.7 (graph theory algorithms)
- tqdm: 4.70.1 (progress bars)
- scipy: 1.18.1 (scientific computing)

PROJECT STRUCTURE
-----------------
D:\CEITEC\SENTINELA-RF\           <- Main project directory
├── lean-project.toml              Lean project configuration
├── lean-toolchain                 Lean version specification
├── SENTINELA-RF.lean              Core Lean mathematical framework
├── verify_bch.py                  BCH code verification script
├── bch_generator.py               BCH code generation script
└── setup_sentinela.bat            Environment setup batch script

LEAN MATHEMATICAL FRAMEWORK
---------------------------
The SENTINELA-RF.lean file contains:

• GF(32) field construction over GF(2^5) with polynomial x^5 + x^2 + 1
• BCH(31,21,5) code parameters: n=31, k=21, r=10, d_min≥5
• Parity-check matrix H (10 × 31 binary matrix from GF(32) expansion)
• Shortened matrix H_s (10 × 16 for 16 health sensors)
• Syndrome computation: s = H·x over GF(2)
• Fundamental lemmas:
  - syndrome_unitError: syndrome of single fault = column of H
  - uniqueSyndrome: distinct columns → distinct syndromes
  - detectable: non-zero columns → detectable faults
  - sentinelaCoverage: combined detection and identification
• Fault classification properties:
  - 100% of single faults identifiable (16/16)
  - 80% of double faults uniquely identifiable (96/120)
  - Up to 3 faults guaranteed detectable
  - Code: (16, 6, 4) BCH-derived code

BCH CODE PROPERTIES (VERIFIED)
-------------------------------
Using the explicit H_s matrix from the document:

Code parameters: [16, 6, 4] binary code
- 10 redundancy bits (rows of H)
- 6 message bits (dimension)
- 4 minimum distance (d_min = 4)

Fault detection capabilities:
- Detects: up to 3 simultaneous faults (d_min - 1 = 3)
- Corrects: up to 1 simultaneous fault (⌊(d_min-1)/2⌋ = 1)
- Single faults: 16/16 identifiable (100%)
- Double faults: 96/120 uniquely identifiable (80%)
- Ambiguous double-fault pairs: 24/120 (20%)
  - Example collisions: {S1,S4} ≡ {S5,S9}, {S1,S5} ≡ {S4,S9}

SENSOR SYNDROME MAP (10-bit binary)
-------------------------------------
S1 Brownout:     1000010000 (0x210)
S2 EEPROM:       0100001000 (0x108)
S3 RO1:          0010000100 (0x84)
S4 RO2:          0001000010 (0x42)
S5 RO3:          0000111111 (0x3F)
S6 RO4:          1100001110 (0x30E)
S7 Delay1:       0110010111 (0x197)
S8 Delay2:       0011011011 (0xDB)
S9 Delay3:       1001101101 (0x26D)
S10 Delay4:      0100110110 (0x136)
S11 Entropy:     1010011011 (0x29B)
S12 Thermal:     1101011101 (0x35D)
S13 RF:          1110101110 (0x3AE)
S14 Current:     1111010111 (0x3D7)
S15 Watchdog:    0111101011 (0x1EB)
S16 Self-Test:   1011110101 (0x2F5)

Each sensor produces a unique 10-bit syndrome.

NEXT STEPS FOR DEVELOPMENT
---------------------------

1. Lean formalization:
   • Complete the Lean proofs for BCH code properties
   • Integrate with Mathlib properly
   • Generate Lean code for syndrome computation
   • Formalize the sentinelaCoverage theorem

2. Python-BC integration:
   • Use verify_bch.py for code generation and verification
   • Generate the complete 10×31 BCH(31,21,5) matrix
   • Implement encoding/decoding algorithms
   • Create API for RFID reader backend

3. Patented technology preparation:
   • Document the BCH-Sentinela code construction
   • Prepare formal proofs for patent submission
   • Create the "Sistema de Monitoramento de Degradação" patent application
   • Reference: BCH(31,21,5) shortened to (16,6,4) with d_min=4

4. Hardware/software integration:
   • Interface with CEITEC XC06 chip prototype
   • Implement RFID reader syndrome decoding
   • Integrate PUF (Physical Unclonable Function) generation
   • Test passive RFID tag operation

DEPENDENCIES FOR FULL FUNCTIONALITY
------------------------------------
• Lean 4.15.0 with Mathlib4 properly configured
• Python 3.15.2 with: galois, numpy, sympy, matplotlib, networkx, tqdm
• Access to CEITEC XC06 development platform
• RFID reader/writer hardware
• GF(32) arithmetic primitives (available via galois library)

REFERENCES
----------
• SENTINELA-RF.md - Main project document with mathematical framework
• BCH(31,21,5) code over GF(32) - Classical narrow-sense BCH code
• Lean 4 + Mathlib - Formal verification framework
• Physical Unclonable Function (PUF) concepts for RFID identification