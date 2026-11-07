#!/usr/bin/env python3
"""
SENTINELA-RF - decodificador de sindrome (lado do leitor / backend).

Usa a matriz H_s construida em verify_bch.py (BCH(31,21,5) encurtado para 16 sensores,
codigo [16, 6, 5]). Apenas biblioteca padrao.

Garantias (provadas por enumeracao em verify_bch.py):
  - sindrome 0            -> nenhuma falha OU >= 5 falhas formando palavra-codigo
  - 1 ou 2 falhas         -> identificadas de forma UNICA
  - 3 ou 4 falhas         -> SEMPRE detectadas (sindrome != 0), mas NAO identificaveis com
                             certeza: em ~7% (3 falhas) e ~6% (4 falhas) dos casos a sindrome
                             coincide com a de 1-2 falhas e o decodificador diagnosticaria errado.

Uso:
    python decoder.py 0x210          # decodifica uma sindrome (hex ou decimal)
    python decoder.py --selftest     # testa todos os padroes de 0 a 4 falhas
"""
import itertools
import sys

from verify_bch import SENSORS, build_Hs_columns, syndrome_of

COLS = build_Hs_columns()
N = len(COLS)

# Tabelas de busca: sindrome -> tupla de sensores (1..16). Para peso <= 2 elas sao injetivas.
_TABLE = {}
for _w in (1, 2):
    for _p in itertools.combinations(range(N), _w):
        _s = syndrome_of(COLS, _p)
        assert _s not in _TABLE, "colisao: o codigo nao teria d_min >= 5"
        _TABLE[_s] = tuple(i + 1 for i in _p)


def compute_syndrome(faulty_sensors):
    """Sindrome (inteiro de 10 bits) para uma lista de sensores defeituosos (1..16)."""
    for k in faulty_sensors:
        if not 1 <= k <= N:
            raise ValueError(f"sensor invalido: {k}")
    return syndrome_of(COLS, [k - 1 for k in faulty_sensors])


def diagnose(syndrome):
    """
    Retorna um dicionario:
      status  : 'ok' | 'single' | 'double' | 'multiple_detected'
      sensors : tupla de sensores (1..16) quando identificados
      names   : nomes correspondentes
      note    : aviso quando o diagnostico nao e garantido
    """
    if not 0 <= syndrome < (1 << 10):
        raise ValueError("a sindrome deve ter 10 bits (0..1023)")
    if syndrome == 0:
        return {"status": "ok", "sensors": (), "names": (),
                "note": "Sindrome zero: nenhuma falha detectada."}
    hit = _TABLE.get(syndrome)
    if hit is None:
        return {"status": "multiple_detected", "sensors": (), "names": (),
                "note": "Falha detectada, mas e compativel com 3 ou mais sensores: nao identificavel."}
    status = "single" if len(hit) == 1 else "double"
    return {
        "status": status,
        "sensors": hit,
        "names": tuple(SENSORS[k - 1] for k in hit),
        "note": "Identificacao unica SE houver no maximo 2 falhas; "
                "3-4 falhas podem coincidir com esta sindrome (ver README, secao Limites).",
    }


def selftest():
    ok = True
    # Pesos 0..2: decodificacao exata
    for w in (0, 1, 2):
        for p in itertools.combinations(range(1, N + 1), w):
            d = diagnose(compute_syndrome(p))
            expected = {0: "ok", 1: "single", 2: "double"}[w]
            if d["status"] != expected or tuple(d["sensors"]) != tuple(p):
                ok = False
                print("ERRO de decodificacao:", p, d)
    print(f"pesos 0-2: {'todos os padroes decodificados corretamente' if ok else 'FALHAS acima'}")
    # Pesos 3..4: sempre detectado; contar diagnosticos errados
    for w in (3, 4):
        total = detected = misdiag = 0
        for p in itertools.combinations(range(1, N + 1), w):
            total += 1
            d = diagnose(compute_syndrome(p))
            if d["status"] != "ok":
                detected += 1
            if d["status"] in ("single", "double"):
                misdiag += 1
        print(f"peso {w}: detectadas {detected}/{total}; diagnostico errado como 1-2 falhas: {misdiag} ({100.0 * misdiag / total:.1f}%)")
        ok = ok and detected == total
    return ok


def _parse(arg):
    return int(arg, 0)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "--selftest":
        sys.exit(0 if selftest() else 1)
    s = _parse(sys.argv[1])
    r = diagnose(s)
    print(f"sindrome 0x{s:03X} ({s:010b}) -> {r['status']}")
    if r["sensors"]:
        print("  sensores:", ", ".join(f"S{k} {SENSORS[k - 1]}" for k in r["sensors"]))
    print("  ", r["note"])
