#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulador de Maquina de Turing (MT) deterministica padrao.

Disciplina: Teoria da Computacao e Complexidade de Algoritmos.

O simulador e generico: a definicao da maquina (estado inicial, estados de
aceitacao e funcao de transicao) e lida de um arquivo de texto, e a palavra de
entrada e informada por linha de comando ou pelo terminal. A execucao e exibida
passo a passo ate a parada (aceitacao ou rejeicao).

Exemplos de uso:
    python simulador_mt.py maquinas/complemento_de_um.txt 101
    python simulador_mt.py maquinas/a_n_b_n.txt aabb --sem-trace
    python simulador_mt.py                      (modo interativo)
"""

import argparse
import os
import sys
import unicodedata
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

BRANCO_PADRAO = "_"  # simbolo que representa a celula vazia da fita

# Direcoes aceitas no arquivo de configuracao e o deslocamento do cabecote.
# R/D = direita (+1), L/E = esquerda (-1).
DIRECOES = {"R": 1, "D": 1, "L": -1, "E": -1}
NOME_DA_DIRECAO = {1: "Direita", -1: "Esquerda"}

LIMITE_DE_PASSOS_PADRAO = 10_000  # protecao contra maquinas que nao param

# Texto do veredito mostrado ao final da simulacao.
VEREDITO = {
    "aceita": "PALAVRA ACEITA",
    "rejeita": "PALAVRA REJEITADA",
    "limite": "EXECUCAO INTERROMPIDA",
}


class ErroDeConfiguracao(Exception):
    """Sinaliza um problema no arquivo que descreve a maquina."""


# ---------------------------------------------------------------------------
# Definicao da maquina
# ---------------------------------------------------------------------------


class MaquinaDeTuring:
    """Definicao estatica de uma MT deterministica.

    transicoes mapeia (estado_atual, simbolo_lido) em
    (novo_estado, simbolo_escrito, deslocamento), onde deslocamento e +1 ou -1.
    """

    def __init__(self, estado_inicial, estados_finais, transicoes,
                 branco=BRANCO_PADRAO, nome=""):
        self.estado_inicial = estado_inicial
        self.estados_finais = set(estados_finais)
        self.transicoes = transicoes
        self.branco = branco
        self.nome = nome or "(sem nome)"

    def transicao(self, estado, simbolo):
        """Funcao de transicao d(estado, simbolo). Devolve None se nao existir."""
        return self.transicoes.get((estado, simbolo))

    def estados(self):
        """Todos os estados citados na definicao, em ordem alfabetica."""
        conjunto = {self.estado_inicial} | self.estados_finais
        for (origem, _), (destino, _, _) in self.transicoes.items():
            conjunto.add(origem)
            conjunto.add(destino)
        return sorted(conjunto)

    def alfabeto_da_fita(self):
        """Simbolos que aparecem nas regras, incluindo o branco."""
        simbolos = {self.branco}
        for (_, lido), (_, escrito, _) in self.transicoes.items():
            simbolos.add(lido)
            simbolos.add(escrito)
        return sorted(simbolos)

    def descrever(self):
        """Texto com o resumo da maquina, exibido antes da simulacao."""
        linhas = [
            f"Maquina........: {self.nome}",
            f"Estado inicial.: {self.estado_inicial}",
            f"Estados finais.: {', '.join(sorted(self.estados_finais))}",
            f"Estados (Q)....: {', '.join(self.estados())}",
            f"Alfabeto da fita: {', '.join(self.alfabeto_da_fita())}",
            f"Transicoes.....: {len(self.transicoes)} regra(s)",
        ]
        for (estado, lido), (novo, escrito, passo) in sorted(self.transicoes.items()):
            direcao = "R" if passo > 0 else "L"
            linhas.append(f"    d({estado}, {lido}) = ({novo}, {escrito}, {direcao})")
        return "\n".join(linhas)


# ---------------------------------------------------------------------------
# Leitura do arquivo de configuracao
# ---------------------------------------------------------------------------


def _normalizar(texto):
    """Remove acentos, espacos das pontas e converte para maiusculas.

    Serve para aceitar cabecalhos escritos como "TRANSICOES" ou "TRANSICOES".
    """
    sem_acentos = unicodedata.normalize("NFKD", texto)
    sem_acentos = sem_acentos.encode("ascii", "ignore").decode("ascii")
    return sem_acentos.strip().upper()


# Cabecalhos reconhecidos no arquivo -> campo interno correspondente.
CABECALHOS = {
    "NOME": "nome",
    "INICIAL": "inicial",
    "ESTADO INICIAL": "inicial",
    "ESTADO_INICIAL": "inicial",
    "FINAIS": "finais",
    "ESTADOS FINAIS": "finais",
    "ACEITACAO": "finais",
    "BRANCO": "branco",
    "TRANSICOES": "transicoes",
}


def carregar_maquina(caminho):
    """Le o arquivo de definicao e devolve uma MaquinaDeTuring.

    Formato aceito (linhas iniciadas por # sao comentarios):

        NOME: Complemento de 1
        INICIAL: q0
        FINAIS: qf
        TRANSICOES:
        q0 0 q0 1 R
        q0 1 q0 0 R
        q0 _ qf _ L
    """
    try:
        with open(caminho, "r", encoding="utf-8-sig") as arquivo:
            linhas = arquivo.readlines()
    except FileNotFoundError:
        raise ErroDeConfiguracao(f"arquivo nao encontrado: {caminho}")
    except OSError as erro:
        raise ErroDeConfiguracao(f"nao foi possivel ler {caminho}: {erro}")

    nome = os.path.splitext(os.path.basename(caminho))[0]
    estado_inicial = None
    estados_finais = set()
    branco = BRANCO_PADRAO
    transicoes = {}

    for numero, linha_bruta in enumerate(linhas, start=1):
        linha = linha_bruta.strip()
        if not linha or linha.startswith("#"):
            continue

        # Linha de cabecalho (CHAVE: valor) ou linha de regra de transicao.
        chave, separador, valor = linha.partition(":")
        campo = CABECALHOS.get(_normalizar(chave)) if separador else None

        if campo == "transicoes":
            # Marcador de secao; as regras vem nas linhas seguintes.
            if valor.strip():
                _registrar_transicao(transicoes, valor.strip(), numero)
        elif campo == "nome":
            nome = valor.strip() or nome
        elif campo == "inicial":
            estado_inicial = valor.strip()
            if not estado_inicial:
                raise ErroDeConfiguracao(f"linha {numero}: estado inicial vazio")
        elif campo == "finais":
            estados_finais = {e for e in valor.replace(",", " ").split() if e}
            if not estados_finais:
                raise ErroDeConfiguracao(f"linha {numero}: nenhum estado final informado")
        elif campo == "branco":
            branco = valor.strip() or BRANCO_PADRAO
            if len(branco) != 1:
                raise ErroDeConfiguracao(
                    f"linha {numero}: o simbolo branco deve ter exatamente 1 caractere")
        else:
            _registrar_transicao(transicoes, linha, numero)

    # Validacoes finais da definicao.
    if estado_inicial is None:
        raise ErroDeConfiguracao("o arquivo nao define o estado inicial (INICIAL:)")
    if not estados_finais:
        raise ErroDeConfiguracao("o arquivo nao define estados de aceitacao (FINAIS:)")
    if not transicoes:
        raise ErroDeConfiguracao("o arquivo nao contem nenhuma regra de transicao")

    return MaquinaDeTuring(estado_inicial, estados_finais, transicoes, branco, nome)


def _registrar_transicao(transicoes, linha, numero):
    """Interpreta uma regra "estado lido novo_estado escrito direcao"."""
    partes = linha.split()
    if len(partes) != 5:
        raise ErroDeConfiguracao(
            f"linha {numero}: a regra deve ter 5 campos "
            f"[estado] [lido] [novo_estado] [escrito] [direcao], "
            f"mas tem {len(partes)}: {linha!r}")

    estado, lido, novo_estado, escrito, direcao = partes
    if len(lido) != 1 or len(escrito) != 1:
        raise ErroDeConfiguracao(
            f"linha {numero}: simbolos lido/escrito devem ter 1 caractere: {linha!r}")

    deslocamento = DIRECOES.get(direcao.upper())
    if deslocamento is None:
        raise ErroDeConfiguracao(
            f"linha {numero}: direcao invalida {direcao!r} (use R/D para direita ou L/E para esquerda)")

    chave = (estado, lido)
    if chave in transicoes:
        # A maquina precisa ser deterministica: no maximo uma regra por par.
        raise ErroDeConfiguracao(
            f"linha {numero}: ja existe uma regra para d({estado}, {lido}) "
            f"- a maquina deixaria de ser deterministica")

    transicoes[chave] = (novo_estado, escrito, deslocamento)


# ---------------------------------------------------------------------------
# Fita
# ---------------------------------------------------------------------------


class Fita:
    """Fita infinita nos dois sentidos, expandida dinamicamente.

    As celulas sao guardadas em um dicionario esparso {posicao: simbolo}; apenas
    os simbolos diferentes do branco ocupam memoria, de modo que a fita cresce
    indefinidamente conforme o cabecote avanca.
    """

    def __init__(self, palavra, branco=BRANCO_PADRAO):
        self.branco = branco
        self._celulas = {i: s for i, s in enumerate(palavra) if s != branco}

    def ler(self, posicao):
        """Simbolo na celula indicada (branco se a celula nunca foi usada)."""
        return self._celulas.get(posicao, self.branco)

    def escrever(self, posicao, simbolo):
        if simbolo == self.branco:
            self._celulas.pop(posicao, None)
        else:
            self._celulas[posicao] = simbolo

    def conteudo(self):
        """Conteudo util da fita (do primeiro ao ultimo simbolo nao branco)."""
        if not self._celulas:
            return ""
        inicio, fim = min(self._celulas), max(self._celulas)
        return "".join(self.ler(i) for i in range(inicio, fim + 1))

    def formatar(self, cabecote):
        """Fita como texto, com a celula do cabecote entre colchetes.

        Exemplo: "0 1 [1] _" mostra o trecho relevante da fita mais os brancos
        adjacentes necessarios para acompanhar o cabecote.
        """
        if self._celulas:
            inicio = min(min(self._celulas), cabecote)
            fim = max(max(self._celulas) + 1, cabecote)
        else:
            inicio, fim = min(0, cabecote), max(0, cabecote)

        celulas = []
        for posicao in range(inicio, fim + 1):
            simbolo = self.ler(posicao)
            celulas.append(f"[{simbolo}]" if posicao == cabecote else simbolo)
        return " ".join(celulas)


# ---------------------------------------------------------------------------
# Simulacao
# ---------------------------------------------------------------------------


@dataclass
class Resultado:
    """Resumo da execucao devolvido por simular()."""

    status: str              # "aceita", "rejeita" ou "limite"
    estado_final: str
    passos: int
    fita_final: str
    motivo: str = ""

    @property
    def aceita(self):
        return self.status == "aceita"


def simular(maquina, palavra, mostrar_trace=True,
            limite_passos=LIMITE_DE_PASSOS_PADRAO, saida=sys.stdout):
    """Executa a maquina sobre a palavra e imprime o rastreamento da execucao.

    A cada passo sao exibidos o estado atual, o conteudo da fita e a posicao do
    cabecote. A execucao para quando a maquina atinge um estado de aceitacao ou
    quando nao existe transicao definida para a configuracao atual (rejeicao).
    """
    fita = Fita(palavra, maquina.branco)
    estado = maquina.estado_inicial
    cabecote = 0
    passo = 0

    def registrar(rotulo, detalhe=""):
        """Imprime a configuracao atual: estado, fita e posicao do cabecote."""
        if not mostrar_trace:
            return
        if detalhe:
            print(f"{rotulo} {detalhe}", file=saida)
        else:
            print(rotulo, file=saida)
        print(f"  Fita..: {fita.formatar(cabecote)}", file=saida)
        print(f"  Estado: {estado}   |   Cabecote na posicao {cabecote}", file=saida)
        print(file=saida)

    registrar("Configuracao inicial:")

    while True:
        # 1) Parada por aceitacao: o estado atual e um estado final.
        if estado in maquina.estados_finais:
            return _finalizar(
                "aceita", estado, passo, fita, mostrar_trace, saida,
                f"parada no estado de aceitacao {estado}")

        # 2) Protecao contra laco infinito (a MT pode simplesmente nao parar).
        if passo >= limite_passos:
            return _finalizar(
                "limite", estado, passo, fita, mostrar_trace, saida,
                f"limite de {limite_passos} passos atingido - possivel laco infinito")

        simbolo_lido = fita.ler(cabecote)
        regra = maquina.transicao(estado, simbolo_lido)

        # 3) Parada por rejeicao: nao ha transicao para (estado, simbolo lido).
        if regra is None:
            return _finalizar(
                "rejeita", estado, passo, fita, mostrar_trace, saida,
                f"nao existe transicao para d({estado}, {simbolo_lido}) "
                f"e {estado} nao e estado de aceitacao")

        # 4) Aplica a regra: escreve, muda de estado e move o cabecote.
        novo_estado, simbolo_escrito, deslocamento = regra
        estado_anterior = estado
        fita.escrever(cabecote, simbolo_escrito)
        estado = novo_estado
        cabecote += deslocamento
        passo += 1

        direcao = "R" if deslocamento > 0 else "L"
        registrar(
            f"Passo {passo}:",
            f"d({estado_anterior}, {simbolo_lido}) = "
            f"({novo_estado}, {simbolo_escrito}, {direcao})   ->   "
            f"le '{simbolo_lido}', escreve '{simbolo_escrito}', "
            f"move para a {NOME_DA_DIRECAO[deslocamento]}")


def _finalizar(status, estado, passos, fita, mostrar_trace, saida, motivo):
    """Imprime o veredito final e monta o objeto Resultado."""
    resultado = Resultado(
        status=status,
        estado_final=estado,
        passos=passos,
        fita_final=fita.conteudo(),
        motivo=motivo,
    )

    if mostrar_trace:
        print("-" * 60, file=saida)
        print(f"Resultado..: {VEREDITO[status]} ({motivo})", file=saida)
        print(f"Fita final.: {resultado.fita_final or '(vazia)'}", file=saida)
        print(f"Passos.....: {passos}", file=saida)
        print("-" * 60, file=saida)

    return resultado


# ---------------------------------------------------------------------------
# Interface de linha de comando
# ---------------------------------------------------------------------------


def _perguntar(mensagem):
    """input() que devolve string vazia quando nao ha terminal (EOF/Ctrl+C)."""
    try:
        return input(mensagem).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def _escolher_maquina_interativamente():
    """Lista os arquivos da pasta maquinas/ e pede que o usuario escolha um."""
    pasta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maquinas")
    arquivos = sorted(f for f in os.listdir(pasta)) if os.path.isdir(pasta) else []

    if not arquivos:
        return _perguntar("Caminho do arquivo da maquina: ")

    print("Maquinas disponiveis:")
    for indice, arquivo in enumerate(arquivos, start=1):
        print(f"  {indice}) {arquivo}")
    escolha = _perguntar("Escolha o numero (ou digite um caminho): ")

    if escolha.isdigit() and 1 <= int(escolha) <= len(arquivos):
        return os.path.join(pasta, arquivos[int(escolha) - 1])
    return escolha


def main(argv=None):
    # No Windows o console pode usar uma codificacao que nao imprime acentos.
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    analisador = argparse.ArgumentParser(
        description="Simulador de Maquina de Turing deterministica.",
        epilog="Exemplo: python simulador_mt.py maquinas/complemento_de_um.txt 101")
    analisador.add_argument("maquina", nargs="?",
                            help="arquivo com a definicao da maquina")
    analisador.add_argument("palavra", nargs="?",
                            help="palavra de entrada (fita inicial)")
    analisador.add_argument("--sem-trace", action="store_true",
                            help="mostra apenas o resultado final")
    analisador.add_argument("--limite", type=int, default=LIMITE_DE_PASSOS_PADRAO,
                            help=f"maximo de passos (padrao: {LIMITE_DE_PASSOS_PADRAO})")
    argumentos = analisador.parse_args(argv)

    print("=" * 60)
    print("        SIMULADOR DE MAQUINA DE TURING")
    print("=" * 60)

    caminho = argumentos.maquina or _escolher_maquina_interativamente()

    try:
        maquina = carregar_maquina(caminho)
    except ErroDeConfiguracao as erro:
        sys.stdout.flush()
        print(f"\nErro na definicao da maquina: {erro}", file=sys.stderr)
        return 2

    print()
    print(maquina.descrever())
    print("=" * 60)

    palavra = argumentos.palavra
    if palavra is None:
        palavra = _perguntar("Palavra de entrada (fita inicial): ")

    print(f"\nPalavra de entrada: {palavra or '(vazia)'}\n")

    resultado = simular(maquina, palavra,
                        mostrar_trace=not argumentos.sem_trace,
                        limite_passos=argumentos.limite)

    if argumentos.sem_trace:
        print(f"Resultado: {VEREDITO[resultado.status]} ({resultado.motivo})")
        print(f"Fita final: {resultado.fita_final or '(vazia)'}")

    return 0 if resultado.aceita else 1


if __name__ == "__main__":
    sys.exit(main())
