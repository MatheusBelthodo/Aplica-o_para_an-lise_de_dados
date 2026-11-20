# Pipeline de Dados – Fintech

Projeto em Python para cumprir os requisitos do exercício: leitura dos arquivos CSV, limpeza e transformação dos dados de transações, filtro vetorizado com operadores bitwise, tabela dinâmica por risco, detecção de possíveis anomalias por Z-Score e gráfico com Matplotlib usando a API orientada a objetos.

## 1. Arquivos do projeto

- `criar_dados.py`: script fornecido pelo professor para gerar `transacoes.csv` e `cotacoes.csv`.
- `main.py`: aplicação principal com o processamento dos dados e geração dos resultados.
- `requirements.txt`: bibliotecas necessárias.
- `saida/`: pasta criada automaticamente com os CSVs tratados, tabelas e gráfico.

## 2. Como executar no Windows

Abra o terminal na pasta do projeto e execute:

```bash
py -m pip install -r requirements.txt
py criar_dados.py
py main.py
```

O primeiro script cria os arquivos de entrada. O segundo processa os dados e cria a pasta `saida`.

## 3. Resultados gerados

- `saida/transacoes_tratadas.csv`: dados limpos, com plataforma, dia da semana, mês e fuso horário.
- `saida/transacoes_filtradas_setembro.csv`: setembro, estado SP ou RJ e valor acima de R$ 5.000.
- `saida/tabela_dinamica_risco.csv`: soma do valor por mês e nível de risco, com totais.
- `saida/transacoes_anomalas_zscore.csv`: possíveis anomalias com Z-Score maior que 2,5.
- `saida/grafico_transacoes.png`: total diário e média móvel de 7 dias.

## 4. Níveis de risco

O enunciado enviado informa explicitamente `C100 = Baixo` e `C101 = Alto`, mas não mostra os níveis de C102, C103 e C104. Por isso, o código classifica esses clientes como `Não classificado`, sem inventar categorias. Se a atividade ou o professor fornecer os níveis restantes, complete o dicionário `RISCO_DICT` no início de `main.py`.

## 5. Observações técnicas

- `transacoes.csv` é lido com `encoding="latin1"`, conforme solicitado.
- Valores ausentes de `valor` são preenchidos pela mediana do estado; existe um fallback para a mediana geral caso algum estado não tenha nenhum valor válido.
- `data_transacao` é convertida para datetime e localizada em `America/Sao_Paulo`.
- O filtro usa `&` e `|` de forma vetorizada.
- O Z-Score é calculado por estado sem laços `for`; são selecionados registros com `Z > 2.5`, conforme a desigualdade do enunciado.
- `cotacoes.csv` é lido em UTF-8 e seu total de registros e cotações ausentes é informado. O enunciado enviado não especifica uma transformação, junção ou cálculo adicional para as cotações, então o código não inventa essas operações.

## 6. Enviar para o GitHub

Crie um repositório no GitHub. Depois, no terminal dentro da pasta do projeto:

```bash
git init
git add .
git commit -m "Adiciona pipeline de dados fintech"
git branch -M main
git remote add origin URL_DO_SEU_REPOSITORIO
git push -u origin main
```

Substitua `URL_DO_SEU_REPOSITORIO` pela URL HTTPS do repositório criado.
