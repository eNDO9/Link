import streamlit as st
import pandas as pd

def main():
    st.title("Network Graph Creator")

    # Step 1: Upload CSV
    st.header("Upload CSV File")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file is not None:
        # Display guidance
        st.write("The file contains some initial rows that may not be data headers. "
                 "Please review the first few lines below to help determine how many rows to skip.")

        # Read the first 10 lines without parsing errors by treating the file as raw text
        raw_lines = uploaded_file.getvalue().decode("utf-8").splitlines()
        st.text("\n".join(raw_lines[:10]))  # Show first 10 lines for reference

        # Option to skip rows
        skip_rows = st.number_input("How many rows should be skipped?", min_value=0, value=0, step=1)

        # Attempt to read the file with the specified skip rows
        try:
            st.write("Attempting to read file with specified skip rows...")
            df = pd.read_csv(uploaded_file, skiprows=skip_rows)
            st.write("File read successfully!")

            # Preview first 50 rows
            st.subheader("Preview of CSV (first 50 rows)")
            st.write(df.head(50))

            # Select Source and Target columns
            columns = df.columns.tolist()
            source_column = st.selectbox("Select Source column", columns)
            target_column = st.selectbox("Select Target column", columns)

            # Save df in session state for use in later steps
            st.session_state['df'] = df
            st.session_state['source_column'] = source_column
            st.session_state['target_column'] = target_column

        except Exception as e:
            st.error(f"Error reading file: {e}")
            st.write("Please adjust the number of rows to skip and try again.")

if __name__ == "__main__":
    main()