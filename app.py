import io

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from pubfig import PALETTE, build_publication_fig

st.set_page_config(page_title="Arrhenius 扩散参数对比库", layout="wide")
st.title("🧪 个人材料扩散系数数据库")

R = 8.314


@st.cache_data
def load_data():
    df = pd.read_csv("data.csv")
    df = df.dropna(subset=["tracer", "matrix_group"])
    num_cols = ["D0_v_m2_s", "D0_gb_m2_s", "P0_m3_s", "Q_kJ_mol", "Tmin_K", "Tmax_K"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["tracer", "matrix_group", "matrix", "structure", "channel", "data_type",
              "method", "reference", "doi", "notes"]:
        if c in df.columns:
            df[c] = df[c].fillna("").astype(str).str.strip()
    return df


df = load_data()

left, right = st.columns([7, 3])

# ---------- 左列上部：四级筛选 + 数据类型 ----------
with left:
    st.markdown("#### 🔍 筛选")
    sel_tracers = st.pills("🟡 Tracer（扩散元素）", sorted(df["tracer"].unique()),
                           selection_mode="multi", key="p_tracer")
    dff = df[df["tracer"].isin(sel_tracers)] if sel_tracers else df

    sel_groups = st.pills("🔵 Matrix（体系）", sorted(dff["matrix_group"].unique()),
                          selection_mode="multi", key="p_group")
    if sel_groups:
        dff = dff[dff["matrix_group"].isin(sel_groups)]

    sel_structs = st.pills("🟣 Structure（晶体结构）", sorted(dff["structure"].unique()),
                           selection_mode="multi", key="p_struct")
    if sel_structs:
        dff = dff[dff["structure"].isin(sel_structs)]

    c1, c2 = st.columns(2)
    with c1:
        sel_channels = st.pills("🟠 通道", ["Dv", "Dgb", "P", "IPB"],
                                selection_mode="multi", key="p_channel")
    with c2:
        sel_dtype = st.pills("⚪ 数据类型", ["实验", "计算"],
                             selection_mode="multi", key="p_dtype")
    if sel_channels:
        dff = dff[dff["channel"].isin(sel_channels)]
    if sel_dtype:
        dff = dff[dff["data_type"].isin(sel_dtype)]

    st.caption(f"当前选中 {len(dff)} 条记录（总库 {len(df)} 条）。成分细节见右侧文献表。")

df_filtered = dff

# ---------- 自动轴范围（左右轴等十年跨度） ----------
def auto_exponents(frame):
    d_vals, p_vals = [], []
    for _, row in frame.iterrows():
        t0, t1 = row["Tmin_K"], row["Tmax_K"]
        if pd.isna(t0) or pd.isna(t1):
            continue
        T = np.linspace(t0, t1, 40)
        for col, acc in (("D0_v_m2_s", d_vals), ("D0_gb_m2_s", d_vals), ("P0_m3_s", p_vals)):
            if pd.notna(row[col]):
                acc.extend(row[col] * np.exp(-(row["Q_kJ_mol"] * 1000) / (R * T)))
    def rng(vals, fallback):
        if not vals:
            return fallback
        return int(np.floor(np.log10(min(vals)))), int(np.ceil(np.log10(max(vals))))
    d_lo, d_hi = rng(d_vals, (-25, -15))
    p_lo, p_hi = rng(p_vals, (-30, -20))
    span = max(d_hi - d_lo, p_hi - p_lo) + 1
    def align(lo, hi):
        centre = (lo + hi) / 2.0
        new_hi = int(np.ceil(centre + span / 2.0))
        return new_hi - span, new_hi
    return align(p_lo, p_hi), align(d_lo, d_hi), span

has_p = df_filtered["P0_m3_s"].notna().any() if len(df_filtered) else False
has_d = df_filtered[["D0_v_m2_s", "D0_gb_m2_s"]].notna().any().any() if len(df_filtered) else False
(p_lo_a, p_hi_a), (d_lo_a, d_hi_a), _span = auto_exponents(df_filtered) if len(df_filtered) else (((-30, -19)), ((-25, -14)), 11)

t_max_data = float(df_filtered["Tmax_K"].max()) if len(df_filtered) else 1300.0
t_min_data = float(df_filtered["Tmin_K"].min()) if len(df_filtered) else 500.0

p_lo, p_hi, d_lo, d_hi = p_lo_a, p_hi_a, d_lo_a, d_hi_a  # 默认值，手动模式下被右侧输入覆盖

# ---------- 右列上部：温度与坐标范围 ----------
with right:
    st.markdown("#### 🌡️ 温度范围")
    rc1, rc2 = st.columns(2)
    view_tmax = rc1.number_input("最高温度 (K)", value=float(t_max_data + 100), step=50.0, key="v_tmax")
    view_tmin = rc2.number_input("最低温度 (K)", value=float(max(1.0, t_min_data - 100)), step=50.0, key="v_tmin")
    t_ticks_input = st.text_input("顶部 T 刻度（逗号分隔，可空）", value="", key="v_ticks")
    auto_y = st.checkbox("Y 轴自动范围（左右等跨度）", value=True, key="v_autoy")
    if has_p:
        yc1, yc2 = st.columns(2)
        p_lo = yc1.number_input("P 最小 (10^x)", value=p_lo_a, step=1, key="v_plo", disabled=auto_y)
        p_hi = yc2.number_input("P 最大 (10^x)", value=p_hi_a, step=1, key="v_phi", disabled=auto_y)
    if has_d:
        yc3, yc4 = st.columns(2)
        d_lo = yc3.number_input("D 最小 (10^x)", value=d_lo_a, step=1, key="v_dlo", disabled=auto_y)
        d_hi = yc4.number_input("D 最大 (10^x)", value=d_hi_a, step=1, key="v_dhi", disabled=auto_y)

try:
    t_ticks = [int(float(x.strip())) for x in t_ticks_input.split(",") if x.strip()]
except Exception:
    t_ticks = []

p_range = None if auto_y else (int(p_lo), int(p_hi))
d_range = None if auto_y else (int(d_lo), int(d_hi))
# 探索模式用数值范围：自动时用对齐后的指数
p_lo_e, p_hi_e = (p_lo_a, p_hi_a) if auto_y else (int(p_lo), int(p_hi))
d_lo_e, d_hi_e = (d_lo_a, d_hi_a) if auto_y else (int(d_lo), int(d_hi))

# ---------- 左列下部：Arrhenius 图 ----------
with left:
    st.markdown("#### 📊 Arrhenius 图")
    if len(df_filtered) == 0:
        st.info("没有符合筛选条件的记录，换一下筛选组合试试。")
    elif not sel_tracers and not sel_groups:
        st.info("先在上方选 Tracer 或体系，下方就会画图（不然 300 多条线挤在一起看不清）。")
    else:
        mode = st.radio("绘图模式", ["📈 探索模式", "🖨️ 出版模式"], horizontal=True, key="v_mode")
        x_min, x_max = 10000.0 / view_tmax, 10000.0 / view_tmin
        T_full = np.linspace(view_tmax, view_tmin, 200)
        X_full = 10000.0 / T_full

        if "探索" in mode:
            fig = go.Figure()
            for i, (_, row) in enumerate(df_filtered.iterrows()):
                color = PALETTE[i % len(PALETTE)]
                t0 = row["Tmin_K"] if pd.notna(row["Tmin_K"]) else view_tmin
                t1 = row["Tmax_K"] if pd.notna(row["Tmax_K"]) else view_tmax
                T_exp = np.linspace(t0, t1, 100)
                X_exp = 10000.0 / T_exp
                name = f"{row['tracer']} in {row['matrix_group']} ({row['structure']}, {row['channel']})"
                for col, axis, dash, prefix in (
                        ("D0_v_m2_s", "y2" if (has_p and has_d) else "y", "solid", "Dv"),
                        ("D0_gb_m2_s", "y2" if (has_p and has_d) else "y", "dash", "Dgb"),
                        ("P0_m3_s", "y", "dashdot", "P")):
                    if pd.isna(row[col]):
                        continue
                    Y_full = row[col] * np.exp(-(row["Q_kJ_mol"] * 1000) / (R * T_full))
                    fig.add_trace(go.Scatter(x=X_full, y=Y_full, mode="lines", yaxis=axis,
                                             line=dict(color=color, width=1.2, dash=dash),
                                             opacity=0.3, showlegend=False, hoverinfo="skip"))
                    Y_exp = row[col] * np.exp(-(row["Q_kJ_mol"] * 1000) / (R * T_exp))
                    hover = (f"<b>{prefix}: {name}</b><br>{row['matrix']}<br>"
                             f"Q = {row['Q_kJ_mol']} kJ/mol<br>{prefix}₀ = {row[col]:.3e}<br>"
                             f"{row['reference']}")
                    fig.add_trace(go.Scatter(x=X_exp, y=Y_exp, mode="lines", name=f"{prefix}: {name}",
                                             yaxis=axis, line=dict(color=color, width=3, dash=dash),
                                             hovertemplate=hover))
            layout = dict(hovermode="closest", height=640, plot_bgcolor="white",
                          legend=dict(x=0.01, y=0.01, bgcolor="rgba(255,255,255,0.85)",
                                      bordercolor="black", borderwidth=1),
                          xaxis=dict(title="10000 / T (K⁻¹)", range=[x_min, x_max], showline=True,
                                     linewidth=1, linecolor="black", gridcolor="lightgrey"))
            if has_p:
                layout["yaxis"] = dict(title="P (m³/s)", type="log", range=[p_lo_e, p_hi_e],
                                       showline=True, linewidth=1, linecolor="black", gridcolor="lightgrey")
            if has_d:
                key = "yaxis2" if has_p else "yaxis"
                layout[key] = dict(title="Dv, Dgb (m²/s)", type="log", range=[d_lo_e, d_hi_e],
                                   showline=True, linewidth=1, linecolor="black", gridcolor="lightgrey")
                if has_p:
                    layout[key].update(dict(overlaying="y", side="right"))
            fig.update_layout(**layout)
            st.plotly_chart(fig, use_container_width=True)
        else:
            rows = df_filtered.to_dict("records")
            for r in rows:  # 温区缺失时用显示范围兜底
                if pd.isna(r["Tmin_K"]):
                    r["Tmin_K"] = view_tmin
                if pd.isna(r["Tmax_K"]):
                    r["Tmax_K"] = view_tmax
            fig = build_publication_fig(rows, view_tmin, view_tmax,
                                        p_exp_range=p_range, d_exp_range=d_range,
                                        t_ticks=t_ticks)
            st.pyplot(fig)
            b1, b2 = st.columns(2)
            buf_svg = io.BytesIO(); fig.savefig(buf_svg, format="svg", bbox_inches="tight")
            b1.download_button("📥 下载 SVG（矢量，进 Origin）", buf_svg.getvalue(),
                               "Arrhenius_publication.svg", "image/svg+xml")
            buf_png = io.BytesIO(); fig.savefig(buf_png, format="png", dpi=300, bbox_inches="tight")
            b2.download_button("📥 下载 PNG（300 dpi）", buf_png.getvalue(),
                               "Arrhenius_publication.png", "image/png")

# ---------- 右列下部：文献溯源 ----------
with right:
    st.markdown("#### 📋 文献")
    if len(df_filtered):
        show = df_filtered.copy()
        show["doi_link"] = show["doi"].apply(lambda d: f"https://doi.org/{d}" if d else "")
        st.dataframe(
            show[["reference", "tracer", "matrix", "structure", "channel", "Q_kJ_mol", "doi_link"]],
            use_container_width=True, height=420, hide_index=True,
            column_config={"doi_link": st.column_config.LinkColumn("doi")})
        st.download_button("📥 下载当前筛选 CSV", df_filtered.to_csv(index=False).encode("utf-8-sig"),
                           "arrhenius_filtered.csv", "text/csv")
    else:
        st.caption("无数据")
    with st.expander("查看完整数据表"):
        st.dataframe(df_filtered, use_container_width=True)
