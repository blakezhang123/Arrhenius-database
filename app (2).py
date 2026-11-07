import io
import os

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
    # v3: 数据文件改用 data.xlsx（「全部数据」页，主表口径 + elem/matrix_group/
    # structure 三列）。在 Excel 里改完保存、替换这个文件即可，程序自动映射成
    # 页面用的列。data.xlsx 不在时回退到旧版 data.csv（app 列口径）。
    if os.path.exists("data.xlsx"):
        raw = pd.read_excel("data.xlsx", sheet_name="全部数据")
        df = pd.DataFrame(index=raw.index)
        if "elem" in raw.columns and raw["elem"].fillna("").astype(str).str.strip().any():
            df["tracer"] = raw["elem"].fillna("").astype(str).str.strip()
        else:
            df["tracer"] = (raw["tracer"].fillna("").astype(str)
                            .str.replace(r"^\d+m?", "", regex=True).str.strip())
        df["matrix_group"] = raw["matrix_group"].fillna("").astype(str).str.strip() \
            if "matrix_group" in raw.columns else ""
        df["matrix"] = raw["matrix"].fillna("").astype(str).str.strip()
        df["structure"] = raw["structure"].fillna("").astype(str).str.strip() \
            if "structure" in raw.columns else ""
        df["channel"] = raw["channel"].fillna("").astype(str).str.strip()
        d0 = pd.to_numeric(raw["D0_value"], errors="coerce")
        df["D0_v_m2_s"] = d0.where(df["channel"] == "Dv")
        df["D0_gb_m2_s"] = d0.where(df["channel"] == "Dgb")
        df["P0_m3_s"] = d0.where(df["channel"].isin(["P", "IPB"]))
        for c in ["Q_kJ_mol", "Tmin_K", "Tmax_K"]:
            df[c] = pd.to_numeric(raw[c], errors="coerce")
        df["method"] = raw["method"].fillna("").astype(str).str.strip() \
            if "method" in raw.columns else ""
        calc = df["method"].str.contains(
            r"DFT|MD|first-principles|Monte Carlo|ab initio", case=False, regex=True)
        df["data_type"] = np.where(calc, "计算", "实验")

        def _ref(a, y):
            a = str(a).strip()
            if a in ("", "nan"):
                return ""
            try:
                y = str(int(float(y)))
            except Exception:
                y = str(y).strip()
            return f"{a} et al. ({y})" if y else a

        df["reference"] = [_ref(a, y) for a, y in zip(raw["first_author"], raw["year"])] \
            if "first_author" in raw.columns else ""
        df["doi"] = raw["doi"].fillna("").astype(str).str.strip() \
            if "doi" in raw.columns else ""
        df["notes"] = raw["notes"].fillna("").astype(str) \
            if "notes" in raw.columns else ""
    else:
        df = pd.read_csv("data.csv")
        num_cols = ["D0_v_m2_s", "D0_gb_m2_s", "P0_m3_s", "Q_kJ_mol", "Tmin_K", "Tmax_K"]
        for c in num_cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        for c in ["tracer", "matrix_group", "matrix", "structure", "channel", "data_type",
                  "method", "reference", "doi", "notes"]:
            if c in df.columns:
                df[c] = df[c].fillna("").astype(str).str.strip()
    df = df.replace({"tracer": {"": np.nan}, "matrix_group": {"": np.nan}})
    df = df.dropna(subset=["tracer", "matrix_group"]).reset_index(drop=True)
    df["rid"] = range(len(df))  # v3: 稳定行号，供勾选/高亮跨重跑对照
    return df


df = load_data()

# v3: 勾选集（None = 画全部筛选结果）与高亮记录，存在 session_state 里
if "checked_rids" not in st.session_state:
    st.session_state["checked_rids"] = None
if "hl_rid" not in st.session_state:
    st.session_state["hl_rid"] = None
if "prev_checked" not in st.session_state:
    st.session_state["prev_checked"] = None

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

# v3: 实际画图的集合 = 筛选结果 ∩ 勾选集（未勾选时 = 全部筛选结果）
checked = st.session_state["checked_rids"]
if checked:
    df_plot = df_filtered[df_filtered["rid"].isin(checked)]
    if len(df_plot) == 0:
        df_plot = df_filtered
else:
    df_plot = df_filtered
hl_rid = st.session_state["hl_rid"]

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

has_p = df_plot["P0_m3_s"].notna().any() if len(df_plot) else False
has_d = df_plot[["D0_v_m2_s", "D0_gb_m2_s"]].notna().any().any() if len(df_plot) else False
(p_lo_a, p_hi_a), (d_lo_a, d_hi_a), _span = auto_exponents(df_plot) if len(df_plot) else (((-30, -19)), ((-25, -14)), 11)

