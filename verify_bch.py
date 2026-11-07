#!/usr/bin/env python3
"""
SENTINELA-RF - construcao e verificacao do codigo BCH encurtado.

Apenas biblioteca padrao do Python (>= 3.8). Nada e assumido: o corpo GF(32),
os polinomios minimos, o polinomio gerador, a matriz H do BCH(31,21,5) e a
matriz encurtada H_s (10 x 16) sao CONSTRUIDOS aqui e depois VERIFICADOS por
enumeracao exaustiva (no maximo 2^16 vetores).

Uso:
    python verify_bch.py            # constroi, verifica, imprime relatorio
    python verify_bch.py --table    # imprime a tabela de sindromes em Markdown
    python verify_bch.py --legacy   # compara com a matriz antiga do repositorio

Codigo de saida: 0 se todas as verificacoes passam, 1 caso contrario.

Convencao de bits: a sindrome de 10 bits e (alpha^i | alpha^(3i)), com os 5 bits
de alpha^i nos bits altos (MSB = linha 0 de H). O sensor S(k) usa a coluna i = k-1.
"""
import itertools
import sys
from collections import Counter

# ----------------------------------------------------------------------------
# 1. Corpo GF(32) = GF(2)[x] / (x^5 + x^2 + 1)
# ----------------------------------------------------------------------------
PRIM_POLY = 0b100101  # x^5 + x^2 + 1
N = 31                # comprimento do BCH
R = 10                # redundancia (bits de sindrome)
N_SENSORS = 16

SENSORS = [
    "Brownout", "EEPROM", "RO1", "RO2", "RO3", "RO4",
    "Delay1", "Delay2", "Delay3", "Delay4",
    "Entropy", "Thermal", "RF", "Current", "Watchdog", "Self-Test",
]


def _build_field():
    exp = [0] * 62
    log = [None] * 32
    x = 1
    for i in range(31):
        exp[i] = x
        log[x] = i
        x <<= 1
        if x & 0b100000:
            x ^= PRIM_POLY
    assert x == 1, "x^5+x^2+1 nao e primitivo"
    for i in range(31, 62):
        exp[i] = exp[i - 31]
    return exp, log


EXP, LOG = _build_field()


def gmul(a, b):
    return 0 if a == 0 or b == 0 else EXP[LOG[a] + LOG[b]]


def pmul(a, b):
    """Produto de polinomios sobre GF(2), representados como inteiros."""
    r = 0
    while b:
        if b & 1:
            r ^= a
        a <<= 1
        b >>= 1
    return r


def min_poly(exponent):
    """Polinomio minimo de alpha^exponent sobre GF(2) (inteiro) e seu coset ciclotomico."""
    coset, e = [], exponent % N
    while e not in coset:
        coset.append(e)
        e = (2 * e) % N
    poly = [1]  # coeficientes em GF(32), do termo de menor grau ao maior
    for c in coset:
        r = EXP[c]
        new = [0] * (len(poly) + 1)
        for i, co in enumerate(poly):
            new[i + 1] ^= co
            new[i] ^= gmul(co, r)
        poly = new
    assert all(c in (0, 1) for c in poly), "coeficientes fora de GF(2)"
    return sum(c << i for i, c in enumerate(poly)), sorted(coset)


def poly_str(p):
    terms = [("1" if i == 0 else "x" if i == 1 else f"x^{i}") for i in range(p.bit_length() - 1, -1, -1) if p >> i & 1]
    return " + ".join(terms)


# ----------------------------------------------------------------------------
# 2. Matriz H do BCH(31,21,5) e matriz encurtada H_s
# ----------------------------------------------------------------------------
def column(i):
    """Coluna i (10 bits) de H: (alpha^i em 5 bits | alpha^(3i) em 5 bits)."""
    return (EXP[i % N] << 5) | EXP[(3 * i) % N]


def build_H_columns():
    return [column(i) for i in range(N)]


def build_Hs_columns(n=N_SENSORS):
    """Encurtamento: mantem as colunas 0..n-1 (posicoes 0..n-1) e descarta as demais."""
    return [column(i) for i in range(n)]


def matrix_rows(cols, r=R):
    """Linhas da matriz (lista de listas de bits); linha 0 = bit mais significativo."""
    return [[(c >> (r - 1 - row)) & 1 for c in cols] for row in range(r)]


# ----------------------------------------------------------------------------
# 3. Ferramentas de verificacao
# ----------------------------------------------------------------------------
def popcount(x):
    return bin(x).count("1")


def syndrome_of(cols, positions):
    s = 0
    for p in positions:
        s ^= cols[p]
    return s


