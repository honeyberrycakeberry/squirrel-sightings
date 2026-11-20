"""
Name: Liz Mullan
CS230: Section 7
Data: central_park_squirrels_2018

#[DEPLOY] IDENTIFY & EXPLAIN - uploaded all necessary files to GitHub, added a requirements txt file so all the packages will be imported
URL: https://squirrel-sightings.streamlit.app/

Description:
This program shows where squirrels were spotted in Central Park by shift,
which dates had the most sightings, and how often each activity was recorded
for different fur colors.

LLM Used: ChatGPT

References:
https://deckgl.readthedocs.io/en/latest/layer.html
https://deck.gl/docs/api-reference/aggregation-layers/heatmap-layer
https://docs.streamlit.io/develop/api-reference/charts/st.pydeck_chart
https://deckgl.readthedocs.io/en/latest/deck.html

"""

import matplotlib.pyplot as plt
import pandas as pd
import pydeck as pdk
import streamlit as st

#Constants
DATA_FILE = "central_park_squirrels_2018.csv"
ACTIVITIES = ["running", "chasing", "climbing", "eating", "foraging"]


def load_sightings(file_name):
    """Input: data file name; Output: df dataframe"""
    # Read date column in as a string
    df = pd.read_csv(file_name, dtype={"date": str})

    #convert text to date/time values, mmddyyyy turned to pandas Timestamp
    dates = pd.to_datetime(df["date"], format="%m%d%Y")
    df["Sighting date"] = dates.dt.date #keep only the date, no time
    return df


#[FUNC2P] A function with two or more parameters, one of which has a default value
#[REUSE_FUNC] AUGMENT – created counting function for fur color table and reused for highest sighting date and daily sightings chart
# #Count sightings by specific column, default is date
def count_sightings(df, column="Sighting date"):
    """Input: df dataframe; Output: sorted counts of sightings"""
    counts = df.groupby(column).size()  #group rows by the input column, size counts how many rows in the group

    #[SORT] Sort data in ascending or descending order, by one or more columns
    return counts.sort_values(ascending=False) #descending, large to small


def show_sighting_map(df):
    """Input: df dataframe"""
    #[ST2] A slider to adjust how much nearby sightings blend together
    map_radius = st.slider("Heatmap smoothing", 20, 60, 40, step=10)
    selected_shift = st.segmented_control(
        "Select a shift", ["All", "AM", "PM"], default="All", required=True)
    st.caption("Yellow areas show fewer nearby sightings, while orange and red areas show more.")

    #Keep sightings that have both coordinates
    # [COLUMNS] Add or drop columns from a DataFrame
    map_df = df.dropna(subset=["lon", "lat"]) #keeps rows that have both longitude and latitude
    if selected_shift != "All": #if they don't click all, all just gives everything
        map_df = map_df[map_df["shift"] == selected_shift] #df has rows with the selected shift AM/PM

    if map_df.empty: #exception catching
        st.info("No sightings with coordinates for this shift")
        return


    #[MAP] PyDeck heatmap using latitude and longitude
    #Each sighting adds one to the heatmap, nearby sightings blend together
    heatmap = pdk.Layer(
        "HeatmapLayer",
        id="squirrel-heatmap",
        data=map_df[["lon", "lat"]],
        get_position="[lon, lat]",
        get_weight=1, #each sighting weighted 1
        aggregation="SUM", #adds weights to show density (darker color) of sightings in area
        radius_pixels=map_radius,
        #Use a smaller heatmap texture to reduce the rendering work
        weights_texture_size=512,
        opacity=0.65,
        color_range=[ #yellow orange to red rgb values
            [255, 255, 178], [254, 217, 118], [254, 178, 76],
            [253, 141, 60], [240, 59, 32], [189, 0, 38],
        ],
    )

    #Center the map on Central Park
    view_state = pdk.ViewState(
        latitude=40.7825, longitude=-73.9665, zoom=13,
        min_zoom=10, max_zoom=19, pitch=0, bearing=0)
    squirrel_map = pdk.Deck(
        layers=[heatmap],
        initial_view_state=view_state,
        map_style=pdk.map_styles.ROAD,
        map_provider="carto",
        tooltip=False,
    )
    st.pydeck_chart(squirrel_map, height=600, key="squirrel_map")
    st.write(f"**{len(map_df):,} total sightings**") #print total sightings across the time period for the selected shift

