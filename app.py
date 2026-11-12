import io
import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from pubfig import PALETTE, build_publication_fig

# ---------- v4: 三语界面 (Deutsch / English / 中文) ----------
# 界面语言只存 session_state["lang"]，切换不影响任何筛选状态；
# data.xlsx 已全英文化，程序内部的分类/类型一律用英文代码，
# 显示时再按当前语言翻译。出版图始终英文（期刊惯例，见 pubfig.py）。
STR = {
    "en": {
        "page_title": "Arrhenius Diffusion Parameter Database",
        "title": "🧪 Materials Diffusion Coefficient Database",
        "current": "Current selection",
        "s_elem": "Element", "s_matrix": "Matrix", "s_structure": "Structure",
        "s_channel": "Channel", "s_type": "Type",
        "all": "All", "clear": "✖ Clear selection",
        "tracer_h": "🟡 Tracer (diffusing element) — click the periodic table; blank = not in database",
        "records_unit": "records",
        "h_isotope": "hydrogen isotope",
        "elem_search": "🔎 Element quick search (type a symbol; kept in sync with the periodic table)",
        "matrix_h": "🔵 Matrix (system) — four categories",
        "cat_pure": "Pure elements", "cat_alloys": "Alloys",
        "cat_hea": "High-entropy", "cat_other": "Other & amorphous",
        "matrix_search": "🔎 Matrix quick search (type a keyword; kept in sync with the four columns above)",
        "struct_h": "🟣 Structure (crystal structure)",
        "channel": "🟠 Channel", "dtype": "⚪ Data type",
        "dtype_experiment": "Experimental", "dtype_calculation": "Calculation",
        "count_caption": "Currently {n} records selected (database total: {total}). See the literature table on the right for composition details.",
        "temp_h": "🌡️ Temperature range",
        "tmax": "Max. temperature (K)", "tmin": "Min. temperature (K)",
        "tticks": "Top T ticks (comma-separated, may be empty)",
        "autoy": "Automatic Y range (equal span on both axes)",
        "p_min": "P min (10^x)", "p_max": "P max (10^x)",
        "d_min": "D min (10^x)", "d_max": "D max (10^x)",
        "plot_h": "📊 Arrhenius plot",
        "no_records": "No records match the current filters — try a different combination.",
        "pick_first": "Select a tracer or a matrix above and the plot will appear here (otherwise over a thousand lines would overlap).",
        "mode": "Plot mode", "mode_explore": "📈 Explore", "mode_pub": "🖨️ Publication",
        "plot_caption": "Click a line in the plot to highlight the corresponding record (see above the literature table on the right); selecting rows in the table plots only the selected records.",
        "highlight_h": "⭐ Highlighted record",
        "temp_range": "Temperature range",
        "clear_highlight": "Clear highlight",
        "literature_h": "📋 Literature",
        "checked_suffix": "Currently plotting {n} selected records.",
        "lit_caption": "Select rows in the table (multi-select) = plot only these records; select none = plot all filtered records.",
        "download_csv": "📥 Download filtered CSV",
        "download_svg": "📥 Download SVG (vector, for Origin)",
        "download_png": "📥 Download PNG (300 dpi)",
        "no_data": "No data",
        "full_table": "View full data table",
        "col_reference": "Reference", "col_tracer": "Tracer", "col_matrix": "Matrix",
        "col_structure": "Structure", "col_channel": "Channel",
        "theme_light": "Light", "theme_dark": "Dark",
    },
    "de": {
        "page_title": "Arrhenius-Datenbank für Diffusionsparameter",
        "title": "🧪 Datenbank für Diffusionskoeffizienten in Materialien",
        "current": "Aktuelle Auswahl",
        "s_elem": "Element", "s_matrix": "Matrix", "s_structure": "Struktur",
        "s_channel": "Kanal", "s_type": "Typ",
        "all": "Alle", "clear": "✖ Auswahl löschen",
        "tracer_h": "🟡 Tracer (diffundierendes Element) — Periodensystem anklicken; leer = nicht in der Datenbank",
        "records_unit": "Datensätze",
        "h_isotope": "Wasserstoffisotop",
        "elem_search": "🔎 Element-Schnellsuche (Symbol eingeben; mit dem Periodensystem synchron)",
        "matrix_h": "🔵 Matrix (System) — vier Kategorien",
        "cat_pure": "Reine Elemente", "cat_alloys": "Legierungen",
        "cat_hea": "Hochentropie", "cat_other": "Sonstige & amorph",
        "matrix_search": "🔎 Matrix-Schnellsuche (Stichwort eingeben; mit den vier Spalten oben synchron)",
        "struct_h": "🟣 Struktur (Kristallstruktur)",
        "channel": "🟠 Kanal", "dtype": "⚪ Datentyp",
        "dtype_experiment": "Experiment", "dtype_calculation": "Berechnung",
        "count_caption": "Aktuell {n} Datensätze ausgewählt (Datenbank gesamt: {total}). Zusammensetzungen siehe Literaturtabelle rechts.",
        "temp_h": "🌡️ Temperaturbereich",
        "tmax": "Höchsttemperatur (K)", "tmin": "Mindesttemperatur (K)",
        "tticks": "Obere T-Skala (kommagetrennt, darf leer sein)",
        "autoy": "Y-Bereich automatisch (gleiche Spanne auf beiden Achsen)",
        "p_min": "P min (10^x)", "p_max": "P max (10^x)",
        "d_min": "D min (10^x)", "d_max": "D max (10^x)",
        "plot_h": "📊 Arrhenius-Diagramm",
        "no_records": "Keine Datensätze für die aktuellen Filter — bitte eine andere Kombination versuchen.",
        "pick_first": "Bitte oben einen Tracer oder eine Matrix wählen, dann erscheint das Diagramm hier (sonst würden über tausend Linien übereinanderliegen).",
        "mode": "Darstellungsmodus", "mode_explore": "📈 Erkunden", "mode_pub": "🖨️ Publikation",
        "plot_caption": "Eine Linie im Diagramm anklicken, um den zugehörigen Datensatz hervorzuheben (siehe rechts über der Literaturtabelle); Zeilen in der Tabelle auswählen = nur diese Datensätze plotten.",
        "highlight_h": "⭐ Hervorgehobener Datensatz",
        "temp_range": "Temperaturbereich",
        "clear_highlight": "Hervorhebung löschen",
        "literature_h": "📋 Literatur",
        "checked_suffix": "Aktuell werden {n} ausgewählte Datensätze geplottet.",
        "lit_caption": "Zeilen in der Tabelle auswählen (Mehrfachauswahl) = nur diese Datensätze plotten; keine Auswahl = alle gefilterten Datensätze plotten.",
        "download_csv": "📥 Gefilterte CSV herunterladen",
        "download_svg": "📥 SVG herunterladen (Vektor, für Origin)",
        "download_png": "📥 PNG herunterladen (300 dpi)",
        "no_data": "Keine Daten",
        "full_table": "Vollständige Datentabelle ansehen",
        "col_reference": "Referenz", "col_tracer": "Tracer", "col_matrix": "Matrix",
        "col_structure": "Struktur", "col_channel": "Kanal",
        "theme_light": "Hell", "theme_dark": "Dunkel",
    },
    "zh": {
        "page_title": "Arrhenius 扩散参数对比库",
        "title": "🧪 个人材料扩散系数数据库",
        "current": "当前选择",
        "s_elem": "元素", "s_matrix": "体系", "s_structure": "结构",
        "s_channel": "通道", "s_type": "类型",
        "all": "全部", "clear": "✖ 清除选择",
        "tracer_h": "🟡 Tracer（扩散元素）— 点周期表选，空白 = 库里没有",
        "records_unit": "条",
        "h_isotope": "氢同位素",
        "elem_search": "🔎 元素快速查找（输入符号，选中与周期表同步）",
        "matrix_h": "🔵 Matrix（体系）— 四类分列",
        "cat_pure": "纯元素", "cat_alloys": "合金",
        "cat_hea": "高熵", "cat_other": "其他及非晶",
        "matrix_search": "🔎 体系快速查找（输入关键词，选中与上方四列同步）",
        "struct_h": "🟣 Structure（晶体结构）",
        "channel": "🟠 通道", "dtype": "⚪ 数据类型",
        "dtype_experiment": "实验", "dtype_calculation": "计算",
        "count_caption": "当前选中 {n} 条记录（总库 {total} 条）。成分细节见右侧文献表。",
        "temp_h": "🌡️ 温度范围",
        "tmax": "最高温度 (K)", "tmin": "最低温度 (K)",
        "tticks": "顶部 T 刻度（逗号分隔，可空）",
        "autoy": "Y 轴自动范围（左右等跨度）",
        "p_min": "P 最小 (10^x)", "p_max": "P 最大 (10^x)",
        "d_min": "D 最小 (10^x)", "d_max": "D 最大 (10^x)",
        "plot_h": "📊 Arrhenius 图",
        "no_records": "没有符合筛选条件的记录，换一下筛选组合试试。",
        "pick_first": "先在上方选 Tracer 或体系，下方就会画图（不然上千条线挤在一起看不清）。",
        "mode": "绘图模式", "mode_explore": "📈 探索模式", "mode_pub": "🖨️ 出版模式",
        "plot_caption": "点图上的线可高亮对应记录（见右侧文献表上方）；在文献表里点选行 = 只画勾选的记录。",
        "highlight_h": "⭐ 高亮记录",
        "temp_range": "温区",
        "clear_highlight": "清除高亮",
        "literature_h": "📋 文献",
        "checked_suffix": "当前勾选后画图 {n} 条。",
        "lit_caption": "在表里点选行（可多选）= 只画这些记录；不选 = 画全部筛选结果。",
        "download_csv": "📥 下载当前筛选 CSV",
        "download_svg": "📥 下载 SVG（矢量，进 Origin）",
        "download_png": "📥 下载 PNG（300 dpi）",
        "no_data": "无数据",
        "full_table": "查看完整数据表",
        "col_reference": "文献", "col_tracer": "Tracer", "col_matrix": "体系",
        "col_structure": "结构", "col_channel": "通道",
        "theme_light": "浅色", "theme_dark": "深色",
    },
}
# v4.1 界面：默认浅色（方案 4 Clean Light），可切换深色（方案 1 Velox Dark）。
# 语言切换用国旗图按钮（内嵌 SVG，不依赖系统 emoji，Windows 上也能显示）；
# 数据值来自英文 Excel，三种界面下保持英文。
_FLAG_SVG = {
    "de": "data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%27%20viewBox%3D%270%200%2060%2040%27%3E%3Crect%20width%3D%2760%27%20height%3D%2740%27%20fill%3D%27%23FFCE00%27%2F%3E%3Crect%20width%3D%2760%27%20height%3D%2726.7%27%20fill%3D%27%23DD0000%27%2F%3E%3Crect%20width%3D%2760%27%20height%3D%2713.3%27%20fill%3D%27%23000%27%2F%3E%3C%2Fsvg%3E",
    "en": "data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%27%20viewBox%3D%270%200%2060%2040%27%3E%3Crect%20width%3D%2760%27%20height%3D%2740%27%20fill%3D%27%23012169%27%2F%3E%3Cpath%20d%3D%27M0%2C0%20L60%2C40%20M60%2C0%20L0%2C40%27%20stroke%3D%27%23fff%27%20stroke-width%3D%278%27%2F%3E%3Cpath%20d%3D%27M0%2C0%20L60%2C40%20M60%2C0%20L0%2C40%27%20stroke%3D%27%23C8102E%27%20stroke-width%3D%273%27%2F%3E%3Crect%20x%3D%2725%27%20width%3D%2710%27%20height%3D%2740%27%20fill%3D%27%23fff%27%2F%3E%3Crect%20y%3D%2715%27%20width%3D%2760%27%20height%3D%2710%27%20fill%3D%27%23fff%27%2F%3E%3Crect%20x%3D%2727%27%20width%3D%276%27%20height%3D%2740%27%20fill%3D%27%23C8102E%27%2F%3E%3Crect%20y%3D%2717%27%20width%3D%2760%27%20height%3D%276%27%20fill%3D%27%23C8102E%27%2F%3E%3C%2Fsvg%3E",
    "zh": "data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%27%20viewBox%3D%270%200%2060%2040%27%3E%3Crect%20width%3D%2760%27%20height%3D%2740%27%20fill%3D%27%23DE2910%27%2F%3E%3Cpolygon%20points%3D%2711.0%2C3.0%2012.6%2C7.8%2017.7%2C7.8%2013.5%2C10.8%2015.1%2C15.7%2011.0%2C12.7%206.9%2C15.7%208.5%2C10.8%204.3%2C7.8%209.4%2C7.8%27%20fill%3D%27%23FFDE00%27%2F%3E%3Cpolygon%20points%3D%2723.0%2C1.9%2023.6%2C3.7%2025.5%2C3.7%2023.9%2C4.8%2024.5%2C6.6%2023.0%2C5.5%2021.5%2C6.6%2022.1%2C4.8%2020.5%2C3.7%2022.4%2C3.7%27%20fill%3D%27%23FFDE00%27%2F%3E%3Cpolygon%20points%3D%2726.0%2C6.9%2026.6%2C8.7%2028.5%2C8.7%2026.9%2C9.8%2027.5%2C11.6%2026.0%2C10.5%2024.5%2C11.6%2025.1%2C9.8%2023.5%2C8.7%2025.4%2C8.7%27%20fill%3D%27%23FFDE00%27%2F%3E%3Cpolygon%20points%3D%2726.0%2C12.9%2026.6%2C14.7%2028.5%2C14.7%2026.9%2C15.8%2027.5%2C17.6%2026.0%2C16.5%2024.5%2C17.6%2025.1%2C15.8%2023.5%2C14.7%2025.4%2C14.7%27%20fill%3D%27%23FFDE00%27%2F%3E%3Cpolygon%20points%3D%2723.0%2C17.9%2023.6%2C19.7%2025.5%2C19.7%2023.9%2C20.8%2024.5%2C22.6%2023.0%2C21.5%2021.5%2C22.6%2022.1%2C20.8%2020.5%2C19.7%2022.4%2C19.7%27%20fill%3D%27%23FFDE00%27%2F%3E%3C%2Fsvg%3E",
}
_THEMES = {
    "light": dict(bg="#eef2f6", panel="#ffffff", panel2="#f7fafc", border="#d7e0e8",
                  text="#17293a", muted="#64798c", accent="#2563eb", cell="#dbeafe",
                  sel="#2563eb", glow="0 2px 10px rgba(30,60,90,.08)", plotbg="#ffffff",
                  grid="#e2eaf1", axis="#17293a"),
    "dark": dict(bg="#131e28", panel="#1b2a38", panel2="#16222d", border="#2c4356",
                 text="#dcebf5", muted="#8fb0c4", accent="#38b6e8", cell="#27506e",
                 sel="#0e7fb8", glow="0 0 14px rgba(56,182,232,.25)", plotbg="#1b2a38",
                 grid="#24404f", axis="#dcebf5"),
}

