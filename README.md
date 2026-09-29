# SALFA CTF code generator

Gerador do codigo de ativacao JLR Gen21 recuperado por engenharia reversa do
firmware fornecido no CTF.

O perfil do `UPDATE.INF` usado pelo desafio ja esta embutido. Para gerar um ou
mais codigos, informe os VINs e a regiao:

```bash
python3 flare_generator.py SALFA2AEXEH401960 --region EU
```

```bash
python3 flare_generator.py \
  SALFA2AEXEH401960 \
  SALFA2AE8DH343605 \
  --region EU
```

Resultado esperado:

```text
SALFA2AEXEH401960 -> 2A8AD051
SALFA2AE8DH343605 -> 2921B711
```

Para usar outra midia de atualizacao:

```bash
python3 flare_generator.py SALFA2AEXEH401960 \
  --region EU \
  --update-inf /caminho/UPDATE.INF
```

## Testes

```bash
python3 -m unittest -v
```

O programa usa apenas a biblioteca padrao do Python. Consulte
[`FLARE_ANALYSIS.md`](FLARE_ANALYSIS.md) para o algoritmo recuperado, enderecos
do firmware e validacoes realizadas.

