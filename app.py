import streamlit as st
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="My Home Care Plus - AI 국어 튜터", layout="wide")
st.title("📚 고1 비문학 매일 3지문 챌린지")
st.caption("사장님이 직접 만드신 자녀를 위한 AI 학습 도구입니다.")

# ---------------------------------------------------------
# [필수 수정 구역]
# 1) 사장님의 구글 시트 주소를 넣으세요.
SHEET_URL = "https://docs.google.com/spreadsheets/d/1GiEiYoMsN3KEzyXV307KERWYhnD8gEo_IXUhytop9xw/edit?usp=sharing"

# 2) 발급받은 Gemini API 키를 넣으세요.
GEMINI_API_KEY = "AIzaSyC6xLPcorUXqLjx8oHVsV4dJ8pl6uCmXBI"
# ---------------------------------------------------------

# Gemini AI 설정
genai.configure(api_key=GEMINI_API_KEY)
# 모델 이름 앞에 'models/'를 붙여주거나, 최신 이름인 'gemini-1.5-flash-latest'를 권장합니다.
ai_model = genai.GenerativeModel('gemini-2.5-flash')

try:
    # 2. 데이터 불러오기 (실시간 반영을 위해 ttl=0)
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=SHEET_URL, ttl=0)

    # 데이터 정제 (공백 제거 및 빈 제목 삭제)
    df.columns = df.columns.str.strip()
    df = df.dropna(subset=['title'])

    # 3. 사이드바 지문 선택
    st.sidebar.header("📖 오늘의 학습")
    selected_title = st.sidebar.selectbox("공부할 지문을 고르세요", df['title'].unique())

    # 4. 선택된 지문 데이터 추출
    data = df[df['title'] == selected_title].iloc[0]

    # 5. 화면 레이아웃 (좌: 지문 / 우: 문제)
    col1, col2 = st.columns([1.5, 1])

    with col1:
        st.subheader(f"📄 {data['title']}")
        st.markdown(f"**분야:** `{data['category']}` | **번호:** `{data['id']}`")
        
        # 지문 전체 출력 (확장기 사용으로 깔끔하게)
        with st.expander("📖 지문 본문 전체 읽기 (클릭하여 펼치기)", expanded=True):
            st.write(data['content'])
        
        # --- AI 선생님 기능 추가 ---
        st.divider()
        st.subheader("🤖 AI 선생님에게 질문하기")
        user_query = st.text_input("지문에서 이해 안 되는 문장이나 단어를 물어보세요!", placeholder="예: '고맥락 문화'가 무슨 뜻이야?")

        if user_query:
            with st.spinner("AI 선생님이 답변을 준비하고 있습니다..."):
                prompt = f"""
                당신은 고등학생을 가르치는 친절한 국어 선생님입니다. 
                아래 지문을 바탕으로 학생의 질문에 아주 쉽게 설명해 주세요.
                
                [지문 내용]: {data['content']}
                [학생 질문]: {user_query}
                """
                response = ai_model.generate_content(prompt)
                st.chat_message("assistant").write(response.text)

    with col2:
        st.subheader("📝 문제 풀이")
        st.info(f"**문제:** {data['question']}")
        
        # 선택지 안내
        st.write("**[보기]**")
        st.code(data['options'], language=None)
        
        # 정답 선택 (중복 방지를 위한 고유 key 설정)
        user_ans = st.radio("정답 선택", [1, 2, 3, 4, 5], horizontal=True, key="ans_radio")
        
        if st.button("제출 및 정답 확인", key="check_btn"):
            if int(user_ans) == int(data['answer']):
                st.success("정답입니다! 정말 잘했어요! 🎉")
                st.balloons()
                with st.expander("✅ 해설 보기"):
                    st.write(data['explanation'])
            else:
                st.error(f"아쉽네요. 정답은 {int(data['answer'])}번입니다.")
                with st.expander("💡 오답 노트 (클릭)"):
                    st.write(data['explanation'])

except Exception as e:
    st.error("연결 중에 문제가 발생했습니다.")
    st.info("1. 시트 주소와 API 키가 정확한지 확인해 주세요.")
    st.info("2. 시트의 첫 번째 줄(헤더)이 영문 소문자로 id, category, title, content... 순서인지 확인해 주세요.")
    st.write("상세 오류:", e)