if "lang" not in st.session_state:
    st.session_state["lang"] = "en"
if "theme" not in st.session_state:
    st.session_state["theme"] = "light"
_lang = st.session_state["lang"]
T = STR[_lang]

st.set_page_config(page_title=T["page_title"], layout="wide")
_title_c, _ctl_c = st.columns([7, 3])
_title_c.title(T["title"])
with _ctl_c:
    _fcols = st.columns([1, 1, 1, 2.4])
    for _col, _code, _name in zip(_fcols[:3], ("de", "en", "zh"),
                                  ("Deutsch", "English", "中文")):
        with _col:
            with st.container(key=f"flag_{_code}"):
                if st.button(_code.upper(), width="stretch", key=f"langbtn_{_code}", help=_name,
                             type="primary" if _lang == _code else "secondary"):
                    st.session_state["lang"] = _code
                    st.rerun()
    with _fcols[3]:
        st.segmented_control(
            "Theme", ["light", "dark"], key="theme", label_visibility="collapsed",
            format_func=lambda m: ("☀ " + T["theme_light"]) if m == "light"
            else ("🌙 " + T["theme_dark"]))
_theme = st.session_state.get("theme", "light")
_th = _THEMES[_theme]

st.markdown(f"""
<style>
.stApp {{ background: {_th['bg']}; color: {_th['text']}; }}
[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 3.4rem; max-width: 1560px; }}
h1 {{ font-size: 1.85rem !important; }}
div[data-testid="stHorizontalBlock"] {{ gap: 0.18rem; }}
div[data-testid="stVerticalBlockBorderWrapper"] {{
  background: {_th['panel']}; border: 1px solid {_th['border']};
  border-radius: 14px; box-shadow: {_th['glow']}; }}
.stButton button {{
  background: {_th['cell']}; color: {_th['text']}; border: 1px solid {_th['border']};
  border-radius: 6px; padding: 0.1rem 0.05rem; min-height: 30px; width: 100%;
  font-weight: 600; font-size: 0.85rem; line-height: 1.1; }}
.stButton button:hover {{ border-color: {_th['accent']}; color: {_th['accent']}; }}
.stButton button[kind="primary"] {{
  background: {_th['sel']}; color: #fff; border-color: {_th['accent']};
  box-shadow: {_th['glow']}; }}
.stButton button[kind="primary"]:hover {{ color: #fff; }}
.stButton button p {{ white-space: nowrap; }}
div.st-key-flag_de button, div.st-key-flag_en button, div.st-key-flag_zh button {{
  background-color: transparent; background-size: cover; background-position: center;
  color: transparent !important; height: 34px; min-width: 54px; border-radius: 6px; }}
[data-testid="stWidgetLabel"] p, [data-testid="stRadio"] p,
[data-testid="stCheckbox"] p {{ color: {_th['text']}; }}
[data-testid="stNumberInput"] button {{
  background: {_th['panel2']}; color: {_th['text']}; }}
[data-testid="stMultiSelect"] [data-baseweb="select"] {{
  background: {_th['panel2']}; }}
div.st-key-flag_de button {{ background-image: url("{_FLAG_SVG['de']}"); }}
div.st-key-flag_en button {{ background-image: url("{_FLAG_SVG['en']}"); }}
div.st-key-flag_zh button {{ background-image: url("{_FLAG_SVG['zh']}"); }}
div.st-key-flag_de button[kind="primary"], div.st-key-flag_en button[kind="primary"],
div.st-key-flag_zh button[kind="primary"] {{
  box-shadow: 0 0 0 2px {_th['accent']}, {_th['glow']}; }}
div.st-key-flag_de button[kind="primary"] {{ background-image: url("{_FLAG_SVG['de']}"); }}
div.st-key-flag_en button[kind="primary"] {{ background-image: url("{_FLAG_SVG['en']}"); }}
div.st-key-flag_zh button[kind="primary"] {{ background-image: url("{_FLAG_SVG['zh']}"); }}
button[data-variant="segmented_control"], button[data-variant="pills"] {{
  border-radius: 999px !important; background: {_th['panel2']};
  color: {_th['text']}; border-color: {_th['border']}; }}
button[data-variant="segmented_control"][aria-checked="true"],
button[data-variant="pills"][aria-checked="true"] {{
  background: {_th['sel']} !important; color: #fff !important;
  border-color: {_th['accent']} !important; }}
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input {{
  background: {_th['panel2']}; color: {_th['text']}; }}
[data-testid="stNumberInput"] input:disabled {{
  background: {_th['panel2']}; color: {_th['muted']};
  -webkit-text-fill-color: {_th['muted']}; }}
[data-testid="stMultiSelect"] [data-baseweb="select"] {{
  background: {_th['panel2']} !important; color: {_th['text']};
  border-color: {_th['border']}; }}
[data-testid="stMultiSelect"] [data-baseweb="select"] > div {{
  background: transparent !important; color: {_th['text']}; }}
[data-testid="stMultiSelect"] [data-baseweb="tag"] {{
  background: {_th['sel']}; }}
[data-testid="stDataFrame"] {{ background: #ffffff; border-radius: 10px; }}
[data-testid="stExpander"] {{ background: {_th['panel']}; border-color: {_th['border']}; }}
[data-testid="stCaptionContainer"], .stCaption {{ color: {_th['muted']}; }}
div.st-key-ptcard button {{
  font-size: 0.60rem; min-height: 22px; padding: 0; border-radius: 4px;
  letter-spacing: -0.4px; }}
div.st-key-ptcard button p {{ font-size: 0.60rem; line-height: 1.1; }}
div.st-key-ptcard div[data-testid="stHorizontalBlock"] {{ gap: 0.12rem; }}
</style>""", unsafe_allow_html=True)

