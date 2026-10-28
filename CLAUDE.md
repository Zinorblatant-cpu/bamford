# Bamford — Lei de Benford aplicada a Notas Fiscais

App em Streamlit para demonstrar a clientes como a Lei de Benford pode apontar indícios de manipulação em valores de notas fiscais. Mostra lado a lado um conjunto de notas "regulares" (segue o padrão) e um conjunto "alteradas" (manipuladas), com gráficos comparando a distribuição observada de dígitos com a esperada pela lei.

## Estrutura

```
bamford/
├── backend/
│   ├── benford.py          # lógica da Lei de Benford (núcleo matemático)
│   └── data_generator.py   # geração de notas fiscais simuladas
├── frontend/
│   ├── app.py               # app Streamlit (interface, duas abas)
│   └── charts.py            # construção do gráfico (Plotly)
└── requirements.txt
```

Não é um repositório git. `frontend/app.py` importa `backend` via `sys.path.append` do diretório pai (`Path(__file__).resolve().parent.parent`), pois são pastas irmãs, não um único pacote instalável.

## Como rodar

```bash
pip install -r requirements.txt
python -m streamlit run frontend/app.py --server.port 8501
```

Acessar em `http://localhost:8501`. (Usar `python -m streamlit`, não `streamlit`, no Git Bash do Windows — o executável `streamlit.exe` não fica no PATH por padrão.)

## backend/benford.py — núcleo da Lei de Benford

- `BENFORD_EXPECTED`: distribuição clássica do 1º dígito, `log10(1 + 1/d)` para d em 1-9.
- `digit_at_position(value, position)`: extrai o dígito significativo na posição pedida (1 = primeiro dígito, 2 = segundo, etc.). Normaliza o valor para a faixa `[1, 10)` preservando os dígitos, depois multiplica por `10**(position-1)` e tira o resto da divisão por 10. Usa `round(..., 9)` para mitigar erro de ponto flutuante.
- `digit_distribution(values, position)`: conta a frequência de cada dígito (1-9 para posição 1, 0-9 para posições 2-4) numa série de valores e devolve `(counts, observed_pct)`.
- `expected_distribution(position)`: distribuição esperada generalizada da Lei de Benford para qualquer posição. Para posição 1 usa `BENFORD_EXPECTED` direto; para posições 2-4 soma `log10(1 + 1/(10*m + d))` sobre todas as combinações possíveis dos dígitos anteriores (`m` variando no intervalo apropriado).
- `deviation_metrics(observed_pct, expected_pct)`: calcula três métricas a partir das diferenças ponto a ponto entre observado e esperado:
  - `std_dev`: desvio padrão das diferenças (métrica principal usada no app, exibida como "Desvio do padrão").
  - `mad`: desvio absoluto médio (calculado mas não exibido na UI — removido por ser redundante com `std_dev` e gerar jargão extra).
  - `chi_square`: estatística qui-quadrado, `Σ (observado-esperado)² / esperado`. É a métrica que resume todas as diferenças num único número — quanto maior, mais forte o indício de manipulação. Exibida na UI como "Qui-quadrado" com tooltip explicativo.

`MAX_POSITION = 4` é só uma constante de referência; o app está fixado em mostrar posições 1 a 4 (não há lógica para "N" posições dinâmico).

## backend/data_generator.py — geração de dados simulados

Duas funções, ambas retornam um `pandas.DataFrame` com colunas `numero_nf` e `valor`:

- `generate_compliant_invoices(n, seed)`: sorteia o primeiro dígito segundo a distribuição real de Benford, depois sorteia uma escala (`_SCALES = [10, 100, 1000, 10000]`) e um valor dentro dela. Resultado: baixo desvio em relação à Lei de Benford (~0.5-2 p.p. de desvio padrão, dependendo da posição do dígito).
- `generate_altered_invoices(n, seed)`: simula fraude típica —
  - distribuição de primeiro dígito quase uniforme (`probs = [0.07, 0.09, 0.10, 0.11, 0.13, 0.13, 0.12, 0.13, 0.12]`), fugindo do padrão natural;
  - 35% de chance de "arredondar" o valor para terminar em `.00`, `.90` ou `.99` (valores fabricados manualmente tendem a ser redondos);
  - 18% de chance de reaproveitar um valor já usado antes (repetição é outro sinal clássico de fraude).
  - Resultado: desvio alto, especialmente no 1º e 4º dígito (~8-10 p.p. de desvio padrão).

