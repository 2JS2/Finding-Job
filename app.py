import json
from datetime import datetime, timedelta
from urllib.parse import quote

import google.generativeai as genai
import streamlit as st

st.set_page_config(
    page_title="Job Recruitment Filtering App",
    page_icon="🎯",
    layout="wide",
)

with st.sidebar:
    st.header("⚙️ Settings")

    api_key = st.text_input(
        "Google AI Studio API Key",
        type="password",
        placeholder="Enter your API key",
    )

    st.divider()
    st.subheader("🔍 Filtering Criteria")

    target_domain = st.text_input(
        "Target Domain/Industry",
        value="반도체",
    )

    target_role = st.text_input(
        "Target Job Role",
        value="양산기술",
    )

    target_process = st.text_input(
        "Target Process/Equipment",
        value="CMP, 세정",
    )

st.title("🎯 Job Recruitment Filtering App")
st.caption("AI 기반 채용 공고 정밀 분석 및 필터링 도구")

st.divider()

col1, col2 = st.columns(2)

with col1:
    corp_nm = st.text_input(
        "Company Name (corpNm)",
        value="삼성전자",
    )

with col2:
    wanted_title = st.text_input(
        "Job Posting Title (wantedTitle)",
        value="반도체 제조 공정 양산기술 엔지니어 채용",
    )

pref_cond = st.text_area(
    "Preferred Qualifications (prefCond)",
    value=(
        "- 반도체 관련 전공(전자, 재료, 화학공학 등) 학사 이상\n"
        "- CMP, 세정 공정 경험자 우대\n"
        "- 반도체 양산 라인 근무 경험자 우대\n"
        "- 통계적 공정관리(SPC) 및 six sigma 관련 지식 보유자 우대\n"
        "- 영어 커뮤니케이션 가능자 우대"
    ),
    height=180,
)

job_cont = st.text_area(
    "Job Description/Duties (jobCont)",
    value=(
        "[담당업무]\n"
        "- 반도체 양산 공정 중 CMP 및 세정 공정 기술 개발 및 관리\n"
        "- 공정 수율 개선 및 불량 분석(Yield Enhancement)\n"
        "- 장비 셋업 및 신규 공정 조건 최적화\n"
        "- 공정 이상 발생 시 원인 분석 및 대응\n"
        "- 협력사 및 유관부서와의 협업을 통한 공정 개선 활동\n\n"
        "[자격요건]\n"
        "- 학사 이상 (전자, 재료, 화학, 기계 관련 전공)\n"
        "- 신입 및 경력 지원 가능"
    ),
    height=220,
)

st.divider()

run_button = st.button("🚀 Run Precise Analysis", use_container_width=True, type="primary")

SYSTEM_PROMPT_TEMPLATE = """
You are an expert Recruitment Agent specializing in Materials Science and Chemical Engineering. Your task is to precisely analyze job postings fetched from the Worknet API and determine if they match the user's specific target criteria.
Target Domain/Industry: {domain}
Target Job Role: {job_role}
Target Process/Equipment: {target_process}
Input Data from Worknet API:
- Company Name: {corpNm}
- Job Posting Title: {wantedTitle}
- Job Description/Duties: {jobCont}
- Preferred Qualifications: {prefCond}
Strict Rules:
1. Match Determination (is_match): Set is_match to true ONLY if academic background and target process (e.g., CMP, cleaning) are mentioned or strongly implied. Otherwise, false.
2. Deadline Extraction (deadline): Format as 'YYYY-MM-DD'. If rolling recruitment ("상시채용", "채용시까지"), set to '2026-12-31'.
3. Objective Rationale (match_reason): One-sentence reason in Korean.
4. Calendar Event Title (calendar_summary): In Korean. Format: [{corpNm}] {wantedTitle} 서류 마감. If rolling: [상시채용][{corpNm}] {wantedTitle}
Target JSON Schema:
{{
  "is_match": boolean,
  "company_name": "string",
  "job_title": "string",
  "deadline": "string (YYYY-MM-DD)",
  "match_reason": "string",
  "calendar_summary": "string"
}}
"""

if run_button:
    if not api_key:
        st.error("Please enter your Google AI Studio API Key in the sidebar.")
    else:
        with st.spinner("Analyzing job posting..."):
            try:
                genai.configure(api_key=api_key)

                prompt = SYSTEM_PROMPT_TEMPLATE.format(
                    domain=target_domain,
                    job_role=target_role,
                    target_process=target_process,
                    corpNm=corp_nm,
                    wantedTitle=wanted_title,
                    jobCont=job_cont,
                    prefCond=pref_cond,
                )

                model = genai.GenerativeModel('gemini-1.5-flash-latest')
                response = model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"},
                )

                result = json.loads(response.text)

                st.divider()
                st.subheader("📋 Analysis Result")

                if result.get("is_match"):
                    st.success(f"✅ MATCH: {result.get('company_name')} - {result.get('job_title')}")
                else:
                    st.error(f"❌ NO MATCH: {result.get('company_name')} - {result.get('job_title')}")

                st.write(f"**Match Reason:** {result.get('match_reason')}")
                st.write(f"**Deadline:** {result.get('deadline')}")
                st.write(f"**Calendar Summary:** {result.get('calendar_summary')}")

                with st.expander("Raw JSON Response"):
                    st.json(result)

                if result.get("is_match"):
                    deadline_str = result.get("deadline", "")
                    start_date = datetime.strptime(deadline_str, "%Y-%m-%d")
                    end_date = start_date + timedelta(days=1)

                    start_str = start_date.strftime("%Y%m%d")
                    end_str = end_date.strftime("%Y%m%d")
                    dates_param = f"{start_str}/{end_str}"

                    encoded_summary = quote(result.get("calendar_summary", ""))
                    encoded_details = quote(result.get("match_reason", ""))

                    calendar_url = (
                        "https://calendar.google.com/calendar/render"
                        f"?action=TEMPLATE&text={encoded_summary}"
                        f"&dates={dates_param}"
                        f"&details={encoded_details}"
                    )

                    st.divider()
                    st.subheader("📅 Save to Calendar")
                    st.link_button(
                        "📅 Add Deadline to Google Calendar",
                        calendar_url,
                        use_container_width=True,
                        type="primary",
                    )

            except json.JSONDecodeError:
                st.error("Failed to parse JSON response from Gemini.")
                st.text(response.text)
            except Exception as e:
                st.error(f"An error occurred: {e}")