def rank_gf2(cols):
    basis = []
    for c in cols:
        for b in basis:
            c = min(c, c ^ b)
        if c:
            basis.append(c)
    return len(basis)


def kernel_vectors(cols):
    """Todos os vetores x != 0 em F2^n com H x = 0 (n <= ~20). Retorna lista de inteiros."""
    n = len(cols)
    out = []
    for x in range(1, 1 << n):
        s, v, i = 0, x, 0
        while v:
            if v & 1:
                s ^= cols[i]
            v >>= 1
            i += 1
        if s == 0:
            out.append(x)
    return out


def unique_syndrome_stats(cols):
    n = len(cols)
    d2 = {}
    for p in itertools.combinations(range(n), 2):
        d2.setdefault(syndrome_of(cols, p), []).append(p)
    unique_pairs = sum(1 for v in d2.values() if len(v) == 1 for _ in v)
    singles = set(cols)
    pair_vs_single = sum(1 for s in d2 if s in singles)
    return unique_pairs, len(list(itertools.combinations(range(n), 2))), pair_vs_single


def alias_stats(cols, weight):
    """Quantos padroes de `weight` falhas tem sindrome igual a zero ou a de algum padrao de peso 1..2."""
    n = len(cols)
    low = {syndrome_of(cols, p) for w in (1, 2) for p in itertools.combinations(range(n), w)}
    zero = aliased = total = 0
    for p in itertools.combinations(range(n), weight):
        total += 1
        s = syndrome_of(cols, p)
        if s == 0:
            zero += 1
        elif s in low:
            aliased += 1
    return total, zero, aliased


# ----------------------------------------------------------------------------
# 4. Matriz antiga (repositorio original) - apenas para comparacao
# ----------------------------------------------------------------------------
LEGACY_SYNDROMES = [
    "1000010000", "0100001000", "0010000100", "0001000010", "0000111111", "1100001110",
    "0110010111", "0011011011", "1001101101", "0100110110", "1010011011", "1101011101",
    "1110101110", "1111010111", "0111101011", "1011110101",
]


def legacy_columns():
    return [int(s, 2) for s in LEGACY_SYNDROMES]


# ----------------------------------------------------------------------------
# 5. Relatorio
# ----------------------------------------------------------------------------
class Report:
    def __init__(self):
        self.failures = 0

    def check(self, name, cond, detail=""):
        mark = "OK  " if cond else "FALHA"
        print(f"  [{mark}] {name}" + (f"  ({detail})" if detail else ""))
        if not cond:
            self.failures += 1


def table_markdown(cols):
    lines = ["| Sensor | Funcao | Sindrome (bin) | Hex |", "|---|---|---|---|"]
    for k, c in enumerate(cols, start=1):
        lines.append(f"| S{k} | {SENSORS[k - 1]} | {c:010b} | 0x{c:03X} |")
    return "\n".join(lines)


