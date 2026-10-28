"""Gráficos usados na interface Streamlit."""

import plotly.graph_objects as go


def benford_chart(observed_pct: dict, expected_pct: dict, title: str) -> go.Figure:
    digits = sorted(expected_pct.keys())
    fig = go.Figure()
    fig.add_bar(
        x=digits,
        y=[observed_pct[d] for d in digits],
        name="Observado",
        marker_color="#1f77b4",
    )
    fig.add_bar(
        x=digits,
        y=[expected_pct[d] for d in digits],
        name="Esperado (Lei de Benford)",
        marker_color="#ff7f0e",
    )
    fig.update_layout(
        title=title,
        barmode="group",
        xaxis_title="Dígito",
        yaxis_title="Frequência (%)",
        xaxis=dict(dtick=1),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig
