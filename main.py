from pathlib import Path
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR
OUTPUT_DIR = BASE_DIR / "saida"
TIMEZONE = "America/Sao_Paulo"

# O enunciado informa explicitamente apenas estes dois níveis.
# Complete C102, C103 e C104 com os níveis fornecidos pelo professor,
# caso exista uma tabela complementar de risco.
RISCO_DICT = {
    "C100": "Baixo",
    "C101": "Alto",
    # "C102": "Médio",
    # "C103": "Baixo",
    # "C104": "Alto",
}

COLUNAS_TRANSACOES = {
    "id_cliente",
    "data_transacao",
    "valor",
    "origem",
    "estado_cliente",
}


def carregar_transacoes(caminho: Path) -> pd.DataFrame:
    """Carrega transacoes.csv usando a codificação legada latin1."""
    if not caminho.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho}\n"
            "Execute primeiro: python criar_dados.py"
        )

    df = pd.read_csv(caminho, encoding="latin1")
    faltantes = COLUNAS_TRANSACOES.difference(df.columns)
    if faltantes:
        raise ValueError(
            "O arquivo transacoes.csv não possui as colunas obrigatórias: "
            + ", ".join(sorted(faltantes))
        )

    # Imputa NaN de valor pela mediana do respectivo estado.
    medianas_por_estado = df.groupby("estado_cliente")["valor"].transform("median")
    df["valor"] = df["valor"].fillna(medianas_por_estado)

    # Fallback para um estado que eventualmente tenha todos os valores ausentes.
    # No CSV gerado pelo exercício, os estados possuem valores válidos.
    if df["valor"].isna().any():
        mediana_geral = df["valor"].median()
        df["valor"] = df["valor"].fillna(mediana_geral)

    # Primeiro converte para datetime64[ns], depois aplica o fuso solicitado.
    datas = pd.to_datetime(df["data_transacao"], errors="coerce")
    if datas.isna().any():
        quantidade = int(datas.isna().sum())
        raise ValueError(f"Existem {quantidade} datas inválidas em data_transacao.")
    df["data_transacao"] = datas.dt.tz_localize(TIMEZONE)

    # Coluna fixa solicitada para rastreabilidade.
    df["plataforma"] = "Mobile"

    # Campos temporais derivados usando o acessor .dt.
    dias = {
        0: "Segunda-feira",
        1: "Terça-feira",
        2: "Quarta-feira",
        3: "Quinta-feira",
        4: "Sexta-feira",
        5: "Sábado",
        6: "Domingo",
    }
    df["dia_semana"] = df["data_transacao"].dt.dayofweek.map(dias)
    df["mes"] = df["data_transacao"].dt.month

    # Descarta duplicatas mantendo a primeira ocorrência.
    quantidade_antes = len(df)
    df = df.drop_duplicates(keep="first").copy()
    quantidade_removida = quantidade_antes - len(df)
    print(f"Duplicatas removidas: {quantidade_removida}")

    return df


def carregar_cotacoes(caminho: Path) -> pd.DataFrame | None:
    """Lê cotacoes.csv (UTF-8); o enunciado não especifica transformações extras."""
    if not caminho.exists():
        print("Aviso: cotacoes.csv não encontrado; somente transações serão processadas.")
        return None

    cotacoes = pd.read_csv(caminho, encoding="utf-8")
    colunas_esperadas = {"data", "cotacao_usd", "volume_negociado"}
    faltantes = colunas_esperadas.difference(cotacoes.columns)
    if faltantes:
        raise ValueError(
            "O arquivo cotacoes.csv não possui as colunas esperadas: "
            + ", ".join(sorted(faltantes))
        )

    cotacoes["data"] = pd.to_datetime(cotacoes["data"], errors="coerce")
    print(
        "Cotações carregadas: "
        f"{len(cotacoes)} registros; "
        f"{int(cotacoes['cotacao_usd'].isna().sum())} cotações USD ausentes."
    )
    return cotacoes


def filtrar_transacoes_setembro(df: pd.DataFrame) -> pd.DataFrame:
    """Filtra setembro, SP ou RJ e valor acima de R$ 5.000 usando bitwise."""
    filtro_estado = (df["estado_cliente"] == "SP") | (df["estado_cliente"] == "RJ")
    filtro_mes = df["data_transacao"].dt.month == 9
    filtro_valor = df["valor"] > 5000
    filtro_final = filtro_mes & filtro_estado & filtro_valor
    return df.loc[filtro_final].copy()


