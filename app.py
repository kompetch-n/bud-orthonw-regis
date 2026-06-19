import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(
    page_title="Form Excel Parser",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Form Excel Parser")
st.write("อัปโหลดไฟล์ Excel เพื่อแยกข้อมูล question_answer เป็นคอลัมน์")

def parse_question_answer(text):
    if pd.isna(text):
        return {}

    lines = str(text).split("\n")
    result = {}
    current_question = None

    for line in lines:
        line = line.strip()

        if not line:
            continue

        q_match = re.match(r"Q\d+\s+(.*)", line)
        if q_match:
            current_question = q_match.group(1).strip()
            continue

        a_match = re.match(r"A\d+\s+(.*)", line)
        if a_match and current_question:
            result[current_question] = a_match.group(1).strip()

    return result


uploaded_file = st.file_uploader(
    "เลือกไฟล์ Excel",
    type=["xlsx", "xls"]
)

if uploaded_file is not None:

    try:
        df = pd.read_excel(uploaded_file)

        st.success(f"อ่านข้อมูลสำเร็จ ({len(df)} รายการ)")

        if "question_answer" not in df.columns:
            st.error("ไม่พบคอลัมน์ question_answer")
            st.stop()

        # แยกข้อมูล
        answers = df["question_answer"].apply(parse_question_answer)

        answers_df = pd.json_normalize(answers)

        # เปลี่ยนชื่อ field id
        column_mapping = {
            "f_8885a8bdad83": "กลุ่มผู้เข้าร่วม",
            "f_2239d4e7b39b": "วันที่เข้าร่วม",
        }

        answers_df.rename(columns=column_mapping, inplace=True)

        # รวมข้อมูล
        result_df = pd.concat(
            [
                df.drop(columns=["question_answer"]),
                answers_df
            ],
            axis=1
        )

        # เรียงลำดับคอลัมน์
        preferred_columns = [
            "submission_id",
            "form_id",
            "form_title",
            "submitted_at",
            "hospital",
            "คำนำหน้า",
            "ชื่อ",
            "นามสกุล",
            "อายุ (ปี)",
            "เพศ",
            "เบอร์โทรศัพท์",
            "อีเมล",
            "อาชีพ",
            "หน่วยงาน / สังกัด",
            "กลุ่มผู้เข้าร่วม",
            "วันที่เข้าร่วม",
            "มีโรคประจำตัวหรือไม่?",
            "เคยได้รับบาดเจ็บกระดูก/ข้อ/กล้ามเนื้อหรือไม่?",
            "หัวข้อที่สนใจ",
            "รู้จักงานจากช่องทาง",
            "PDPA Consent",
            "has_replied",
            "from_page",
        ]

        existing_columns = [
            c for c in preferred_columns
            if c in result_df.columns
        ]

        remaining_columns = [
            c for c in result_df.columns
            if c not in existing_columns
        ]

        result_df = result_df[
            existing_columns + remaining_columns
        ]

        st.subheader("Preview")
        st.dataframe(
            result_df.head(20),
            use_container_width=True
        )

        st.write(f"จำนวนข้อมูล: {len(result_df):,} รายการ")

        # Export เป็น Excel ใน Memory
        output = BytesIO()

        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:
            result_df.to_excel(
                writer,
                index=False,
                sheet_name="Result"
            )

        output.seek(0)

        st.download_button(
            label="📥 ดาวน์โหลดไฟล์ Result.xlsx",
            data=output,
            file_name="result.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {str(e)}")