R = 8.314


@st.cache_data
def load_data():
    # v4: 数据文件为全英文 data.xlsx（「All data」页）。在 Excel 里改完保存、
    # 替换这个文件即可，程序自动映射成页面用的列。旧中文版 data.xlsx
    # （「全部数据」页）与旧版 data.csv 仍可回退读取。
    if os.path.exists("data.xlsx"):
        xls = pd.ExcelFile("data.xlsx")
        sheet = "All data" if "All data" in xls.sheet_names else xls.sheet_names[0]
        raw = pd.read_excel(xls, sheet_name=sheet)
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
        df["data_type"] = np.where(calc, "calculation", "experiment")

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
        df["data_type"] = df["data_type"].replace({"实验": "experiment", "计算": "calculation"})
    df = df.replace({"tracer": {"": np.nan}, "matrix_group": {"": np.nan}})
    df = df.dropna(subset=["tracer", "matrix_group"]).reset_index(drop=True)
    df["rid"] = range(len(df))  # 稳定行号，供勾选/高亮跨重跑对照
    return df


df = load_data()

# 勾选集（None = 画全部筛选结果）与高亮记录，存在 session_state 里
if "checked_rids" not in st.session_state:
    st.session_state["checked_rids"] = None
if "hl_rid" not in st.session_state:
    st.session_state["hl_rid"] = None
