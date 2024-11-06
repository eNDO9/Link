import streamlit as st
import pandas as pd

def main():
    st.title("Network Graph Creator")

    # Step 1: Upload CSV
    st.header("Upload CSV File")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        # Option to skip rows
        skip_rows = st.number_input("Number of rows to skip", min_value=0, value=0, step=1)

        # Attempt to read the CSV with the specified number of rows to skip
        try:
            df = pd.read_csv(uploaded_file, skiprows=skip_rows)

            # Preview first 50 rows
            st.subheader("Preview of CSV (first 50 rows)")
            st.write(df.head(50))

            # Select Source and Target columns
            columns = df.columns.tolist()
            source_column = st.selectbox("Select Source column", columns)
            target_column = st.selectbox("Select Target column", columns)

            # Print notifications
            st.write(f"**Source:** {source_column}")
            st.write(f"**Target:** {target_column}")

            # Save df in session state for use in later steps
            st.session_state['df'] = df
            st.session_state['source_column'] = source_column
            st.session_state['target_column'] = target_column

        except pd.errors.ParserError:
            st.info("This file may contain extra rows or inconsistent formatting at the beginning, likley from BrandWatch. "
                     "**Try increasing the number of rows to skip.**")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()