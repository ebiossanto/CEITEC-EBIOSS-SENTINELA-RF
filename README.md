# CEITEC EBIOSS - SENTINELA-RF Project

## Overview
SENTINELA-RF is a national RFID chip health monitoring project developed by CEITEC researchers. This project implements a BCH error-correcting code based fault diagnosis system for passive RFID tags.

## Project Description
The SENTINELA-RF project addresses the need for national RFID technology with built-in health monitoring capabilities, avoiding dependency on foreign semiconductor technologies (TSMC 3nm, Intel 18A, Samsung GAA).

## Core Technology
- **BCH Error-Correcting Codes**: Shortened BCH(31,21,5) code over GF(32), reduced to (16,6,4) code for 16 health sensors
- **Fault Detection**: Can detect up to 3 simultaneous faults
- **Fault Identification**: 100% of single faults identifiable, 80% of double faults uniquely identifiable
- **Physical Unclonable Function (PUF)**: Sovereign chip identity through silicon imperfections

## Mathematical Foundation
The code uses BCH codes over Galois Field GF(32) with primitive polynomial x^5 + x^2 + 1 and primitive element α. The parity-check matrix H_s (10×16) enables syndrome-based fault diagnosis.

### Code Parameters
- Code: [16, 6, 4] binary BCH-derived code
- Minimum distance d_min = 4
- 10 redundancy bits, 6 message bits

### Fault Detection Capabilities
- Detects: up to 3 simultaneous sensor failures
- Identifies uniquely: up to 2 simultaneous failures
- Single faults: 16/16 identifiable (100%)
- Double faults: 96/120 uniquely identifiable (80%)
- Ambiguous pairs: 24/120 (20%)

## Sensor Syndromes (10-bit binary)

| Sensor | Function | Syndrome (binary) | Hex |
|--------|----------|-------------------|-----|
| S1 | Brownout | 1000010000 | 0x210 |
| S2 | EEPROM | 0100001000 | 0x108 |
| S3 | RO1 | 0010000100 | 0x84 |
| S4 | RO2 | 0001000010 | 0x42 |
| S5 | RO3 | 0000111111 | 0x3F |
| S6 | RO4 | 1100001110 | 0x30E |
| S7 | Delay1 | 0110010111 | 0x197 |
| S8 | Delay2 | 0011011011 | 0xDB |
| S9 | Delay3 | 1001101101 | 0x26D |
| S10 | Delay4 | 0100110110 | 0x136 |
| S11 | Entropy | 1010011011 | 0x29B |
| S12 | Thermal | 1101011101 | 0x35D |
| S13 | RF | 1110101110 | 0x3AE |
| S14 | Current | 1111010111 | 0x3D7 |
| S15 | Watchdog | 0111101011 | 0x1EB |
| S16 | Self-Test | 1011110101 | 0x2F5 |

## Documentation

### Key Files
1. **ENVIRONMENT_SETUP.md** - Development environment configuration
2. **SENTINELA-RF.lean** - Lean 4 mathematical framework  
3. **verify_bch.py** - BCH code verification script
4. **decoder.py** - Syndrome decoder for RFID reader
5. **REQUISITOS_PARA_DESENVOLVIMENTO.txt** - Development requirements

### Lean 4 Formalization
The project includes formal mathematical proofs in Lean 4, integrated with Mathlib4. The core theorems include:
- syndrome_unitError: Syndrome of unit error = column of H
- uniqueSyndrome: Distinct columns → distinct syndromes
- detectable: Non-zero columns → detectable faults
- sentinelaCoverage: Combined detection and identification

### Python Verification
The verify_bch.py and decoder.py scripts provide computational verification of all BCH code properties, confirming the mathematical analysis presented in the SENTINELA-RF.md document.

## Citation

If you use this work, please cite:

```
@misc{ebiossanto2026sentinela,
  author = {Eubio Soares},
  title = {SENTINELA-RF: Sistema de Monitoramento de Degradação de Circuitos Integrados Baseado em Síndromes BCH para RFID Nacional},
  year = {2026},
  institution = {CEITEC},
  note = {Available at: https://seducsp-my.sharepoint.com/personal/euzebiosoares_professor_educacao_sp_gov_br/Documents/Arquivos%20de%20Microsoft%20Copilot%20Chat/SENTINELA-RF.md}
}
```

## Contact
CEITEC - Centro de Excelência em Tecnologia Eletrônica e Microeletrônica
Para mais informações, consulte o documento SENTINELA-RF.md completo.