if "prev_checked" not in st.session_state:
    st.session_state["prev_checked"] = None

# ---------- 周期表选元素 + 体系四分类 + 搜索框双向同步 ----------
_PT_ROWS = [
    [("H", 1)] + [None] * 16 + [("He", 2)],
    [("Li", 3), ("Be", 4)] + [None] * 10 + [("B", 5), ("C", 6), ("N", 7), ("O", 8), ("F", 9), ("Ne", 10)],
    [("Na", 11), ("Mg", 12)] + [None] * 10 + [("Al", 13), ("Si", 14), ("P", 15), ("S", 16), ("Cl", 17), ("Ar", 18)],
    [("K", 19), ("Ca", 20), ("Sc", 21), ("Ti", 22), ("V", 23), ("Cr", 24), ("Mn", 25), ("Fe", 26), ("Co", 27), ("Ni", 28), ("Cu", 29), ("Zn", 30), ("Ga", 31), ("Ge", 32), ("As", 33), ("Se", 34), ("Br", 35), ("Kr", 36)],
    [("Rb", 37), ("Sr", 38), ("Y", 39), ("Zr", 40), ("Nb", 41), ("Mo", 42), ("Tc", 43), ("Ru", 44), ("Rh", 45), ("Pd", 46), ("Ag", 47), ("Cd", 48), ("In", 49), ("Sn", 50), ("Sb", 51), ("Te", 52), ("I", 53), ("Xe", 54)],
    [("Cs", 55), ("Ba", 56), ("La", 57), ("Hf", 72), ("Ta", 73), ("W", 74), ("Re", 75), ("Os", 76), ("Ir", 77), ("Pt", 78), ("Au", 79), ("Hg", 80), ("Tl", 81), ("Pb", 82), ("Bi", 83), ("Po", 84), ("At", 85), ("Rn", 86)],
    [("Fr", 87), ("Ra", 88), ("Ac", 89), ("Rf", 104), ("Db", 105), ("Sg", 106), ("Bh", 107), ("Hs", 108), ("Mt", 109), ("Ds", 110), ("Rg", 111), ("Cn", 112), ("Nh", 113), ("Fl", 114), ("Mc", 115), ("Lv", 116), ("Ts", 117), ("Og", 118)],
    [None, None, ("Ce", 58), ("Pr", 59), ("Nd", 60), ("Pm", 61), ("Sm", 62), ("Eu", 63), ("Gd", 64), ("Tb", 65), ("Dy", 66), ("Ho", 67), ("Er", 68), ("Tm", 69), ("Yb", 70), ("Lu", 71), None, None],
    [None, None, ("Th", 90), ("Pa", 91), ("U", 92), ("Np", 93), ("Pu", 94), ("Am", 95), ("Cm", 96), ("Bk", 97), ("Cf", 98), ("Es", 99), ("Fm", 100), ("Md", 101), ("No", 102), ("Lr", 103), None, None],
]
ELEMENT_SYMBOLS = {c[0] for row in _PT_ROWS for c in row if c}
GROUP_CATS = ["pure", "alloys", "hea", "other"]
CAT_LABEL_KEY = {"pure": "cat_pure", "alloys": "cat_alloys", "hea": "cat_hea", "other": "cat_other"}