def criar_tabela_dinamica(df: pd.DataFrame) -> pd.DataFrame:
    """Agrupa a soma do valor por mês e nível de risco, incluindo totais."""
    dados = df.copy()
    dados["nivel_risco"] = dados["id_cliente"].map(RISCO_DICT).fillna("Não classificado")

    tabela = pd.pivot_table(
        dados,
        index="mes",
        columns="nivel_risco",
        values="valor",
        aggfunc="sum",
        fill_value=0,
        margins=True,
        margins_name="Total",
    )
    return tabela


def detectar_anomalias_zscore(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula Z-Score vetorizado por estado e seleciona Z > 2.5."""
    resultado = df.copy()
    grupos = resultado.groupby("estado_cliente")["valor"]
    medias = grupos.transform("mean")
    desvios = grupos.transform(lambda serie: serie.std(ddof=0))

    # Em grupos com desvio zero, atribui Z-Score 0 para evitar divisão por zero.
    z_score = (resultado["valor"] - medias) / desvios.replace(0, np.nan)
    resultado["z_score"] = z_score.replace([np.inf, -np.inf], np.nan).fillna(0)

    anomalias = resultado.loc[resultado["z_score"] > 2.5].copy()
    return anomalias


def gerar_grafico_transacoes(df: pd.DataFrame, caminho_saida: Path) -> None:
    """Gera gráfico de total diário e média móvel de 7 dias com Matplotlib OO."""
    total_diario = (
        df.set_index("data_transacao")["valor"]
        .resample("D")
        .sum()
        .sort_index()
    )
    media_movel_7_dias = total_diario.rolling(7).mean()

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(total_diario.index, total_diario.values, label="Total diário de transações")
    ax.plot(
        media_movel_7_dias.index,
        media_movel_7_dias.values,
        label="Média móvel de 7 dias",
        linewidth=2,
    )
    ax.set_ylim(bottom=0)
    ax.set_title("Desempenho diário das transações financeiras")
    ax.set_xlabel("Data da transação")
    ax.set_ylabel("Valor total (R$)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(caminho_saida, dpi=150, bbox_inches="tight")
    plt.close(fig)


def salvar_resultados(
    df: pd.DataFrame,
    filtradas: pd.DataFrame,
    anomalias: pd.DataFrame,
    tabela: pd.DataFrame,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_DIR / "transacoes_tratadas.csv", index=False, encoding="utf-8-sig")
    filtradas.to_csv(
        OUTPUT_DIR / "transacoes_filtradas_setembro.csv",
        index=False,
        encoding="utf-8-sig",
    )
    anomalias.to_csv(
        OUTPUT_DIR / "transacoes_anomalas_zscore.csv",
        index=False,
        encoding="utf-8-sig",
    )
    tabela.to_csv(OUTPUT_DIR / "tabela_dinamica_risco.csv", encoding="utf-8-sig")
    gerar_grafico_transacoes(df, OUTPUT_DIR / "grafico_transacoes.png")


def main() -> int:
    print("=== PIPELINE DE DADOS FINTECH ===")
    try:
        cotacoes = carregar_cotacoes(DATA_DIR / "cotacoes.csv")
        df = carregar_transacoes(DATA_DIR / "transacoes.csv")

        filtradas = filtrar_transacoes_setembro(df)
        tabela = criar_tabela_dinamica(df)
        anomalias = detectar_anomalias_zscore(df)

        salvar_resultados(df, filtradas, anomalias, tabela)

        print("\n=== RESUMO DA EXECUÇÃO ===")
        print(f"Transações tratadas: {len(df)}")
        print(f"Transações filtradas (setembro, SP/RJ, > R$ 5.000): {len(filtradas)}")
        print(f"Possíveis anomalias (Z-Score > 2,5): {len(anomalias)}")
        print(f"Registros de cotações carregados: {0 if cotacoes is None else len(cotacoes)}")
        print("\nTabela dinâmica por mês e nível de risco:")
        print(tabela)
        print(f"\nArquivos e gráfico salvos em: {OUTPUT_DIR}")
        return 0

    except (FileNotFoundError, ValueError, KeyError) as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
