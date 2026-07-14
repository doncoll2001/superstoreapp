import streamlit as st
import pandas as pd
import altair as alt # new
import plotly.express as px # new

@st.cache_data
def load_data():
    data = pd.read_excel("Super+Store+Data.xlsx")
    df = data.copy()
    df = df.rename(columns={
        "Rows ID":"Row_ID",
        "Order ID":"Order_ID",
        "Ship Date":"Ship_Date",
        "Customer ID":"Customer_ID",
        "Product ID":"Product_ID",
        "Ship Mode":"Ship_Mode",
        "Order Date":"Order_Date",
        "Sub-Category":"Sub_Category",
        "Product Name":"Product_Name",
        "Customer Name":"Customer_Name"
    })
    # add year column
    df["Year"] = df["Order_Date"].dt.year
    df["Month"] = df["Order_Date"].dt.month_name
    df["Quarter"] = df["Order_Date"].dt.quarter
    df["Month_No"] = df["Order_Date"].dt.month
    df["Year_Month"]= df["Order_Date"].dt.to_period("M").dt.to_timestamp()
    df["Shipping_Days"] = (
        df["Ship_Date"] - df["Order_Date"]
        ).dt.days
    df["Profit_Margin"] = (df["Profit"]/df["Sales"])
    df["Loss"] = df["Profit"] < 0
    return df

try:
    df= load_data()
    st.title("SUPER STORE ANALYSIS")
    # st.dataframe(df)
    # st.write(df.isnull().sum()) # check for null values
    # st.write(df.dtypes)
    # filters
    filters = {
        "Year":df["Year"].unique(),
        "Month":df["Month"].unique(),
        "Ship_Mode":df["Ship_Mode"].unique(),
        "Segment":df["Segment"].unique(),
        "State":df["State"].unique(),
        "Category":df["Category"].unique(),
        "City":df["City"].unique()
    }
    # store user selection
    selected_filters = {}

    #generate multi-select widgets dynamically
    for key, options in filters.items ():
         selected_filters[key] = st.sidebar.multiselect(key , options)

    # selected data filtered
    filtered_df = df.copy()

    # apply user selections to the data
    for key, selected_values in selected_filters.items():
        if selected_values:
            filtered_df = filtered_df[filtered_df[key].isin(selected_values)]

    # view data
    st.dataframe(filtered_df)
    
    # section 2: Calculations
    total_sales = filtered_df["Sales"].sum()
    total_profit = filtered_df["Profit"].sum()
    no_orders = len(filtered_df)
    no_customers = filtered_df["Customer_ID"].nunique()

    col1 , col2 , col3 , col4 = st.columns(4)

    with col1:
        
        st.metric("Total Sales",f"${total_sales:,.2f}")
    with col2:
        st.metric("Total Profit",f"${total_profit:,.2f}")

    with col3:
        st.metric("Order",f"{no_orders}")

    with col4:
        st.metric("Customers",f"{no_customers}")
    
# charts
    # chart data
    temp_df = (
       filtered_df.groupby("Year",as_index=False)
       .agg(Sales=("Sales","sum"), Profit = ("Profit","sum"))
       .sort_values("Year")
    )
# not part of the code (only used for troubleshooting)
    # st.write("check table")
    # st.dataframe(temp_df)
    st.header("Yearly Trend - Sales & Profit")
    
    metric_choice = st.radio(
        "Trend Metric",
        ["Sales","Profit"],
        horizontal=True, key="trend_metric",
    )

    trend = (
        alt.Chart(temp_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("Year:O",title="Year"),
            y=alt.Y(f"{metric_choice}:Q", title=metric_choice),
            tooltip=[
                alt.Tooltip("Year:O",title="Year"),
                alt.Tooltip(f"{metric_choice}:Q",format="$,.2f")

            ],
        )
        .properties(height=360)
        .interactive()
    )

    st.altair_chart(trend,use_container_width=True)
    # side bar
    #st.sidebar.multiselect("1","Name")

    # chart 2
    st.header("Locations & Operational Performance")

    geo_col,ship_col = st.columns([1.2,1])

    # chart data
    state_df = (
        filtered_df.groupby(["State","Region"], as_index=False)
        .agg(Sales=("Sales","sum"),Profit=("Profit","sum"))
        .sort_values("Sales",ascending=False)
        .head(15)
    )
    
    with geo_col:
        st.write("Location Performance")
        fig_state= px.bar(
            state_df.sort_values("Profit"), x="Profit",y="State",
            orientation = "h",color="Region",
            title= "Top states by sales , ranked by profit",
            hover_data = {"Sales":":,.2f"},
    )

        fig_state.add_vline(x=0, line_dash="dash")
        fig_state.update_layout(height=480,
                        margin=dict(l=10,r=10,t=50,b=10))
        st.plotly_chart(fig_state, use_container_width=True)

    # shipping data 
    ship_df =(
        filtered_df.groupby("Ship_Mode", as_index=False)
        .agg(
            Average_Shipping_Days = ("Shipping_Days","mean"),
            Sales=("Sales","sum"),
            Profit=("Profit","sum"),
            Orders=("Order_ID","nunique"),

        )

    )
    
    # chart
    with ship_col:
        st.write("Operational Performance")
        ship_chart = (
            alt.Chart(ship_df).mark_bar()
            .encode(
                x=alt.X("Average_Shipping_Days:Q",
                    title="Average Shipping Days"),
                y=alt.Y("Ship_Mode:N",sort="-x",title=None)
            )
            .properties(title="Delivery speed by ship mode",height=380)
        )
        st.altair_chart(ship_chart,use_container_width=True) 

    #  summary
    st.header("summary")
    st.write()
    
        
except Exception as e:
    st.exception(e)