def group_category(name):
    # v4: matrix_group 已英文化；旧中文值一并兼容
    if name in ELEMENT_SYMBOLS:
        return "pure"
    if "HEA" in name or "高熵" in name:
        return "hea"
    if (name in ("Other", "其他", "Ceramics and ionic crystals", "陶瓷/离子晶体等",
                 "Metallic glass", "非晶合金")
            or "非晶" in name or any(ch.isdigit() for ch in name)):
        return "other"
    return "alloys"


for _k in ("sel_tracers", "elem_search", "matrix_search",
           "mg_pure", "mg_alloys", "mg_hea", "mg_other",
           "p_struct", "p_channel", "p_dtype"):
    if _k not in st.session_state:
        st.session_state[_k] = []


def _toggle_elem(el):
    cur = list(st.session_state["sel_tracers"])
    cur = [x for x in cur if x != el] if el in cur else cur + [el]
    st.session_state["sel_tracers"] = cur
    st.session_state["elem_search"] = cur


def _sync_elem_from_search():
    st.session_state["sel_tracers"] = list(st.session_state["elem_search"])


def _sync_matrix_from_search():
    sel = list(st.session_state["matrix_search"])
    for cat in GROUP_CATS:
        st.session_state[f"mg_{cat}"] = [g for g in sel if group_category(g) == cat]


def _sync_matrix_from_pills():
    sel = []
    for cat in GROUP_CATS:
        sel += st.session_state[f"mg_{cat}"]
    st.session_state["matrix_search"] = sel


def _clear_filters():
    for k in ("sel_tracers", "elem_search", "matrix_search",
              "mg_pure", "mg_alloys", "mg_hea", "mg_other",
              "p_struct", "p_channel", "p_dtype"):
        st.session_state[k] = []
    st.session_state["checked_rids"] = None
    st.session_state["hl_rid"] = None


