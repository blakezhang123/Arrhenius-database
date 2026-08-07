import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, NullFormatter
import io

st.set_page_config(page_title="Arrhenius 扩散参数对比库", layout="wide")
st.title("🧪 个人材料扩散系数数据库")

@st.cache_data
def load_data():
    df = pd.read_csv("data.csv")
    # 1. 自动丢弃那些连 Tracer 或 Matrix 都没有填的无效空行
    df = df.dropna(subset=['tracer', 'matrix'])
    # 2. 强制将这三列转换为字符串，彻底杜绝 float 混入
    df['tracer'] = df['tracer'].astype(str)
    df['matrix'] = df['matrix'].astype(str)
    df['phase'] = df['phase'].astype(str)
    return df


df = load_data()

st.markdown("### 🔍 第一步：点选元素与基体")

all_tracers = sorted(df['tracer'].unique().tolist())
selected_tracers = st.pills("🟡 1. 选取 Tracer (扩散元素)：", all_tracers, selection_mode="multi")

df_filtered = df.copy()
if selected_tracers:
    df_filtered = df_filtered[df_filtered['tracer'].isin(selected_tracers)]

available_matrices = sorted(df_filtered['matrix'].unique().tolist())
selected_matrices = st.pills("🔵 2. 选取 Matrix (基体材料)：", available_matrices, selection_mode="multi")

if selected_matrices:
    df_filtered = df_filtered[df_filtered['matrix'].isin(selected_matrices)]

available_phases = sorted(df_filtered['phase'].unique().tolist())
selected_phases = st.pills("🟣 3. 选取 Phase (相结构)：", available_phases, selection_mode="multi")

if selected_phases:
    df_filtered = df_filtered[df_filtered['phase'].isin(selected_phases)]

st.markdown("---")
st.markdown("### 📊 第二步：生成 Arrhenius 图")
mode = st.radio("切换绘图引擎", ["📈 探索模式 (动态交互、鼠标悬停显示文献)", "🖨️ 出版模式 (高精度双坐标轴、自动分列双单位)"], horizontal=True)

if len(df_filtered) == 0:
    st.info("👈 请在上方点击按钮，选择你要对比的数据。")
