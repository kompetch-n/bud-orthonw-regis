import streamlit as st
import pandas as pd
from pymongo import MongoClient

# ==========================
# MongoDB Config
# ==========================
MONGO_URI = st.secrets["MONGO_URI"]
DB_NAME = st.secrets["DB_NAME"]
COLLECTION_NAME = st.secrets["COLLECTION_NAME"]


# ==========================
# Upload Function
# ==========================
def upload_to_mongodb(df):
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    # แทน NaN เป็น None
    df = df.where(pd.notnull(df), None)

    new_records = []

    for record in df.to_dict(orient="records"):

        # ถ้ามี submission_id นี้แล้ว ให้ข้าม
        if collection.find_one({"submission_id": record["submission_id"]}):
            continue

        new_records.append(record)

    if len(new_records) > 0:
        result = collection.insert_many(new_records)
        return len(result.inserted_ids), len(df) - len(new_records)

    return 0, len(df)


# ==========================
# Streamlit UI
# ==========================

st.set_page_config(page_title="Upload Excel", layout="wide")

st.title("📤 Upload Excel to MongoDB")

uploaded_file = st.file_uploader(
    "เลือกไฟล์ Excel",
    type=["xlsx", "xls"]
)

if uploaded_file is not None:

    try:
        df = pd.read_excel(uploaded_file, dtype=str)

        # แทน NaN เป็นค่าว่าง
        df = df.fillna("")

        st.success("อ่านไฟล์สำเร็จ")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("จำนวนข้อมูล", len(df))

        with col2:
            st.metric("จำนวนคอลัมน์", len(df.columns))

        st.subheader("Columns")
        st.write(list(df.columns))

        st.subheader("Preview")
        st.dataframe(df.head(10), use_container_width=True)

        st.warning(
            f"กำลังจะ Upload จำนวน **{len(df)} รายการ** ไปยัง MongoDB"
        )

        if st.button(
            "✅ Confirm Upload",
            type="primary",
            use_container_width=True
        ):

            with st.spinner("Uploading..."):

                inserted, duplicated = upload_to_mongodb(df)

            st.success("Upload เสร็จเรียบร้อย")

            st.write(f"✅ เพิ่มข้อมูลใหม่ : {inserted} รายการ")
            st.write(f"⏭️ ข้ามข้อมูลซ้ำ : {duplicated} รายการ")

    except Exception as e:
        st.error(str(e))