# 先按当前状态算好筛选结果（控件在后面只是显示同一份状态，保证顶部摘要、
# 级联选项与实际筛选一致；顺手把已被级联淘汰的旧选择清掉）
_present_elems = sorted(df["tracer"].unique())
_all_groups = sorted(df["matrix_group"].unique())
st.session_state["sel_tracers"] = [e for e in st.session_state["sel_tracers"] if e in _present_elems]
st.session_state["elem_search"] = list(st.session_state["sel_tracers"])
sel_tracers = list(st.session_state["sel_tracers"])
dff = df[df["tracer"].isin(sel_tracers)] if sel_tracers else df
_avail_groups = sorted(dff["matrix_group"].unique())
for cat in GROUP_CATS:
    _opts = [g for g in _avail_groups if group_category(g) == cat]
    st.session_state[f"mg_{cat}"] = [g for g in st.session_state[f"mg_{cat}"] if g in _opts]
sel_groups = [g for cat in GROUP_CATS for g in st.session_state[f"mg_{cat}"]]
st.session_state["matrix_search"] = list(sel_groups)
if sel_groups:
    dff = dff[dff["matrix_group"].isin(sel_groups)]
_struct_opts = sorted(dff["structure"].unique())
st.session_state["p_struct"] = [s for s in st.session_state["p_struct"] if s in _struct_opts]
sel_structs = list(st.session_state["p_struct"])
if sel_structs:
    dff = dff[dff["structure"].isin(sel_structs)]
sel_channels = [c for c in st.session_state["p_channel"] if c in ("Dv", "Dgb", "P", "IPB")]
sel_dtype = [c for c in st.session_state["p_dtype"] if c in ("experiment", "calculation")]
if sel_channels:
    dff = dff[dff["channel"].isin(sel_channels)]
if sel_dtype:
    dff = dff[dff["data_type"].isin(sel_dtype)]
df_filtered = dff

# 顶部摘要：当前选了什么，一眼可见
def _fmt_sel(lst):
    return ", ".join(lst) if lst else T["all"]


def _fmt_dtype(lst):
    lab = {"experiment": T["dtype_experiment"], "calculation": T["dtype_calculation"]}
    return ", ".join(lab.get(x, x) for x in lst) if lst else T["all"]


_sum_c, _clr_c = st.columns([9, 1])
_sum_c.markdown(
    f"**{T['current']}**: {T['s_elem']} {_fmt_sel(sel_tracers)} | {T['s_matrix']} {_fmt_sel(sel_groups)} | "
    f"{T['s_structure']} {_fmt_sel(sel_structs)} | {T['s_channel']} {_fmt_sel(sel_channels)} | "
    f"{T['s_type']} {_fmt_dtype(sel_dtype)}")
_clr_c.button(T["clear"], on_click=_clear_filters, key="clr_filters")

left, right = st.columns([10, 27])

# ---------- 左列：筛选区（三张卡片；图在右列上方，打开页面一眼可见） ----------
with left:
    with st.container(border=True, key="ptcard"):
        st.markdown(f"#### {T['tracer_h']}")
        _counts = df["tracer"].value_counts().to_dict()
        _present = set(_present_elems)
        for _row in _PT_ROWS:
            _cols = st.columns(18, gap="small")
            for _c, _cell in zip(_cols, _row):
                if _cell and _cell[0] in _present:
                    _sym = _cell[0]
                    _c.button(_sym, width="stretch",
                              key=f"pt_{_sym}",
                              type="primary" if _sym in sel_tracers else "secondary",
                              on_click=_toggle_elem, args=(_sym,),
                              help=f"{_counts.get(_sym, 0)} {T['records_unit']}")
                else:
                    _c.write("")
        _iso = [e for e in ("D", "T") if e in _present]
        if _iso:
            _ic = st.columns([1] * len(_iso) + [8])
            for _c, _sym in zip(_ic, _iso):
                _c.button(_sym, width="stretch", key=f"pt_{_sym}",
                          type="primary" if _sym in sel_tracers else "secondary",
                          on_click=_toggle_elem, args=(_sym,),
                          help=f"{T['h_isotope']} · {_counts.get(_sym, 0)} {T['records_unit']}")
        st.multiselect(T["elem_search"], _present_elems,
                       key="elem_search", on_change=_sync_elem_from_search)
    with st.container(height=330, border=True):
        st.markdown(f"#### {T['matrix_h']}")
        for _cat in GROUP_CATS:
            st.markdown(f"**{T[CAT_LABEL_KEY[_cat]]}**")
            st.pills(_cat, [g for g in _avail_groups if group_category(g) == _cat],
                     selection_mode="multi", key=f"mg_{_cat}",
                     on_change=_sync_matrix_from_pills, label_visibility="collapsed")
        st.multiselect(T["matrix_search"], _all_groups,
                       key="matrix_search", on_change=_sync_matrix_from_search)
        st.markdown(f"#### {T['struct_h']}")
        st.pills("Structure", _struct_opts, selection_mode="multi", key="p_struct",
                 label_visibility="collapsed")
        c1, c2 = st.columns(2)
        with c1:
            st.pills(T["channel"], ["Dv", "Dgb", "P", "IPB"],
                     selection_mode="multi", key="p_channel")
        with c2:
            st.pills(T["dtype"], ["experiment", "calculation"],
                     selection_mode="multi", key="p_dtype",
                     format_func=lambda c: T["dtype_experiment"] if c == "experiment"
                     else T["dtype_calculation"])
    st.caption(T["count_caption"].format(n=len(df_filtered), total=len(df)))

