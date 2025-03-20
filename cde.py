import streamlit as st
import pandas as pd
import io

# Set page configuration
st.set_page_config(page_title="Climate Data Editor", layout="wide")

# --- Page Functions ---

def editor_page():
    st.header("How to")
    st.write("""
    **Review Data:** The uploaded data will be displayed in a table labeled 'Input Data'. The calculated monthly averages will be displayed in a table labeled 'Output Data'. Check for any errors.
    **Copy R Code:** The generated R code will appear in a code block. Copy this code.
    **Run in R/RStudio:** Paste the copied code into your RStudio console or an R script and run it. This will create the Walter-Lieth diagram. Make sure you have the `climatol` package installed (`install.packages("climatol")`). After running the code, the Walter-Lieth diagram will be generated in your RStudio Plots pane (or the default graphics device).

    **Format 1:** Separate **Year** and **Month** columns, along with **Rain**, **Tmin**, and **Tmax**.
    **Format 2:** A combined **YearMonth** or **Time** column (e.g., 202301 for January 2023), along with **Rain**, **Tmin**, and **Tmax**.
    **Format 3:** Data from the Hungarian Meteorological Service, with columns **'Time'** (YYYYMM), **'rau'** (Rain), **'tn'** (Tmin), and **'tx'** (Tmax).

    """)

    uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

    # Station Name and Elevation ONLY for non-HMS formats
    col1, col2 = st.columns(2)
    with col1:
        station_name_input = st.text_input("Enter Station Name:", value="StationName")
    with col2:
        elevation_input = st.text_input("Enter Elevation (in meters):", value="Altitude")


    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)

            # --- Data Validation and Preprocessing ---

            # 1. Check for Hungarian Meteorological Service format
            if {'Time', 'rau', 'tn', 'tx'}.issubset(df.columns):
                st.write("Detected Hungarian Meteorological Service data format.")
                # Rename columns to standard names
                df.rename(columns={
                    'Time': 'YearMonth',  # Keep 'Time' renamed to YearMonth for consistency
                    'rau': 'Rain',  #  <-- This is correct
                    'tn': 'Tmin',
                    'tx': 'Tmax'
                }, inplace=True)

                # Parse YearMonth
                df['YearMonth'] = pd.to_numeric(df['YearMonth'], errors='coerce')
                df.dropna(subset=['YearMonth'], inplace=True)
                df['YearMonth'] = df['YearMonth'].astype(int)
                df['Year'] = df['YearMonth'] // 100
                df['Month'] = df['YearMonth'] % 100
                df.drop(columns=['YearMonth'], inplace=True)

                # Station name and elevation are NOT used for HMS format.
                station_name = station_name_input  # Use input values
                elevation = elevation_input

                required_columns = ["Year", "Month", "Rain", "Tmin", "Tmax"] # Correct

            # 2. Check for standard formats (separate or combined Year/Month)
            else:
                required_columns = ["Rain", "Tmin", "Tmax"]  #  Correct
                if 'Year' in df.columns and 'Month' in df.columns:
                    st.write("Detected separate Year and Month columns.")
                    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
                    df['Month'] = pd.to_numeric(df['Month'], errors='coerce')
                    df.dropna(subset=['Year', 'Month'], inplace=True)
                    df['Year'] = df['Year'].astype(int)
                    df['Month'] = df['Month'].astype(int)
                    if not df['Month'].between(1, 12).all():
                        st.error("Error: 'Month' values must be between 1 and 12.")
                        return
                    required_columns.extend(['Year', 'Month']) # Correct

                elif 'YearMonth' in df.columns or 'Time' in df.columns:  # Check for YearMonth OR Time
                    st.write("Detected combined YearMonth or Time column.")
                    year_month_col = 'YearMonth' if 'YearMonth' in df.columns else 'Time'  # Determine which column exists

                    df[year_month_col] = pd.to_numeric(df[year_month_col], errors='coerce')
                    df.dropna(subset=[year_month_col], inplace=True)
                    df[year_month_col] = df[year_month_col].astype(int)
                    df['Year'] = df[year_month_col] // 100
                    df['Month'] = df[year_month_col] % 100
                    df.drop(columns=[year_month_col], inplace=True)  # Drop the original column
                    if not df['Month'].between(1, 12).all():
                        st.error("Error: Extracted 'Month' values must be between 1 and 12.")
                        return
                    required_columns.extend(['Year', 'Month'])  #Correct

                else:
                    st.error("Error: The Excel file must contain either separate **'Year'** and **'Month'** columns, a combined **'YearMonth'** or **'Time'** column.")
                    return

                # For standard formats, get station name and elevation from user input
                station_name = station_name_input
                elevation = elevation_input


            # --- Common Validation (for all formats) ---
            # ***CRITICAL CHECK HERE***
            if not all(col in df.columns for col in required_columns):
                st.error(f"Error: The Excel file must contain the following columns: {', '.join(required_columns)}")
                return  #  Exit early if columns are missing

            if df[required_columns].isnull().any().any():
                st.error("Error: Missing values found in the required columns.")
                return  # Exit early if there are missing values

            year_counts = df.groupby('Year')['Month'].count()
            incomplete_years = year_counts[year_counts != 12].index.tolist()
            if incomplete_years:
                st.error(f"Error: Incomplete data for year(s): {', '.join(map(str, incomplete_years))}. Each year must have data for all 12 months.")
                return # Exit early if there are incomplete years

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

             # Calculate yearly average rainfall and overall average
            yearly_rainfall = df.groupby('Year')['Rain'].sum()  # Correct
            average_yearly_rainfall = yearly_rainfall.mean()  # Correct


            st.header("Output Data")
            st.dataframe(monthly_avg)
            st.write(f"Absolute minimum temperature (°C): {Absolute_Tmin:.1f}")
            st.write(f"Absolute maximum temperature (°C): {Absolute_Tmax:.1f}")
            st.write(f"Average rainfall in a year (mm): {average_yearly_rainfall:.2f}")


            # --- Climatol Output ---
            st.header("Output text for climatol/diagwl")

            rain_str = ", ".join([f"{x:.1f}" for x in monthly_avg['Rain']]) # Correct
            tmax_str = ", ".join([f"{x:.1f}" for x in monthly_avg['Tmax']])
            tmin_mean_str = ", ".join([f"{x:.1f}" for x in monthly_avg['Tmin']])
            tmin_abs_str = ", ".join([f"{x:.1f}" for x in monthly_avg['Tmin_abs']])

            output_buffer = io.StringIO()
            output_buffer.write("library(climatol)\n\n")
            output_buffer.write(f"rain <- c({rain_str})\n")
            output_buffer.write(f"tmax <- c({tmax_str})\n")
            output_buffer.write(f"tmin <- c({tmin_mean_str})\n")
            output_buffer.write(f"tmin_abs <- c({tmin_abs_str})\n\n")
            output_buffer.write("data.matrix <- rbind(\n")
            output_buffer.write("  rain,\n")
            output_buffer.write("  tmax,\n")
            output_buffer.write("  tmin,\n")
            output_buffer.write("  tmin_abs)\n\n")
            output_buffer.write(f'diagwl(data.matrix,\n')
            # Use the values obtained from user input
            output_buffer.write(f'       est="{station_name}",\n')
            output_buffer.write(f'       cols=NULL,\n')
            output_buffer.write(f'       alt="{elevation}",\n')
            output_buffer.write(f'       mlab="en")\n')

            st.code(output_buffer.getvalue(), language="r")

        except Exception as e:
            st.error(f"An error occurred: {e}")



