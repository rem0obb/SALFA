# SALFA CTF Code Generator

Gerador com interface grafica para codigos JLR Gen21 recuperados do firmware do
CTF. O perfil de 160 bytes do `UPDATE.INF` esta embutido no programa.

## Usar pelo terminal

```bash
python3 flare_generator.py SALFA2AEXEH401960 --region EU
```

Mais de um VIN pode ser informado na mesma execucao:

```bash
python3 flare_generator.py \
  SALFA2AEXEH401960 \
  SALFA2AE8DH343605 \
  --region EU
```

## Interface grafica

```bash
python3 ctf_generator_gui.py
```

A interface aceita varios VINs separados por linha, espaco, virgula ou
ponto-e-virgula.

## Build para Windows

No Windows, execute:

```powershell
.\build_windows_exe.ps1
```

Ou abra `build_windows_exe.bat`. O script:

1. Localiza Python 3.10 ou mais recente.
2. Instala Python com `winget` quando necessario.
3. Instala ou atualiza o PyInstaller.
4. Gera um unico `dist\SALFAGenerator.exe` sem dependencias externas.
5. Executa o autoteste do EXE para validar o arquivo PKG embutido.

Python e PyInstaller sao necessarios somente para compilar. A maquina que
executa `SALFAGenerator.exe` nao precisa ter Python instalado.

## Build para Linux

```bash
./build_linux_app.sh
```

O executavel sera criado em `dist/SALFAGenerator` e validado automaticamente.

## Testes

```bash
python3 -m unittest -v
```

Veja [`FLARE_ANALYSIS.md`](FLARE_ANALYSIS.md) para o algoritmo e os enderecos
relevantes do firmware.