# 实际画图的集合 = 筛选结果 ∩ 勾选集（未勾选时 = 全部筛选结果）
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
    def rng(vals):
        if not vals:
            return None
        return int(np.floor(np.log10(min(vals)))), int(np.ceil(np.log10(max(vals))))
    d_r, p_r = rng(d_vals), rng(p_vals)
    if d_r and p_r:
        # 两轴都有数据时才做等跨度对齐（原设计）
        span = max(d_r[1] - d_r[0], p_r[1] - p_r[0]) + 1
        def align(lo, hi):
            centre = (lo + hi) / 2.0
            new_hi = int(np.ceil(centre + span / 2.0))
            return new_hi - span, new_hi
        return align(*p_r), align(*d_r), span
    # 只有一根轴有数据时就按它自己的实际线段范围，不再被另一根轴的
    # 兜底范围撑大跨度
    if d_r:
        return d_r, d_r, d_r[1] - d_r[0]
    if p_r:
        return p_r, p_r, p_r[1] - p_r[0]
    return (-30, -19), (-25, -14), 11

has_p = df_plot["P0_m3_s"].notna().any() if len(df_plot) else False
has_d = df_plot[["D0_v_m2_s", "D0_gb_m2_s"]].notna().any().any() if len(df_plot) else False
(p_lo_a, p_hi_a), (d_lo_a, d_hi_a), _span = auto_exponents(df_plot) if len(df_plot) else (((-30, -19)), ((-25, -14)), 11)

# 温度范围 = 所选记录实验线段的温区并集（不再 ±100 填充）。带 key 的
# 输入控件不会跟随新的 value= 默认值，所选集合一变必须显式把控件状态重置到
# 新范围；集合不变时保留用户手动改的值。
_seg = df_plot.dropna(subset=["Tmin_K", "Tmax_K"]) if len(df_plot) else df_plot
t_hi_sel = float(_seg["Tmax_K"].max()) if len(_seg) else 1300.0
t_lo_sel = float(_seg["Tmin_K"].min()) if len(_seg) else 500.0
_range_sig = tuple(df_plot["rid"].tolist())
if st.session_state.get("_range_sig") != _range_sig:
    st.session_state["_range_sig"] = _range_sig
    st.session_state["v_tmax"] = t_hi_sel
    st.session_state["v_tmin"] = t_lo_sel
    st.session_state["v_plo"] = p_lo_a
    st.session_state["v_phi"] = p_hi_a
    st.session_state["v_dlo"] = d_lo_a
    st.session_state["v_dhi"] = d_hi_a
t_max_data, t_min_data = t_hi_sel, t_lo_sel

p_lo, p_hi, d_lo, d_hi = p_lo_a, p_hi_a, d_lo_a, d_hi_a  # 默认值，手动模式下被右侧输入覆盖

# ---------- 左列下部：温度与坐标范围 + 模式开关（布局 A） ----------
with left:
  with st.container(border=True):
    st.markdown(f"#### {T['temp_h']}")
    rc1, rc2 = st.columns(2)
    view_tmax = rc1.number_input(T["tmax"], value=float(t_max_data), step=50.0, key="v_tmax")
    view_tmin = rc2.number_input(T["tmin"], value=float(t_min_data), step=50.0, key="v_tmin")
    t_ticks_input = st.text_input(T["tticks"], value="", key="v_ticks")
    auto_y = st.checkbox(T["autoy"], value=True, key="v_autoy")
    if has_p:
        yc1, yc2 = st.columns(2)
        p_lo = yc1.number_input(T["p_min"], value=p_lo_a, step=1, key="v_plo", disabled=auto_y)
        p_hi = yc2.number_input(T["p_max"], value=p_hi_a, step=1, key="v_phi", disabled=auto_y)
    if has_d:
        yc3, yc4 = st.columns(2)
        d_lo = yc3.number_input(T["d_min"], value=d_lo_a, step=1, key="v_dlo", disabled=auto_y)
        d_hi = yc4.number_input(T["d_max"], value=d_hi_a, step=1, key="v_dhi", disabled=auto_y)
    st.markdown(f"**{T['mode']}**")
    st.segmented_control(T["mode"], ["explore", "publication"], key="v_mode",
                         default="explore", label_visibility="collapsed",
                         format_func=lambda m: T["mode_explore"] if m == "explore"
                         else T["mode_pub"])

try:
    t_ticks = [int(float(x.strip())) for x in t_ticks_input.split(",") if x.strip()]
except Exception:
    t_ticks = []

# 温度输入兜底——非正或上下倒置时回到所选线段范围（10000/T 恒为正）
if not (view_tmax > 0):
    view_tmax = t_hi_sel
if not (0 < view_tmin < view_tmax):
    view_tmin = t_lo_sel if t_lo_sel < view_tmax else view_tmax * 0.5

p_range = None if auto_y else (int(p_lo), int(p_hi))
d_range = None if auto_y else (int(d_lo), int(d_hi))
# 探索模式用数值范围：自动时用对齐后的指数
p_lo_e, p_hi_e = (p_lo_a, p_hi_a) if auto_y else (int(p_lo), int(p_hi))
d_lo_e, d_hi_e = (d_lo_a, d_hi_a) if auto_y else (int(d_lo), int(d_hi))

