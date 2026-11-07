# SENTINELA-RF

Proposta de monitoramento de saúde de circuitos integrados RFID passivos por **síndromes de um código BCH encurtado**.

**Autor:** Euzébio Soares dos Santos
**Status:** prova de conceito matemática, verificada por computação exaustiva. **Não há validação em silício.**

> Este repositório é uma proposta independente de desenvolvimento, apresentada à CEITEC para avaliação. Não é um produto nem um resultado da CEITEC.

## Ideia

Um tag RFID passivo tem 16 sensores de saúde (tensão, memória, osciladores, atraso, temperatura, RF, corrente, watchdog, autoteste). Cada sensor produz 1 bit: 0 = normal, 1 = falha. Em vez de transmitir os 16 bits, o chip transmite uma **síndrome de 10 bits**, `s = H_s · e` sobre GF(2), onde `e` é o vetor de falhas. O leitor recebe `s` e identifica, por consulta a uma tabela, quais sensores falharam. Isso mantém o circuito no silício mínimo e leva a inteligência para o backend.

## Construção do código

Tudo abaixo é construído e verificado por `verify_bch.py`, sem bibliotecas externas.

| Item | Valor |
|---|---|
| Corpo | GF(32) = GF(2)[x]/(x⁵ + x² + 1) |
| Polinômios mínimos | M₁ = x⁵ + x² + 1 ; M₃ = x⁵ + x⁴ + x³ + x² + 1 |
| Gerador | g(x) = M₁·M₃ = x¹⁰ + x⁹ + x⁸ + x⁶ + x⁵ + x³ + 1 |
| Código base | BCH(31, 21), d_min = 5 |
| Matriz H (10×31) | coluna *i* = (αⁱ \| α³ⁱ), i = 0..30, cada elemento em 5 bits |
| Encurtamento | mantém as colunas 0..15; **H_s** é 10×16 |
| Código resultante | **[16, 6, 5]** (posto de H_s = 10) |

O encurtamento não diminui a distância mínima. O resultado foi confirmado de forma independente: enumerei as 63 palavras-código não nulas do código de comprimento 16 (kernel de H_s) e conferi que elas coincidem com os múltiplos m(x)·g(x) de grau ≤ 15. O peso mínimo é 5.

## Resultados verificados

| Propriedade | Resultado |
|---|---|
| Falhas simples identificáveis | **16/16** |
| Falhas duplas identificáveis de forma única | **120/120** |
| Detecção garantida | **até 4 falhas simultâneas** (sindrome ≠ 0 em todas as 2.516 combinações de 1 a 4 falhas) |
| Identificação garantida | até **2** falhas |
| Falhas de 5 sensores não detectadas | 4 de 4.368 combinações (as 4 palavras-código de peso 5) |

## Limites (o que não é garantido)

- **3 ou 4 falhas** são sempre detectadas, mas **não são identificáveis com certeza**. Em 40 das 560 combinações de 3 falhas (7,1%) e 110 das 1.820 de 4 falhas (6,0%), a síndrome é igual à de 1 ou 2 falhas. Um decodificador que assume "no máximo 2 falhas" diagnosticaria errado nesses casos. O `decoder.py` sinaliza essa ressalva em suas respostas.
- A garantia vale para o **modelo**: cada sensor é um bit independente e a síndrome é a soma (XOR) das colunas dos sensores em falha.

## O que ainda não foi feito

- Implementação dos 16 sensores em CMOS (350/600 nm), com estimativa de área e consumo.
- Modelo de falhas físicas. Degradação real (envelhecimento, NBTI/HCI, deriva) é analógica e correlacionada, e o modelo de bits independentes precisa ser justificado ou ajustado.
- Cálculo de como os 10 bits trafegam no canal RFID e do orçamento de energia de um tag passivo.
- Simulação com injeção de falhas e, depois, teste em hardware.
- PUF (identidade física do chip): citada como ideia, **sem desenvolvimento aqui**.
- Formalização em Lean 4: a versão anterior não compilava e foi retirada. O que está provado neste repositório é computacional, por enumeração exaustiva.

## Tabela de síndromes por sensor

Convenção: 10 bits, com αⁱ nos 5 bits altos e α³ⁱ nos 5 bits baixos.

| Sensor | Função | Síndrome (bin) | Hex |
|---|---|---|---|
| S1 | Brownout | 0000100001 | 0x021 |
| S2 | EEPROM | 0001001000 | 0x048 |
| S3 | RO1 | 0010001010 | 0x08A |
| S4 | RO2 | 0100011010 | 0x11A |
| S5 | RO3 | 1000001110 | 0x20E |
| S6 | RO4 | 0010111111 | 0x0BF |
| S7 | Delay1 | 0101000011 | 0x143 |
| S8 | Delay2 | 1010011000 | 0x298 |
| S9 | Delay3 | 0110111110 | 0x1BE |
| S10 | Delay4 | 1101001011 | 0x34B |
| S11 | Entropy | 1000110010 | 0x232 |
| S12 | Thermal | 0011100100 | 0x0E4 |
| S13 | RF | 0111000101 | 0x1C5 |
| S14 | Current | 1110001101 | 0x38D |
| S15 | Watchdog | 1110100111 | 0x3A7 |
| S16 | Self-Test | 1111111101 | 0x3FD |

A tabela é gerada por `python verify_bch.py --table`.

## Como reproduzir

Requer apenas Python 3.8 ou superior.

```bash
python verify_bch.py             # constrói H e H_s e verifica tudo (código de saída 0 = OK)
python verify_bch.py --table     # tabela de síndromes em Markdown
python verify_bch.py --legacy    # métricas da matriz da versão anterior
python decoder.py --selftest     # testa todos os padrões de 0 a 4 falhas
python decoder.py 0x021          # decodifica uma síndrome (ex.: S1 sozinho)
```

## Mudanças em relação à versão anterior

- A matriz anterior **não era derivada do BCH(31,21)** (nenhuma das 16 colunas aparecia nele), tinha d_min = 4 e identificava só 96/120 duplas. A nova é derivada do BCH e tem d_min = 5 e 120/120.
- A documentação dizia ora d_min ≥ 5, ora d_min = 4. Agora há um único valor, verificado: **5**.
- As tabelas de síndromes **mudaram**. Qualquer material que use os valores antigos precisa ser atualizado.
- Os scripts citados e ausentes agora existem e rodam sem dependências.

## Arquivos

| Arquivo | Função |
|---|---|
| `verify_bch.py` | Constrói GF(32), H, H_s e verifica todas as propriedades |
| `decoder.py` | Decodificador de síndrome com autoteste |
| `README.md` | Este documento |

## Licença

A definir pelo autor.

## Citação

```
Euzébio Soares dos Santos. SENTINELA-RF: monitoramento de saúde de circuitos integrados
RFID por síndromes de um código BCH encurtado. 2026.
```
