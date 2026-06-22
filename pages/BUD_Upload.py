import streamlit as st
import pandas as pd
import re
from io import BytesIO
from pymongo import MongoClient
import streamlit as st

MONGO_URI = st.secrets["MONGO_URI"]
DB_NAME = st.secrets["DB_NAME"]
COLLECTION_NAME = st.secrets["COLLECTION_NAME"]

def upload_to_mongodb(df):

    client = MongoClient(MONGO_URI)

    try:
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]

        inserted = 0
        updated = 0

        records = (
            df.where(pd.notnull(df), None)
            .to_dict("records")
        )

        for row in records:

            submission_id = row.get("submission_id")

            if not submission_id:
                continue

            result = collection.update_one(
                {"submission_id": submission_id},
                {"$set": row},
                upsert=True
            )

            if result.upserted_id:
                inserted += 1
            else:
                updated += 1

        return inserted, updated

    finally:
        client.close()

def check_existing(df):

    client = MongoClient(MONGO_URI)

    try:
        collection = client[DB_NAME][COLLECTION_NAME]

        ids = (
            df["submission_id"]
            .dropna()
            .tolist()
        )

        existing = collection.count_documents(
            {
                "submission_id": {
                    "$in": ids
                }
            }
        )

        new = len(ids) - existing

        return new, existing

    finally:
        client.close()

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
            "f_59fbd8776643": "หมายเหตุ",
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
            "หมายเหตุ",
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

        st.subheader("📋 รายละเอียดข้อมูลที่จะอัปโหลด")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("จำนวนรายการ", len(result_df))

        with col2:
            st.metric("จำนวนคอลัมน์", len(result_df.columns))

        with col3:
            st.metric(
                "Submission ID ไม่ซ้ำ",
                result_df["submission_id"].nunique()
            )

        st.write("### Columns")

        st.write(result_df.columns.tolist())
        
        # ตรวจสอบข้อมูลใน MongoDB
        new_count, update_count = check_existing(result_df)

        st.info(f"""
        📦 ข้อมูลที่จะอัปโหลด

        ➕ เพิ่มใหม่ : {new_count:,} รายการ

        🔄 อัปเดต : {update_count:,} รายการ
        """)

        st.warning("กรุณาตรวจสอบข้อมูลก่อนอัปโหลด")

        confirm = st.checkbox(
            "ฉันตรวจสอบข้อมูลเรียบร้อยแล้ว"
        )

        if confirm:

            if st.button(
                "🚀 Upload to MongoDB",
                type="primary",
                use_container_width=True
            ):

                with st.spinner("กำลังอัปโหลด..."):

                    try:

                        inserted, updated = upload_to_mongodb(result_df)

                        st.success(
                            f"""
        อัปโหลดสำเร็จ

        ➕ เพิ่มใหม่ : {inserted:,} รายการ

        🔄 อัปเดต : {updated:,} รายการ
        """
                        )

                    except Exception as e:

                        st.error(
                            f"Upload ไม่สำเร็จ : {e}"
                        )
        
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