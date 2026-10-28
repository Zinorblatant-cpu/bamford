"""Interface Streamlit: duas telas comparando notas fiscais regulares e alteradas
com a distribuição esperada pela Lei de Benford."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from backend.benford import deviation_metrics, digit_distribution, expected_distribution
from backend.data_generator import generate_altered_invoices, generate_compliant_invoices
from charts import benford_chart

_CSV_GOLD = Path(__file__).resolve().parent.parent / "GoldUSD.csv"
_CSV_CARS = Path(__file__).resolve().parent.parent / "used_car_price_prediction_1M-selected-columns.csv"
_CSV_PRODUCTS = Path(__file__).resolve().parent.parent / "products.csv"


@st.cache_data
def load_gold():
    return pd.read_csv(_CSV_GOLD)


@st.cache_data
def load_cars():
    return pd.read_csv(_CSV_CARS)


@st.cache_data
def load_products():
    return pd.read_csv(_CSV_PRODUCTS)

st.set_page_config(page_title="Lei de Benford - Notas Fiscais", layout="wide")

st.title("Lei de Benford aplicada a Notas Fiscais")
st.caption("Compare notas fiscais normais com notas que apresentam indícios de alteração.")

with st.sidebar:
    st.header("Configurações")
    n_invoices = st.slider("Quantidade de notas fiscais", min_value=100, max_value=5000, value=800, step=100)
    seed = st.number_input("Seed (reprodutibilidade)", min_value=0, value=42, step=1)
    st.markdown("---")
    st.caption("Os dados são gerados artificialmente apenas para fins de demonstração.")

POSITION_LABELS = {1: "Primeiro dígito", 2: "Segundo dígito", 3: "Terceiro dígito", 4: "Quarto dígito"}

DESVIO_HELP = (
    "O quanto, em média, os números se afastam do padrão natural da Lei de Benford. "
    "Perto de 0 = números naturais. Quanto maior, mais incomum."
)
QUI_HELP = (
    "Qui-quadrado: um teste estatístico que resume, em um único número, a diferença "
    "entre os números observados e o esperado pela Lei de Benford. Quanto maior o "
    "valor, mais forte é o indício de que os números foram manipulados."
)


def render_tab(df, value_col: str = "valor", alerta_se_alto_desvio=None, expander_label: str = "Ver dados"):
    metrics_por_posicao = {}

    for linha in ((1, 2), (3, 4)):
        cols = st.columns(2)
        for col, position in zip(cols, linha):
            observed_pct = digit_distribution(df[value_col], position=position)[1]
            expected_pct = expected_distribution(position)
            metrics = deviation_metrics(observed_pct, expected_pct)
            metrics_por_posicao[position] = metrics

            with col:
                st.markdown(f"**{POSITION_LABELS[position]}**")
                metric_col1, metric_col2 = st.columns(2)
                metric_col1.metric("Desvio do padrão", f"{metrics['std_dev']:.2f} p.p.", help=DESVIO_HELP)
                metric_col2.metric("Qui-quadrado", f"{metrics['chi_square']:.2f}", help=QUI_HELP)
                fig = benford_chart(observed_pct, expected_pct, POSITION_LABELS[position])
                st.plotly_chart(fig, use_container_width=True)

    std_dev_1o_digito = metrics_por_posicao[1]["std_dev"]
    if alerta_se_alto_desvio is True and std_dev_1o_digito > 3:
        st.error("⚠️ Esses números fogem do padrão esperado — isso pode indicar que foram alterados.")
    elif alerta_se_alto_desvio is False:
        st.success("✅ Os números parecem naturais, dentro do padrão esperado.")
    elif alerta_se_alto_desvio is None:
        if std_dev_1o_digito <= 3:
            st.success("✅ Os preços seguem o padrão esperado pela Lei de Benford.")
        else:
            st.warning("⚠️ Os preços fogem do padrão esperado pela Lei de Benford.")

    with st.expander(expander_label):
        st.dataframe(df, use_container_width=True)


tab_regular, tab_alterada, tab_ouro, tab_carros, tab_products = st.tabs(
    ["✅ Notas Fiscais Regulares", "⚠️ Notas Fiscais Alteradas", "🥇 Ouro (Dados Reais)", "🚗 Preço de Carros (Dados Reais)", "🛒 Produtos (Dados Reais)"]
)

with tab_regular:
    df_regular = generate_compliant_invoices(n=n_invoices, seed=seed)
    render_tab(df_regular, value_col="valor", alerta_se_alto_desvio=False, expander_label="Ver notas fiscais geradas")

with tab_alterada:
    df_alterada = generate_altered_invoices(n=n_invoices, seed=seed)
    render_tab(df_alterada, value_col="valor", alerta_se_alto_desvio=True, expander_label="Ver notas fiscais geradas")

with tab_ouro:
    st.caption("Preços históricos de fechamento do ouro em USD (GoldUSD.csv) — dados reais.")
    render_tab(load_gold(), value_col="Close", alerta_se_alto_desvio=None, expander_label="Ver dados históricos do ouro")

with tab_carros:
    st.caption("Preços de carros usados — 1.005.000 registros reais.")
    render_tab(load_cars(), value_col="Price", alerta_se_alto_desvio=None, expander_label="Ver dados de preços de carros")

with tab_products:
    st.caption("Preços de produtos — 1.000 registros reais.")
    render_tab(load_products(), value_col="price", alerta_se_alto_desvio=None, expander_label="Ver dados de produtos")
