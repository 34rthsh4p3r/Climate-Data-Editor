import streamlit as st
import pandas as pd
import io

# Set page configuration
st.set_page_config(page_title="Climate Data Editor", layout="wide")

# --- Introduction and Instructions (from README) ---
st.title("Climate Data Editor (CDE) for Walter-Lieth Diagrams")
st.write("""
This application helps you prepare climate data for creating Walter-Lieth diagrams using the `climatol` package in R.  It takes monthly climate data, validates it, performs calculations, and generates the R code needed for the `diagwl` function.
""")

st.subheader("Input Data Format")
st.write("""
The input Excel file (`.xlsx`) must have the following columns, *exactly* as named (case-sensitive):

*   **Year:** The year of the observation.
*   **Month:** The month of the observation (1-12).
*   **Rain:** Monthly precipitation in mm.
*   **Tavg:** Average monthly temperature in °C.
*   **Tmin:** Minimum monthly temperature in °C.
*   **Tmax:** Maximum monthly temperature in °C.

The data should represent a single, continuous time series for one station.  The tool will treat the entire uploaded dataset as belonging to a single location.

**Input Data Example:**
""")

example_input = pd.DataFrame({
    'Year': [2014, 2014, 2014, 2024],
    'Month': [1, 2, 3, 12],
    'Rain': [36.9, 21.7, 11.6, 14.9],
    'Tavg': [2.7, 3.9, 9.3, 2.2],
    'Tmin': [-7.4, -13.5, -2.5, -3.5],
    'Tmax': [13.8, 15.7, 23.1, 11.2]
})
st.dataframe(example_input)



st.subheader("Usage")
st.write("""
1.  **Upload Data:** Use the "Choose an Excel file" button to upload your climate data file.
2.  **Enter Station Information:** Type the station name and elevation (in meters) in the provided text boxes.
3.  **Review Data:** The uploaded data will be displayed in a table labeled 'Input Data'.  The calculated monthly averages will be displayed in a table labeled 'Output Data'.  Check for any errors.
4. **Copy R Code:** The generated R code will appear in a code block.  Copy this code.
5.  **Run in R/RStudio:** Paste the copied code into your RStudio console or an R script and run it.  This will create the Walter-Lieth diagram. Make sure you have the `climatol` package installed (`install.packages("climatol")`). After running the code, the Walter-Lieth diagram will be generated in your RStudio Plots pane (or the default graphics device).
""")

st.subheader("Output Data Example")
st.write("""
The Output data frame that's calculated consists of:

*   **Rain_mean:** The average of all the values of rain for that month.
*   **Tmax_max:** The maximum temperature of all maximum temperatures for that month.
*   **Tmin_mean:** The average of all the values of minimum temperatures for that month.
*   **Tmin_min:** The absolute minimum temperature of all the minimum temperatures for that month.
""")

example_output = pd.DataFrame({
     'Month': [1, 2, 12],
     'Rain_mean': [39.1455, 32.8182, 46.6364],
     'Tmax_max': [13.8, 21.0, 17.8],
     'Tmin_mean': [-11.9727, -7.5727, -6.9091],
     'Tmin_min': [-18.6, -13.5, -12.2]
})
st.dataframe(example_output)
st.write("Absolute minimum temperature (°C): -18.6")
st.write("Absolute maximum temperature (°C): 40.3")

st.subheader("Example of generated R code")
st.code("""
library(climatol)

precipitation <- c(39.1, 32.8, 36.2, 38.4, 50.0, 48.7, 57.9, 54.5, 46.1, 49.3, 42.8, 46.6)
mean_monthly_tmax <- c(13.8, 21.0, 24.3, 29.8, 34.7, 38.1, 40.3, 39.7, 34.6, 28.8, 21.5, 17.8)
mean_monthly_tmin <- c(-12.0, -7.6, -4.2, 2.1, 8.5, 13.3, 15.5, 14.6, 9.1, 3.4, -2.3, -6.9)
absolute_monthly_min_t <- c(-18.6, -13.5, -9.9, -4.5, 1.2, 6.8, 9.2, 8.0, 3.0, -3.0, -8.8, -12.2)

data.matrix <- rbind(
  precipitation,
  mean_monthly_tmax,
  mean_monthly_tmin,
  absolute_monthly_min_t)

diagwl(data.matrix,
        est="Pocsaj",
        cols=NULL,
        alt="97",
        per="1991-2020", # Add the period. Very important for climatol
        mlab="en")
""", language='r')

# --- File Upload and Data Validation ---
st.header("Upload Climate Data")
st.write("Excel data should have these specific columns: Year, Month, Rain, Tavg, Tmin, Tmax. Only full years with no missing data should be added.")

uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

# --- Station Information Input ---
station_name = st.text_input("Enter Station Name:", value="StationName")
elevation = st.text_input("Enter Elevation (in meters):", value="Altitude")

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
                'Tmin': ['mean', 'min'],  # Correct: Keep Tmin aggregated
                'Tmax': 'max'  #Keep tmax aggregated to avoid repetition
            })
            # Flatten the MultiIndex columns *correctly*
            monthly_avg.columns = [f'{col[0]}_{col[1]}' if col[1] else col[0] for col in monthly_avg.columns]
            monthly_avg = monthly_avg.reset_index()  # Reset index *after* flattening
          #  st.write(monthly_avg.columns) # For debugging, uncomment to check the column names

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
            rain_str = ", ".join([f"{x:.1f}" for x in monthly_avg['Rain_mean']])
            tmax_str = ", ".join([f"{x:.1f}" for x in monthly_avg['Tmax_max']]) #Tmax values
            tmin_mean_str = ", ".join([f"{x:.1f}" for x in monthly_avg['Tmin_mean']])
            tmin_abs_str = ", ".join([f"{x:.1f}" for x in monthly_avg['Tmin_min']]) #tmin values


            # Create the R code string
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
            output_buffer.write(f'diagwl(data.matrix,\n')
            output_buffer.write(f'       est="{station_name}",\n')
            output_buffer.write(f'       cols=NULL,\n')
            output_buffer.write(f'       alt="{elevation}",\n')
            output_buffer.write(f'       mlab="en")\n')

            # Display the code and allow copying
            st.code(output_buffer.getvalue(), language="r")
            output_buffer.close()

    except Exception as e:
        st.error(f"An error occurred: {e}")
