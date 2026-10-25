import pandas as pd
import streamlit as st

# 配置表：所有能源的因子、单位、所在 Scope 都写在一处
ENERGY = {
    "电力": {"factor": 0.5568, "unit": "kWh", "scope": 2},
    "天然气": {"factor": 2.16, "unit": "m³", "scope": 1},
    "柴油": {"factor": 2.68, "unit": "L", "scope": 1},
    "汽油": {"factor": 2.36, "unit": "L", "scope": 1},
}

st.title("工厂碳排放计算器")
st.caption("按 GHG Protocol 口径，区分 Scope 1（直接排放）与 Scope 2（外购电力）")

# 1. 侧边栏：输入年度用量
with st.sidebar:
    st.header("年度用量")
    usage = {}
    for name, info in ENERGY.items():
        usage[name] = st.number_input(f"{name}（{info['unit']}）", min_value=0.0)
    last_year = st.number_input("去年总排放（tCO2e）", min_value=0.0)

# 2. 按配置表自动算排放量（吨）
emissions = {}
for name, info in ENERGY.items():
    emissions[name] = usage[name] * info["factor"] / 1000

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

# 5. 各能源排放量对比
df = pd.DataFrame(
    {
        "能源": list(emissions.keys()),
        "排放量": list(emissions.values()),
    }
)
st.subheader("各能源排放量")
st.bar_chart(df, x="能源", y="排放量", alt="各能源排放量对比")

trees = total * 1000 / 18.3
st.caption(f"相当于 {trees:.0f} 棵树一年的吸收量")
