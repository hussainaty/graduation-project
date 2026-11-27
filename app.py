"""Streamlit dashboard for the EGX price-only risk forecasts."""

from __future__ import annotations

from math import isfinite
from typing import TYPE_CHECKING

from m1_har import (
    HORIZONS,
    download_prices,
    evaluate_ticker,
    prepare_prices,
    read_cached_prices,
    read_tickers,
    ticker_filename,
)


if TYPE_CHECKING:
    import pandas as pd
    import plotly.graph_objects as go


def test_chart(forecasts: pd.DataFrame, adaptive: bool = False) -> go.Figure:
    import plotly.graph_objects as go

    fig = go.Figure()
    fields = ["lo_adaptive", "hi_adaptive"] if adaptive else ["lo", "hi"]
    lo, hi = (forecasts[field] for field in fields)
    finite = hi.map(isfinite) & lo.le(hi)
    label = "Adaptive 90% range" if adaptive else "Standard 90% range"
    for bound, name, fill in [(lo, "Lower bound", None), (hi, label, "tonexty")]:
        fig.add_trace(go.Scatter(
            x=forecasts["date"], y=100 * bound.where(finite), name=name,
            mode="lines", line={"width": 0}, fill=fill, fillcolor="rgba(79, 150, 225, 0.24)",
            showlegend=fill is not None, hoverinfo="skip",
        ))
    for series, name, color in [
        ("actual", "Actual move", "#de8533"), ("point", "Point forecast", "#4f96e1"),
    ]:
        fig.add_trace(go.Scatter(
            x=forecasts["date"], y=100 * forecasts[series], name=name,
            mode="lines", line={"color": color, "width": 1.4},
            hovertemplate="%{y:.2f}%<extra>%{fullData.name}</extra>",
        ))
    fig.update_layout(
        xaxis_title="Forecast date", yaxis_title="Absolute log return (%)",
        hovermode="x unified", legend={"orientation": "h", "y": 1.02, "yanchor": "bottom"},
        margin={"t": 30},
    )
    return fig


