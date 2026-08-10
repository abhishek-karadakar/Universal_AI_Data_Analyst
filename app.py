
import os
import streamlit as st
import pandas as pd
import plotly.express as px

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Universal AI Data Analyst",
    page_icon="🤖",
    layout="wide"
)


# ============================================================
# GEMINI SETUP
# ============================================================

GEMINI_AVAILABLE = False
client = None

try:

    from google import genai

    api_key = os.environ.get(
        "GEMINI_API_KEY"
    )

    if api_key:

        client = genai.Client(
            api_key=api_key
        )

        GEMINI_AVAILABLE = True

except Exception:

    GEMINI_AVAILABLE = False


# ============================================================
# GEMINI INTERPRETATION
# ============================================================

def get_gemini_interpretation(
    question,
    df
):

    if not GEMINI_AVAILABLE:

        return None

    columns = ", ".join(
        str(column)
        for column in df.columns
    )

    prompt = f"""
You are an expert data analyst.

Dataset columns:
{columns}

User question:
{question}

Return EXACTLY four lines:

METRIC: <numeric column name or None>
GROUP BY: <categorical column name or None>
AGGREGATION: <SUM, MEAN, MAX, MIN, COUNT>
RANKING: <DESCENDING, ASCENDING, or None>

Rules:

1. Highest/most/top/largest by category:
   SUM + DESCENDING

2. Lowest/least/bottom/smallest by category:
   SUM + ASCENDING

3. Average/mean:
   MEAN

4. Maximum value:
   MAX

5. Minimum value:
   MIN

6. Total:
   SUM

7. Count/how many:
   COUNT

Use only columns that exist in the dataset.

Return ONLY the four lines.
"""

    try:

        response = client.models.generate_content(

            model="gemini-3.5-flash",

            contents=prompt
        )

        return response.text.strip()

    except Exception as e:

        # Gemini failure should NOT stop the application
        return None


# ============================================================
# PARSE GEMINI RESPONSE
# ============================================================

def parse_gemini_response(
    response,
    df
):

    if response is None:

        return None

    parsed = {}

    for line in response.splitlines():

        if ":" not in line:
            continue

        key, value = line.split(
            ":",
            1
        )

        parsed[
            key.strip().upper()
        ] = value.strip()

    metric = parsed.get(
        "METRIC"
    )

    group_column = parsed.get(
        "GROUP BY"
    )

    aggregation = parsed.get(
        "AGGREGATION"
    )

    ranking = parsed.get(
        "RANKING"
    )

    # ----------------------------------------
    # None handling
    # ----------------------------------------

    if (
        metric is None
        or metric.lower() == "none"
    ):

        metric = None

    if (
        group_column is None
        or group_column.lower() == "none"
    ):

        group_column = None

    if (
        ranking is None
        or ranking.lower() == "none"
    ):

        ranking = None

    # ----------------------------------------
    # Match to actual dataframe columns
    # ----------------------------------------

    if metric is not None:

        matched = None

        for column in df.columns:

            if (
                str(column).lower()
                == metric.lower()
            ):

                matched = column
                break

        metric = matched

    if group_column is not None:

        matched = None

        for column in df.columns:

            if (
                str(column).lower()
                == group_column.lower()
            ):

                matched = column
                break

        group_column = matched

    if aggregation:

        aggregation = aggregation.upper()

    if ranking:

        ranking = ranking.upper()

    return {

        "value_column": metric,

        "group_column": group_column,

        "aggregation": aggregation,

        "ranking": ranking
    }


# ============================================================
# BUSINESS INSIGHT
# ============================================================

