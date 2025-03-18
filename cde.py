import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import openpyxl  # Make sure to install: pip install openpyxl

def plot_walter_lieth(df):
    """
    Generates a Walter-Lieth climate diagram from a DataFrame.

    Args:
        df: DataFrame with 'Month', 'Avg Rain' (precipitation), and
            'Avg Max T' (temperature) columns.  'Month' should be
            integers from 1 to 12.

    Returns:
        A matplotlib Figure object.
    """

    # --- Data Validation (Essential) ---
    required_columns = ['Month', 'Avg Rain', 'Avg Max T']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"Input DataFrame must contain columns: {', '.join(required_columns)}")
    if df.isnull().values.any():
        raise ValueError("Missing values found. Clean the data before processing.")
    if not df['Month'].between(1, 12).all():
        raise ValueError("The 'Month' column must contain integer values between 1 and 12.")
    if not pd.api.types.is_numeric_dtype(df['Avg Rain']):
        raise TypeError("The 'Avg Rain' column must contain numeric values.")
    if not pd.api.types.is_numeric_dtype(df['Avg Max T']):
        raise TypeError("The 'Avg Max T' column must contain numeric values.")

    # Sort by month (important for plotting)
    df = df.sort_values('Month')

    # --- Plotting ---
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Temperature (left y-axis)
    color = 'tab:red'
    ax1.set_xlabel('Month')
    ax1.set_ylabel('Temperature (°C)', color=color)
    ax1.plot(df['Month'], df['Avg Max T'], color=color, label='Avg Max T')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.set_xticks(df['Month'])  # Ensure all months are displayed
    ax1.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])


    # Precipitation (right y-axis) - create a twin axis
    ax2 = ax1.twinx()
    color = 'tab:blue'
    ax2.set_ylabel('Precipitation (mm)', color=color)
    ax2.bar(df['Month'], df['Avg Rain'], color=color, alpha=0.5, label='Avg Rain')  # Use bars for precipitation
    ax2.tick_params(axis='y', labelcolor=color)

    # Walter-Lieth 10:20 scaling.  Crucially important!
    # Find the maximum values to set appropriate limits
    max_temp = df['Avg Max T'].max()
    max_precip = df['Avg Rain'].max()

    # Set y-axis limits based on the 10:20 ratio.
    ax1.set_ylim(0, max(max_temp, max_precip / 2) * 1.1)  # Add some padding
    ax2.set_ylim(0, max(max_temp * 2, max_precip) * 1.1)  # Add some padding

    # Add shaded areas (Humid and Arid periods)
    for i in range(len(df)):
      if df['Avg Rain'].iloc[i] > df['Avg Max T'].iloc[i]*2:
        ax2.fill_between(
          [df['Month'].iloc[i] - 0.4, df['Month'].iloc[i] + 0.4],
          [df['Avg Max T'].iloc[i]*2, df['Avg Max T'].iloc[i]*2],
          [df['Avg Rain'].iloc[i],df['Avg Rain'].iloc[i]],
          color = "blue",
          alpha=0.2
        )
      if df['Avg Rain'].iloc[i] < df['Avg Max T'].iloc[i]*2:
        ax1.fill_between(
          [df['Month'].iloc[i] - 0.4, df['Month'].iloc[i] + 0.4],
          [df['Avg Rain'].iloc[i]/2, df['Avg Rain'].iloc[i]/2],
          [df['Avg Max T'].iloc[i],df['Avg Max T'].iloc[i]],
          color = "red",
          alpha = 0.2
        )
    # Add title and legend
    plt.title('Walter-Lieth Climate Diagram')
    fig.tight_layout()  # Adjust layout to prevent labels from overlapping
    #  Place legend outside the plot area
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    fig.legend(handles1 + handles2, labels1 + labels2, loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=2)

    return fig



def process_climate_data(df):
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

    return output_df, output_text, monthly_data # Return monthly_data


st.title("Climate Data Processor")

uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)

        st.subheader("Input Data")
        st.dataframe(df)

        if st.button("Process Data"):
            try:
                output_df, output_text, monthly_data = process_climate_data(df)

                st.subheader("Output Data")
                st.dataframe(output_df)

                st.subheader("Output Text (Copyable)")
                st.text_area("", output_text, height=300)

                # Walter-Lieth Diagram
                st.subheader("Walter-Lieth Climate Diagram")
                try:
                    fig = plot_walter_lieth(monthly_data)
                    st.pyplot(fig)  # Display the matplotlib figure
                except (ValueError, TypeError) as e:
                    st.error(f"Error creating Walter-Lieth diagram: {e}")


            except (ValueError, TypeError) as e:
                st.error(f"Error processing data: {e}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

    except Exception as e:
        st.error(f"Error loading input data: {e}")
