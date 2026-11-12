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
    },
}
# 注：不用 emoji 国旗——Windows 上不渲染、只剩字母；用各语言自称，
# 每种语言界面只出现该语言文字（数据值来自英文 Excel，保持英文）。
LANG_LABELS = {"de": "Deutsch", "en": "English", "zh": "中文"}

if "lang" not in st.session_state:
    st.session_state["lang"] = "en"
_lang = st.session_state["lang"]
T = STR[_lang]

st.set_page_config(page_title=T["page_title"], layout="wide")
_title_c, _lang_c = st.columns([8, 2])
_title_c.title(T["title"])
_lang_c.segmented_control(
    "Language / Sprache / 语言", ["de", "en", "zh"],
    format_func=lambda c: LANG_LABELS[c], key="lang", label_visibility="collapsed")

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
    ["H"] + [None] * 16 + ["He"],
    ["Li", "Be"] + [None] * 10 + ["B", "C", "N", "O", "F", "Ne"],
    ["Na", "Mg"] + [None] * 10 + ["Al", "Si", "P", "S", "Cl", "Ar"],
    ["K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr"],
    ["Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe"],
    ["Cs", "Ba", "La", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn"],
    ["Fr", "Ra", "Ac", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og"],
    [None, None, "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu", None, None],
    [None, None, "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr", None, None],
]
ELEMENT_SYMBOLS = {s for row in _PT_ROWS for s in row if s}
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

left, right = st.columns([7, 3])

# ---------- 左列上部：筛选区（定高可滚动，图始终一眼可见） ----------
with left:
    _box = st.container(height=400, border=True)
    with _box:
        st.markdown(f"#### {T['tracer_h']}")
        _counts = df["tracer"].value_counts().to_dict()
        _present = set(_present_elems)
        for _row in _PT_ROWS:
            _cols = st.columns(18, gap="small")
            for _c, _sym in zip(_cols, _row):
                if _sym and _sym in _present:
                    _c.button(_sym, key=f"pt_{_sym}",
                              type="primary" if _sym in sel_tracers else "secondary",
                              on_click=_toggle_elem, args=(_sym,),
                              help=f"{_counts.get(_sym, 0)} {T['records_unit']}")
                else:
                    _c.write("")
        _iso = [e for e in ("D", "T") if e in _present]
        if _iso:
            _ic = st.columns([1] * len(_iso) + [8])
            for _c, _sym in zip(_ic, _iso):
                _c.button(_sym, key=f"pt_{_sym}",
                          type="primary" if _sym in sel_tracers else "secondary",
                          on_click=_toggle_elem, args=(_sym,),
                          help=f"{T['h_isotope']} · {_counts.get(_sym, 0)} {T['records_unit']}")
        st.multiselect(T["elem_search"], _present_elems,
                       key="elem_search", on_change=_sync_elem_from_search)
        st.markdown(f"#### {T['matrix_h']}")
        _mc = st.columns(4, gap="small")
        for _col, _cat in zip(_mc, GROUP_CATS):
            with _col:
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

# ---------- 右列上部：温度与坐标范围 ----------
with right:
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

# ---------- 左列下部：Arrhenius 图 ----------
with left:
    st.markdown(f"#### {T['plot_h']}")
    if len(df_plot) == 0:
        st.info(T["no_records"])
    elif not sel_tracers and not sel_groups:
        st.info(T["pick_first"])
    else:
        mode = st.radio(T["mode"], ["explore", "publication"], horizontal=True, key="v_mode",
                        format_func=lambda m: T["mode_explore"] if m == "explore" else T["mode_pub"])
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
            layout = dict(hovermode="closest", height=580, plot_bgcolor="white",
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
            # 点图上的线 -> 高亮对应记录（selection 事件回传 curveNumber）
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
