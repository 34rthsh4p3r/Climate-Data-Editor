# Climate Data Editor for Walter-Lieth Diagrams

This Streamlit application, **Climate Data Editor (CDE)**, is designed to simplify the process of preparing climate data for creating Walter-Lieth diagrams using the `climatol` package (specifically the `diagwl` function) in R/RStudio.  It takes raw monthly climate data and transforms it into the specific format required by `climatol`.  The app handles data validation, aggregation, and generates the necessary R code.

**Streamlit App:** [https://cdeditor.streamlit.app/](https://cdeditor.streamlit.app/)

## Features

*   **Data Upload:** Upload your climate data in Excel format (`.xlsx`).
*   **Data Validation:**  The application checks for the required columns ("Year", "Month", "Rain", "Tavg", "Tmin", "Tmax") and ensures that all data are valid. Only full years, with complete data in required columns, are processed.
*   **Station Information:**  Enter the station name and elevation, which are used directly in the generated R code.
*   **Data Processing:**
    *   Calculates monthly averages for precipitation (Rain), maximum temperature (Tmax), and mean minimum temperature (Tmin_mean).
    *   Determines the absolute minimum of monthly Tmin values (Tmin_min).
    *   Calculates the absolute minimum and maximum temperatures across the entire dataset.
    *   Calculates the mean annual temperature and total annual precipitation.
*   **R Code Generation:**  Automatically generates the complete R code needed to create the Walter-Lieth diagram using `climatol::diagwl`.  This includes:
    *   Defining vectors for precipitation, mean monthly maximum temperature, mean monthly minimum temperature, and absolute monthly minimum temperature.
    *   Creating the `data.matrix` required by `diagwl`.
    *   Calling the `diagwl` function with the correct parameters, including station name (`est`), elevation (`alt`), and language for month labels (`mlab="en"` for English).
* **Data Preview:** Displays both input dataframe and output dataframe (monthly average).
* **Error Handling**: Shows errors if there are problems with the file or data.
* **Copy-Paste Output:** The generated R code is displayed in a code block, ready to be copied and pasted directly into RStudio.

## Input Data Format

The input Excel file (`.xlsx`) must have the following columns, *exactly* as named:

*   **Year:**  The year of the observation.
*   **Month:** The month of the observation (1-12).
*   **Rain:**  Monthly precipitation (e.g., in mm).
*   **Tavg:**  Average monthly temperature (e.g., in °C).
*   **Tmin:**  Minimum monthly temperature (e.g., in °C).
*   **Tmax:**  Maximum monthly temperature (e.g., in °C).

The data should be continuous; no missing values or incomplete years are allowed. The tool process the whole dataframe as a single input.

## Usage

1.  **Upload Data:**  Use the "Choose an Excel file" button to upload your climate data file.
2.  **Enter Station Information:**  Type the station name and elevation (in meters) in the provided text boxes.
3.  **Review Data:**  The uploaded data and calculated monthly averages will be displayed in tables.  Check for any errors.
4.  **Copy R Code:**  The generated R code will appear in a code block.  Copy this code.
5.  **Run in R/RStudio:**  Paste the copied code into your RStudio console or an R script and run it.  This will create the Walter-Lieth diagram.  Make sure you have the `climatol` package installed (`install.packages("climatol")`).

## Example R Output

```R
library(climatol)

precipitation <- c(39.1, 32.8, 27.3, 30.4, 57.9, 54.6, 56.8, 35.6, 48.6, 41.7, 56.4, 46.6)
mean_monthly_tmax <- c(13.8, 21.0, 25.1, 30.8, 32.2, 38.9, 40.3, 39.1, 36.5, 27.8, 25.0, 17.8)
mean_monthly_tmin <- c(-12.0, -7.6, -5.6, -1.3, 3.7, 8.5, 9.3, 9.6, 4.3, -1.3, -3.8, -6.9)
absolute_monthly_min_t <- c(-18.6, -13.5, -15.7, -7.5, 0.0, 7.1, 6.9, 7.2, 0.3, -3.8, -6.0, -12.2)

data.matrix <- rbind(
  precipitation,
  mean_monthly_tmax,
  mean_monthly_tmin,
  absolute_monthly_min_t)

diagwl(data.matrix,
       est="Pocsaj",
       cols=NULL,
       alt="97",
       mlab="en")