def data_format_page(): #Renamed function
    st.header("Input Data Format")
    st.write("""
    The input Excel file (`.xlsx`) can be in one of three formats:

    **Format 1: Separate Year and Month Columns**

    *   **Year:** The year of the observation.
    *   **Month:** The month of the observation (1-12).
    *   **Rain:** Monthly precipitation in mm.
    *   **Tmin:** Minimum monthly temperature in °C.
    *   **Tmax:** Maximum monthly temperature in °C.

    **Example (Separate Year/Month):**
    """)
    example_input_separate = pd.DataFrame({
        'Year': [2014, 2014, 2014, 2024],
        'Month': [1, 2, 3, 12],
        'Rain': [36.9, 21.7, 11.6, 14.9],
        'Tmin': [-7.4, -13.5, -2.5, -3.5],
        'Tmax': [13.8, 15.7, 23.1, 11.2]
    })
    st.dataframe(example_input_separate)

    st.write("**Format 2: Combined YearMonth or Time Column**")
    st.write("""
    *   **YearMonth** or **Time**:  A combined year and month column in the format YYYYMM (e.g., 201401 for January 2014).
    *   **Rain:** Monthly precipitation in mm.
    *   **Tmin:** Minimum monthly temperature in °C.
    *   **Tmax:** Maximum monthly temperature in °C.
    """)

    st.write("**Example (Combined YearMonth/Time):**")
    example_input_combined = pd.DataFrame({
        'Time': [201401, 201402, 201403, 202412],  # Use 'Time' here
        'Rain': [36.9, 21.7, 11.6, 14.9],
        'Tmin': [-7.4, -13.5, -2.5, -3.5],
        'Tmax': [13.8, 15.7, 23.1, 11.2]
    })
    st.dataframe(example_input_combined)


    st.write("**Format 3: Hungarian Meteorological Service Data**")
    st.write("""
        *   **Time:**  A combined year and month column in the format YYYYMM (e.g., 201401 for January 2014).
        *   **rau:** Monthly precipitation in mm.
        *   **tn:** Minimum monthly temperature in °C.
        *   **tx:** Maximum monthly temperature in °C.
        """)
    st.write("**Example (Hungarian Meteorological Service):**")
    example_input_hms = pd.DataFrame({
    'Time': [201401, 201402, 201403, 202412],
    'rau': [36.9, 21.7, 11.6, 14.9],
    'tn': [-7.4, -13.5, -2.5, -3.5],
    'tx': [13.8, 15.7, 23.1, 11.2]
    })

    st.dataframe(example_input_hms)

