import streamlit as st
import PyPDF2
import re
from openai import OpenAI
import plotly.graph_objects as go

# ===================== 配置区（替换为你的API Key）=====================
LLM_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxxxxx"  # 这里替换成你的DeepSeek API Key
LLM_BASE_URL = "https://api.deepseek.com"
MODEL_NAME = "deepseek-chat"
# =================================================================

# 初始化大模型客户端
llm_client = OpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL
)

# ---------------------- 工具函数 ----------------------
def parse_pdf_resume(pdf_file) -> str:
    """解析PDF简历为纯文本"""
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        full_text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"
        return full_text.strip()
    except Exception as e:
        return f"简历解析失败：{str(e)}"

def llm_chat(prompt: str, temp: float = 0.3) -> str:
    """调用大模型统一入口"""
    resp = llm_client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=temp,
        stream=False
    )
    return resp.choices[0].message.content.strip()

def extract_score(text: str) -> list:
    """提取四项分数：硬技能、项目、软技能、学历"""
    pattern = r"硬技能[:：]\s*(\d+).*?项目经验[:：]\s*(\d+).*?软技能[:：]\s*(\d+).*?学历背景[:：]\s*(\d+)"
    res = re.search(pattern, text, re.S)
    if res:
        return [int(res.group(1)), int(res.group(2)), int(res.group(3)), int(res.group(4))]
    return [70,70,70,70]

# ---------------------- 页面配置 ----------------------
st.set_page_config(
    page_title="Offer捕手 | 求职匹配智能体",
    layout="wide",
    page_icon="🚀"
)
st.title("🚀 Offer 捕手 — 学生求职匹配智能体")
st.markdown("##### 上传简历 + 粘贴岗位JD，一键匹配、简历优化、能力诊断")

# 隐藏Streamlit默认菜单和页脚
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["🔍 岗位智能匹配", "✏️ 简历逐句优化", "📈 能力提升方案", "👔 HR模拟初筛"])

# 全局缓存简历 & JD
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "jd_text" not in st.session_state:
    st.session_state.jd_text = ""

# ---------------------- 标签页1：岗位智能匹配 ----------------------
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("1. 上传简历（仅PDF）")
        resume_file = st.file_uploader("选择简历文件", type="pdf", key="resume_up")
        if resume_file:
            st.session_state.resume_text = parse_pdf_resume(resume_file)
            st.success("✅ 简历解析完成")
    with c2:
        st.subheader("2. 粘贴岗位JD")
        jd_input = st.text_area("岗位描述 / 招聘要求", height=320, key="jd_input")
        if jd_input:
            st.session_state.jd_text = jd_input.strip()

    run_btn = st.button("开始智能匹配", type="primary", use_container_width=True)
    if run_btn:
        if not st.session_state.resume_text or not st.session_state.jd_text:
            st.warning("请先上传简历并填写岗位JD")
        else:
            with st.spinner("AI 正在多维分析匹配度，请稍候..."):
                # 匹配分析提示词
                match_prompt = f"""
请你作为资深互联网HR，分析简历与岗位JD的匹配情况，严格按照以下格式输出：
1. 总匹配度：0-100分
2. 硬技能：0-100分
3. 项目经验：0-100分
4. 软技能：0-100分
5. 学历背景：0-100分

然后分两块说明：【匹配优势】【现存差距】，每条简洁说明。

简历内容：
{st.session_state.resume_text}

岗位JD：
{st.session_state.jd_text}
                """
                match_result = llm_chat(match_prompt)
                st.subheader("📊 匹配分析报告")
                st.write(match_result)

                # 绘制雷达图
                scores = extract_score(match_result)
                cats = ["硬技能","项目经验","软技能","学历背景"]
                fig = go.Figure(go.Scatterpolar(
                    r=scores + [scores[0]],
                    theta=cats + [cats[0]],
                    fill="toself",
                    line_color="#1f77b4"
                ))
                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0,100])),
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)

# ---------------------- 标签页2：简历逐句优化 ----------------------
with tab2:
    st.subheader("简历针对性优化建议")
    if st.button("生成优化方案", use_container_width=True):
        if not st.session_state.resume_text or not st.session_state.jd_text:
            st.warning("请先完成简历上传与JD填写")
        else:
            with st.spinner("正在逐句拆解、优化简历..."):
                opt_prompt = f"""
结合下面岗位JD，对这份简历做逐段优化指导：指出不足、给出修改方向、可直接复用的表述，
区分：保留内容、补充内容、删减内容、话术润色。

简历：
{st.session_state.resume_text}

目标岗位JD：
{st.session_state.jd_text}
                """
                opt_res = llm_chat(opt_prompt)
                st.write(opt_res)

# ---------------------- 标签页3：能力提升方案 ----------------------
with tab3:
    st.subheader("个性化能力提升路径")
    if st.button("生成提升计划", use_container_width=True):
        if not st.session_state.resume_text or not st.session_state.jd_text:
            st.warning("请先完成简历上传与JD填写")
        else:
            with st.spinner("定制学习与提升方案..."):
                plan_prompt = f"""
基于简历和目标岗位的差距，为求职者制定短期能力提升方案：
1. 急需补齐的技能清单
2. 推荐学习渠道/练习方向
3. 可落地的小项目/实践建议
4. 投递前准备要点

简历：
{st.session_state.resume_text}
岗位JD：
{st.session_state.jd_text}
                """
                plan_res = llm_chat(plan_prompt)
                st.write(plan_res)

# ---------------------- 标签页4：HR模拟初筛 ----------------------
with tab4:
    st.subheader("模拟企业HR简历初筛")
    if st.button("开始模拟初筛", use_container_width=True):
        if not st.session_state.resume_text or not st.session_state.jd_text:
            st.warning("请先完成简历上传与JD填写")
        else:
            with st.spinner("HR正在审阅简历..."):
                hr_prompt = f"""
你是互联网大厂HR，执行简历初筛，只输出三部分：
1. 初筛结论：通过 / 待定 / 淘汰
2. 核心打分与理由
3. 简历风险点与改进建议

简历：
{st.session_state.resume_text}
招聘JD：
{st.session_state.jd_text}
                """
                hr_res = llm_chat(hr_prompt)
                st.write(hr_res)

# 页脚说明
st.divider()
st.caption("Offer捕手 · AI求职匹配智能体 | 用于Demo课题作业")
