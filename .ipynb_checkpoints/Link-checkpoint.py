def main():
    st.title("Network Graph Creator")

    # Step 1: Upload CSV
    st.header("Upload CSV File")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        # Option to skip rows
        skip_rows = st.number_input("Number of rows to skip", min_value=0, value=0, step=1)
        st.write("Reading file...")

        # Read the CSV with option to skip rows
        try:
            df = pd.read_csv(uploaded_file, skiprows=skip_rows)
            st.write("File read successfully!")
        except Exception as e:
            st.error(f"Error reading file: {e}")
            return

        # Preview first 50 rows
        st.subheader("Preview of CSV (first 50 rows)")
        st.write(df.head(50))

        # Select Source and Target columns
        columns = df.columns.tolist()
        source_column = st.selectbox("Select Source column", columns)
        target_column = st.selectbox("Select Target column", columns)

        # Print notifications
        st.write("Source and Target columns selected.")
        st.write(f"Source: {source_column}, Target: {target_column}")

        # Save df in session state for use in later steps
        st.session_state['df'] = df
        st.session_state['source_column'] = source_column
        st.session_state['target_column'] = target_column

if __name__ == "__main__":
    main()