def show_peak_date(df):
    """Input: df dataframe, filtered in main"""
    st.subheader("Highest Sighting Date") #output highest sighting date section
    if df.empty: #exception catching
        st.info("No sightings recorded for this fur color")
        return

    #[FUNCCALL2] A function that you call at least two different places in your program
    #Count by date to find what date had the highest number of sightings for whatever fur color filter is applied
    daily_counts = count_sightings(df)

    #[MAXMIN] Find the largest or smallest values
    #[MANUAL_CALC] AUGMENT - created manual calculation loop for the maximum daily count
    peak_count = 0
    for i in daily_counts:
        if i > peak_count:
            peak_count = i # once for loop ends then tempmax should contain the largest value in daily_counts

    #peak_count = daily_counts.max() #find the max count of sightings <-- FINDING THE MAX REGULARLY
    peak_date = daily_counts.idxmax() #find the index/date of the max count

    st.write(f"**{peak_date:%B %d, %Y}**: **{peak_count:,}** sightings")


def show_daily_table(df, first_date, last_date):
    """Input: filtered df dataframe, first date, last date"""
    st.subheader("Total Sightings by Fur Color")
    selected_date = st.date_input( #date picker
        "Select a date for the table",
        value=first_date, #date picker starts on earliest date
        min_value=first_date, #dates available are between the earliest and latest date in the file
        max_value=last_date,
    )
    day_df = df[df["Sighting date"] == selected_date] #new dataframe containing only rows with the selected date

    if day_df.empty: #no rows
        st.info("No sightings recorded")
    else:
        color_counts = count_sightings(day_df, "primary_fur_color") #using previous count function
        color_table = color_counts.reset_index(name="Sightings") #turn counts into a table, name counts column
        color_table.columns = ["Primary Fur Color", "Sightings"] #set table column headers
        st.dataframe(color_table, hide_index=True) #don't show auto row numbers