def main():
    if "--table" in sys.argv:
        print(table_markdown(build_Hs_columns()))
        return 0

    rep = Report()

    print("=" * 66)
    print("SENTINELA-RF - verificacao do codigo BCH encurtado (16 sensores)")
    print("=" * 66)

    # --- Corpo e polinomios -------------------------------------------------
    print("\n1) Corpo GF(32) e polinomio gerador")
    rep.check("x^5+x^2+1 gera 31 elementos nao nulos distintos", len({EXP[i] for i in range(31)}) == 31)
    m1, c1 = min_poly(1)
    m3, c3 = min_poly(3)
    print(f"     M1(x) = {poly_str(m1)}   coset {c1}")
    print(f"     M3(x) = {poly_str(m3)}   coset {c3}")
    rep.check("M1 = x^5+x^2+1", m1 == PRIM_POLY)
    g = pmul(m1, m3)
    print(f"     g(x)  = M1*M3 = {poly_str(g)}")
    rep.check("grau de g = 10 (redundancia 10, k = 21)", g.bit_length() - 1 == 10)

    # --- BCH(31,21) completo -----------------------------------------------
    print("\n2) BCH(31,21): matriz H = (alpha^i | alpha^3i), i = 0..30")
    Hc = build_H_columns()
    rep.check("posto de H em GF(2) = 10", rank_gf2(Hc) == 10)
    ok_cw = all(
        syndrome_of(Hc, [i for i in range(N) if pmul(1 << j, g) >> i & 1]) == 0
        for j in range(21)
    )
    rep.check("os 21 deslocamentos x^j*g(x) sao palavras-codigo (H c = 0)", ok_cw)
    dep_le4 = any(
        syndrome_of(Hc, p) == 0
        for w in range(1, 5)
        for p in itertools.combinations(range(N), w)
    )
    rep.check("nenhum conjunto de <=4 colunas de H soma zero (d_min >= 5)", not dep_le4)
    dep5 = any(syndrome_of(Hc, p) == 0 for p in itertools.combinations(range(N), 5))
    rep.check("existe conjunto de 5 colunas que soma zero (d_min = 5 exato)", dep5)

    # --- Encurtamento -------------------------------------------------------
    print("\n3) Encurtamento para 16 sensores (colunas 0..15)")
    cols = build_Hs_columns()
    rows = matrix_rows(cols)
    print("     H_s (10 x 16):")
    for r in rows:
        print("       " + " ".join(map(str, r)))
    rk = rank_gf2(cols)
    rep.check("16 colunas distintas e nao nulas", len(set(cols)) == 16 and 0 not in cols)
    rep.check("posto de H_s = 10  =>  codigo [16, 6]", rk == 10, f"k = {16 - rk}")

    ker = kernel_vectors(cols)  # independente de qualquer teoria de BCH
    weights = Counter(popcount(v) for v in ker)
    dmin = min(weights)
    print(f"     palavras-codigo nao nulas: {len(ker)};  distribuicao de pesos: {dict(sorted(weights.items()))}")
    rep.check("|codigo| = 2^6 (63 palavras nao nulas)", len(ker) == 63)
    rep.check("d_min do codigo encurtado = 5 (enumeracao exaustiva)", dmin == 5, f"d_min = {dmin}")

    from_g = {pmul(m, g) for m in range(1, 1 << 6)}
    rep.check("codigo encurtado == { m(x)*g(x) : grau m <= 5 } (confere com o gerador)", set(ker) == from_g)

    # --- Capacidades --------------------------------------------------------
    print("\n4) Capacidades de deteccao e identificacao")
    undetected = [
        p for w in range(1, 5) for p in itertools.combinations(range(16), w)
        if syndrome_of(cols, p) == 0
    ]
    rep.check("toda combinacao de 1 a 4 falhas tem sindrome != 0 (detecta ate 4)", not undetected)
    five = [p for p in itertools.combinations(range(16), 5) if syndrome_of(cols, p) == 0]
    print(f"     combinacoes de 5 falhas com sindrome 0 (nao detectadas): {len(five)} de {len(list(itertools.combinations(range(16), 5)))}")

    uniq, tot, pair_vs_single = unique_syndrome_stats(cols)
    rep.check("16/16 falhas simples identificaveis", len(set(cols)) == 16)
    rep.check("120/120 falhas duplas identificaveis de forma unica", uniq == tot == 120, f"{uniq}/{tot}")
    rep.check("nenhuma falha dupla tem sindrome de falha simples", pair_vs_single == 0)

    print("\n     Limites (o que NAO e garantido):")
    for w in (3, 4):
        total, zero, aliased = alias_stats(cols, w)
        print(f"     {w} falhas: {total} combinacoes; sindrome=0: {zero}; "
              f"sindrome igual a de 1-2 falhas (diagnostico errado): {aliased} ({100.0 * aliased / total:.1f}%)")
        rep.check(f"{w} falhas sempre detectadas (sindrome != 0)", zero == 0)

    # --- Comparacao com a matriz antiga ------------------------------------
    print("\n5) Comparacao com a matriz do repositorio original")
    leg = legacy_columns()
    lk = kernel_vectors(leg)
    ldmin = min(popcount(v) for v in lk)
    luniq, ltot, _ = unique_syndrome_stats(leg)
    bch_cols = set(Hc)
    print(f"     matriz antiga: d_min = {ldmin}, duplas unicas = {luniq}/{ltot}, "
          f"colunas presentes no BCH(31,21) = {sum(c in bch_cols for c in leg)}/16")
    print(f"     matriz nova  : d_min = {dmin}, duplas unicas = {uniq}/{tot}, "
          f"colunas presentes no BCH(31,21) = {sum(c in bch_cols for c in cols)}/16")
    rep.check("matriz nova e estritamente melhor que a antiga (d_min e duplas)", dmin > ldmin and uniq > luniq)

    print("\n" + "=" * 66)
    if rep.failures:
        print(f"RESULTADO: {rep.failures} verificacao(oes) FALHARAM")
        return 1
    print("RESULTADO: todas as verificacoes passaram")
    return 0


if __name__ == "__main__":
    if "--legacy" in sys.argv:
        leg = legacy_columns()
        ker = kernel_vectors(leg)
        print("matriz antiga: d_min =", min(popcount(v) for v in ker), "| duplas unicas =", unique_syndrome_stats(leg)[:2])
        sys.exit(0)
    sys.exit(main())