**Detalhe importante de `_SCALE_WEIGHTS = [0.05, 0.30, 0.40, 0.25]`**: a escala 10 (valores pequenos, ex. R$ 3,46) tem peso baixo de propósito. Valores pequenos arredondados a 2 casas decimais têm poucos dígitos significativos, então o 4º dígito ficaria artificialmente sempre 0 (viés de arredondamento, não de manipulação real). Reduzir o peso dessa escala foi a correção aplicada para que a análise do 3º/4º dígito do conjunto "regular" não desse falso alarme. Se for ajustar os pesos de escala, ter esse efeito em mente.

## frontend/app.py — interface Streamlit

- Duas abas: "✅ Notas Fiscais Regulares" e "⚠️ Notas Fiscais Alteradas".
- Sidebar: slider de quantidade de notas (100-5000, padrão 800) e campo de seed (reprodutibilidade).
- Cada aba renderiza uma grade 2x2 com um gráfico por posição de dígito (1º a 4º), via `render_tab()`. Cada célula mostra:
  - título com o nome da posição (`POSITION_LABELS`, ex. "Primeiro dígito" — nomes escritos por extenso, não "1º Dígito", para soar menos acadêmico);
  - dois `st.metric` lado a lado ("Desvio do padrão" e "Qui-quadrado"), cada um com `help=` mostrando uma explicação em linguagem simples ao passar o mouse — isso evita que o cliente precise perguntar o que as métricas significam;
  - o gráfico (`benford_chart`).
- Mensagem de alerta no fim da aba, baseada no desvio padrão do **1º dígito apenas** (`metrics_por_posicao[1]["std_dev"] > 3`): erro (vermelho) na aba "alterada" se o desvio for alto, sucesso (verde) na aba "regular".
- Expander "Ver notas fiscais geradas" com a tabela completa.

## frontend/charts.py

`benford_chart(observed_pct, expected_pct, title)` monta um gráfico Plotly: barras azuis para o observado, linha vermelha com marcadores para o esperado pela Lei de Benford. Eixo X chamado genericamente de "Dígito" (não hardcoded para "Primeiro dígito" — isso já foi um bug corrigido, ver histórico abaixo).

## Decisões de design e histórico relevante

- **Por que 4 posições de dígito, não só a primeira**: pedido explícito do usuário para tornar a demonstração mais robusta — análises de 2º, 3º e 4º dígito são técnicas reais de auditoria forense (forensic accounting) que complementam a clássica análise do 1º dígito.
- **Por que sem MAD na UI**: usuário pediu para "deixar menos acadêmico" — MAD e desvio padrão medem coisas parecidas (dispersão média da diferença), manter os dois era jargão redundante. MAD continua calculado no backend, só não é exibido.
- **Por que tooltips de ajuda em vez de texto fixo explicando qui-quadrado**: usuário queria entender o que é "Qui" sem poluir a tela com texto técnico permanente — o `help=` do `st.metric` resolve isso (ícone "i", aparece só ao passar o mouse).
- **Bug corrigido**: o eixo X do gráfico estava sempre escrito "Primeiro dígito", independente da posição real sendo exibida (textinho hardcoded em `charts.py`). Corrigido para "Dígito" genérico.
- **Separação backend/frontend**: pedido explícito do usuário, mesmo sendo um app Streamlit (que normalmente não separa front/back). A separação aqui é só organizacional — toda a lógica de dados/matemática fica em `backend/`, toda a apresentação em `frontend/`.
