import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px

# ======================================
# CONFIG
# ======================================

st.set_page_config(
    page_title="Registration Dashboard",
    page_icon="📊",
    layout="wide"
)

MONGO_URI = st.secrets["MONGO_URI"]
DB_NAME = st.secrets["DB_NAME"]
COLLECTION_NAME = st.secrets["COLLECTION_NAME"]

# ======================================
# LOAD DATA
# ======================================

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


# ======================================
# MULTI SELECT COUNT
# ======================================

def count_multi_select(series):

    values = []

    for item in series.dropna():

        for value in str(item).split(","):

            value = value.strip()

            if value:
                values.append(value)

    if not values:
        return pd.DataFrame(
            columns=["name", "count"]
        )

    result = (
        pd.Series(values)
        .value_counts()
        .reset_index()
    )

    result.columns = [
        "name",
        "count"
    ]

    return result


def count_join_dates(series):

    values = []

    for item in series.dropna():

        text = str(item)

        # แยกด้วย comma
        for value in text.split(","):

            value = value.strip()

            if value:
                values.append(value)

    if not values:

        return pd.DataFrame(
            columns=["วันที่", "จำนวน"]
        )

    result = (
        pd.Series(values)
        .value_counts()
        .reset_index()
    )

    result.columns = [
        "วันที่",
        "จำนวน"
    ]

    return result

# ======================================
# DATA
# ======================================

df = load_data()

st.title("📊 Registration Dashboard")

if df.empty:
    st.warning("ไม่พบข้อมูล")
    st.stop()
    
def split_multi_values(series):

    values = []

    for item in series.dropna():

        for value in str(item).split(","):

            value = value.strip()

            if value:
                values.append(value)

    return values


def get_multi_select_options(series):

    values = split_multi_values(series)

    return sorted(
        list(set(values))
    )

# ======================================
# SIDEBAR FILTER
# ======================================

st.sidebar.header("🔍 Filters")

gender_filter = st.sidebar.multiselect(
    "เพศ",
    sorted(df["เพศ"].dropna().unique())
    if "เพศ" in df.columns else []
)

group_filter = st.sidebar.multiselect(
    "กลุ่มผู้เข้าร่วม",
    get_multi_select_options(
        df["กลุ่มผู้เข้าร่วม"]
    )
)

date_filter = st.sidebar.multiselect(
    "วันที่เข้าร่วม",
    get_multi_select_options(
        df["วันที่เข้าร่วม"]
    )
)

keyword = st.sidebar.text_input(
    "ค้นหา"
)

filtered_df = df.copy()

if gender_filter:
    filtered_df = filtered_df[
        filtered_df["เพศ"].isin(
            gender_filter
        )
    ]

if group_filter:

    mask = pd.Series(
        False,
        index=filtered_df.index
    )

    for value in group_filter:

        mask |= (
            filtered_df["กลุ่มผู้เข้าร่วม"]
            .astype(str)
            .str.contains(
                value,
                regex=False,
                na=False
            )
        )

    filtered_df = filtered_df[mask]

if date_filter:

    mask = pd.Series(
        False,
        index=filtered_df.index
    )

    for value in date_filter:

        mask |= (
            filtered_df["วันที่เข้าร่วม"]
            .astype(str)
            .str.contains(
                value,
                regex=False,
                na=False
            )
        )

    filtered_df = filtered_df[mask]

if keyword:

    search_cols = [
        c
        for c in [
            "ชื่อ",
            "นามสกุล",
            "เบอร์โทรศัพท์",
            "อีเมล"
        ]
        if c in filtered_df.columns
    ]

    mask = pd.Series(
        False,
        index=filtered_df.index
    )

    for col in search_cols:

        mask |= (
            filtered_df[col]
            .astype(str)
            .str.contains(
                keyword,
                case=False,
                na=False
            )
        )

    filtered_df = filtered_df[mask]

# ======================================
# KPI
# ======================================

total = len(filtered_df)

male = 0
female = 0

if "เพศ" in filtered_df.columns:

    male = len(
        filtered_df[
            filtered_df["เพศ"]
            .astype(str)
            .str.contains("ชาย", na=False)
        ]
    )

    female = len(
        filtered_df[
            filtered_df["เพศ"]
            .astype(str)
            .str.contains("หญิง", na=False)
        ]
    )
    
    unknown = len(
        filtered_df[
            (
                filtered_df["เพศ"].isna()
            )
            |
            (
                filtered_df["เพศ"]
                .astype(str)
                .str.strip()
                .isin([
                    "",
                    "None",
                    "N/A",
                    "nan"
                ])
            )
        ]
    )

