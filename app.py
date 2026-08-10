def find_value_column(question, df):

    question_lower = question.lower()

    numeric_columns = (
        df.select_dtypes(include=["number"])
        .columns
        .tolist()
    )

    # Exact column-name match
    for column in numeric_columns:

        if str(column).lower() in question_lower:
            return column

    # Common business synonyms
    synonyms = {

        "sales": [
            "sales",
            "sale",
            "revenue",
            "turnover"
        ],

        "profit": [
            "profit",
            "earnings",
            "profitability"
        ],

        "quantity": [
            "quantity",
            "qty",
            "units",
            "items"
        ],

        "price": [
            "price",
            "amount",
            "cost"
        ],

        "rating": [
            "rating",
            "score"
        ],

        "discount": [
            "discount"
        ]
    }

    for actual_column, words in synonyms.items():

        for word in words:

            if word in question_lower:

                for column in numeric_columns:

                    if (
                        str(column).lower()
                        == actual_column
                    ):
                        return column

    # Partial matching
    for column in numeric_columns:

        column_name = (
            str(column)
            .lower()
            .replace("_", " ")
            .replace("-", " ")
        )

        if column_name in question_lower:
            return column

    # If only one numeric column exists
    if len(numeric_columns) == 1:
        return numeric_columns[0]

    return None


def find_group_column(question, df):

    question_lower = question.lower()

    categorical_columns = (
        df.select_dtypes(
            include=[
                "object",
                "category",
                "bool"
            ]
        )
        .columns
        .tolist()
    )

    # Exact column-name matching
    for column in categorical_columns:

        if str(column).lower() in question_lower:
            return column

    # Common group synonyms
    synonyms = {

        "city": [
            "city",
            "cities"
        ],

        "state": [
            "state",
            "region",
            "province"
        ],

        "country": [
            "country",
            "nation"
        ],

        "product": [
            "product",
            "item"
        ],

        "category": [
            "category",
            "segment",
            "type"
        ],

        "customer": [
            "customer",
            "client",
            "buyer"
        ],

        "department": [
            "department",
            "dept"
        ]
    }

    for actual_column, words in synonyms.items():

        for word in words:

            if word in question_lower:

                for column in categorical_columns:

                    if (
                        str(column).lower()
                        == actual_column
                    ):
                        return column

    return None


def detect_operation(question):

    question_lower = question.lower()

    # Average
    if any(
        word in question_lower
        for word in [
            "average",
            "avg",
            "mean"
        ]
    ):
        return "average"

    # Count
    if any(
        word in question_lower
        for word in [
            "count",
            "how many",
            "number of"
        ]
    ):
        return "count"

    # Maximum individual value
    if any(
        phrase in question_lower
        for phrase in [
            "maximum value",
            "max value",
            "maximum"
        ]
    ):
        return "maximum_value"

    # Minimum individual value
    if any(
        phrase in question_lower
        for phrase in [
            "minimum value",
            "min value",
            "minimum"
        ]
    ):
        return "minimum_value"

    # Highest grouped result
    if any(
        word in question_lower
        for word in [
            "highest",
            "top",
            "best",
            "largest",
            "most"
        ]
    ):
        return "highest"

    # Lowest grouped result
    if any(
        word in question_lower
        for word in [
            "lowest",
            "bottom",
            "worst",
            "smallest",
            "least"
        ]
    ):
        return "lowest"

    # Default
    return "total"


