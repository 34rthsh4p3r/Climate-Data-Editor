import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Set page configuration
st.set_page_config(page_title="Climate Data Editor", layout="wide")

# --- Main Page ---
st.title("Walter-Lieth Diagram")

# --- Station Information Input ---
st.header("Station Information (Optional)")
col1, col2, col3, col4 = st.columns(4)
with col1:
    station_number = st.text_input("Number", "")
with col2:
    station_location = st.text_input("Location", "")
with col3:
    station_coordinates = st.text_input("Coordinates", "")
with col4:
    station_elevation = st.text_input("Elevation", "")


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
            #check for complete year, no missing data
            df['YearMonth'] = pd.to_datetime(df[['Year', 'Month']].assign(DAY=1))
            if not (df.groupby('Year')['Month'].count() == 12).all():
                st.error("Error: Only full years with no missing monthly data should be included.")
            else: #all data validation passed
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



                # --- Walter-Lieth Diagram Generation ---
                st.header("Walter-Lieth Diagram")

                fig, ax1 = plt.subplots(figsize=(10, 6))

                # --- Axis Setup ---
                months = monthly_avg['Month']
                ax1.set_xticks(months)
                ax1.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], color='black')
                ax1.set_xlabel("Month", color='black')

                ax1.set_ylabel("Temperature (°C)", color='red')
                ax1.tick_params(axis='y', labelcolor='red')
                ax2 = ax1.twinx()
                ax2.set_ylabel("Precipitation (mm)", color='blue')
                ax2.tick_params(axis='y', labelcolor='blue')

                # --- Scaling ---
                temp_min = min(0, monthly_avg['Mean_Tmin'].min())  # Use Mean_Tmin for lower bound
                temp_max = max(50, monthly_avg['Mean_Tmax'].max())

                ax1.set_ylim(temp_min, temp_max)

                precip_min = min(0, monthly_avg['Mean_Rain'].min())

                if temp_max <= 50:
                    ax2.set_ylim(precip_min, temp_max*2)
                else:
                    ax2.set_ylim(precip_min, 100)  # Cap at 100, not temp_max*2

                # --- Humid and Arid Periods (Climatol style) ---
                m = np.array(months)
                precip = np.array(monthly_avg['Mean_Rain'])
                temp = np.array(monthly_avg['Mean_Tmax']) * 2

                # 1. Humid (Vertical Lines) -  Fill *between* precip and 2*temp
                ax1.fill_between(m, precip, temp, where=(precip >= temp), color="#0E67F5", alpha=0.8, hatch='||', edgecolor="#0E67F5", linewidth=0.0)

                # 2. "Wet" Period (> 100 mm, solid blue)
                wet = np.where(precip > 100, precip, 100)
                ax1.fill_between(m, wet, 100, where=(precip > 100), color="#0E67F5")
                # "Cheat" to cover up extra solid blue
                ax1.fill_between(m, precip, np.maximum(precip, 100), color='white', edgecolor='white', linewidth=0)

                # 3. Dry Period (Red Dots)
                dry = np.where(precip < temp, temp, precip)
                ax1.fill_between(m, temp, precip, where=(precip < temp), color='white', edgecolor='white', linewidth=0) #cover with white
                ax1.fill_between(m, temp, precip, where=(precip < temp), color="#FA4141", alpha=0.6, hatch='....', edgecolor="#FA4141", linewidth=0.0)

                # --- Plot lines *AFTER* the shading ---
                ax1.plot(months, monthly_avg['Mean_Tmax'], color="#FA4141", linewidth=2.4, label="Temperature")
                ax1.plot(months, monthly_avg['Mean_Tmin'], color="#FA4141", linestyle='dashed', linewidth=1.5, label="Min Temperature") #changed to dashed red
                ax2.plot(months, monthly_avg['Mean_Rain'], color="#0E67F5", linewidth=2.4, label="Precipitation")


                # --- Frost Bars ---
                for i in range(len(months)):
                    if monthly_avg['Absolute_Monthly_Tmin'][i] < 0:
                        ax1.bar(months[i], height=2, bottom=-2, width=0.6, color='lightblue', align='center') #frostbar smaller


                # --- Top Text --- (Moved to top, using figure coordinates)
                fig.text(0.5, 0.95,
                        f"{station_location} #{station_number} ({station_elevation}) [{station_coordinates}]",
                        ha='center', va='top', fontsize=12)

                years = sorted(df['Year'].unique())
                fig.text(0.15, 0.95, f"{years[0]} - {years[-1]}", ha='left', va='top', fontsize=10)

                fig.text(0.85, 0.95, f"{mean_year_temp:.1f} °C | {sum_year_precipitation:.0f} mm", ha='right', va='top', fontsize=12)

                # Absolute Temps (Moved and adjusted position)
                fig.text(0.05, 0.80, f"{Absolute_Tmax:.1f} °C", ha='left', va='top', color='red', fontsize=10)  # Left, higher
                fig.text(0.05, 0.75, f"{Absolute_Tmin:.1f} °C", ha='left', va='top', color='blue', fontsize=10) # Left, a bit below max

                plt.tight_layout(rect=[0, 0, 1, 0.93])  # Adjust layout for top text
                st.pyplot(fig)

    except Exception as e:
        st.error(f"An error occurred: {e}")