def generate_business_insight(
    analysis
):

    value_column = analysis.get(
        "value_column"
    )

    group_column = analysis.get(
        "group_column"
    )

    operation = analysis.get(
        "operation"
    )

    best_category = analysis.get(
        "best_category"
    )

    best_value = analysis.get(
        "best_value"
    )

    # ----------------------------------------
    # Grouped analysis
    # ----------------------------------------

    if (
        group_column is not None
        and best_category is not None
    ):

        if operation == "highest":

            return (
                f"{best_category} has the "
                f"highest total "
                f"{value_column}, with "
                f"{best_value:,.2f}."
            )

        if operation == "lowest":

            return (
                f"{best_category} has the "
                f"lowest total "
                f"{value_column}, with "
                f"{best_value:,.2f}."
            )

        if operation == "average":

            return (
                f"{best_category} has the "
                f"highest average "
                f"{value_column}, at "
                f"{best_value:,.2f}."
            )

        if operation == "count":

            return (
                f"{best_category} has the "
                f"highest number of records, "
                f"with {best_value:,.0f}."
            )

        if operation == "maximum_value":

            return (
                f"{best_category} has the "
                f"highest individual "
                f"{value_column}, at "
                f"{best_value:,.2f}."
            )

        if operation == "minimum_value":

            return (
                f"{best_category} has the "
                f"lowest individual "
                f"{value_column}, at "
                f"{best_value:,.2f}."
            )

    # ----------------------------------------
    # Overall analysis
    # ----------------------------------------

    if best_value is not None:

        if operation == "total":

            return (
                f"The total {value_column} "
                f"is {best_value:,.2f}."
            )

        if operation == "average":

            return (
                f"The average {value_column} "
                f"is {best_value:,.2f}."
            )

        if operation == "maximum_value":

            return (
                f"The maximum {value_column} "
                f"is {best_value:,.2f}."
            )

        if operation == "minimum_value":

            return (
                f"The minimum {value_column} "
                f"is {best_value:,.2f}."
            )

        if operation == "count":

            return (
                f"There are "
                f"{best_value:,.0f} "
                f"available {value_column} "
                f"records."
            )

    return "Analysis completed successfully."


# ============================================================
# CREATE CHART
# ============================================================

def create_chart(
    analysis
):

    result = analysis.get(
        "result"
    )

    group_column = analysis.get(
        "group_column"
    )

    value_column = analysis.get(
        "value_column"
    )

    if (
        result is None
        or group_column is None
        or not isinstance(
            result,
            pd.Series
        )
    ):

        return None

    chart_data = (
        result
        .head(10)
        .reset_index()
    )

    chart_data.columns = [
        group_column,
        value_column
    ]

    fig = px.bar(

        chart_data,

        x=value_column,

        y=group_column,

        orientation="h",

        title=(
            f"{value_column} by "
            f"{group_column}"
        ),

        text_auto=".2s"
    )

    fig.update_layout(
        height=500
    )

    return fig


# ============================================================
# PAGE TITLE
# ============================================================

st.title(
    "🤖 Universal AI Data Analyst"
)

st.write(
    "Upload a CSV or Excel dataset "
    "and ask questions using natural language."
)


# ============================================================
# GEMINI STATUS
# ============================================================

if GEMINI_AVAILABLE:

    st.success(
        "🟢 Gemini 3.5 Flash connected"
    )

else:

    st.warning(
        "🟡 Gemini unavailable. "
        "V4 engine will be used."
    )


# ============================================================
# FILE UPLOAD
# ============================================================

uploaded_file = st.file_uploader(

    "📁 Upload your dataset",

    type=[
        "csv",
        "xlsx",
        "xls"
    ]
)


# ============================================================
# APPLICATION
# ============================================================

