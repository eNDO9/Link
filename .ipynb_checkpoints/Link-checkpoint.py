import streamlit as st
import pandas as pd

def main():
    st.title("Network Graph Creator")

    # Step 1: Upload CSV
    st.header("Upload CSV File")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file is not None:
        # Step 2: Show initial lines to help the user identify the rows to skip
        st.write("Loading file as raw text to display initial lines...")
        raw_lines = uploaded_file.getvalue().decode("utf-8").splitlines()
        st.text("\n".join(raw_lines[:10]))  # Show first 10 lines

        # Option to skip rows
        skip_rows = st.number_input("Number of rows to skip", min_value=0, value=0, step=1)
        
        # Step 3: Attempt to read CSV with skip rows option
        st.write("Attempting to read file with specified skip rows...")
        try:
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
            st.write("Adjust the 'Number of rows to skip' option and try again.")

if __name__ == "__main__":
    main()