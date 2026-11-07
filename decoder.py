#!/usr/bin/env python3
"""
SENTINELA-RF Syndrome Decoder for RFID Reader
Implements the fault diagnosis decoder using the verified BCH(16,6,4) code.

Based on the verified H_s matrix (10 × 16 over GF(2)):
- Code: [16, 6, 4] binary BCH-derived code
- d_min = 4
- 100% single fault identification (16/16)
- 80% double fault unique identification (96/120)

Syndrome table (10-bit binary) verified:
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
"""

import numpy as np
from itertools import combinations
from typing import Dict, List, Tuple, Optional

print("=" * 60)
print("SENTINELA-RF SYNDROME DECODER")
print("=" * 60)

# ============================================================
# H_s MATRIX (10 × 16) from the verified document
# ============================================================
H_16 = np.array([
    [1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 1, 1, 0, 1],
    [0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1, 1, 0],
    [0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1, 1],
    [0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1],
    [0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1],
    [1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1],
    [0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0],
    [0, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1],
    [0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0],
    [0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1]
], dtype=int)

rank_16 = np.linalg.matrix_rank(H_16)
print(f"\n1. H_matrix properties:")
print(f"   10 × 16 over GF(2)")
print(f"   Rank: {rank_16}")
print(f"   Code dimension: [16, {16 - rank_16}]")
print(f"   Minimum distance d_min: 4")

# ============================================================
# Syndrome Table (verified)
# ============================================================
sensor_names = [
    "Brownout (S1)", "EEPROM (S2)", "RO1 (S3)", "RO2 (S4)", "RO3 (S5)", "RO4 (S6)",
    "Delay1 (S7)", "Delay2 (S8)", "Delay3 (S9)", "Delay4 (S10)",
    "Entropy (S11)", "Thermal (S12)", "RF (S13)", "Current (S14)", 
    "Watchdog (S15)", "Self-Test (S16)"
]

# Verified syndromes (10-bit binary → integer)
syndrome_table: Dict[str, int] = {
    "Brownout (S1)":     int("1000010000", 2),
    "EEPROM (S2)":       int("0100001000", 2),
    "RO1 (S3)":          int("0010000100", 2),
    "RO2 (S4)":          int("0001000010", 2),
    "RO3 (S5)":          int("0000111111", 2),
    "RO4 (S6)":          int("1100001110", 2),
    "Delay1 (S7)":       int("0110010111", 2),
    "Delay2 (S8)":       int("0011011011", 2),
    "Delay3 (S9)":       int("1001101101", 2),
    "Delay4 (S10)":      int("0100110110", 2),
    "Entropy (S11)":     int("1010011011", 2),
    "Thermal (S12)":     int("1101011101", 2),
    "RF (S13)":          int("1110101110", 2),
    "Current (S14)":     int("1111010111", 2),
    "Watchdog (S15)":    int("0111101011", 2),
    "Self-Test (S16)":   int("1011110101", 2),
}

# Reverse lookup: syndrome integer → sensor name
syndrome_to_sensor: Dict[int, str] = {v: k for k, v in syndrome_table.items()}

# Also build syndrome → binary string mapping
syndrome_bin: Dict[str, str] = {}
for sensor, syn_int in syndrome_table.items():
    sbin = format(syn_int, '010b')
    syndrome_bin[sensor] = sbin

print(f"\n2. Syndrome Table (10-bit binary):")
for sensor, s_int in syndrome_table.items():
    sbin = format(s_int, '010b')
    print(f"   {sensor:15s} -> {sbin} (0x{s_int:x})")

# ============================================================
# 3. Decodificador Principal
# ============================================================

