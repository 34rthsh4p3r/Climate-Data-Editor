import streamlit as st
import pandas as pd
import io
import openpyxl

def process_climate_data(df):
    """Processes the climate data DataFrame.  Moved to a function for better organization."""

    # --- Validation ---
    required_columns = ['Year', 'Month', 'Rainfall', 'Avg T', 'Min T', 'Max T']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"Input Excel file must contain columns: {', '.join(required_columns)}")
    if df.isnull().values.any():
        raise ValueError("Missing values found. Clean the data before processing.")
    numeric_cols = ['Rainfall', 'Avg T', 'Min T', 'Max T']
    for col in numeric_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise TypeError(f"Column '{col}' must contain only numeric values.")
    if not df['Month'].between(1, 12).all():
        raise ValueError("The 'Month' column must contain integer values between 1 and 12.")
    # --- End Validation ---

    # --- Calculations ---
    monthly_data = df.groupby('Month').agg({
        'Rainfall': 'mean',
        'Max T': 'mean',
        'Min T': ['mean', 'min']
    })
    monthly_data.columns = ['Avg Rain', 'Avg Max T', 'Avg Min T', 'Abs Min T']

    abs_min_temp = df['Min T'].min()
    abs_max_temp = df['Max T'].max()
    # --- End Calculations ---

    # --- Create Output DataFrame ---
    output_df = pd.DataFrame({
        'Mean precipitation (mm)': monthly_data['Avg Rain'],
        'Mean maximum daily temperature': monthly_data['Avg Max T'],
        'Mean minimum daily temperature': monthly_data['Avg Min T'],
        'Absolute monthly minimum temperature': monthly_data['Abs Min T']
    }).transpose().reset_index()
    output_df = output_df.rename(columns={'index': ''})
    months_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    output_df.columns = [''] + months_order
    # --- End Create Output DataFrame ---



    # --- Generate Output Text ---
    output_text_buffer = io.StringIO()  # Use StringIO for efficient string building
    output_text_buffer.write("## Mean precipitation in mm\n")
    output_text_buffer.write(f"mean_prec <- c({', '.join(map(str, monthly_data['Avg Rain'].round(1)))})\n\n")
    output_text_buffer.write("## Mean maximum daily temperature\n")
    output_text_buffer.write(f"m_max_dt <- c({', '.join(map(str, monthly_data['Avg Max T'].round(1)))})\n\n")
    output_text_buffer.write("## Mean minimum daily temperature\n")
    output_text_buffer.write(f"m_min_dt <- c({', '.join(map(str, monthly_data['Avg Min T'].round(1)))})\n\n")
    output_text_buffer.write("## Absolute monthly minimum temperature\n")
    output_text_buffer.write(f"abs_m_min_t <- c({', '.join(map(str, monthly_data['Abs Min T'].round(1)))})\n\n")
    output_text_buffer.write(f"Absolute min T: {abs_min_temp}\n")
    output_text_buffer.write(f"Absolute max T: {abs_max_temp}\n")

    output_text = output_text_buffer.getvalue()
    output_text_buffer.close()

    return output_df, output_text



st.title("Climate Data Processor")

uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)

        st.subheader("Input Data")
        st.dataframe(df)  # Use st.dataframe for interactive tables

        if st.button("Process Data"):
            try:
                output_df, output_text = process_climate_data(df)

                st.subheader("Output Data")
                st.dataframe(output_df)

                st.subheader("Output Text (Copyable)")
                st.text_area("", output_text, height=300)  # Use text_area for copyable text

            except (ValueError, TypeError) as e:
                st.error(f"Error processing data: {e}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")


    except Exception as e:
        st.error(f"Error loading input data: {e}")
