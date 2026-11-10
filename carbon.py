import pandas as pd
import streamlit as st

# 配置表：每种能源的因子、单位、所属 Scope，以及因子的来源和适用年份
ENERGY = {
    "电力": {
        "factor": 0.5306,
        "unit": "kWh",
        "scope": 2,
        "source": "生态环境部、国家统计局《关于发布2023年电力二氧化碳排放因子的公告》（公告 2025 年第 47 号）",
        "year": 2023,
    },
    "天然气": {
        "factor": 2.16,
        "unit": "m³",
        "scope": 1,
        "source": "《省级温室气体清单编制指南（试行）》缺省值",
        "year": 2011,
    },
    "柴油": {
        "factor": 2.68,
        "unit": "L",
        "scope": 1,
        "source": "《省级温室气体清单编制指南（试行）》缺省值",
        "year": 2011,
    },
    "汽油": {
        "factor": 2.36,
        "unit": "L",
        "scope": 1,
        "source": "《省级温室气体清单编制指南（试行）》缺省值",
        "year": 2011,
    },
}

# 分区域电力排放因子（2023 年，kgCO2/kWh）
# 水电占比高的区域因子低（西南、南方），火电占比高的区域因子高（华北、西北）
REGIONS = {
    "全国平均": 0.5306,
    "华北": 0.6361,
    "东北": 0.5122,
    "华东": 0.5500,
    "华中": 0.5271,
    "西北": 0.5543,
    "南方": 0.4042,
    "西南": 0.2472,
}

st.title("工厂碳排放计算器")
st.caption("按 GHG Protocol 口径，区分 Scope 1（直接排放）与 Scope 2（外购电力）")

# 1. 侧边栏：参数与用量
with st.sidebar:
    st.header("参数设置")
    region = st.selectbox(
        "工厂所在区域",
        list(REGIONS),
        help="电力排放因子随区域变化：西南、南方水电多，因子低；华北、西北火电多，因子高。",
    )
    st.header("年度用量")
    usage = {}
    for name, info in ENERGY.items():
        usage[name] = st.number_input(f"{name}（{info['unit']}）", min_value=0.0)
    last_year = st.number_input("去年总排放（tCO2e）", min_value=0.0)


def factor_for(name: str) -> float:
    """电力因子随所选区域变化，其余能源用缺省值。"""
    if name == "电力":
        return REGIONS[region]
    return ENERGY[name]["factor"]


# 2. 按配置表算排放量（吨）
emissions = {}
for name in ENERGY:
    emissions[name] = usage[name] * factor_for(name) / 1000

# 3. 按 scope 归并
scope1 = 0
scope2 = 0
for name, value in emissions.items():
    if ENERGY[name]["scope"] == 1:
        scope1 = scope1 + value
    else:
        scope2 = scope2 + value

total = scope1 + scope2

# 4. 与去年同比
if last_year > 0:
    delta = f"{(total - last_year) / last_year * 100:.1f}%"
else:
    delta = None

with st.container(horizontal=True):
    st.metric(
        "总排放",
        f"{total:.1f} tCO2e",
        delta=delta,
        delta_color="inverse",
        border=True,
    )
    st.metric("Scope 1（直接）", f"{scope1:.1f} t", border=True)
    st.metric("Scope 2（电力）", f"{scope2:.1f} t", border=True)

st.caption(
    f"当前电力因子：{REGIONS[region]:.4f} kgCO₂/kWh（{region}）。"
    "同样一度电，西南比华北少排 61%。"
)

# 5. 各能源排放量对比
df = pd.DataFrame(
    {
        "能源": list(emissions.keys()),
        "排放量": list(emissions.values()),
    }
)
st.subheader("各能源排放量")
st.bar_chart(df, x="能源", y="排放量", alt="各能源排放量对比")
if total > 0:
    st.caption(
        f"电力（Scope 2）占总排放 {scope2 / total * 100:.0f}%，"
        "是主要排放源，所以柱状图上燃料那三根看起来很短。"
    )

trees = total * 1000 / 18.3
st.caption(
    f"约相当于 {trees:.0f} 棵树一年的 CO₂ 吸收量"
    "（按每棵每年 18.3 kg 估算，仅作直观参考，不用于核算）"
)

# 6. 月度趋势：按月填用量，看全年排放走势
st.divider()
st.subheader("月度排放趋势")
st.caption(
    "按月的用量填进表格，折线图会自动出来。"
    "工厂的碳盘查通常按月报送，年度总数只是汇总。"
)

months = [f"{m}月" for m in range(1, 13)]
col_table, col_chart = st.columns([1.2, 1])

with col_table:
    monthly_input = st.data_editor(
        pd.DataFrame({"月份": months, **{name: [0.0] * 12 for name in ENERGY}}),
        hide_index=True,
        width="stretch",
        height=372,
        row_height=28,
        num_rows="fixed",
    )

monthly_emissions = 0
for name in ENERGY:
    monthly_emissions = monthly_emissions + monthly_input[name] * factor_for(name) / 1000

with col_chart:
    if monthly_emissions.sum() > 0:
        # 横轴用数字月份，否则 Vega 会按字符串排序（10月排在 2月 前面）
        chart_df = pd.DataFrame(
            {"月": list(range(1, 13)), "排放量（tCO2e）": monthly_emissions.to_numpy()}
        )
        st.line_chart(
            chart_df,
            x="月",
            y="排放量（tCO2e）",
            x_label="月份",
            height=390,
            alt="月度排放趋势",
        )
        st.caption(f"12 个月合计：{monthly_emissions.sum():.1f} tCO2e")
    else:
        st.info("在左侧表格里填几个月的用量，折线图就会出来。")

# 7. 因子来源：让每个数字都能追溯
with st.expander("排放因子与数据来源"):
    factor_df = pd.DataFrame(
        [
            {
                "能源": name,
                "因子": factor_for(name),
                "单位": info["unit"],
                "所属 Scope": info["scope"],
                "来源": info["source"],
                "适用年份": info["year"],
            }
            for name, info in ENERGY.items()
        ]
    )
    st.dataframe(factor_df, hide_index=True, width="stretch")
    st.caption("以上为常用缺省因子。正式碳核算请以最新官方发布文件为准。")

    region_df = pd.DataFrame(
        [{"区域": r, "电力因子（kgCO₂/kWh）": f} for r, f in REGIONS.items()]
    )
    st.dataframe(region_df, hide_index=True, width="stretch")
