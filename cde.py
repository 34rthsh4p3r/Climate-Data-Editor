import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt  # Import but don't use it directly for plotting in this example
import numpy as np
import io  # Import io for creating an in-memory text stream

# Set page configuration
st.set_page_config(page_title="Climate Data Editor", layout="wide")

# --- File Upload and Data Validation ---
st.header("Upload Climate Data")
st.write("Excel data should have these specific columns: Year, Month, Rain, Tavg, Tmin, Tmax. Only full years with no missing data should be added.")

uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

# --- Station Information Input ---
station_name = st.text_input("Enter Station Name:", value="StationName")  # Default value
elevation = st.text_input("Enter Elevation (in meters):", value="Altitude") # Default Value

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        # --- Data Validation ---
        required_columns = ["Year", "Month", "Rain", "Tavg", "Tmin", "Tmax"]
        if not all(col in df.columns for col in required_columns):
            st.error(f"Error: The Excel file must contain the following columns: {', '.join(required_columns)}")
        else:
            st.header("Input Data")
            st.dataframe(df)

            # --- Data Processing ---
            monthly_avg = df.groupby('Month').agg({
                'Rain': 'mean',
                'Tmax': 'mean',
                'Tmin': 'mean',
                'Tmin': ['mean', 'min'], # Keep both mean and min of Tmin
                'Tmax': 'max'
            }).reset_index()

            # Correct the column names after multi-level aggregation
            monthly_avg.columns = ['Month', 'Mean_Rain', 'trash', 'Mean_Tmin', 'Absolute_Monthly_Tmin','Mean_Tmax']
            monthly_avg = monthly_avg.drop('trash', axis=1) # Drop trash

            Absolute_Tmin = df['Tmin'].min()
            Absolute_Tmax = df['Tmax'].max()

            mean_year_temp = df['Tavg'].mean()
            sum_year_precipitation = df['Rain'].sum()

            st.header("Output Data")
            st.dataframe(monthly_avg)
            st.write(f"Absolute minimum temperature (°C): {Absolute_Tmin:.1f}")
            st.write(f"Absolute maximum temperature (°C): {Absolute_Tmax:.1f}")

            # --- Climatol Output ---
            st.header("Output text for climatol/diagwl")

            # Prepare data for climatol
            rain_str = ", ".join([f"{x:.1f}" for x in monthly_avg['Mean_Rain']])
            tmax_str = ", ".join([f"{x:.1f}" for x in monthly_avg['Mean_Tmax']])
            tmin_mean_str = ", ".join([f"{x:.1f}" for x in monthly_avg['Mean_Tmin']])
            tmin_abs_str = ", ".join([f"{x:.1f}" for x in monthly_avg['Absolute_Monthly_Tmin']])


            # Create the R code string using an in-memory text stream
            output_buffer = io.StringIO()
            output_buffer.write("library(climatol)\n\n")
            output_buffer.write(f"precipitation <- c({rain_str})\n")
            output_buffer.write(f"mean_monthly_tmax <- c({tmax_str})\n")
            output_buffer.write(f"mean_monthly_tmin <- c({tmin_mean_str})\n")
            output_buffer.write(f"absolute_monthly_min_t <- c({tmin_abs_str})\n\n")
            output_buffer.write("data.matrix <- rbind(\n")
            output_buffer.write("  precipitation,\n")
            output_buffer.write("  mean_monthly_tmax,\n")
            output_buffer.write("  mean_monthly_tmin,\n")
            output_buffer.write("  absolute_monthly_min_t)\n\n")
            output_buffer.write(f"diagwl(data.matrix,\n")
            output_buffer.write(f'       est="{station_name}",\n')  # Use user-input station name
            output_buffer.write(f'       cols=NULL,\n')
            output_buffer.write(f'       alt="{elevation}",\n')  # Use user-input elevation
            output_buffer.write(f'       mlab="en")\n')

            # Display the code and allow copying
            st.code(output_buffer.getvalue(), language="r")


            #Close Buffer
            output_buffer.close()

    except Exception as e:
        st.error(f"An error occurred: {e}")