pdpa = 0

if "PDPA Consent" in filtered_df.columns:

    pdpa = len(
        filtered_df[
            filtered_df["PDPA Consent"]
            .notna()
        ]
    )

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "ผู้ลงทะเบียน",
    f"{total:,}"
)

c2.metric(
    "เพศชาย",
    f"{male:,}"
)

c3.metric(
    "เพศหญิง",
    f"{female:,}"
)

c4.metric(
    "ไม่ระบุเพศ",
    f"{unknown:,}"
)

c5.metric(
    "PDPA",
    f"{pdpa:,}"
)

st.divider()

st.subheader("📋 คุณภาพข้อมูล")

dq1, dq2, dq3 = st.columns(3)

dq1.metric(
    "ไม่ระบุเพศ",
    f"{unknown:,}"
)

dq2.metric(
    "ไม่มีเบอร์โทร",
    len(
        filtered_df[
            filtered_df["เบอร์โทรศัพท์"]
            .isna()
        ]
    )
)

dq3.metric(
    "ไม่มีอีเมล",
    len(
        filtered_df[
            filtered_df["อีเมล"]
            .isna()
        ]
    )
)

# ======================================
# ROW 1
# ======================================

col1, col2 = st.columns([1, 2])

with col1:

    if "เพศ" in filtered_df.columns:

        gender_df = filtered_df.copy()

        gender_df["เพศ"] = (
            gender_df["เพศ"]
            .fillna("ไม่ระบุ")
            .replace("", "ไม่ระบุ")
        )

        gender_df = (
            gender_df["เพศ"]
            .value_counts(dropna=False)
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
            title="เพศ"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

with col2:

    if "อายุ (ปี)" in filtered_df.columns:

        age_df = filtered_df.copy()

        age_df["อายุ (ปี)"] = pd.to_numeric(
            age_df["อายุ (ปี)"],
            errors="coerce"
        )

        age_df["ช่วงอายุ"] = pd.cut(
            age_df["อายุ (ปี)"],
            bins=[0,29,39,49,59,69,200],
            labels=[
                "<30",
                "30-39",
                "40-49",
                "50-59",
                "60-69",
                "70+"
            ]
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
            title="ช่วงอายุ"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# ======================================
# กลุ่มผู้เข้าร่วม
# ======================================

if "กลุ่มผู้เข้าร่วม" in filtered_df.columns:

    st.subheader("👥 กลุ่มผู้เข้าร่วม")

    group_df = count_multi_select(
        filtered_df["กลุ่มผู้เข้าร่วม"]
    )

    group_df.columns = [
        "กลุ่ม",
        "จำนวน"
    ]

    group_df = group_df.sort_values(
        "จำนวน",
        ascending=True
    )

    fig = px.bar(
        group_df,
        x="จำนวน",
        y="กลุ่ม",
        orientation="h",
        text="จำนวน",
        title="จำนวนผู้เข้าร่วมตามกลุ่ม"
    )

    fig.update_layout(
        height=450,
        yaxis_title="",
        xaxis_title="จำนวน"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# ======================================
# ROW 2
# ======================================

col1, col2 = st.columns(2)

with col1:

    if "วันที่เข้าร่วม" in filtered_df.columns:

        join_df = count_join_dates(
            filtered_df["วันที่เข้าร่วม"]
        )

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

with col2:

    if "หัวข้อที่สนใจ" in filtered_df.columns:

        topic_df = count_multi_select(
            filtered_df["หัวข้อที่สนใจ"]
        )

        fig = px.bar(
            topic_df.head(20),
            x="count",
            y="name",
            orientation="h",
            title="หัวข้อที่สนใจ"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# ======================================
# ROW 3
# ======================================

if "รู้จักงานจากช่องทาง" in filtered_df.columns:

    source_df = count_multi_select(
        filtered_df["รู้จักงานจากช่องทาง"]
    )

    fig = px.pie(
        source_df,
        names="name",
        values="count",
        title="ช่องทางรับรู้ข่าวสาร"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# ======================================
# TABLE
# ======================================

st.subheader(
    f"📋 รายชื่อผู้ลงทะเบียน ({len(filtered_df):,} รายการ)"
)

st.dataframe(
    filtered_df,
    use_container_width=True,
    height=600
)

csv = filtered_df.to_csv(
    index=False
).encode("utf-8-sig")

st.download_button(
    "📥 Export CSV",
    csv,
    "participants.csv",
    "text/csv"
)