def universal_analyze_v4(
    question,
    df,
    gemini_info=None
):

    # ========================================================
    # USE GEMINI INTERPRETATION
    # ========================================================

    if gemini_info is not None:

        value_column = (
            gemini_info[
                "value_column"
            ]
        )

        group_column = (
            gemini_info[
                "group_column"
            ]
        )

        aggregation = (
            gemini_info[
                "aggregation"
            ]
        )

        ranking = (
            gemini_info[
                "ranking"
            ]
        )

        # Determine operation
        if aggregation == "MAX":

            operation = "maximum_value"

        elif aggregation == "MIN":

            operation = "minimum_value"

        elif aggregation == "MEAN":

            operation = "average"

        elif aggregation == "COUNT":

            operation = "count"

        elif ranking == "ASCENDING":

            operation = "lowest"

        elif ranking == "DESCENDING":

            operation = "highest"

        else:

            operation = "total"

    # ========================================================
    # FALLBACK TO V4 RULE ENGINE
    # ========================================================

    else:

        value_column = (
            find_value_column(
                question,
                df
            )
        )

        group_column = (
            find_group_column(
                question,
                df
            )
        )

        operation = (
            detect_operation(
                question
            )
        )

        aggregation = None
        ranking = None

    # ========================================================
    # VALIDATE METRIC
    # ========================================================

    if value_column is None:

        return {

            "question": question,

            "value_column": None,

            "group_column": group_column,

            "operation": operation,

            "aggregation": None,

            "ranking": None,

            "result": None,

            "best_category": None,

            "best_value": None
        }

    # ========================================================
    # GROUPED ANALYSIS
    # ========================================================

    if group_column is not None:

        clean_df = df.dropna(
            subset=[
                group_column,
                value_column
            ]
        )

        grouped = (
            clean_df
            .groupby(group_column)
            [value_column]
        )

        # Highest / lowest / total
        if operation in [
            "highest",
            "lowest",
            "total"
        ]:

            result = grouped.sum()

            aggregation = "SUM"

            if operation == "lowest":

                result = result.sort_values(
                    ascending=True
                )

                ranking = "ASCENDING"

            else:

                result = result.sort_values(
                    ascending=False
                )

                ranking = "DESCENDING"

        # Average
        elif operation == "average":

            result = grouped.mean()

            result = result.sort_values(
                ascending=False
            )

            aggregation = "MEAN"

            ranking = "DESCENDING"

        # Count
        elif operation == "count":

            result = grouped.count()

            result = result.sort_values(
                ascending=False
            )

            aggregation = "COUNT"

            ranking = "DESCENDING"

        # Maximum
        elif operation == "maximum_value":

            result = grouped.max()

            result = result.sort_values(
                ascending=False
            )

            aggregation = "MAX"

            ranking = "DESCENDING"

        # Minimum
        elif operation == "minimum_value":

            result = grouped.min()

            result = result.sort_values(
                ascending=True
            )

            aggregation = "MIN"

            ranking = "ASCENDING"

        else:

            result = grouped.sum()

            result = result.sort_values(
                ascending=False
            )

            aggregation = "SUM"

            ranking = "DESCENDING"

        # Best category
        if len(result) > 0:

            best_category = (
                result.index[0]
            )

            best_value = (
                result.iloc[0]
            )

        else:

            best_category = None
            best_value = None

        return {

            "question": question,

            "value_column": value_column,

            "group_column": group_column,

            "operation": operation,

            "aggregation": aggregation,

            "ranking": ranking,

            "result": result,

            "best_category": best_category,

            "best_value": best_value
        }

    # ========================================================
    # SINGLE COLUMN ANALYSIS
    # ========================================================

    series = (
        df[value_column]
        .dropna()
    )

    if operation == "average":

        result = series.mean()

        aggregation = "MEAN"

    elif operation == "count":

        result = series.count()

        aggregation = "COUNT"

    elif operation == "maximum_value":

        result = series.max()

        aggregation = "MAX"

    elif operation == "minimum_value":

        result = series.min()

        aggregation = "MIN"

    else:

        result = series.sum()

        aggregation = "SUM"

    return {

        "question": question,

        "value_column": value_column,

        "group_column": None,

        "operation": operation,

        "aggregation": aggregation,

        "ranking": None,

        "result": result,

        "best_category": None,

        "best_value": result
    }



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

    api_key = os.environ.get("GEMINI_API_KEY")

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

def get_gemini_interpretation(question, df):

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

    except Exception:

        return None


# ============================================================
# PARSE GEMINI RESPONSE
# ============================================================

def parse_gemini_response(response, df):

    if response is None:
        return None

    parsed = {}

    for line in response.splitlines():

        if ":" not in line:
            continue

        key, value = line.split(":", 1)

        parsed[key.strip().upper()] = value.strip()

    metric = parsed.get("METRIC")
    group_column = parsed.get("GROUP BY")
    aggregation = parsed.get("AGGREGATION")
    ranking = parsed.get("RANKING")

    if metric is None or metric.lower() == "none":
        metric = None

    if group_column is None or group_column.lower() == "none":
        group_column = None

    if ranking is None or ranking.lower() == "none":
        ranking = None

    if metric is not None:

        matched = None

        for column in df.columns:

            if str(column).lower() == metric.lower():

                matched = column
                break

        metric = matched

    if group_column is not None:

        matched = None

        for column in df.columns:

            if str(column).lower() == group_column.lower():

                matched = column
                break

        group_column = matched

    return {
        "value_column": metric,
        "group_column": group_column,
        "aggregation": aggregation.upper() if aggregation else None,
        "ranking": ranking.upper() if ranking else None
    }


# ============================================================
# BUSINESS INSIGHT
# ============================================================

def generate_business_insight(analysis):

    value_column = analysis.get("value_column")
    group_column = analysis.get("group_column")
    operation = analysis.get("operation")
    best_category = analysis.get("best_category")
    best_value = analysis.get("best_value")

    if group_column is not None and best_category is not None:

        if operation == "highest":
            return (
                f"{best_category} has the highest total "
                f"{value_column}, with {best_value:,.2f}."
            )

        if operation == "lowest":
            return (
                f"{best_category} has the lowest total "
                f"{value_column}, with {best_value:,.2f}."
            )

        if operation == "average":
            return (
                f"{best_category} has the highest average "
                f"{value_column}, at {best_value:,.2f}."
            )

        if operation == "count":
            return (
                f"{best_category} has the highest number "
                f"of records, with {best_value:,.0f}."
            )

        if operation == "maximum_value":
            return (
                f"{best_category} has the highest individual "
                f"{value_column}, at {best_value:,.2f}."
            )

        if operation == "minimum_value":
            return (
                f"{best_category} has the lowest individual "
                f"{value_column}, at {best_value:,.2f}."
            )

    if best_value is not None:

        if operation == "total":
            return f"The total {value_column} is {best_value:,.2f}."

        if operation == "average":
            return f"The average {value_column} is {best_value:,.2f}."

        if operation == "maximum_value":
            return f"The maximum {value_column} is {best_value:,.2f}."

        if operation == "minimum_value":
            return f"The minimum {value_column} is {best_value:,.2f}."

        if operation == "count":
            return (
                f"There are {best_value:,.0f} "
                f"available {value_column} records."
            )

    return "Analysis completed successfully."


