# Blacksmith of the Sand Kingdom — Tradução PT-BR

Tradução de fã completa para português brasileiro de **Blacksmith of the Sand Kingdom** (versão PC/GOG).

- ~8.800 textos: diálogos, pedidos, itens, equipamentos, habilidades, runas, inimigos, manual, troféus e menus.
- Personalidade de cada personagem mantida (o Aegon fala de forma rude e regional, a Hannah é formal, o Horick é pedante...).
- Acentos e ç funcionando: as fontes do jogo são estendidas na hora da instalação.
- Textos ajustados para caber nas caixas de diálogo e menus.
- Nomes de locais e golpes seguem um glossário (ex.: ATQ/DEF/MAG, Oficina, Taverna, Guilda, Quebra de Limite).

> Este repositório **não contém arquivos do jogo**. O instalador lê o *seu* jogo e aplica a tradução nele. É preciso ter o jogo.

## Instalação (Windows)

1. Instale o [Python 3.10+](https://www.python.org/downloads/) (marque **Add python.exe to PATH**).
2. Baixe este repositório (**Code → Download ZIP**) e extraia.
3. Dê dois cliques em `Aplicar_Traducao.bat` e cole o caminho da pasta do jogo, por exemplo:
   `D:\Games\Blacksmith of the Sand Kingdom`
4. Abra o jogo e vá em **Opções → Configurações de Idioma → "Português"**.

Linha de comando (qualquer sistema):

```
pip install -r requirements.txt
python patch.py "caminho/da/pasta/do/jogo"
```

O instalador guarda os arquivos originais em `_backup_original` (dentro de `StreamingAssets/100`).

## Desinstalar

Execute `Restaurar_Original.bat` (ou `python patch.py "<pasta>" --restore`).

## Como funciona

O jogo só tem japonês e inglês. A tradução **substitui o slot "English"**, e a opção de idioma passa a se chamar "Português". Os arquivos alterados são `exceldb` (textos), `ui_prefab` e `commonsystem` (fontes TextMeshPro, onde são injetados os glifos acentuados gerados a partir da própria fonte do jogo).

## Limitações

- Testado na versão GOG para PC; outras versões podem ter diferenças.
- Textos que são imagens (logo, alguns cartazes) não foram traduzidos; nomes aleatórios de personagens seguem em inglês.
- Se atualizar/verificar os arquivos pelo GOG Galaxy, o jogo volta ao original; rode o instalador de novo.
- Algum rótulo de menu pode ficar apertado. Abra uma *issue* com um print.

## Contribuir

Os textos estão em `translations/<Tabela>.json`, no formato `"índice:campo": "texto"`. Preserve as tags (`<style="Blue">`, `<sprite index=N>`, `#NAME#`, `[ValA]`, `$ValB$`) e o número de quebras de linha (`\n`). Correções por *pull request* são bem-vindas.

## Créditos e aviso legal

Tradução por fãs. O jogo pertence a KEMCO / Rideon Japan, Inc.; este projeto não é afiliado nem endossado por eles. Código sob licença MIT (veja `LICENSE`).

---

### English

Complete fan translation of *Blacksmith of the Sand Kingdom* into Brazilian Portuguese. No game files are included: run `python patch.py "<game folder>"` (needs Python 3.10+ and `pip install -r requirements.txt`) to patch your own copy. It replaces the "English" language slot (shown as "Português"), extends the in-game TMP fonts with accented glyphs, and backs up the originals to `_backup_original`. Use `--restore` to undo.
