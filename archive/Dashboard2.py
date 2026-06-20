import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px

st.set_page_config(
    page_title="Dashboard",
    page_icon="📊",
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

        return df

    finally:
        client.close()


def count_multi_select(series):

    values = []

    for item in series.dropna():

        text = str(item)

        for v in text.split(","):
            v = v.strip()

            if v:
                values.append(v)

    return (
        pd.Series(values)
        .value_counts()
        .reset_index()
    )


st.title("📊 Registration Dashboard")

df = load_data()

if df.empty:
    st.warning("ไม่พบข้อมูล")
    st.stop()


# =====================
# KPI
# =====================

total = len(df)

male = 0
female = 0

if "เพศ" in df.columns:
    male = len(
        df[df["เพศ"].astype(str).str.contains("ชาย", na=False)]
    )

    female = len(
        df[df["เพศ"].astype(str).str.contains("หญิง", na=False)]
    )

pdpa = 0

if "PDPA Consent" in df.columns:
    pdpa = len(
        df[
            df["PDPA Consent"]
            .notna()
        ]
    )

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "ผู้ลงทะเบียน",
    f"{total:,}"
)

col2.metric(
    "เพศชาย",
    f"{male:,}"
)

col3.metric(
    "เพศหญิง",
    f"{female:,}"
)

col4.metric(
    "PDPA Consent",
    f"{pdpa:,}"
)

st.divider()

# =====================
# เพศ
# =====================

c1, c2 = st.columns(2)

with c1:

    if "เพศ" in df.columns:

        gender_df = (
            df["เพศ"]
            .value_counts()
            .reset_index()
        )

        gender_df.columns = [
            "เพศ",
            "จำนวน"
        ]

        fig = px.pie(
            gender_df,
            names="เพศ",
            values="จำนวน",
            title="สัดส่วนเพศ"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# =====================
# อายุ
# =====================

with c2:

    if "อายุ (ปี)" in df.columns:

        age_df = df.copy()

        age_df["อายุ (ปี)"] = pd.to_numeric(
            age_df["อายุ (ปี)"],
            errors="coerce"
        )

        bins = [
            0,
            29,
            39,
            49,
            59,
            69,
            200
        ]

        labels = [
            "<30",
            "30-39",
            "40-49",
            "50-59",
            "60-69",
            "70+"
        ]

        age_df["ช่วงอายุ"] = pd.cut(
            age_df["อายุ (ปี)"],
            bins=bins,
            labels=labels
        )

        summary = (
            age_df["ช่วงอายุ"]
            .value_counts()
            .sort_index()
            .reset_index()
        )

        summary.columns = [
            "ช่วงอายุ",
            "จำนวน"
        ]

        fig = px.bar(
            summary,
            x="ช่วงอายุ",
            y="จำนวน",
            title="ช่วงอายุผู้เข้าร่วม"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# =====================
# กลุ่มผู้เข้าร่วม
# =====================

c1, c2 = st.columns(2)

with c1:

    if "กลุ่มผู้เข้าร่วม" in df.columns:

        group_df = (
            df["กลุ่มผู้เข้าร่วม"]
            .value_counts()
            .reset_index()
        )

        group_df.columns = [
            "กลุ่ม",
            "จำนวน"
        ]

        fig = px.pie(
            group_df,
            names="กลุ่ม",
            values="จำนวน",
            hole=0.4,
            title="กลุ่มผู้เข้าร่วม"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# =====================
# วันที่เข้าร่วม
# =====================

with c2:

    if "วันที่เข้าร่วม" in df.columns:

        join_df = (
            df["วันที่เข้าร่วม"]
            .value_counts()
            .reset_index()
        )

        join_df.columns = [
            "วันที่",
            "จำนวน"
        ]

        fig = px.bar(
            join_df,
            x="วันที่",
            y="จำนวน",
            title="วันที่เข้าร่วม"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# =====================
# หัวข้อที่สนใจ
# =====================

if "หัวข้อที่สนใจ" in df.columns:

    st.subheader("📌 หัวข้อที่สนใจ")

    topic_df = count_multi_select(
        df["หัวข้อที่สนใจ"]
    )

    topic_df.columns = [
        "หัวข้อ",
        "จำนวน"
    ]

    fig = px.bar(
        topic_df.head(20),
        x="จำนวน",
        y="หัวข้อ",
        orientation="h"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =====================
# ช่องทางรับรู้
# =====================

if "รู้จักงานจากช่องทาง" in df.columns:

    st.subheader("📣 ช่องทางรับรู้ข่าวสาร")

    source_df = count_multi_select(
        df["รู้จักงานจากช่องทาง"]
    )

    source_df.columns = [
        "ช่องทาง",
        "จำนวน"
    ]

    fig = px.pie(
        source_df,
        names="ช่องทาง",
        values="จำนวน"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =====================
# ตารางข้อมูล
# =====================

st.subheader("📋 รายชื่อผู้ลงทะเบียน")

keyword = st.text_input(
    "ค้นหา"
)

if keyword:

    search_cols = [
        c
        for c in [
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

st.dataframe(
    df,
    use_container_width=True,
    height=600
)