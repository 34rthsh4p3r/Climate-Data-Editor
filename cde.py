import streamlit as st
import pandas as pd
import io

# Set page configuration
st.set_page_config(page_title="Climate Data Editor", layout="wide")

# --- Page Functions ---

def editor_page():
    st.title("Climate Data Editor (CDE) for Walter-Lieth Diagrams")
    st.write("""
    This application helps you prepare climate data for creating Walter-Lieth diagrams using the `climatol` package in R. It takes monthly climate data, validates it, performs calculations, and generates the R code needed for the `diagwl` function.
    """)

    st.header("Upload Climate Data")
    st.write("Excel data should have these specific columns: Rain, Tavg, Tmin, Tmax, and either separate Year and Month columns OR a combined YearMonth column (e.g., 202301 for January 2023). Only full years with no missing data should be added.")

    uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

    col1, col2 = st.columns(2)
    with col1:
        station_name = st.text_input("Enter Station Name:", value="StationName")
    with col2:
        elevation = st.text_input("Enter Elevation (in meters):", value="Altitude")

    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)

            # --- Data Validation and Preprocessing ---
            required_columns = ["Rain", "Tavg", "Tmin", "Tmax"]  # Columns that MUST exist

            # Check for Year and Month columns (either separate or combined)
            if 'Year' in df.columns and 'Month' in df.columns:
                # Separate Year and Month columns
                df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
                df['Month'] = pd.to_numeric(df['Month'], errors='coerce')
                df.dropna(subset=['Year', 'Month'], inplace=True)
                df['Year'] = df['Year'].astype(int)
                df['Month'] = df['Month'].astype(int)
                if not df['Month'].between(1, 12).all():
                    st.error("Error: 'Month' values must be between 1 and 12.")
                    return

            elif 'YearMonth' in df.columns:
                # Combined YearMonth column
                df['YearMonth'] = pd.to_numeric(df['YearMonth'], errors='coerce')
                df.dropna(subset=['YearMonth'], inplace=True)
                df['YearMonth'] = df['YearMonth'].astype(int)  # Ensure it's an integer
                df['Year'] = df['YearMonth'] // 100  # Integer division to get the year
                df['Month'] = df['YearMonth'] % 100  # Modulo to get the month
                if not df['Month'].between(1, 12).all():
                    st.error("Error: Extracted 'Month' values must be between 1 and 12.")
                    return
                # Drop the original YearMonth column
                df.drop(columns=['YearMonth'], inplace=True, errors='ignore')
            else:
                st.error("Error: The Excel file must contain either separate 'Year' and 'Month' columns OR a combined 'YearMonth' column.")
                return

            # Check if all required columns exist
            if not all(col in df.columns for col in required_columns):
                st.error(f"Error: The Excel file must also contain the following columns: {', '.join(required_columns)}")
                return

             # Check for missing values in ALL required columns (including Year/Month)
            if df[required_columns + ['Year', 'Month']].isnull().any().any():
                st.error("Error: Missing values found in the required columns.")
                return

            # Group by year and check if each year has 12 months
            year_counts = df.groupby('Year')['Month'].count()
            incomplete_years = year_counts[year_counts != 12].index.tolist()
            if incomplete_years:
                st.error(f"Error: Incomplete data for year(s): {', '.join(map(str, incomplete_years))}. Each year must have data for all 12 months.")
                return

            st.header("Input Data")
            st.dataframe(df)

            # --- Data Processing ---
            monthly_avg = df.groupby('Month').agg({
                'Rain': 'mean',
                'Tmax': 'max',
                'Tmin': ['mean', 'min'],
            })
            monthly_avg.columns = [f'{col[0]}_{col[1]}' if col[1] else col[0] for col in monthly_avg.columns]
            monthly_avg = monthly_avg.reset_index()

            Absolute_Tmin = df['Tmin'].min()
            Absolute_Tmax = df['Tmax'].max()

            st.header("Output Data")
            st.dataframe(monthly_avg)
            st.write(f"Absolute minimum temperature (°C): {Absolute_Tmin:.1f}")
            st.write(f"Absolute maximum temperature (°C): {Absolute_Tmax:.1f}")

            # --- Climatol Output ---
            st.header("Output text for climatol/diagwl")

            rain_str = ", ".join([f"{x:.1f}" for x in monthly_avg['Rain_mean']])
            tmax_str = ", ".join([f"{x:.1f}" for x in monthly_avg['Tmax_max']])
            tmin_mean_str = ", ".join([f"{x:.1f}" for x in monthly_avg['Tmin_mean']])
            tmin_abs_str = ", ".join([f"{x:.1f}" for x in monthly_avg['Tmin_min']])

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

            st.code(output_buffer.getvalue(), language="r")

        except Exception as e:
            st.error(f"An error occurred: {e}")