def compute_syndrome(sensor_faults: List[int], H: np.ndarray = H_16) -> int:
    """
    Compute the syndrome for given sensor faults.
    
    Args:
        sensor_faults: List of sensor indices (1-16) that are faulty
        H: The 10×16 parity-check matrix
    
    Returns:
        Syndrome as 10-bit integer
    """
    e = np.zeros(16, dtype=int)
    for idx in sensor_faults:
        if 1 <= idx <= 16:
            e[idx - 1] = 1  # Convert to 0-indexed
    
    # Syndrome = H · e over GF(2)
    s = (H @ e) % 2
    # Convert to integer
    s_int = 0
    for bit in s:
        s_int = (s_int << 1) | int(bit)
    
    return int(s_int)

def decode_syndrome(syndrome_int: int, H: np.ndarray = H_16) -> Optional[str]:
    """
    Decode syndrome to identify the faulty sensor(s).
    
    Args:
        syndrome_int: 10-bit syndrome integer
        H: The 10×16 parity-check matrix
    
    Returns:
        Sensor name if identified, None if ambiguous or undetectable
    """
    # Check if syndrome is zero (no fault)
    if syndrome_int == 0:
        return "Nenhum defeito (syndrome zero)"
    
    # Check single fault identification (16/16 guaranteed)
    # Look up in the syndrome table
    if syndrome_int in syndrome_to_sensor:
        return syndrome_to_sensor[syndrome_int]
    
    # Check double faults - find which pairs produce this syndrome
    double_faults = []
    for i, j in combinations(range(1, 17), 2):
        e = np.zeros(16, dtype=int)
        e[i - 1] = 1
        e[j - 1] = 1
        s = compute_syndrome([i, j])
        if s == syndrome_int:
            double_faults.append((i, j))
    
    if len(double_faults) == 0:
        return None  # Undetectable syndrome (shouldn't happen for d_min=4)
    elif len(double_faults) == 1:
        # Unique double fault identification
        i, j = double_faults[0]
        return f"Falha dupla: {sensor_names[i-1]} + {sensor_names[j-1]}"
    elif len(double_faults) > 1:
        # Ambiguous - multiple pairs produce same syndrome
        pairs_str = "; ".join([f"S{i}+S{j}" for i, j in double_faults])
        return f"Falha ambígua: {len(double_faults)} pares possíveis ({pairs_str})"
    else:
        return None

def diagnose_faults(syndrome_int: int) -> str:
    """
    Main diagnosis function - returns human-readable fault description.
    
    Args:
        syndrome_int: 10-bit syndrome from RFID reader
    
    Returns:
        Description of the diagnosed fault(s)
    """
    # Try single fault identification first
    result = decode_syndrome(syndrome_int)
    if result is not None:
        return result
    
    # If not unique single or double, try to determine what we can
    # Check weight 1 (single faults)
    for i in range(1, 17):
        s = compute_syndrome([i])
        if s == syndrome_int:
            return f"Falha simples: {sensor_names[i-1]}"
    
    # Check weight 2 (double faults)
    double_faults = []
    for i, j in combinations(range(1, 17), 2):
        s = compute_syndrome([i, j])
        if s == syndrome_int:
            double_faults.append((i, j))
    
    if len(double_faults) == 1:
        i, j = double_faults[0]
        return f"Falha dupla identificada: {sensor_names[i-1]} + {sensor_names[j-1]}"
    elif len(double_faults) > 1:
        pairs_str = "; ".join([f"S{i}+S{j}" for i, j in double_faults[:3]])
        return f"Falha dupla detectada, mas ambígua ({len(double_faults)} possibilidades): {pairs_str}..."
    else:
        # Check weight 3
        triple_faults = []
        for combo in combinations(range(1, 17), 3):
            s = compute_syndrome(list(combo))
            if s == syndrome_int:
                triple_faults.append(list(combo))
        
        if len(triple_faults) == 1:
            combo = triple_faults[0]
            return f"Falha tripla detectada: {', '.join([sensor_names[c-1] for c in combo])}"
        else:
            return f"Falha detectada (peso desconhecido), {syndrome_int} em binário: {format(syndrome_int, '010b')}"