# ============================================================
# CHART
# ============================================================

def create_chart(analysis):

    result = analysis.get("result")
    group_column = analysis.get("group_column")
    value_column = analysis.get("value_column")

    if (
        result is None
        or group_column is None
        or not isinstance(result, pd.Series)
    ):
        return None

    chart_data = result.head(10).reset_index()

    chart_data.columns = [
        group_column,
        value_column
    ]

    fig = px.bar(
        chart_data,
        x=value_column,
        y=group_column,
        orientation="h",
        title=f"{value_column} by {group_column}",
        text_auto=".2s"
    )

    fig.update_layout(height=500)

    return fig


# ============================================================
# PAGE
# ============================================================

st.title("🤖 Universal AI Data Analyst")

st.write(
    "Upload a CSV or Excel dataset and ask "
    "questions using natural language."
)

if GEMINI_AVAILABLE:

    st.success("🟢 Gemini 3.5 Flash connected")

else:

    st.warning(
        "🟡 Gemini unavailable. V4 engine will be used."
    )


# ============================================================
# FILE UPLOAD
# ============================================================

uploaded_file = st.file_uploader(
    "📁 Upload your dataset",
    type=["csv", "xlsx", "xls"]
)


# ============================================================
# APPLICATION
# ============================================================

if uploaded_file is not None:

    try:

        if uploaded_file.name.lower().endswith(".csv"):

            df = pd.read_csv(uploaded_file)

        else:

            df = pd.read_excel(uploaded_file)

        if df.empty:

            st.error("The uploaded dataset is empty.")
            st.stop()

        # --------------------------------------------
        # OVERVIEW
        # --------------------------------------------

        st.subheader("📊 Dataset Overview")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Rows", f"{df.shape[0]:,}")

        col2.metric("Columns", df.shape[1])

        col3.metric(
            "Missing Values",
            f"{df.isnull().sum().sum():,}"
        )

        col4.metric(
            "Duplicate Rows",
            f"{df.duplicated().sum():,}"
        )

        # --------------------------------------------
        # PREVIEW
        # --------------------------------------------

        st.subheader("🔍 Data Preview")

        st.dataframe(
            df.head(10),
            use_container_width=True
        )

        # --------------------------------------------
        # QUESTION
        # --------------------------------------------

        st.subheader("💬 Ask Your Data")

        question = st.text_input(
            "Enter your question",
            placeholder="Which city has the highest revenue?"
        )

        if st.button(
            "🔎 Analyze",
            type="primary"
        ):

            if not question.strip():

                st.warning("Please enter a question.")

            else:

                gemini_response = None
                gemini_info = None

                # ------------------------------------
                # GEMINI
                # ------------------------------------

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

                # ------------------------------------
                # V4
                # ------------------------------------

                with st.spinner(
                    "Analyzing dataset..."
                ):

                    analysis = universal_analyze_v4(
                        question,
                        df,
                        gemini_info
                    )

                # ------------------------------------
                # GEMINI INTERPRETATION
                # ------------------------------------

                if gemini_response:

                    with st.expander(
                        "🤖 Gemini Interpretation"
                    ):

                        st.code(
                            gemini_response
                        )

                # ------------------------------------
                # INTERPRETATION
                # ------------------------------------

                st.subheader(
                    "🧠 Question Interpretation"
                )

                i1, i2, i3, i4 = st.columns(4)

                i1.metric(
                    "Metric",
                    analysis.get("value_column") or "None"
                )

                i2.metric(
                    "Group By",
                    analysis.get("group_column") or "None"
                )

                i3.metric(
                    "Aggregation",
                    analysis.get("aggregation") or "None"
                )

                i4.metric(
                    "Ranking",
                    analysis.get("ranking") or "None"
                )

                # ------------------------------------
                # RESULT
                # ------------------------------------

                result = analysis.get("result")

                if result is None:

                    st.error(
                        "I couldn't determine the answer "
                        "from the dataset."
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

                        if analysis.get(
                            "best_category"
                        ) is not None:

                            st.success(
                                f"**Answer:** "
                                f"{analysis['best_category']} "
                                f"with **"
                                f"{analysis['best_value']:,.2f}"
                                f"**"
                            )

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

                    # --------------------------------
                    # BUSINESS INSIGHT
                    # --------------------------------

                    st.subheader(
                        "💡 Business Insight"
                    )

                    st.info(
                        generate_business_insight(
                            analysis
                        )
                    )

    except Exception as e:

        st.error("Something went wrong.")

        st.exception(e)