def show_daily_chart(df, survey_dates):
    """Input: filtered df dataframe, dates with sightings in the file"""
    with st.container(horizontal=True, horizontal_alignment="center"): #container holding subheading
        st.subheader("Daily Sightings", width=600)
    if df.empty:
        st.info("No sightings recorded for this fur color")
        return

    #Use date order for the line chart and show zero if the color was not seen that day
    daily_counts = count_sightings(df).reindex(survey_dates, fill_value=0)
    #[LISTCOMP] A list comprehension
    #[LIST_COMP] IDENTIFY & EXPLAIN – formats each dates as short labels for the chart x axis,
    # %b gives the abbreviated month, like Oct, and %d gives the two-digit day, like 06 or 10
    date_labels = [day.strftime("%b %d") for day in survey_dates]

    #[CHART2] Line chart showing how sightings changed by date
    fig, ax = plt.subplots(figsize=(6, 4)) #make chart 6x4
    ax.plot(survey_dates, daily_counts, color="#2E7D32", marker="o") #plot date counts with green line and dot at each point
    ax.set_xticks(survey_dates, date_labels) #put a tick at each survey date and use the formatted date as label
    ax.set_title("Sightings on Survey Dates") #title
    ax.set_xlabel("Sighting date") #x axis label
    ax.set_ylabel("Sightings") #y axis label
    ax.set_ylim(bottom=0) #start axis at zero

    highest_count = int(daily_counts.max()) #highest daily count, no decimal point
    tick_step = max(1, highest_count // 5) #evenly spaced tick marks, ticks of 1 minimum or divide the highest count by 5 and round down
    ax.set_yticks(range(0, highest_count + 1, tick_step)) #place ticks from zero up to the highest count, use step amt
    ax.tick_params(axis="x", labelrotation=55) #tilt date labels so they fit better
    fig.tight_layout() #tight spacing
    st.pyplot(fig) #display chart
    plt.close(fig) #ends Matplotlib after displaying it


# def show_activity_chart(df, color_options):
#     with st.container(width=350):
#         selected_color = st.radio("Select a fur color for activities", color_options, horizontal=True)
#         count_type = st.selectbox("Show activities as", ["Percentages", "Counts"])
#
#     activity_df = df
#     if selected_color != "All":
#         activity_df = df[df["primary_fur_color"] == selected_color]
#
#     activity_counts = activity_df[ACTIVITIES].sum()
#     x_label = "Sightings (#)"
#     if count_type == "Percentages":
#         activity_counts = activity_counts / len(activity_df) * 100
#         x_label = "Sightings (%)"
#
#     activity_counts = activity_counts.sort_values(ascending=False)
#
#     activity_labels = []
#     for activity in activity_counts.index:
#         activity_labels.append(activity.title())
#
#     fur_colors = {"All": "#2E7D32", "Black": "#292D32",
#                   "Cinnamon": "#B56535", "Gray": "#85939A"}
#
#     fig, ax = plt.subplots(figsize=(7, 4))
#     bars = ax.barh(activity_labels, activity_counts, color=fur_colors[selected_color])
#     ax.invert_yaxis()
#     ax.set_title(f"Recorded Activities - {selected_color}")
#     ax.set_xlabel(x_label)
#     ax.set_ylabel("Activity")
#     if count_type == "Percentages":
#         ax.set_xlim(0, 100)
#         ax.bar_label(bars, fmt="{:.1f}%", padding=3)
#     else:
#         highest_count = int(activity_counts.max())
#         tick_step = max(1, highest_count // 5)
#         ax.set_xticks(range(0, highest_count + 1, tick_step))
#         ax.bar_label(bars, fmt="{:.0f}", padding=3)
#         ax.margins(x=0.15)
#     fig.tight_layout()
#     st.pyplot(fig)
#     plt.close(fig)

#[AI_REWRITE] REVISE/REWRITE - rewrote the AI's activity chart function in a way that is simpler, easier to follow, and slightly more efficient
#Original AI output above
def show_activity_chart(df, color_options):
    """Input: df dataframe, fur color choices for the radio buttons"""
    with st.container(width=350):
        selected_color = st.radio("Select a fur color for activities", color_options, horizontal=True)
        #[ST1] A Streamlit dropdown list
        count_type = st.selectbox("Show activities as", ["Percentages", "Counts"])
    show_percent = count_type == "Percentages" #checking the user chart type selection, used to see if values will need
    #to be converted to % and to change the x axis

    if selected_color == "All": #all keeps the whole df
        activity_df = df
    else:
        activity_df = df[df["primary_fur_color"] == selected_color] #otherwise, filter df for selected fur color

    #uses ACTIVITIES constant, sums rows where there was a match, most common activity shown at the top
    values = activity_df[ACTIVITIES].sum().sort_values(ascending=False)

    if show_percent:
        values = values / len(activity_df) * 100 #convert values to % if selected

    #[ITERLOOP] Loop through the sorted activities to make chart labels
    labels = []
    for activity in values.index:  #index holds the activity names, already sorted largest to smallest
        labels.append(activity.title())  #capitalize each name for y axis

    #[DICT_DRIVEN] IDENTIFY & EXPLAIN
    # This dictionary stores a bar color for each fur color option
    # The chart uses it to look up which color to use for the bars
    # If the user picks "Cinnamon", fur_colors["Cinnamon"] gives "#B56535", so the bars are drawn in brown
    fur_colors = {"All": "#2E7D32", "Black": "#292D32",
                  "Cinnamon": "#B56535", "Gray": "#85939A"}

    #[CHART1] Horizontal bar chart with custom colors, titles, and labels
    fig, ax = plt.subplots(figsize=(7, 4)) #make chart 7x4
    bars = ax.barh(labels, values, color=fur_colors[selected_color]) #bar labeled, plotted, colored
    ax.invert_yaxis() #flip to put the largest bar at the top, because barh puts the smallest at top default
    ax.set_title(f"Recorded Activities - {selected_color}") #chart title
    ax.set_ylabel("Activity") #y axis title

    #The differences between the two modes are the x axis and data labels
    if show_percent:
        ax.set_xlabel("Sightings (%)") #x axis for %
        ax.set_xlim(0, 100) #x axis is 0-100
        ax.bar_label(bars, fmt="{:.1f}%", padding=3) #format data labels with % and one decimal
    else:
        ax.set_xlabel("Sightings (#)") #x axis for the counts
        ax.bar_label(bars, fmt="{:.0f}", padding=3) #format data labels
        ax.margins(x=0.15) #leave space for the numbers at the ends of the bars

    fig.tight_layout() #tight spacing
    st.pyplot(fig) #plot chart
    plt.close(fig) #end MatPlotLib

def main():
    st.set_page_config(page_title="Central Park Squirrel Sightings", page_icon="🐿️", layout="wide") #browser tab title and layout

    #[ST3] Header photo and footer photo at the bottom and easter egg
    with st.container(horizontal=True, horizontal_alignment="center"):
        st.image("images/image1.jpg", width=1200)

    #One centered column keeps headings, controls, and charts aligned
    with st.container(horizontal=True, horizontal_alignment="center"): #outside column to center everything on the page
        with st.container(width=1150): #inner column holding everything, creates margin on the sides
            st.title("Central Park Squirrel Sightings")

            #[INPUT_CHECK] AUGMENT - added a directory check for the data file and an error message for if not found
            try:
                df = load_sightings(DATA_FILE)
            except FileNotFoundError: #if data file is missing, give error message then exit main
                st.error(f"Could not find {DATA_FILE}")
                return

            st.header("Where Were the Most Squirrels Spotted?")
            show_sighting_map(df)

            #Finding earliest and latest sighting dates in file
            #[MAXMIN] Find the largest or smallest values of a DataFrame
            first_date = df["Sighting date"].min()
            last_date = df["Sighting date"].max()
            survey_dates = sorted(df["Sighting date"].unique()) #one copy of each date in calendar order

            #[COLUMNS] Add or drop columns from a DataFrame
            recorded_colors = df["primary_fur_color"].dropna() #store colors, skip rows where no primary color recorded
            color_options = ["All"] + sorted(recorded_colors.unique()) #filter options are "All" plus every unique color
            df["primary_fur_color"] = df["primary_fur_color"].fillna("Not recorded") #replace blanks with not recorded

            st.header("When Were the Most Squirrels Spotted?")
            selected_color = st.segmented_control( #create segmented control, store value in selected_color
                "Select a primary fur color", color_options, default="All", required=True) #colors and "All" options

            filtered_df = df #temp filtered df so not changing og
            if selected_color != "All":
                #[FILTER1] Filter data by one condition
                #Only keep sightings of the selected fur color
                filtered_df = df[df["primary_fur_color"] == selected_color] #inner df checks which rows are the selected color,
                #the ones that return true are stored in outer df

            show_peak_date(filtered_df)
            #streamlit columns for displaying table and chart side by side
            table_column, chart_column = st.columns([1,2]) #making chart column 2x the width of table column, table mini and chart BIG
            with table_column:
                show_daily_table(filtered_df, first_date, last_date) #call table function in column
            with chart_column:
                show_daily_chart(filtered_df, survey_dates) #call chart function in column

            st.header("What Were the Squirrels Doing?")
            show_activity_chart(df, color_options)

    #[ST3] Footer photo
    with st.container(horizontal=True, horizontal_alignment="center"):
        st.image("images/image2.jpg", width=900)

    if st.button("🐿️"): #secret button easter egg
        st.balloons()


if __name__ == "__main__":
    main()