t_max_data = float(df_plot["Tmax_K"].max()) if len(df_plot) else 1300.0
t_min_data = float(df_plot["Tmin_K"].min()) if len(df_plot) else 500.0

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
    if len(df_plot) == 0:
        st.info("没有符合筛选条件的记录，换一下筛选组合试试。")
    elif not sel_tracers and not sel_groups:
        st.info("先在上方选 Tracer 或体系，下方就会画图（不然上千条线挤在一起看不清）。")
    else:
        mode = st.radio("绘图模式", ["📈 探索模式", "🖨️ 出版模式"], horizontal=True, key="v_mode")
        x_min, x_max = 10000.0 / view_tmax, 10000.0 / view_tmin
        T_full = np.linspace(view_tmax, view_tmin, 200)
        X_full = 10000.0 / T_full

        if "探索" in mode:
            fig = go.Figure()
            trace_owner = []  # v3: 每条 trace 对应的 rid，供点图高亮反查
            hl_active = hl_rid is not None and (df_plot["rid"] == hl_rid).any()
            for i, (_, row) in enumerate(df_plot.iterrows()):
                color = PALETTE[i % len(PALETTE)]
                is_hl = hl_active and row["rid"] == hl_rid
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
                                             opacity=0.10 if (hl_active and not is_hl) else 0.3,
                                             showlegend=False, hoverinfo="skip"))
                    trace_owner.append(row["rid"])
                    Y_exp = row[col] * np.exp(-(row["Q_kJ_mol"] * 1000) / (R * T_exp))
                    hover = (f"<b>{prefix}: {name}</b><br>{row['matrix']}<br>"
                             f"Q = {row['Q_kJ_mol']} kJ/mol<br>{prefix}₀ = {row[col]:.3e}<br>"
                             f"{row['reference']}")
                    fig.add_trace(go.Scatter(x=X_exp, y=Y_exp, mode="lines",
                                             name=("★ " if is_hl else "") + f"{prefix}: {name}",
                                             yaxis=axis,
                                             line=dict(color=color,
                                                       width=5 if is_hl else 3, dash=dash),
                                             opacity=0.35 if (hl_active and not is_hl) else 1.0,
                                             hovertemplate=hover))
                    trace_owner.append(row["rid"])
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
            # v3: 点图上的线 -> 高亮对应记录（selection 事件回传 curveNumber）
            plot_state = st.plotly_chart(fig, width="stretch", key="arr_plot",
                                         on_select="rerun", selection_mode="points")
            try:
                pts = plot_state.selection.points
            except Exception:
                pts = []
            if pts:
                cn = pts[0].get("curveNumber")
                if cn is not None and 0 <= cn < len(trace_owner):
                    new_hl = int(trace_owner[cn])
                    if new_hl != st.session_state["hl_rid"]:
                        st.session_state["hl_rid"] = new_hl
                        st.rerun()
            st.caption("点图上的线可高亮对应记录（见右侧文献表上方）；在文献表里点选行 = 只画勾选的记录。")
        else:
            rows = df_plot.to_dict("records")
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

# ---------- 右列下部：高亮详情 + 文献溯源 ----------
with right:
    # v3: 高亮记录详情卡（点曲线或在表中新勾一行都会更新到这里）
    if hl_rid is not None and (df_filtered["rid"] == hl_rid).any():
        hr = df_filtered[df_filtered["rid"] == hl_rid].iloc[0]
        d0txt = ""
        for col, lab in (("D0_v_m2_s", "Dv₀"), ("D0_gb_m2_s", "Dgb₀"), ("P0_m3_s", "P₀")):
            if pd.notna(hr[col]):
                d0txt = f"{lab} = {hr[col]:.3e} {'m³/s' if lab == 'P₀' else 'm²/s'}"
        st.markdown("#### ⭐ 高亮记录")
        st.info(f"**{hr['reference']}**\n\n"
                f"{hr['tracer']} in {hr['matrix']}（{hr['structure']}，{hr['channel']}）\n\n"
                f"Q = {hr['Q_kJ_mol']} kJ/mol · {d0txt} · 温区 {hr['Tmin_K']}–{hr['Tmax_K']} K"
                + (f"\n\n[doi.org/{hr['doi']}]" if hr["doi"] else ""))
        if st.button("清除高亮", key="clr_hl"):
            st.session_state["hl_rid"] = None
            st.rerun()
    st.markdown("#### 📋 文献")
    if len(df_filtered):
        show = df_filtered.copy()
        show["doi_link"] = show["doi"].apply(lambda d: f"https://doi.org/{d}" if d else "")
        # v3: 表格点选（可多选）= 勾选集；不选 = 画全部筛选结果
        lit_state = st.dataframe(
            show[["reference", "tracer", "matrix", "structure", "channel", "Q_kJ_mol", "doi_link"]],
            width="stretch", height=420, hide_index=True,
            column_config={"doi_link": st.column_config.LinkColumn("doi")},
            on_select="rerun", selection_mode="multi-row", key="lit_sel")
        try:
            sel_rows = list(lit_state.selection.rows)
        except Exception:
            sel_rows = []
        new_checked = None
        if sel_rows:
            valid = [p for p in sel_rows if 0 <= p < len(show)]
            if valid:
                new_checked = set(int(x) for x in show.iloc[valid]["rid"])
        if new_checked != st.session_state["checked_rids"]:
            prev = st.session_state["prev_checked"] or set()
            added = (new_checked or set()) - prev
            st.session_state["checked_rids"] = new_checked
            st.session_state["prev_checked"] = new_checked
            if added:  # v3: 新勾上的一行同时设为高亮（行 -> 图）
                st.session_state["hl_rid"] = int(sorted(added)[-1])
            st.rerun()
        n_checked = len(df_plot) if checked else 0
        st.caption("在表里点选行（可多选）= 只画这些记录；不选 = 画全部筛选结果。"
                   + (f"当前勾选后画图 {len(df_plot)} 条。" if checked else ""))
        st.download_button("📥 下载当前筛选 CSV", df_filtered.to_csv(index=False).encode("utf-8-sig"),
                           "arrhenius_filtered.csv", "text/csv")
    else:
        st.caption("无数据")
    with st.expander("查看完整数据表"):
        st.dataframe(df_filtered, width="stretch")
