import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.colors as pcolors
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, NullFormatter
import io

st.set_page_config(page_title="Arrhenius 扩散参数对比库", layout="wide")
st.title("🧪 个人材料扩散系数数据库")

@st.cache_data
def load_data():
    df = pd.read_csv("data.csv")
    df = df.dropna(subset=['tracer', 'matrix'])
    num_cols = ['D0_v_m2_s', 'D0_gb_m2_s', 'P0_m3_s', 'Q_kJ_mol', 'Tmin_K', 'Tmax_K']
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    df['tracer'] = df['tracer'].astype(str).str.strip()
    df['matrix'] = df['matrix'].astype(str).str.strip()
    df['phase'] = df['phase'].astype(str).str.strip()
    return df

df = load_data()

st.markdown("### 🔍 第一步：点选元素与基体")

all_tracers = sorted(df['tracer'].unique().tolist())
selected_tracers = st.pills("🟡 1. 选取 Tracer (扩散元素)：", all_tracers, selection_mode="multi")

df_filtered = df.copy()
if selected_tracers: df_filtered = df_filtered[df_filtered['tracer'].isin(selected_tracers)]

available_matrices = sorted(df_filtered['matrix'].unique().tolist())
selected_matrices = st.pills("🔵 2. 选取 Matrix (基体材料)：", available_matrices, selection_mode="multi")

if selected_matrices: df_filtered = df_filtered[df_filtered['matrix'].isin(selected_matrices)]

available_phases = sorted(df_filtered['phase'].unique().tolist())
selected_phases = st.pills("🟣 3. 选取 Phase (相结构)：", available_phases, selection_mode="multi")

if selected_phases: df_filtered = df_filtered[df_filtered['phase'].isin(selected_phases)]

st.markdown("---")

if len(df_filtered) == 0:
    st.info("👈 请在上方点击按钮，选择你要对比的数据。")
