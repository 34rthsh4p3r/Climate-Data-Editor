import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Set page configuration
st.set_page_config(page_title="Climate Data Editor", layout="wide")

# --- File Upload and Data Validation ---
st.header("Upload Climate Data")
st.write("Excel data should have these specific columns: Year, Month, Rain, Tavg, Tmin, Tmax. Only full years with no missing data should be added.")

uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

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
                    'Tmin': ['mean', 'min'],
                    'Tmax': 'max'
                }).reset_index()

                monthly_avg.columns = ['Month', 'Mean_Rain', 'Mean_Tmax', 'Mean_Tmin', 'Absolute_Monthly_Tmin']

                Absolute_Tmin = df['Tmin'].min()
                Absolute_Tmax = df['Tmax'].max()

                mean_year_temp = df['Tavg'].mean()
                sum_year_precipitation = df['Rain'].sum()

                st.header("Output Data")
                st.dataframe(monthly_avg)
                st.write(f"Absolute minimum temperature (°C): {Absolute_Tmin:.1f}")
                st.write(f"Absolute maximum temperature (°C): {Absolute_Tmax:.1f}")


                #output for climatol
                st.header("Output text for climatol/diagwl")
                rain_str = ", ".join([f"{x:.1f}" for x in monthly_avg['Mean_Rain']])
                tmax_str = ", ".join([f"{x:.1f}" for x in monthly_avg['Mean_Tmax']])
                tmin_mean_str = ", ".join([f"{x:.1f}" for x in monthly_avg['Mean_Tmin']])
                tmin_abs_str = ", ".join([f"{x:.1f}" for x in monthly_avg['Absolute_Monthly_Tmin']])

                st.text(f"c({rain_str}),\nc({tmax_str}),\nc({tmin_mean_str}),\nc({tmin_abs_str})")

    except Exception as e:
        st.error(f"An error occurred: {e}")