def usage_page():
    st.header("Input Data Format")
    st.write("""
    The input Excel file (`.xlsx`) must have the following columns, *exactly* as named (case-sensitive):

    *   **Rain:** Monthly precipitation in mm.
    *   **Tavg:** Average monthly temperature in °C.
    *   **Tmin:** Minimum monthly temperature in °C.
    *   **Tmax:** Maximum monthly temperature in °C.

    AND EITHER:

    *   **Year:** The year of the observation.
    *   **Month:** The month of the observation (1-12).

    OR:

    *   **YearMonth:**  A combined year and month column in the format YYYYMM (e.g., 201401 for January 2014).

    The data should represent a single, continuous time series for one station. The tool will treat the entire uploaded dataset as belonging to a single location.

    **Input Data Example (Separate Year/Month):**
    """)
    example_input_separate = pd.DataFrame({
        'Year': [2014, 2014, 2014, 2024],
        'Month': [1, 2, 3, 12],
        'Rain': [36.9, 21.7, 11.6, 14.9],
        'Tavg': [2.7, 3.9, 9.3, 2.2],
        'Tmin': [-7.4, -13.5, -2.5, -3.5],
        'Tmax': [13.8, 15.7, 23.1, 11.2]
    })
    st.dataframe(example_input_separate)

    st.write("**Input Data Example (Combined YearMonth):**")
    example_input_combined = pd.DataFrame({
        'YearMonth': [201401, 201402, 201403, 202412],
        'Rain': [36.9, 21.7, 11.6, 14.9],
        'Tavg': [2.7, 3.9, 9.3, 2.2],
        'Tmin': [-7.4, -13.5, -2.5, -3.5],
        'Tmax': [13.8, 15.7, 23.1, 11.2]
    })
    st.dataframe(example_input_combined)


    st.subheader("Usage")
    st.write("""
    1.  **Go to EDITOR Page:** Use the navigation on the top to go to the editor.
    2.  **Upload Data:** Use the "Choose an Excel file" button to upload your climate data file.
    3.  **Enter Station Information:** Type the station name and elevation (in meters) in the provided text boxes.
    4.  **Review Data:** The uploaded data will be displayed in a table labeled 'Input Data'. The calculated monthly averages will be displayed in a table labeled 'Output Data'. Check for any errors.
    5.  **Copy R Code:** The generated R code will appear in a code block. Copy this code.
    6.  **Run in R/RStudio:** Paste the copied code into your RStudio console or an R script and run it. This will create the Walter-Lieth diagram. Make sure you have the `climatol` package installed (`install.packages("climatol")`). After running the code, the Walter-Lieth diagram will be generated in your RStudio Plots pane (or the default graphics device).
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

def data_source_page():
    st.header("Data Source (Hungarian Meteorological Service)")
    st.write("""
    This application is compatible with climate data from the Hungarian Meteorological Service (OMSZ, also referred to as HungaroMet).

    Data Access: [Monthly climate data for Hungarian stations](https://odp.met.hu/climate/observations_hungary/monthly/historical/)

    Station Metadata: [Station metadata](https://odp.met.hu/climate/observations_hungary/monthly/station_meta_auto.csv)

    Data Usage Terms: Using climate data from the Hungarian Meteorological Service is bound to general terms and conditions of use. Key points from these terms include:

    *   Data from HungaroMet is freely available.
    *   Citation is required: When using data, you must cite the source. The recommended citation is:
        *   Text: Source: Hungarian Meteorological Service
        *   Graphically: Use the HungaroMet logo.
    *   If you substantially transform or process the data, you should mention this in a central reference list or imprint.
    *   If the data is used inappropriately, the source references shall be deleted.
    *   To ask questions or provide feedback on the Meteorological Database, contact: [odp@met.hu](mailto:odp@met.hu)
    """)

def about_page():
    st.header("About")
    st.subheader("Contributing")
    st.write("""
    Contributions are welcome! If you'd like to contribute:

    1.  **Fork the repository.**
    2.  **Create a new branch:** `git checkout -b feature/your-feature-name`
    3.  **Make your changes and commit them:** `git commit -m "Add some feature"`
    4.  **Push to the branch:** `git push origin feature/your-feature-name`
    5.  **Create a pull request.**

    Please follow good coding practices, include clear commit messages, and test your changes thoroughly.
    """)

    st.subheader("Maintainer")
    st.write("*   [34rthsh4p3r](https://github.com/34rthsh4p3r)")

    st.subheader("Acknowledgments")
    st.write("This project was developed with significant assistance from Google AI Studio (Gemini 2.0 Pro Experimental 02-05) on Visual Studio Code.")

    st.subheader("License")
    st.write("This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.")

# --- Main App Logic with Top Navigation ---

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = 'EDITOR'  # Start on the EDITOR page

# Navigation buttons
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button('EDITOR'):
        st.session_state['current_page'] = 'EDITOR'
with col2:
    if st.button('Usage'):
        st.session_state['current_page'] = 'Usage'
with col3:
    if st.button('Data Source'):
        st.session_state['current_page'] = 'Data Source'
with col4:
    if st.button('About'):
        st.session_state['current_page'] = 'About'

# Page display
if st.session_state['current_page'] == 'EDITOR':
    editor_page()
elif st.session_state['current_page'] == 'Usage':
    usage_page()
elif st.session_state['current_page'] == 'Data Source':
    data_source_page()
elif st.session_state['current_page'] == 'About':
    about_page()