def main() -> None:
    import plotly.express as px
    import streamlit as st

    st.set_page_config(page_title="EGX Risk Radar", layout="wide")
    st.title("EGX Risk Radar")
    st.caption("Research demo, not investment advice")

    listed = st.sidebar.selectbox("Ticker from watchlist", read_tickers(), index=0)
    custom = st.sidebar.text_input("Or enter a Yahoo Finance ticker", placeholder="XXXX.CA")
    refresh = st.sidebar.checkbox("Download latest Yahoo prices")
    ticker = custom.strip().upper() or listed
    if not ticker:
        st.info("Enter a Yahoo Finance ticker to view forecasts.")
        return
    try:
        ticker_filename(ticker)
    except ValueError as error:
        st.error(str(error))
        return

    try:
        cached = read_cached_prices(ticker)
    except FileNotFoundError:
        cached = None
    except (OSError, KeyError, ValueError) as error:
        st.warning(f"Couldn't read the local price cache for {ticker}. {error}")
        cached = None

    raw = cached
    source = "Local CSV cache"
    if custom.strip() or refresh or cached is None:
        live_download = st.cache_data(ttl=900, show_spinner="Downloading Yahoo Finance prices…")(
            download_prices
        )
        try:
            raw = live_download(ticker)
            source = "Yahoo Finance"
        except Exception as error:
            if cached is None:
                st.error(f"Couldn't download {ticker} from Yahoo Finance. {error}")
                return
            st.warning(f"Yahoo Finance was unavailable for {ticker}. Showing the local CSV cache.")

    try:
        prices, data_issues = prepare_prices(raw)
    except ValueError as error:
        st.error(str(error))
        return
    if prices.empty:
        st.warning(f"{ticker} has no usable price history since 2013.")
        return
    evaluate = st.cache_data(ttl=300, show_spinner="Fitting forecast models…")(evaluate_ticker)
    evaluation = evaluate(ticker, prices)

    horizon = st.sidebar.selectbox("Test horizon (trading sessions)", HORIZONS)
    horizon_metrics = evaluation.metrics.loc[evaluation.metrics["horizon"].eq(horizon)]
    horizon_latest = evaluation.latest.loc[evaluation.latest["horizon"].eq(horizon)]
    models = list(dict.fromkeys([*horizon_metrics["model"], *horizon_latest["model"]]))
    if not models:
        models = evaluation.latest["model"].unique().tolist()
    default = evaluation.best_combinations.get(horizon, "HAR")
    model = (
        st.sidebar.selectbox(
            "Forecast model", models, index=models.index(default) if default in models else 0,
            key=f"forecast_model_{ticker}_{horizon}",
        )
        if models else None
    )

    st.header(ticker)
    st.caption(f"{source} · Last usable session {prices.index[-1].date():%Y-%m-%d}")
    st.subheader("Latest forecast")
    latest = evaluation.latest.loc[evaluation.latest["model"].eq(model)].set_index("horizon")
    for days, column in zip(HORIZONS, st.columns(len(HORIZONS))):
        column.markdown(f"**{days} trading {'session' if days == 1 else 'sessions'}**")
        if days not in latest.index:
            column.write("Forecast unavailable")
            continue
        row = latest.loc[days]
        column.write(
            f"Expected move size {row['point']:.2%}, 90% range {row['lo']:.2%}–{row['hi']:.2%}"
        )
        lo, hi = row["lo_adaptive"], row["hi_adaptive"]
        if lo <= hi:
            interval = f"{lo:.2%}–{hi:.2%}" if isfinite(hi) else "unbounded"
            column.caption(f"Adaptive 90% range {interval}")
        elif hi < lo:
            column.caption("Adaptive interval is empty")
    st.caption("Move sizes use absolute adjusted-close log returns. Horizons count sessions with usable prices.")

    issues = data_issues + evaluation.issues
    if issues:
        with st.expander("Data and forecast notes", expanded=latest.empty):
            for issue in issues:
                st.write(issue)

    st.subheader("Adjusted close")
    price_fig = px.line(prices.reset_index(), x="date", y="Adj Close",
                        labels={"date": "Date", "Adj Close": "Adjusted close"})
    st.plotly_chart(price_fig, width="stretch")

    st.subheader("Held-out test performance")
    metrics = horizon_metrics.loc[horizon_metrics["model"].eq(model)]
    if metrics.empty:
        st.info("No test results are available at this horizon.")
        return

    metric = metrics.iloc[0]
    fixed, adaptive, width, count = st.columns(4)
    fixed.metric("Standard coverage", f"{metric['coverage_90']:.1%}")
    has_adaptive = isfinite(metric["coverage_90_adaptive"])
    adaptive.metric("Adaptive coverage", f"{metric['coverage_90_adaptive']:.1%}" if has_adaptive else "—")
    width.metric("Standard average width", f"{100 * metric['avg_width']:.2f} pp")
    count.metric("Test forecasts", f"{metric['n_test']:,}")

    show_adaptive = False
    if has_adaptive:
        interval = st.radio("Show range", ("Standard", "Adaptive"), horizontal=True)
        show_adaptive = interval == "Adaptive"
        unbounded = metric["unbounded_rate_adaptive"]
        if unbounded > 0:
            st.caption(f"Adaptive ranges were unbounded on {unbounded:.1%} of test dates. Unbounded "
                       "and empty intervals are omitted from the shaded area.")
    else:
        st.caption("Adaptive ranges are evaluated for the top individual model and combination "
                   "chosen before the test period.")
    forecasts = evaluation.test.loc[
        evaluation.test["model"].eq(model) & evaluation.test["horizon"].eq(horizon)
    ]
    st.plotly_chart(test_chart(forecasts, adaptive=show_adaptive), width="stretch")
    st.caption("The nominal coverage target is 90%. Coverage can vary as market conditions change.")


if __name__ == "__main__":
    main()