def example_page(): #renamed function
    st.header("Output Data Example")
    st.write("""
    The Output data frame that's calculated consists of:

    *   **Precipitation:** The average of all the values of rain for that month.
    *   **Tmax:** The maximum temperature of all maximum temperatures for that month.
    *   **Tmin:** The average of all the values of minimum temperatures for that month.
    *   **Abs_Tmin:** The absolute minimum temperature of all the minimum temperatures for that month.
    """)
    example_output = pd.DataFrame({
         'Month': [1, 2, 12],
         'Rain': [39.1455, 32.8182, 46.6364],
         'Tmax_max': [13.8, 21.0, 17.8],
         'Tmin_mean': [-11.9727, -7.5727, -6.9091],
         'Tmin_min': [-18.6, -13.5, -12.2]
    })
    st.dataframe(example_output)
    st.write("Absolute minimum temperature (°C): -18.6")
    st.write("Absolute maximum temperature (°C): 40.3")
    st.write("Average rainfall in a year (mm): 527.81")

    st.header("Example of generated R code")
    st.code("""

    # Install the 'climatol' package if not already installed
    install.packages('climatol')

    # Load the climatol library to access its functions
    library(climatol)

    # Create monthly values in the same order as the columns in the input data
    rain <- c(39.1, 32.8, 27.3, 30.4, 57.9, 54.6, 56.8, 35.6, 48.6, 41.7, 56.4, 46.6) # Mean total precipitation
    tmax <- c(13.8, 21.0, 25.1, 30.8, 32.2, 38.9, 40.3, 39.1, 36.5, 27.8, 25.0, 17.8) # Mean maximum daily temperature
    tmin <- c(-12.0, -7.6, -5.6, -1.3, 3.7, 8.5, 9.3, 9.6, 4.3, -1.3, -3.8, -6.9) # Mean minimum daily temperature
    tmin_abs <- c(-18.6, -13.5, -15.7, -7.5, 0.0, 7.1, 6.9, 7.2, 0.3, -3.8, -6.0, -12.2) # Absolute minimum daily temperature. This last row is used only to determine the probable frost months (when absolute monthly minimums are equal or lower than 0 C).

    # Combine all climate variables into a single matrix for analysis
    # Each row represents a different variable, each column represents a month
    data.matrix <- rbind(
                   rain,
                   tmax,
                   tmin,
                   tmin_abs)

    diagwl(                     # diagwl - the function to generate the Walter-Lieth diagram
        data.matrix,            # data.matrix - the climate data to visualize
        est  = "Pocsaj",        # Name of the climatological station.
        cols = NULL,            # Columns containing dates and daily data of precipitation and extreme temperatures. Set to NULL if a monthly climate summary is provided.
        alt  = "97",            # Elevation (altitude) of the climatological station.
        shem = NULL,            # NULL by default. Set to TRUE or FALSE to force southern or northern hemisphere.
        p3line = FALSE,         # Draw a supplementary precipitation line referenced to three times the temperature? (FALSE by default.)
        mlab = "en")            # Vector of 12 monthly labels for the X axis. It may be set to just 'en' or 'es' to use the first letter of month names in English or Spanish respectively.

    # As described by Walter and Lieth, when monthly precipitation is greater than 100 mm, the scale is increased from 2 mm/C to 20 mm/C to avoid too high diagrams in very wet locations. This change is indicated by a black horizontal line, and the graph over it is filled in solid blue.
    # When the precipitation graph lies under the temperature graph (P < 2T) we have an arid period (filled in dotted red vertical lines). Otherwise the period is considered wet (filled in blue lines), unless p3line=TRUE, that draws a precipitation black line with a scale P = 3T; in this case the period in which 3T > P > 2T is considered semi-arid.
    # Daily maximum average temperature of the hottest month and daily minimum average temperature of the coldest month are frequently used in vegetation studies, and are labeled in black at the left margin of the diagram.
    """, language='r')

