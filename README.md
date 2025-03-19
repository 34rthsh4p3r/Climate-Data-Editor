# Climate Data Editor (CDE) for Walter-Lieth Diagrams

This Streamlit application, **Climate Data Editor (CDE)**, is designed to simplify the process of preparing climate data for creating Walter-Lieth diagrams using the `climatol` package (specifically the `diagwl` function) in R/RStudio.  It takes raw monthly climate data and transforms it into the specific format required by `climatol`. The app handles data validation, aggregation, and generates the necessary R code.  This tool was initially developed for a project using Hungarian climate data.

**Streamlit App:** [https://cdeditor.streamlit.app/](https://cdeditor.streamlit.app/)

---

## Features

*   **Data Upload:** Upload your climate data in Excel format (`.xlsx`).
*   **Data Validation:** The application performs thorough data validation:
    *   Checks for correctly named columns: 'Year', 'Month', 'Rain', 'Tavg', 'Tmin', 'Tmax' (case-sensitive).
    *   Ensures all months (1-12) are present for each year.
    *   Flags any missing values within the required columns.
    *   Validates that 'Month' values are within the range of 1-12.
    *   Only complete years, with data for all 12 months and no missing values in the required columns, will be processed.
*   **Station Information:** Enter the station name and elevation (in meters), which are used directly in the generated R code.
*   **Data Processing:**
    *   Calculates monthly averages for precipitation (Rain, in mm), maximum temperature (Tmax, in °C), and mean minimum temperature (Tmin_mean, in °C).
    *   Calculates the absolute minimum temperature for *each month* (Tmin_min, in °C) based on the Tmin values.
    *   Calculates the *overall* absolute minimum and maximum temperatures across the *entire dataset*.
    *   Calculates the mean annual temperature and total annual precipitation *for each year* and then averages these values *across all years*.
*   **R Code Generation:** Automatically generates the complete R code needed to create the Walter-Lieth diagram using `climatol::diagwl`. This includes:
    *   Defining vectors for precipitation, mean monthly maximum temperature, mean monthly minimum temperature, and absolute monthly minimum temperature.
    *   Creating the `data.matrix` required by `diagwl`.
    *   Calling the `diagwl` function with the correct parameters, including station name (`est`), elevation (`alt`), the period of the data (`per`), and language for month labels (`mlab="en"` for English).
    *   The generated R code is ready to be copied and pasted directly into R or RStudio.  It assumes you have the `climatol` package installed. If not, you can install it using: `install.packages('climatol')`
* **Data Preview:** Displays both input dataframe ("Input Data") and output dataframe ("Output Data") (monthly average).
* **Error Handling**: Shows errors if there are problems with the file or data.
* **Copy-Paste Output:** The generated R code is displayed in a code block, ready to be copied and pasted directly into RStudio.

---

## Data Source (Hungarian Meteorological Service)

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

---

## Input Data Format

The input Excel file (`.xlsx`) must have the following columns, *exactly* as named:

*   **Year:** The year of the observation.
*   **Month:** The month of the observation (1-12).
*   **Rain:** Monthly precipitation (e.g., in mm).
*   **Tavg:** Average monthly temperature (e.g., in °C).
*   **Tmin:** Minimum monthly temperature (e.g., in °C).
*   **Tmax:** Maximum monthly temperature (e.g., in °C).
*   **Input Data Example:**

     | Year | Month | Rain | Tavg | Tmin  | Tmax  |
     |------|-------|------|------|-------|-------|
     | 2014 | 1     | 36.9 | 2.7  | -7.4  | 13.8  |
     | 2014 | 2     | 21.7 | 3.9  | -13.5 | 15.7  |
     | 2014 | 3     | 11.6 | 9.3  | -2.5  | 23.1  |
     | ...  | ...   | ...  | ...  | ...   | ...   |
     | 2024 | 12    | 14.9 | 2.2  | -3.5  | 11.2  |

The column names must be *exactly* as listed above, including capitalization. The data should represent a single, continuous time series for one station. The tool will treat the entire uploaded dataset as belonging to a single location.

---

## Usage

1.  **Upload Data:** Use the "Choose an Excel file" button to upload your climate data file.
2.  **Enter Station Information:** Type the station name and elevation (in meters) in the provided text boxes.
3.  **Review Data:** The uploaded data will be displayed in a table labeled 'Input Data'. The calculated monthly averages will be displayed in a table labeled 'Output Data'.  Check for any errors.

    *   **Output Data Example:**

        | Month | Rain_mean | Tmax_max | Tmin_mean | Tmin_min |
        |-------|-----------|----------|-----------|----------|
        | 1     | 39.1455   | 13.8     | -11.9727  | -18.6    |
        | 2     | 32.8182   | 21       | -7.5727   | -13.5    |
        | ...   | ...       | ...      | ...       | ...      |
        | 12    | 46.6364   | 17.8     | -6.9091   | -12.2    |

        Absolute minimum temperature (°C): -18.6

        Absolute maximum temperature (°C): 40.3

4.  **Copy R Code:** The generated R code will appear in a code block.  Copy this code.
5.  **Run in R/RStudio:** Paste the copied code into your RStudio console or an R script and run it.  This will create the Walter-Lieth diagram. Make sure you have the `climatol` package installed (`install.packages("climatol")`). After running the code, the Walter-Lieth diagram will be generated in your RStudio Plots pane (or the default graphics device).

---
## Example R Output
```R
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
```

---


## Contributing

Contributions are welcome!  If you'd like to contribute:

1.  **Fork the repository.**
2.  **Create a new branch:** `git checkout -b feature/your-feature-name`
3.  **Make your changes and commit them:** `git commit -m "Add some feature"`
4.  **Push to the branch:** `git push origin feature/your-feature-name`
5.  **Create a pull request.**

Please follow good coding practices, include clear commit messages, and test your changes thoroughly.

## Maintainer

*   [34rthsh4p3r](https://github.com/34rthsh4p3r)

## Acknowledgments

This project was developed with significant assistance from Google AI Studio (Gemini 2.0 Pro Experimental 02-05) on Visual Studio Code.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](documents/LICENSE) file for details.


