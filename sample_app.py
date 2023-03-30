import streamlit as st
import pandas as pd
import calendar
import plost

st.title("Streamlit Sample")
st.subheader("A simple Streamlit app by :blue[Tyler Smith]")

# function used to get data for the dashboards, uses a variable url to get the data from.
# Implements the cache data decorator in Streamlit to boost performance by removing the need to fetch the data each time the app is rerun. 
@st.cache_data
def get_data(url):
    df = pd.read_csv(url)
    return df

# converts dataframe to csv for exporting
@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')

def weather_filter(state, city, month, colname, weather_df):
    return weather_df[colname].where((weather_df['Station.State']==state) & (weather_df['Station.City']==city) & (weather_df['Date.Month']==month)).dropna().tolist()

# calls to get_data function to get data sets to be used in the dashboards
weather_df = get_data("https://corgis-edu.github.io/corgis/datasets/csv/weather/weather.csv")
weather_df = weather_df[(weather_df['Date.Year']==2016)]
revenue_df = get_data("https://data.cityofnewyork.us/api/views/qbvv-9nzz/rows.csv?accessType=DOWNLOAD")

# tabs used to display two different options of how one might format a Streamlit app.
dashboard_view, scroll_view = st.tabs(["Dashboard View", "Scroll View"])

# --------------------- Traditional Style Dashboard ---------------------
with dashboard_view:

    # 3 dropdown selectors to select fields that will be used to filter the data.
    state_select, city_select, month_select = st.columns(3)

    with state_select:
        state_list =  weather_df['Station.State'].unique()
        state = st.selectbox("State", state_list)
    with city_select:
        city_list =  weather_df['Station.City'].where(weather_df['Station.State']==state).dropna().unique()
        city = st.selectbox("City", city_list)
    with month_select:
        month_list =  weather_df['Date.Month'].unique()
        month = st.selectbox("Month", month_list)

    # Horizontal divider
    st.markdown("---")

    # 2 metric displays including one with a delta indicating changes from past data. 
    avg_temp, high_low = st.columns(2)

    with avg_temp:
        temp_metric = weather_filter(state, city, month, 'Data.Temperature.Avg Temp', weather_df)
        last_month_temp = weather_filter(state, city, month-1, 'Data.Temperature.Avg Temp', weather_df)
        temp_metric = sum(temp_metric)/len(temp_metric)
        try:
            last_month_temp = sum(last_month_temp)/len(last_month_temp)
            temp_change = round(temp_metric - last_month_temp,1)
            temp_change = f'{temp_change} from last month'
        except:
            temp_change = "N/A"
        st.metric("Average Temperature", f'{temp_metric}\N{DEGREE SIGN}', f'{temp_change} from last month')

    with high_low:
        temp_high = weather_filter(state, city, month, 'Data.Temperature.Max Temp', weather_df)
        avg_high = sum(temp_high)/len(temp_high)
        temp_low = weather_filter(state, city, month, 'Data.Temperature.Min Temp', weather_df)
        avg_low = sum(temp_low)/len(temp_low)
        st.metric("Average High/Low", f'{avg_high}\N{DEGREE SIGN}/{avg_low}\N{DEGREE SIGN}')

    # Horizontal divider
    st.markdown("---")
    
    # Dataframe manipulation to prepare for the multiline chart
    st.subheader("High and low temperatures over the last 12 months")
    filtered_weather = weather_df[(weather_df['Station.State']==state) & (weather_df['Station.City']==city)]
    chart_data = filtered_weather[['Date.Month', 'Data.Temperature.Max Temp', 'Data.Temperature.Min Temp']].groupby('Date.Month').mean().T.transpose().reset_index()
    chart_data = chart_data.rename(columns={'Date.Month': 'Month', 'Data.Temperature.Max Temp': 'High', 'Data.Temperature.Min Temp': 'Low'})
    for i, row in chart_data.iterrows():
        val = chart_data.at[i, 'Month']
        new_val = calendar.month_abbr[val]
        chart_data.at[i, 'Month'] = new_val
    chart_data.columns = chart_data.columns.astype(str)     
    st.line_chart(chart_data, x='Month')
    
    with st.expander("See detailed data"):
        st.write("Below is the dataset used in the chart above.")
        st.dataframe(chart_data, use_container_width=True)


# --------------------- Scroll Style Dashboard ---------------------
with scroll_view:
    st.subheader("Revenue categories comparison for fiscal year")
    
    categories_filter, categories_hist = st.columns([1,2])

    # Filters section of the scrolling dashboard set nicely to the side of the chart
    with categories_filter:
        fiscal_year_list = revenue_df['FISCAL YEAR'].unique()
        latest = len(fiscal_year_list)-1
        fiscal_year = st.selectbox("Fiscal Year", fiscal_year_list, latest)
        categories_list = revenue_df['REVENUE CATEGORY'].where(revenue_df['FISCAL YEAR']==fiscal_year).dropna().unique()
        categories_list = categories_list[categories_list != 'TOTAL CITYWIDE REVENUES']
        categories = st.multiselect("Revenue Categories", categories_list, categories_list)

    with categories_hist:
        fiscal_chart_data = revenue_df[(revenue_df['FISCAL YEAR']==fiscal_year) & (revenue_df['REVENUE CATEGORY'].isin(categories))] 
        plost.bar_chart(
            data=fiscal_chart_data,
            bar='REVENUE CATEGORY',
            value='REVENUE AMOUNT',
            direction='horizontal'
        )

    # Horizontal divider
    st.markdown("---")

    st.subheader("Total yearly revenue over time")    
    revenue_chart_data = revenue_df[revenue_df['REVENUE CATEGORY']=='TOTAL CITYWIDE REVENUES']
    revenue_chart_data['FISCAL YEAR'] = pd.to_datetime(revenue_chart_data['FISCAL YEAR'], format='%Y')
    plost.line_chart(
        data=revenue_chart_data,
        x='FISCAL YEAR',
        y='REVENUE AMOUNT'
    )

    # Code used to export a set of data to a csv. Includes an expander to preview the data before exporting    
    st.subheader("Export Data")
    with st.expander("Data to be exported"):
        st.dataframe(revenue_df)

    csv = convert_df(revenue_df)

    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name='revenue.csv',
        mime='text/csv',)
    
# dataset used in this app located at https://corgis-edu.github.io/corgis/csv/weather/