else:
    R = 8.314
    has_m2 = df_filtered[['D0_v_m2_s', 'D0_gb_m2_s']].notna().any().any()
    has_m3 = df_filtered['P0_m3_s'].notna().any()

    t_max_data = df_filtered['Tmax_K'].max()
    t_min_data = df_filtered['Tmin_K'].min()
    
    D_vals, P_vals = [], []
    for _, row in df_filtered.iterrows():
        T = np.linspace(row['Tmin_K'], row['Tmax_K'], 50)
        if pd.notna(row['D0_v_m2_s']): D_vals.extend(row['D0_v_m2_s'] * np.exp(-(row['Q_kJ_mol'] * 1000) / (R * T)))
        if pd.notna(row['D0_gb_m2_s']): D_vals.extend(row['D0_gb_m2_s'] * np.exp(-(row['Q_kJ_mol'] * 1000) / (R * T)))
        if pd.notna(row['P0_m3_s']): P_vals.extend(row['P0_m3_s'] * np.exp(-(row['Q_kJ_mol'] * 1000) / (R * T)))

    y_d_min_data = int(np.floor(np.log10(min(D_vals)))) if D_vals else -20
    y_d_max_data = int(np.ceil(np.log10(max(D_vals)))) if D_vals else -10
    y_p_min_data = int(np.floor(np.log10(min(P_vals)))) if P_vals else -30
    y_p_max_data = int(np.ceil(np.log10(max(P_vals)))) if P_vals else -20

    span_D = y_d_max_data - y_d_min_data
    span_P = y_p_max_data - y_p_min_data
    target_span = max(span_D, span_P) + 2 
    
    def_y_d_max = int(np.ceil((y_d_max_data + y_d_min_data)/2 + target_span/2))
    def_y_d_min = def_y_d_max - target_span
    def_y_p_max = int(np.ceil((y_p_max_data + y_p_min_data)/2 + target_span/2))
    def_y_p_min = def_y_p_max - target_span

    st.markdown("### ⚙️ 第二步：图表显示范围微调")
    
    col_x, col_y = st.columns(2)
    with col_x:
        st.markdown("**1. 横轴显示范围 (直接输入温度)**")
        xc1, xc2 = st.columns(2)
        view_tmax = xc1.number_input("最高温度 (K)", value=float(t_max_data + 100), step=50.0)
        view_tmin = xc2.number_input("最低温度 (K)", value=float(max(1, t_min_data - 100)), step=50.0)
        x_min, x_max = 10000 / view_tmax, 10000 / view_tmin
        t_ticks_input = st.text_input("出版模式顶部特定刻度 (选填，逗号分隔)", value="")
        
    with col_y:
        st.markdown("**2. Y轴对数范围 (填写 10 的指数)**")
        if has_m3:
            yp1, yp2 = st.columns(2)
            y_p_min = yp1.number_input("左侧 P 最小值 (10^x)", value=def_y_p_min, step=1)
            y_p_max = yp2.number_input("左侧 P 最大值 (10^x)", value=def_y_p_max, step=1)
        if has_m2:
            yd1, yd2 = st.columns(2)
            y_d_min = yd1.number_input("右侧 Dv/Dgb 最小值 (10^x)", value=def_y_d_min, step=1)
            y_d_max = yd2.number_input("右侧 Dv/Dgb 最大值 (10^x)", value=def_y_d_max, step=1)

    try:
        t_ticks = [float(x.strip()) for x in t_ticks_input.split(',') if x.strip()]
    except:
        t_ticks = []
    
    if not t_ticks:
        start_h = int(np.floor(view_tmax / 100) * 100)
        end_h = int(np.ceil(view_tmin / 100) * 100)
        t_ticks = list(range(start_h, end_h - 1, -100))

    st.markdown("---")
    st.markdown("### 📊 第三步：生成 Arrhenius 图")
    mode = st.radio("切换绘图引擎", ["📈 探索模式 (动态交互、鼠标悬停显示文献)", "🖨️ 出版模式 (高精度双坐标轴、带有透明外推延长线)"], horizontal=True)

    color_palette = pcolors.qualitative.Plotly
    
    # 核心：生成用于外推的全屏幕温度范围
    T_full = np.linspace(view_tmax, view_tmin, 100)
    X_full = 10000 / T_full

    if "探索模式" in mode:
        fig = go.Figure()
        for i, (idx, row) in enumerate(df_filtered.iterrows()):
            T_exp = np.linspace(row['Tmin_K'], row['Tmax_K'], 100)
            X_exp = 10000 / T_exp
            base_name = f"{row['tracer']} in {row['matrix']} ({row['phase']})"
            line_color = color_palette[i % len(color_palette)]
            
            def add_plotly_traces(val_col, y_axis_name, dash_style, prefix):
                if pd.notna(row[val_col]):
                    # 1. 画全幅透明外推线 (不加图例，不响应悬停)
                    Y_full = row[val_col] * np.exp(-(row['Q_kJ_mol'] * 1000) / (R * T_full))
                    fig.add_trace(go.Scatter(x=X_full, y=Y_full, mode='lines', yaxis=y_axis_name,
                                             line=dict(color=line_color, width=1.5, dash=dash_style),
                                             opacity=0.3, showlegend=False, hoverinfo='skip'))
                    # 2. 画真实实验粗实线
                    Y_exp = row[val_col] * np.exp(-(row['Q_kJ_mol'] * 1000) / (R * T_exp))
                    hover_text = f"<b>{prefix}: {base_name}</b><br>Q={row['Q_kJ_mol']} kJ/mol<br>{prefix}₀={row[val_col]}<br>Ref: {row['reference']}"
                    fig.add_trace(go.Scatter(x=X_exp, y=Y_exp, mode='lines', name=f"{prefix}: {base_name}", 
                                             yaxis=y_axis_name, line=dict(color=line_color, width=3.5, dash=dash_style), 
                                             hovertemplate=hover_text))

            add_plotly_traces('D0_v_m2_s', 'y2' if has_m3 and has_m2 else 'y', 'solid', 'Dv')
            add_plotly_traces('D0_gb_m2_s', 'y2' if has_m3 and has_m2 else 'y', 'dash', 'Dgb')
            add_plotly_traces('P0_m3_s', 'y', 'dashdot', 'P')
                                         
        layout_update = dict(hovermode="closest", height=650, plot_bgcolor="white", legend=dict(x=0.01, y=0.01, bgcolor='rgba(255,255,255,0.8)', bordercolor='black', borderwidth=1))
        layout_update['xaxis'] = dict(title="10000 / T (K⁻¹)", range=[x_min, x_max], showline=True, linewidth=1, linecolor='black', gridcolor='lightgrey')
        
        if has_m3: layout_update['yaxis'] = dict(title="P (m³/s)", type="log", range=[y_p_min, y_p_max], showline=True, linewidth=1, linecolor='black', gridcolor='lightgrey')
        if has_m2:
            y_key = 'yaxis2' if has_m3 else 'yaxis'
            layout_update[y_key] = dict(title="Dv, Dgb (m²/s)", type="log", range=[y_d_min, y_d_max], showline=True, linewidth=1, linecolor='black', gridcolor='lightgrey')
            if has_m3: layout_update[y_key].update(dict(overlaying='y', side='right'))
            
        fig.update_layout(**layout_update)
        st.plotly_chart(fig, use_container_width=True)

    else:
        fig, ax1 = plt.subplots(figsize=(10, 7))
        
        if has_m3 and has_m2: ax_left, ax_right = ax1, ax1.twinx(); ax_P, ax_D = ax_left, ax_right
        elif has_m3 and not has_m2: ax_left, ax_right = ax1, None; ax_P, ax_D = ax_left, None
        elif has_m2 and not has_m3: ax_left, ax_right = ax1, None; ax_P, ax_D = None, ax_left
            
        lines = []
        for i, (idx, row) in enumerate(df_filtered.iterrows()):
            color = color_palette[i % len(color_palette)]
            T_exp = np.linspace(row['Tmin_K'], row['Tmax_K'], 100)
            X_exp = 10000 / T_exp
            base_label = f"{row['tracer']} in {row['matrix']} ({row['phase']})"
            
            def add_mpl_traces(ax_target, val_col, ls, prefix):
                if ax_target is not None and pd.notna(row[val_col]):
                    # 1. 画透明外推线
                    Y_full = row[val_col] * np.exp(-(row['Q_kJ_mol'] * 1000) / (R * T_full))
                    ax_target.plot(X_full, Y_full, color=color, linewidth=1.5, linestyle=ls, alpha=0.3)
                    # 2. 画真实加粗实验线
                    Y_exp = row[val_col] * np.exp(-(row['Q_kJ_mol'] * 1000) / (R * T_exp))
                    l, = ax_target.plot(X_exp, Y_exp, label=f"{prefix}: {base_label}", color=color, linewidth=3, linestyle=ls, alpha=1.0)
                    lines.append(l)

            add_mpl_traces(ax_D, 'D0_v_m2_s', '-', 'Dv')
            add_mpl_traces(ax_D, 'D0_gb_m2_s', '--', 'Dgb')
            add_mpl_traces(ax_P, 'P0_m3_s', '-.', 'P')

        ax1.set_xlim(x_min, x_max)
        if ax_P is not None: ax_P.set_ylim(10**y_p_min, 10**y_p_max)
        if ax_D is not None: ax_D.set_ylim(10**y_d_min, 10**y_d_max)

        if ax_P is not None:
            ax_P.set_yscale('log')
            ax_P.set_ylabel(r'$P$ (m$^3$/s)', fontsize=16, fontweight='bold', color='black')
            ax_P.yaxis.set_minor_locator(LogLocator(base=10.0, subs=np.arange(2, 10) * .1, numticks=12))
            ax_P.yaxis.set_minor_formatter(NullFormatter())
            if ax_right is not None and ax_P == ax_left: ax_P.tick_params(axis='y', which='both', direction='in', length=6, width=1.5, right=False)
            elif ax_right is None: ax_P.tick_params(axis='y', which='both', direction='in', length=6, width=1.5, right=True)
                
        if ax_D is not None:
            ax_D.set_yscale('log')
            ax_D.set_ylabel(r'$D_v, D_{gb}$ (m$^2$/s)', fontsize=16, fontweight='bold', color='black')
            ax_D.yaxis.set_minor_locator(LogLocator(base=10.0, subs=np.arange(2, 10) * .1, numticks=12))
            ax_D.yaxis.set_minor_formatter(NullFormatter())
            if ax_right is not None and ax_D == ax_right: ax_D.tick_params(axis='y', which='both', direction='in', length=6, width=1.5, left=False)
            elif ax_right is None: ax_D.tick_params(axis='y', which='both', direction='in', length=6, width=1.5, right=True)

        ax1.set_xlabel(r'10000 / T (10$^{-4}$ K$^{-1}$)', fontsize=16, fontweight='bold')
        ax1.tick_params(axis='x', which='major', direction='in', length=8, width=1.5, labelsize=14)

        secax = ax1.secondary_xaxis('top', functions=(lambda x: np.where(x==0, np.inf, 10000/x), lambda t: np.where(t==0, np.inf, 10000/t)))
        secax.set_xlabel('T (K)', fontsize=16, fontweight='bold', labelpad=10)
        secax.set_xticks(t_ticks)
        secax.get_xaxis().set_major_formatter(plt.ScalarFormatter())
        secax.tick_params(axis='x', which='major', direction='in', length=8, width=1.5, labelsize=14)
        secax.tick_params(axis='x', which='minor', bottom=False, top=False)

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
st.markdown("### 📋 第四步：当前选中数据的文献溯源")
st.dataframe(df_filtered)