def data_source_page():
    st.header("Data Source (Hungarian Meteorological Service)")
    st.write("""
    This application is compatible with climate data from the Hungarian Meteorological Service (OMSZ, also referred to as HungaroMet).
    """)

    st.image("HungaroMet_logo_800x_ENG.png")

    st.write("""
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
    st.header("Contributing")
    st.write("""
    Contributions are welcome! If you'd like to contribute:

    1.  **Fork the repository.**
    2.  **Create a new branch:** `git checkout -b feature/your-feature-name`
    3.  **Make your changes and commit them:** `git commit -m "Add some feature"`
    4.  **Push to the branch:** `git push origin feature/your-feature-name`
    5.  **Create a pull request.**

    Please follow good coding practices, include clear commit messages, and test your changes thoroughly.
    """)

    st.header("Maintainer")
    st.write("*   [34rthsh4p3r](https://github.com/34rthsh4p3r)")

    st.header("Acknowledgments")
    st.write("This project was developed with significant assistance from Google AI Studio (Gemini 2.0 Pro Experimental 02-05) on Visual Studio Code.")

    st.header("License")
    st.write("This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.")

# --- Main App Logic with Top Navigation ---

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = 'Editor'  # Start on the Editor page

# Navigation buttons
col1, col2, col3, col4, col5 = st.columns(5) #Added a column
with col1:
    if st.button('Editor'):
        st.session_state['current_page'] = 'Editor'
with col2:
    if st.button('Data Format'): #Renamed button
        st.session_state['current_page'] = 'Data Format'
with col3:
     if st.button('Example'): #Renamed button
        st.session_state['current_page'] = 'Example'
with col4:
    if st.button('Data Source'):
        st.session_state['current_page'] = 'Data Source'
with col5:
    if st.button('About'):
        st.session_state['current_page'] = 'About'

# Page display
if st.session_state['current_page'] == 'Editor':
    editor_page()
elif st.session_state['current_page'] == 'Data Format': #Renamed
    data_format_page()
elif st.session_state['current_page'] == 'Example': #Renamed
    example_page()
elif st.session_state['current_page'] == 'Data Source':
    data_source_page()
elif st.session_state['current_page'] == 'About':
    about_page()