else:
    R = 8.314
    # 智能判断当前选择的数据中包含哪些单位类型
    has_m2 = df_filtered[['D0_v_m2_s', 'D0_gb_m2_s']].notna().any().any()
    has_m3 = df_filtered['P0_m3_s'].notna().any()

    if "探索模式" in mode:
        fig = go.Figure()
        
        for i, (idx, row) in enumerate(df_filtered.iterrows()):
            T = np.linspace(row['Tmin_K'], row['Tmax_K'], 100)
            X = 10000 / T
            base_name = f"{row['tracer']} in {row['matrix']} ({row['phase']})"
            
            # 画 Dv (实线)
            if pd.notna(row['D0_v_m2_s']):
                D = row['D0_v_m2_s'] * np.exp(-(row['Q_kJ_mol'] * 1000) / (R * T))
                hover_text = f"<b>Dv: {base_name}</b><br>Q={row['Q_kJ_mol']} kJ/mol<br>D₀_v={row['D0_v_m2_s']} m²/s<br>Ref: {row['reference']}"
                fig.add_trace(go.Scatter(x=X, y=D, mode='lines', name=f"Dv: {base_name}",
                                         yaxis='y2' if has_m3 and has_m2 else 'y1',
                                         line=dict(width=3, dash='solid'), hovertemplate=hover_text))
            # 画 Dgb (虚线)
            if pd.notna(row['D0_gb_m2_s']):
                D = row['D0_gb_m2_s'] * np.exp(-(row['Q_kJ_mol'] * 1000) / (R * T))
                hover_text = f"<b>Dgb: {base_name}</b><br>Q={row['Q_kJ_mol']} kJ/mol<br>D₀_gb={row['D0_gb_m2_s']} m²/s<br>Ref: {row['reference']}"
                fig.add_trace(go.Scatter(x=X, y=D, mode='lines', name=f"Dgb: {base_name}",
                                         yaxis='y2' if has_m3 and has_m2 else 'y1',
                                         line=dict(width=3, dash='dash'), hovertemplate=hover_text))
            # 画 P (点划线)
            if pd.notna(row['P0_m3_s']):
                P = row['P0_m3_s'] * np.exp(-(row['Q_kJ_mol'] * 1000) / (R * T))
                hover_text = f"<b>P: {base_name}</b><br>Q={row['Q_kJ_mol']} kJ/mol<br>P₀={row['P0_m3_s']} m³/s<br>Ref: {row['reference']}"
                fig.add_trace(go.Scatter(x=X, y=P, mode='lines', name=f"P: {base_name}",
                                         yaxis='y1',
                                         line=dict(width=3, dash='dashdot'), hovertemplate=hover_text))
                                         
        layout_update = dict(xaxis_title="10000 / T (K⁻¹)", hovermode="closest", height=650, plot_bgcolor="white", legend=dict(x=0.01, y=0.01, bgcolor='rgba(255,255,255,0.8)', bordercolor='black', borderwidth=1))
        
        # 动态设置双轴布局
        if has_m3 and has_m2:
            layout_update['yaxis'] = dict(title="P (m³/s)", type="log", showline=True, linewidth=1, linecolor='black')
            layout_update['yaxis2'] = dict(title="Dv, Dgb (m²/s)", type="log", overlaying='y', side='right', showline=True, linewidth=1, linecolor='black')
        elif has_m3:
            layout_update['yaxis'] = dict(title="P (m³/s)", type="log", showline=True, linewidth=1, linecolor='black')
        else:
            layout_update['yaxis'] = dict(title="Dv, Dgb (m²/s)", type="log", showline=True, linewidth=1, linecolor='black')
            
        fig.update_xaxes(showline=True, linewidth=1, linecolor='black', gridcolor='lightgrey')
        fig.update_yaxes(gridcolor='lightgrey')
        fig.update_layout(**layout_update)
        st.plotly_chart(fig, use_container_width=True)

    else:
        # ---- Matplotlib 出版模式 ----
        fig, ax1 = plt.subplots(figsize=(10, 7))
        
        # 智能双轴逻辑映射
        if has_m3 and has_m2:
            ax_left, ax_right = ax1, ax1.twinx()
            ax_P, ax_D = ax_left, ax_right
        elif has_m3 and not has_m2:
            ax_left, ax_right = ax1, None
            ax_P, ax_D = ax_left, None
        elif has_m2 and not has_m3:
            ax_left, ax_right = ax1, None
            ax_P, ax_D = None, ax_left
            
        lines = []
        colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
        
        for i, (idx, row) in enumerate(df_filtered.iterrows()):
            color = colors[i % len(colors)] # 同一文献的一组数据用同一颜色
            T = np.linspace(row['Tmin_K'], row['Tmax_K'], 100)
            X = 10000 / T
            base_label = f"{row['tracer']} in {row['matrix']} ({row['phase']})"
            
            if pd.notna(row['D0_v_m2_s']):
                D = row['D0_v_m2_s'] * np.exp(-(row['Q_kJ_mol'] * 1000) / (R * T))
                l, = ax_D.plot(X, D, label=f"Dv: {base_label}", color=color, linewidth=2.5, linestyle='-')
                lines.append(l)
                
            if pd.notna(row['D0_gb_m2_s']):
                D = row['D0_gb_m2_s'] * np.exp(-(row['Q_kJ_mol'] * 1000) / (R * T))
                l, = ax_D.plot(X, D, label=f"Dgb: {base_label}", color=color, linewidth=2.5, linestyle='--')
                lines.append(l)
                
            if pd.notna(row['P0_m3_s']):
                P = row['P0_m3_s'] * np.exp(-(row['Q_kJ_mol'] * 1000) / (R * T))
                l, = ax_P.plot(X, P, label=f"P: {base_label}", color=color, linewidth=2.5, linestyle='-.')
                lines.append(l)

        # 设置 P 轴样式
        if ax_P is not None:
            ax_P.set_yscale('log')
            ax_P.set_ylabel(r'$P$ (m$^3$/s)', fontsize=16, fontweight='bold', color='black')
            locmin = LogLocator(base=10.0, subs=np.arange(2, 10) * .1, numticks=12)
            ax_P.yaxis.set_minor_locator(locmin)
            ax_P.yaxis.set_minor_formatter(NullFormatter())
            if ax_right is not None and ax_P == ax_left:
                ax_P.tick_params(axis='y', which='both', direction='in', length=6, width=1.5, right=False)
            elif ax_right is None:
                ax_P.tick_params(axis='y', which='both', direction='in', length=6, width=1.5, right=True)
                
        # 设置 D 轴样式
        if ax_D is not None:
            ax_D.set_yscale('log')
            ax_D.set_ylabel(r'$D_v, D_{gb}$ (m$^2$/s)', fontsize=16, fontweight='bold', color='black')
            locmin = LogLocator(base=10.0, subs=np.arange(2, 10) * .1, numticks=12)
            ax_D.yaxis.set_minor_locator(locmin)
            ax_D.yaxis.set_minor_formatter(NullFormatter())
            if ax_right is not None and ax_D == ax_right:
                ax_D.tick_params(axis='y', which='both', direction='in', length=6, width=1.5, left=False)
            elif ax_right is None:
                ax_D.tick_params(axis='y', which='both', direction='in', length=6, width=1.5, right=True)

        ax1.set_xlabel(r'10000 / T (10$^{-4}$ K$^{-1}$)', fontsize=16, fontweight='bold')
        ax1.tick_params(axis='x', which='major', direction='in', length=8, width=1.5, labelsize=14)

        # 严格绑定上方温度轴
        def x_to_t(x): return np.where(x == 0, np.inf, 10000 / x)
        def t_to_x(t): return np.where(t == 0, np.inf, 10000 / t)

        secax = ax1.secondary_xaxis('top', functions=(x_to_t, t_to_x))
        secax.set_xlabel('T (K)', fontsize=16, fontweight='bold', labelpad=10)
        secax.set_xticks([1400, 1373, 1273, 1173, 1073, 973, 873, 773, 673, 500])
        secax.get_xaxis().set_major_formatter(plt.ScalarFormatter())
        secax.tick_params(axis='x', which='major', direction='in', length=8, width=1.5, labelsize=14)
        secax.tick_params(axis='x', which='minor', bottom=False, top=False)

        # 封边加粗
        for ax_ in [ax1, ax_right]:
            if ax_ is not None:
                for spine in ax_.spines.values(): spine.set_linewidth(1.5)

        if lines:
            ax1.legend(lines, [l.get_label() for l in lines], fontsize=13, frameon=True, edgecolor='black')

        st.pyplot(fig)

        buf = io.BytesIO()
        fig.savefig(buf, format="svg", bbox_inches='tight')
        st.download_button(label="📥 下载出版级双轴 SVG 矢量图", data=buf.getvalue(), file_name="Arrhenius_Plot_Pro.svg", mime="image/svg+xml")

st.markdown("---")
st.markdown("### 📋 第三步：当前选中数据的文献溯源")
st.dataframe(df_filtered)