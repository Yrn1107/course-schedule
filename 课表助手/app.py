import streamlit as st
import json
import os
from datetime import datetime, timedelta
from openai import OpenAI

# ================= 配置区 =================
import streamlit as st
API_KEY = st.secrets["API_KEY"]  # 请替换成你自己的Key
DATA_FILE = "data.json"
# ==========================================

# 初始化DeepSeek客户端
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

# ---------- 数据读写函数 ----------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------- 页面设置 ----------
st.set_page_config(page_title="课表提醒助手", page_icon="📅")
st.title("📅 校园课表提醒助手")

# 初始化session状态
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

data = load_data()

# ---------- 用户管理模块 ----------
if not st.session_state.logged_in:
    st.subheader("用户登录 / 注册")
    tab1, tab2 = st.tabs(["登录", "注册"])
    
    with tab1:
        login_user = st.text_input("用户名", key="login_user")
        login_pwd = st.text_input("密码", type="password", key="login_pwd")
        if st.button("登录"):
            if login_user in data["users"] and data["users"][login_user]["password"] == login_pwd:
                st.session_state.logged_in = True
                st.session_state.username = login_user
                st.rerun()
            else:
                st.error("用户名或密码错误")
                
    with tab2:
        reg_user = st.text_input("新用户名", key="reg_user")
        reg_pwd = st.text_input("新密码", type="password", key="reg_pwd")
        if st.button("注册"):
            if reg_user in data["users"]:
                st.error("用户名已存在")
            elif reg_user and reg_pwd:
                data["users"][reg_user] = {"password": reg_pwd, "courses": []}
                save_data(data)
                st.success("注册成功，请登录")
            else:
                st.warning("请填写完整信息")

else:
    # ---------- 已登录状态 ----------
    st.sidebar.write(f"👤 当前用户：{st.session_state.username}")
    if st.sidebar.button("退出登录"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    user_courses = data["users"][st.session_state.username]["courses"]

    # 1. 提醒模块（在每次刷新时检查）
    now = datetime.now()
    for course in user_courses:
        # 简化逻辑：假设课程按星期几匹配，且时间差在30分钟内
        # 这里为了Demo演示，我们简化判断逻辑，只要今天有课且时间接近就提醒
        # 实际项目中需要更精确的日期换算
        pass # 提醒逻辑稍后放在AI查询后触发，方便演示

    # 2. 课表录入模块
    with st.expander("➕ 添加课程", expanded=False):
        with st.form("add_course"):
            c_name = st.text_input("课程名称")
            c_day = st.selectbox("星期", ["周一", "周二", "周三", "周四", "周五", "周六", "周日"])
            c_time = st.text_input("节次（如：1-2节）")
            c_room = st.text_input("教室")
            submit = st.form_submit_button("添加")
            if submit and c_name:
                user_courses.append({
                    "course_name": c_name,
                    "day_of_week": c_day,
                    "period": c_time,
                    "classroom": c_room
                })
                save_data(data)
                st.success(f"已添加 {c_name}")
                st.rerun()

    # 3. 展示当前课表
    st.subheader("📋 我的课表")
    if user_courses:
        st.table(user_courses)
    else:
        st.info("暂无课程，请先添加。")

    # 4. AI对话查询模块
    st.subheader("💬 AI 课表助手")
    user_query = st.text_input("输入你的问题（如：我明天有什么课？）")
    
    if st.button("发送") and user_query:
        with st.spinner("AI思考中..."):
            # 构造Prompt给DeepSeek
            course_context = json.dumps(user_courses, ensure_ascii=False)
            prompt = f"""
            你是一个校园课表助手。用户的课表数据如下（JSON格式）：
            {course_context}
            
            用户的问题是：{user_query}
            
            请根据课表数据回答用户的问题。如果用户问的是时间，请先判断今天是星期几（今天是{now.strftime('%A')}），然后推算。
            回答要自然、简洁。如果查询不到相关课程，请如实告知。
            """
            
            try:
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "你是一个 helpful 的校园课表助手。"},
                        {"role": "user", "content": prompt}
                    ],
                    stream=False
                )
                ai_reply = response.choices[0].message.content
                st.success(ai_reply)

                # 触发提醒演示（演示脚本关键部分）
                if "明天" in user_query or "今天" in user_query:
                    st.warning("🔔 【提醒】检测到您正在查询近期课程，如果临近上课时间，系统会在此处弹窗提醒！")
                    
            except Exception as e:
                st.error(f"API调用失败：{e}")