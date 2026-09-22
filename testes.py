#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bateria de testes do simulador.

Executa cada maquina da pasta maquinas/ sobre varias palavras e compara o
resultado (aceita/rejeita e fita final) com o valor esperado.

Uso:
    python testes.py
"""

import io
import os
import sys

from simulador_mt import carregar_maquina, simular

PASTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maquinas")

# (arquivo da maquina, palavra, deve aceitar?, fita final esperada ou None)
CASOS = [
    ("complemento_de_um.txt", "101", True, "010"),
    ("complemento_de_um.txt", "0110", True, "1001"),
    ("complemento_de_um.txt", "1111", True, "0000"),
    ("complemento_de_um.txt", "", True, ""),

    ("a_n_b_n.txt", "", True, None),
    ("a_n_b_n.txt", "ab", True, None),
    ("a_n_b_n.txt", "aabb", True, None),
    ("a_n_b_n.txt", "aaabbb", True, None),
    ("a_n_b_n.txt", "aab", False, None),
    ("a_n_b_n.txt", "abb", False, None),
    ("a_n_b_n.txt", "ba", False, None),
    ("a_n_b_n.txt", "aba", False, None),

    ("palindromo_binario.txt", "", True, None),
    ("palindromo_binario.txt", "0", True, None),
    ("palindromo_binario.txt", "11", True, None),
    ("palindromo_binario.txt", "101", True, None),
    ("palindromo_binario.txt", "1001", True, None),
    ("palindromo_binario.txt", "01010", True, None),
    ("palindromo_binario.txt", "10", False, None),
    ("palindromo_binario.txt", "100", False, None),
    ("palindromo_binario.txt", "1101", False, None),
]


def main():
    falhas = 0

    for arquivo, palavra, esperado_aceita, esperado_fita in CASOS:
        maquina = carregar_maquina(os.path.join(PASTA, arquivo))
        # saida=io.StringIO() descarta o trace: aqui so interessa o veredito.
        resultado = simular(maquina, palavra, mostrar_trace=False, saida=io.StringIO())

        erros = []
        if resultado.aceita != esperado_aceita:
            erros.append(f"esperado {'ACEITA' if esperado_aceita else 'REJEITA'}, "
                         f"obtido {resultado.status.upper()}")
        if esperado_fita is not None and resultado.fita_final != esperado_fita:
            erros.append(f"fita esperada {esperado_fita!r}, obtida {resultado.fita_final!r}")

        rotulo = f"{arquivo:<26} palavra={palavra or '(vazia)':<8}"
        if erros:
            falhas += 1
            print(f"FALHOU  {rotulo} -> {'; '.join(erros)}")
        else:
            print(f"ok      {rotulo} -> {resultado.status} "
                  f"(fita: {resultado.fita_final or '(vazia)'}, {resultado.passos} passos)")

    print()
    print(f"{len(CASOS) - falhas}/{len(CASOS)} testes passaram.")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
