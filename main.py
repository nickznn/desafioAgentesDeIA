"""
Desafio Agentes IA — Roteiro + Thumbnails para vídeos de videogames (CrewAI)

Fluxo (processo sequencial):
  1. Roteirista de Vídeo  -> pesquisa na web e escreve o roteiro completo
  2. Criador de Thumbnail -> cria 3 opções de thumbnail a partir do roteiro e escolhe 1
  3. Revisor              -> revisa o roteiro e entrega o documento final (roteiro + thumbnails)

Uso:
  python main.py                              # usa o tema padrão
  python main.py "Melhores jogos de 2020"     # tema pela linha de comando
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from crewai import Agent, Crew, LLM, Process, Task
from crewai_tools import DallETool, SerperDevTool

load_dotenv()

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
MODELO = os.getenv("MODEL", "gpt-4o-mini")
GERAR_IMAGENS = os.getenv("GERAR_IMAGENS", "false").lower() == "true"
PASTA_SAIDA = Path("output")
PASTA_SAIDA.mkdir(exist_ok=True)

llm = LLM(model=MODELO, temperature=0.7)

# Ferramentas
ferramenta_busca = SerperDevTool(n_results=8)  # precisa de SERPER_API_KEY

ferramentas_thumbnail = []
if GERAR_IMAGENS:
    # Gera as imagens de verdade (custa créditos da OpenAI).
    # 1792x1024 é o formato horizontal mais próximo do 16:9 do YouTube.
    ferramentas_thumbnail.append(
        DallETool(model="dall-e-3", size="1792x1024", quality="standard", n=1)
    )

# ---------------------------------------------------------------------------
# Agentes
# ---------------------------------------------------------------------------
roteirista = Agent(
    role="Roteirista de Vídeo",
    goal=(
        "Pesquisar a fundo o tema '{query}' e escrever um roteiro detalhado e "
        "envolvente para um vídeo completo no YouTube sobre videogames."
    ),
    backstory=(
        "Você é um roteirista experiente de canais de games no YouTube. "
        "Domina storytelling, ganchos de abertura que prendem nos primeiros "
        "10 segundos e ritmo de edição. Sempre confere fatos (datas de "
        "lançamento, desenvolvedoras, notas, vendas) antes de escrever."
    ),
    tools=[ferramenta_busca],
    llm=llm,
    allow_delegation=False,
    verbose=True,
)

criador_thumbnail = Agent(
    role="Criador de Thumbnail",
    goal=(
        "Criar três opções de thumbnail chamativas e fiéis ao conteúdo do "
        "roteiro e escolher a mais forte para o vídeo."
    ),
    backstory=(
        "Você é designer gráfico especializado em thumbnails de YouTube com "
        "alto CTR. Entende hierarquia visual, contraste, leitura em tela "
        "pequena, uso de rostos/expressões e textos curtos (até 4 palavras)."
    ),
    tools=ferramentas_thumbnail,
    llm=llm,
    allow_delegation=False,
    verbose=True,
)

revisor = Agent(
    role="Revisor",
    goal=(
        "Revisar o roteiro (gramática, clareza, ritmo e precisão) e montar a "
        "versão final contendo o roteiro revisado e as thumbnails."
    ),
    backstory=(
        "Você é editor-chefe de um canal de games. Corrige erros sem tirar a "
        "voz do roteirista, corta trechos arrastados e garante que tudo "
        "esteja pronto para gravação."
    ),
    llm=llm,
    allow_delegation=False,
    verbose=True,
)

# ---------------------------------------------------------------------------
# Tarefas
# ---------------------------------------------------------------------------
tarefa_roteiro = Task(
    description=(
        "Pesquise na web sobre o tema: '{query}'.\n"
        "Depois escreva um roteiro completo para um vídeo de 8 a 12 minutos "
        "no YouTube, em português do Brasil, com:\n"
        "1. Título do vídeo (e 2 alternativas)\n"
        "2. Gancho de abertura (primeiros 10–15 segundos)\n"
        "3. Introdução\n"
        "4. Desenvolvimento dividido em blocos/tópicos, cada um com: fala do "
        "apresentador, sugestão de imagens/gameplay (B-roll) e tempo estimado\n"
        "5. Momento de chamada para inscrição/like no meio do vídeo\n"
        "6. Conclusão e chamada para comentários\n"
        "Use apenas informações confirmadas na pesquisa e cite as fontes no final."
    ),
    expected_output=(
        "Roteiro completo em Markdown, com títulos, blocos com tempos "
        "estimados, falas, indicações de B-roll e lista de fontes."
    ),
    agent=roteirista,
    output_file=str(PASTA_SAIDA / "1_roteiro.md"),
)

instrucao_imagem = (
    "Para CADA opção, use a ferramenta de geração de imagem com o prompt "
    "visual e inclua a URL da imagem gerada."
    if GERAR_IMAGENS
    else "Não gere imagens; apenas descreva as opções e escreva o prompt visual."
)

tarefa_thumbnails = Task(
    description=(
        "Com base no roteiro, crie TRÊS opções de thumbnail diferentes entre si "
        "para o vídeo sobre '{query}'. Para cada opção informe:\n"
        "- Nome do conceito\n"
        "- Composição (elementos, posição, plano de fundo)\n"
        "- Texto da thumbnail (no máximo 4 palavras)\n"
        "- Paleta de cores e tipografia\n"
        "- Prompt visual em inglês, detalhado, para um gerador de imagens "
        "(formato 16:9, sem logos ou personagens protegidos por direitos autorais, "
        "use cenas e personagens genéricos inspirados no tema)\n"
        f"{instrucao_imagem}\n\n"
        "Por fim, ESCOLHA a melhor das três e justifique em 3 a 5 linhas "
        "(legibilidade em tela pequena, curiosidade, fidelidade ao conteúdo)."
    ),
    expected_output=(
        "Markdown com as 3 opções de thumbnail detalhadas e uma seção "
        "'Thumbnail escolhida' com a justificativa."
    ),
    agent=criador_thumbnail,
    context=[tarefa_roteiro],
    output_file=str(PASTA_SAIDA / "2_thumbnails.md"),
)

tarefa_revisao = Task(
    description=(
        "Revise o roteiro: corrija gramática e ortografia, melhore clareza e "
        "ritmo, elimine repetições e verifique coerência das informações.\n"
        "Depois monte o DOCUMENTO FINAL em Markdown com:\n"
        "1. Título final do vídeo\n"
        "2. Roteiro revisado completo\n"
        "3. As 3 opções de thumbnail (resumidas)\n"
        "4. A thumbnail escolhida, com a justificativa\n"
        "5. Lista curta das principais alterações feitas na revisão"
    ),
    expected_output="Documento final em Markdown, pronto para produção do vídeo.",
    agent=revisor,
    context=[tarefa_roteiro, tarefa_thumbnails],
    output_file=str(PASTA_SAIDA / "3_versao_final.md"),
)

# ---------------------------------------------------------------------------
# Crew
# ---------------------------------------------------------------------------
crew = Crew(
    agents=[roteirista, criador_thumbnail, revisor],
    tasks=[tarefa_roteiro, tarefa_thumbnails, tarefa_revisao],
    process=Process.sequential,
    verbose=True,
)


def main():
    tema = " ".join(sys.argv[1:]) or "Melhores jogos de 2020"
    resultado = crew.kickoff(inputs={"query": tema})

    print("\n" + "=" * 70)
    print("VERSÃO FINAL")
    print("=" * 70)
    print(resultado.raw)
    print(f"\nArquivos salvos em: {PASTA_SAIDA.resolve()}")


if __name__ == "__main__":
    main()
