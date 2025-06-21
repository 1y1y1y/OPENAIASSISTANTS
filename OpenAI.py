import streamlit as st
import openai
import time
import datetime
import os

if "API_KEY" in st.secrets:
    api_key = st.secrets["API_KEY"]
    assistant_id = st.secrets["ASSISTANT_ID"]
else:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("API_KEY")
    assistant_id = os.getenv("ASSISTANT_ID")

st.title("(주)사나이시스템 규정집 챗봇")


# 세션 상태에 대화 기록 초기화
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

user_input = st.text_input("무엇이 궁금한가요?")

if st.button("전송"):
    if not api_key or api_key.startswith("sk-여기에"):
        st.error("API Key가 코드에 올바르게 입력되지 않았습니다.")
    elif not user_input.strip():
        st.error("무엇이 궁금한가요?")
    else:
        client = openai.OpenAI(api_key=api_key)
        try:
            # 최초 1회 thread 생성
            if st.session_state.thread_id is None:
                thread = client.beta.threads.create()
                st.session_state.thread_id = thread.id

            # 사용자 메시지 추가
            st.session_state.messages.append({"role": "user", "content": user_input})

            # 메시지 전송
            client.beta.threads.messages.create(
                thread_id=st.session_state.thread_id,
                role="user",
                content=user_input
            )

            # 대기 메시지 표시
            wait_placeholder = st.empty()
            wait_msgs = [
                "문서를 확인중입니다. 잠시만 기다려주세요.",
                "문서를 확인중입니다. 잠시만 기다려주세요. .",
                "문서를 확인중입니다. 잠시만 기다려주세요. ..",
                "문서를 확인중입니다. 잠시만 기다려주세요. ..."
            ]
            wait_idx = 0

            # Run 생성 및 완료 대기
            run = client.beta.threads.runs.create(
                thread_id=st.session_state.thread_id,
                assistant_id=assistant_id
            )

            while True:
                run_status = client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id,
                    run_id=run.id
                )
                wait_placeholder.info(wait_msgs[wait_idx % len(wait_msgs)])
                wait_idx += 1
                if run_status.status in ["completed", "failed", "cancelled"]:
                    break
                time.sleep(0.7)

            wait_placeholder.empty()

            # 메시지 목록 가져오기 (최신 assistant 메시지 추출)
            messages = client.beta.threads.messages.list(
                thread_id=st.session_state.thread_id
            )
            # 최신 assistant 메시지 찾기
            assistant_message = None
            for msg in reversed(messages.data):
                if msg.role == "assistant":
                    assistant_message = msg.content[0].text.value
                    break

            if assistant_message:
                st.session_state.messages.append({"role": "assistant", "content": assistant_message})
                st.write("챗봇:")
                st.write(assistant_message)
            else:
                st.error("Assistant의 응답을 찾을 수 없습니다.")
        except Exception as e:
            if "Incorrect API key" in str(e) or "No API key provided" in str(e):
                st.error("API Key가 잘못되었습니다. 코드에 올바른 API Key를 입력해주세요.")
            else:
                st.error(f"응답 생성 중 오류 발생: {e}")

# 대화 내역 표시
st.subheader("대화 내역")
for message in st.session_state.messages:
    role = "사용자" if message["role"] == "user" else "챗봇"
    timestamp = datetime.datetime.now().strftime("%y.%m.%d.%H:%M")
    if role == "사용자":
        st.write(f"-- {timestamp} --------------")
    st.write(f"**{role} :** {message['content']}")