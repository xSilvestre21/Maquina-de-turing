# Simulador de Máquina de Turing

Trabalho da disciplina **Teoria da Computação e Complexidade de Algoritmos**
(Engenharia de Computação — Prof. Sérgio Yoshioka).

Simulador **genérico** de Máquina de Turing determinística padrão, escrito em
Python 3 (sem bibliotecas externas). A máquina é descrita em um arquivo de
texto, a palavra de entrada é informada pelo terminal e o programa imprime o
rastreamento (*trace*) passo a passo até a parada por aceitação ou rejeição.

## Estrutura do projeto

```
Simulador_Maquina_de_Turing/
├── simulador_mt.py                  # programa principal (leitura, fita, simulação, trace)
├── testes.py                        # bateria de testes automáticos (21 casos)
├── README.md
└── maquinas/
    ├── complemento_de_um.txt        # exemplo de validação exigido na tarefa
    ├── a_n_b_n.txt                  # reconhece a^n b^n
    └── palindromo_binario.txt       # reconhece palíndromos sobre {0,1}
```

## Como executar

Requer apenas **Python 3.8 ou superior**.

```bash
python simulador_mt.py maquinas/complemento_de_um.txt 101
```

Outras formas de uso:

```bash
python simulador_mt.py                                    # modo interativo: escolhe a máquina e pede a palavra
python simulador_mt.py maquinas/a_n_b_n.txt aabb          # máquina e palavra por argumento
python simulador_mt.py maquinas/a_n_b_n.txt aabb --sem-trace     # só o resultado final
python simulador_mt.py maquinas/a_n_b_n.txt aabb --limite 500    # muda o limite de passos
python testes.py                                          # roda todos os testes automáticos
```

## Formato do arquivo de configuração

Arquivo de texto simples. Linhas iniciadas por `#` são comentários e linhas em
branco são ignoradas.

| Campo | Obrigatório | Descrição |
|---|---|---|
| `NOME:` | não | Nome exibido no cabeçalho da execução |
| `INICIAL:` | **sim** | Estado inicial da máquina |
| `FINAIS:` | **sim** | Estados de aceitação (separados por espaço ou vírgula) |
| `BRANCO:` | não | Símbolo de célula vazia (padrão: `_`) |
| `TRANSICOES:` | **sim** | Marcador de seção; as regras vêm nas linhas seguintes |

Cada regra de transição ocupa uma linha com cinco campos:

```
[estado_atual] [simbolo_lido] [novo_estado] [simbolo_escrito] [direcao]
```

A direção é `R` (direita) ou `L` (esquerda) — também são aceitos `D` e `E`.
Formalmente, a linha representa:

```
δ(estado_atual, simbolo_lido) = (novo_estado, simbolo_escrito, direcao)
```

Exemplo completo (`maquinas/complemento_de_um.txt`):

```
NOME: Complemento de 1 (inverte bits)
INICIAL: q0
FINAIS: qf

TRANSICOES:
q0 0 q0 1 R
q0 1 q0 0 R
q0 _ qf _ L
```

## Exemplo de execução (validação da tarefa)

```
$ python simulador_mt.py maquinas/complemento_de_um.txt 101

Palavra de entrada: 101

Configuracao inicial:
  Fita..: [1] 0 1 _
  Estado: q0   |   Cabecote na posicao 0

Passo 1: d(q0, 1) = (q0, 0, R)   ->   le '1', escreve '0', move para a Direita
  Fita..: 0 [0] 1 _
  Estado: q0   |   Cabecote na posicao 1

Passo 2: d(q0, 0) = (q0, 1, R)   ->   le '0', escreve '1', move para a Direita
  Fita..: 0 1 [1] _
  Estado: q0   |   Cabecote na posicao 2

Passo 3: d(q0, 1) = (q0, 0, R)   ->   le '1', escreve '0', move para a Direita
  Fita..: 0 1 0 [_]
  Estado: q0   |   Cabecote na posicao 3

Passo 4: d(q0, _) = (qf, _, L)   ->   le '_', escreve '_', move para a Esquerda
  Fita..: 0 1 [0] _
  Estado: qf   |   Cabecote na posicao 2

------------------------------------------------------------
Resultado..: PALAVRA ACEITA (parada no estado de aceitacao qf)
Fita final.: 010
Passos.....: 4
------------------------------------------------------------
```

A saída corresponde exatamente à execução esperada descrita no enunciado: a
fita resultante para a entrada `101` é `010`, com parada no estado `qf`.

## Como o simulador funciona

1. **Leitura da máquina** (`carregar_maquina`): interpreta o arquivo linha a
   linha, valida cada regra e monta o dicionário da função de transição
   `(estado, símbolo lido) → (novo estado, símbolo escrito, deslocamento)`.
   Regras malformadas, direções inválidas e pares `(estado, símbolo)`
   duplicados (que quebrariam o determinismo) geram erro com o número da linha.
2. **Fita** (`Fita`): implementada como um dicionário esparso `{posição: símbolo}`.
   Só as células com símbolo diferente do branco ocupam memória, portanto a fita
   é **infinita e expandida dinamicamente** — inclusive para posições negativas,
   quando o cabeçote anda para a esquerda do início da palavra.
3. **Ciclo de execução** (`simular`): lê o símbolo sob o cabeçote, busca a regra
   correspondente, escreve o novo símbolo, atualiza o estado e move o cabeçote,
   exibindo a configuração a cada passo.
4. **Parada**:
   - o estado atual é de aceitação → `PALAVRA ACEITA`;
   - não existe transição para o par `(estado, símbolo lido)` → `PALAVRA REJEITADA`;
   - o limite de passos é atingido → `EXECUCAO INTERROMPIDA` (proteção contra
     máquinas que não param; o limite padrão é 10.000 e pode ser alterado com
     `--limite`).

## Máquinas de exemplo incluídas

| Arquivo | Linguagem / função | Aceita | Rejeita |
|---|---|---|---|
| `complemento_de_um.txt` | Complemento de 1 (inverte os bits) | `101` → `010`, `0110` → `1001` | — (sempre para em `qf`) |
| `a_n_b_n.txt` | `L = { aⁿbⁿ \| n ≥ 0 }` | `ab`, `aabb`, `aaabbb` | `aab`, `abb`, `ba`, `aba` |
| `palindromo_binario.txt` | Palíndromos sobre `{0,1}` | `0`, `11`, `101`, `1001`, `01010` | `10`, `100`, `1101` |

Para criar uma máquina nova, basta copiar um desses arquivos, alterar as regras
e rodar o simulador apontando para ele — nenhum código precisa ser modificado.