if uploaded_file is not None:

    try:

        # ----------------------------------------
        # Load dataset
        # ----------------------------------------

        if uploaded_file.name.lower().endswith(
            ".csv"
        ):

            df = pd.read_csv(
                uploaded_file
            )

        else:

            df = pd.read_excel(
                uploaded_file
            )

        if df.empty:

            st.error(
                "The uploaded dataset is empty."
            )

            st.stop()

        # ----------------------------------------
        # Dataset overview
        # ----------------------------------------

        st.subheader(
            "📊 Dataset Overview"
        )

        col1, col2, col3, col4 = (
            st.columns(4)
        )

        col1.metric(
            "Rows",
            f"{df.shape[0]:,}"
        )

        col2.metric(
            "Columns",
            df.shape[1]
        )

        col3.metric(
            "Missing Values",
            f"{df.isnull().sum().sum():,}"
        )

        col4.metric(
            "Duplicate Rows",
            f"{df.duplicated().sum():,}"
        )

        # ----------------------------------------
        # Dataset preview
        # ----------------------------------------

        st.subheader(
            "🔍 Data Preview"
        )

        st.dataframe(
            df.head(10),
            use_container_width=True
        )

        # ----------------------------------------
        # Ask your data
        # ----------------------------------------

        st.subheader(
            "💬 Ask Your Data"
        )

        question = st.text_input(

            "Enter your question",

            placeholder=(
                "Which city has the "
                "highest sales?"
            )
        )

        if st.button(
            "🔎 Analyze",
            type="primary"
        ):

            if not question.strip():

                st.warning(
                    "Please enter a question."
                )

            else:

                # ====================================
                # GEMINI
                # ====================================

                gemini_response = None
                gemini_info = None

                if GEMINI_AVAILABLE:

                    with st.spinner(
                        "Understanding question..."
                    ):

                        gemini_response = (
                            get_gemini_interpretation(
                                question,
                                df
                            )
                        )

                    if gemini_response:

                        gemini_info = (
                            parse_gemini_response(
                                gemini_response,
                                df
                            )
                        )

                # ====================================
                # V4 ENGINE
                # ====================================

                with st.spinner(
                    "Analyzing dataset..."
                ):

                    analysis = (
                        universal_analyze_v4(
                            question,
                            df,
                            gemini_info
                        )
                    )

                # ====================================
                # AI INTERPRETATION
                # ====================================

                if gemini_response:

                    with st.expander(
                        "🤖 Gemini Interpretation"
                    ):

                        st.code(
                            gemini_response
                        )

                # ====================================
                # QUESTION INTERPRETATION
                # ====================================

                st.subheader(
                    "🧠 Question Interpretation"
                )

                i1, i2, i3, i4 = (
                    st.columns(4)
                )

                i1.metric(
                    "Metric",
                    analysis.get(
                        "value_column"
                    ) or "None"
                )

                i2.metric(
                    "Group By",
                    analysis.get(
                        "group_column"
                    ) or "None"
                )

                i3.metric(
                    "Aggregation",
                    analysis.get(
                        "aggregation"
                    ) or "None"
                )

                i4.metric(
                    "Ranking",
                    analysis.get(
                        "ranking"
                    ) or "None"
                )

                # ====================================
                # RESULT
                # ====================================

                result = analysis.get(
                    "result"
                )

                if result is None:

                    st.error(
                        "I couldn't determine "
                        "the answer from the "
                        "dataset."
                    )

                else:

                    st.subheader(
                        "📈 Analysis Result"
                    )

                    if isinstance(
                        result,
                        pd.Series
                    ):

                        display_result = (
                            result
                            .head(10)
                            .rename("Value")
                            .reset_index()
                        )

                        st.dataframe(
                            display_result,
                            use_container_width=True
                        )

                        if (
                            analysis.get(
                                "best_category"
                            ) is not None
                        ):

                            st.success(

                                f"**Answer:** "
                                f"{analysis['best_category']} "
                                f"with **"
                                f"{analysis['best_value']:,.2f}"
                                f"**"
                            )

                        # Chart

                        chart = create_chart(
                            analysis
                        )

                        if chart is not None:

                            st.subheader(
                                "📊 Visualization"
                            )

                            st.plotly_chart(
                                chart,
                                use_container_width=True
                            )

                    else:

                        st.success(

                            f"**Answer:** "
                            f"{result:,.2f}"
                        )

                    # =================================
                    # BUSINESS INSIGHT
                    # =================================

                    st.subheader(
                        "💡 Business Insight"
                    )

                    st.info(
                        generate_business_insight(
                            analysis
                        )
                    )

    except Exception as e:

        st.error(
            "Something went wrong."
        )

        st.exception(e)
