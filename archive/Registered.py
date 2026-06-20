import streamlit as st
import pandas as pd
from pymongo import MongoClient

st.set_page_config(
    page_title="รายการผู้ลงทะเบียน",
    page_icon="📋",
    layout="wide"
)

MONGO_URI = st.secrets["MONGO_URI"]
DB_NAME = st.secrets["DB_NAME"]
COLLECTION_NAME = st.secrets["COLLECTION_NAME"]


@st.cache_data(ttl=60)
def load_data():

    client = MongoClient(MONGO_URI)

    try:

        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]

        data = list(
            collection.find(
                {},
                {"_id": 0}
            )
        )

        df = pd.DataFrame(data)

        column_mapping = {
            "f_59fbd8776643": "หมายเหตุ"
        }

        df.rename(
            columns=column_mapping,
            inplace=True
        )

        return df

    finally:
        client.close()


st.title("📋 รายการผู้ลงทะเบียน")

try:

    df = load_data()

    if df.empty:
        st.warning("ไม่พบข้อมูล")
        st.stop()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "จำนวนทั้งหมด",
            f"{len(df):,}"
        )

    with col2:
        if "เพศ" in df.columns:
            st.metric(
                "เพศชาย",
                len(df[df["เพศ"] == "ชาย"])
            )

    with col3:
        if "เพศ" in df.columns:
            st.metric(
                "เพศหญิง",
                len(df[df["เพศ"] == "หญิง"])
            )

    st.divider()

    keyword = st.text_input(
        "ค้นหา ชื่อ / นามสกุล / เบอร์โทรศัพท์"
    )

    if keyword:

        search_cols = [
            c for c in [
                "ชื่อ",
                "นามสกุล",
                "เบอร์โทรศัพท์",
                "อีเมล"
            ]
            if c in df.columns
        ]

        mask = False

        for col in search_cols:
            mask |= (
                df[col]
                .astype(str)
                .str.contains(
                    keyword,
                    case=False,
                    na=False
                )
            )

        df = df[mask]

    st.write(
        f"พบข้อมูล {len(df):,} รายการ"
    )

    st.dataframe(
        df,
        use_container_width=True,
        height=700
    )

    csv = df.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        "📥 Export CSV",
        csv,
        "participants.csv",
        "text/csv"
    )

except Exception as e:

    st.error(str(e))