# ---------- 右列：Arrhenius 图 ----------
with right:
    st.markdown(f"#### {T['plot_h']}")
    if len(df_plot) == 0:
        st.info(T["no_records"])
    elif not sel_tracers and not sel_groups:
        st.info(T["pick_first"])
    else:
        mode = st.session_state.get("v_mode") or "explore"
        x_min = max(0.0, 10000.0 / view_tmax)  # 10000/T 最小到 0，不可能为负
        x_max = 10000.0 / view_tmin
        if x_max <= x_min:
            x_max = x_min + 1.0
        T_full = np.linspace(view_tmax, view_tmin, 200)
        X_full = 10000.0 / T_full

        if mode == "explore":
            fig = go.Figure()
            trace_owner = []  # 每条 trace 对应的 rid，供点图高亮反查
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
            layout = dict(hovermode="closest", height=700, plot_bgcolor=_th["plotbg"],
                          paper_bgcolor=_th["plotbg"], font=dict(color=_th["text"]),
                          legend=dict(x=0.01, y=0.01, font=dict(color=_th["text"]),
                                      bgcolor="rgba(27,42,56,0.9)" if _theme == "dark" else "rgba(255,255,255,0.85)",
                                      bordercolor=_th["border"], borderwidth=1),
                          xaxis=dict(title="10000 / T (K⁻¹)", range=[x_min, x_max], showline=True,
                                     linewidth=1, linecolor=_th["axis"], gridcolor=_th["grid"]))
            if has_p:
                layout["yaxis"] = dict(title="P (m³/s)", type="log", range=[p_lo_e, p_hi_e],
                                       showline=True, linewidth=1, linecolor=_th["axis"], gridcolor=_th["grid"])
            if has_d:
                key = "yaxis2" if has_p else "yaxis"
                layout[key] = dict(title="Dv, Dgb (m²/s)", type="log", range=[d_lo_e, d_hi_e],
                                   showline=True, linewidth=1, linecolor=_th["axis"], gridcolor=_th["grid"])
                if has_p:
                    layout[key].update(dict(overlaying="y", side="right"))
            fig.update_layout(**layout)
            # 点图上的线 -> 高亮对应记录（selection 事件回传 curveNumber）
            plot_state = st.plotly_chart(fig, width="stretch", key="arr_plot", theme=None,
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
            st.caption(T["plot_caption"])
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
            b1.download_button(T["download_svg"], buf_svg.getvalue(),
                               "Arrhenius_publication.svg", "image/svg+xml")
            buf_png = io.BytesIO(); fig.savefig(buf_png, format="png", dpi=300, bbox_inches="tight")
            b2.download_button(T["download_png"], buf_png.getvalue(),
                           "Arrhenius_publication.png", "image/png")

# ---------- 右列下部：高亮详情 + 文献溯源 ----------
with right:
    # 高亮记录详情卡（点曲线或在表中新勾一行都会更新到这里）
    if hl_rid is not None and (df_filtered["rid"] == hl_rid).any():
        hr = df_filtered[df_filtered["rid"] == hl_rid].iloc[0]
        d0txt = ""
        for col, lab in (("D0_v_m2_s", "Dv₀"), ("D0_gb_m2_s", "Dgb₀"), ("P0_m3_s", "P₀")):
            if pd.notna(hr[col]):
                d0txt = f"{lab} = {hr[col]:.3e} {'m³/s' if lab == 'P₀' else 'm²/s'}"
        st.markdown(f"#### {T['highlight_h']}")
        st.info(f"**{hr['reference']}**\n\n"
                f"{hr['tracer']} in {hr['matrix']} ({hr['structure']}, {hr['channel']})\n\n"
                f"Q = {hr['Q_kJ_mol']} kJ/mol · {d0txt} · {T['temp_range']} {hr['Tmin_K']}–{hr['Tmax_K']} K"
                + (f"\n\n[doi.org/{hr['doi']}]" if hr["doi"] else ""))
        if st.button(T["clear_highlight"], key="clr_hl"):
            st.session_state["hl_rid"] = None
            st.rerun()
    st.markdown(f"#### {T['literature_h']}")
    if len(df_filtered):
        show = df_filtered.copy()
        show["doi_link"] = show["doi"].apply(lambda d: f"https://doi.org/{d}" if d else "")
        show_disp = show[["reference", "tracer", "matrix", "structure", "channel", "Q_kJ_mol", "doi_link"]].rename(
            columns={"reference": T["col_reference"], "tracer": T["col_tracer"],
                     "matrix": T["col_matrix"], "structure": T["col_structure"],
                     "channel": T["col_channel"], "doi_link": "doi"})
        # 表格点选（可多选）= 勾选集；不选 = 画全部筛选结果
        lit_state = st.dataframe(
            show_disp,
            width="stretch", height=420, hide_index=True,
            column_config={"doi": st.column_config.LinkColumn("doi")},
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
            if added:  # 新勾上的一行同时设为高亮（行 -> 图）
                st.session_state["hl_rid"] = int(sorted(added)[-1])
            st.rerun()
        st.caption(T["lit_caption"]
                   + (T["checked_suffix"].format(n=len(df_plot)) if checked else ""))
        st.download_button(T["download_csv"], df_filtered.to_csv(index=False).encode("utf-8-sig"),
                           "arrhenius_filtered.csv", "text/csv")
    else:
        st.caption(T["no_data"])
    with st.expander(T["full_table"]):
        st.dataframe(df_filtered, width="stretch")
