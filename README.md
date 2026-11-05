# 🎮 Roteiro + Thumbnails para vídeos de games (CrewAI)

Sistema multiagente que recebe um tema e entrega um roteiro de YouTube revisado, três opções de thumbnail e a thumbnail escolhida.

## Agentes

| Agente | Função | Ferramentas |
|---|---|---|
| Roteirista de Vídeo | Pesquisa o tema e escreve o roteiro completo | `SerperDevTool` (busca web) |
| Criador de Thumbnail | Cria 3 conceitos a partir do roteiro e escolhe 1 | `DallETool` (opcional) |
| Revisor | Revisa o roteiro e monta o documento final | — |

Processo **sequencial**: a tarefa de thumbnails recebe o roteiro como contexto, e a revisão recebe roteiro + thumbnails.

## Como rodar

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # preencha as chaves
python main.py "Melhores jogos de 2020"
```

Ou, no código, a chamada do enunciado:

```python
crew.kickoff(inputs={'query': 'Melhores jogos de 2020'})
```

## Saídas (pasta `output/`)

- `1_roteiro.md` — roteiro original do Roteirista
- `2_thumbnails.md` — 3 opções + escolhida
- `3_versao_final.md` — roteiro revisado + thumbnails (entrega final)

## Geração de imagens

Com `GERAR_IMAGENS=true` no `.env`, o Criador de Thumbnail usa o DALL-E 3 (1792x1024) para gerar as três imagens e inclui as URLs no resultado. Com `false`, ele entrega só os conceitos e prompts — útil para testar sem gastar créditos.
