"""Streamlit dashboard for the EGX price-only risk forecasts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from m1_har import (
    HORIZONS,
    MODELS,
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


def test_chart(forecasts: pd.DataFrame) -> go.Figure:
    import plotly.graph_objects as go

    fig = go.Figure()
    for bound, name, fill in [("lo", "Lower bound", None), ("hi", "90% range", "tonexty")]:
        fig.add_trace(go.Scatter(
            x=forecasts["date"], y=100 * forecasts[bound], name=name,
            mode="lines", line={"width": 0}, fill=fill, fillcolor="rgba(79, 150, 225, 0.24)",
            showlegend=bound == "hi", hoverinfo="skip",
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
    model = st.sidebar.selectbox("Forecast model", MODELS)
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
    evaluation = evaluate_ticker(ticker, prices)

    st.header(ticker)
    st.caption(f"{source} · Last usable session {prices.index[-1].date():%Y-%m-%d} · {model}")
    st.subheader("Latest forecast")
    latest = evaluation.latest.loc[evaluation.latest["model"].eq(model)].set_index("horizon")
    for horizon, column in zip(HORIZONS, st.columns(len(HORIZONS))):
        column.markdown(f"**{horizon} trading {'session' if horizon == 1 else 'sessions'}**")
        if horizon in latest.index:
            row = latest.loc[horizon]
            column.write(
                f"Expected move size {row['point']:.2%}, 90% range {row['lo']:.2%}–{row['hi']:.2%}"
            )
        else:
            column.write("Forecast unavailable")
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
    metrics = evaluation.metrics.loc[evaluation.metrics["model"].eq(model)]
    if metrics.empty:
        st.info("No test results are available for this ticker.")
        return
    horizon = st.selectbox("Test horizon (trading sessions)", metrics["horizon"].tolist())
    metric = metrics.loc[metrics["horizon"].eq(horizon)].iloc[0]
    coverage, width, count = st.columns(3)
    coverage.metric("Observed coverage", f"{metric['coverage_90']:.1%}")
    width.metric("Average range width", f"{100 * metric['avg_width']:.2f} pp")
    count.metric("Test forecasts", f"{metric['n_test']:,}")
    forecasts = evaluation.test.loc[
        evaluation.test["model"].eq(model) & evaluation.test["horizon"].eq(horizon)
    ]
    st.plotly_chart(test_chart(forecasts), width="stretch")
    st.caption("The nominal range target is 90%. Observed coverage can vary as market conditions change.")


if __name__ == "__main__":
    main()
