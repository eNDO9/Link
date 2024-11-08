import streamlit as st
import pandas as pd
from io import StringIO, BytesIO
import networkx as nx

def main():
    # Initialize session state variables if they are not already set
    if "step" not in st.session_state:
        st.session_state.step = 1
        st.session_state.df = None
        st.session_state.source_column = None
        st.session_state.target_column = None

    st.title("Network Graph Creator")
    
    # Step-by-step process using session state
    if st.session_state.step == 1:
        step1_upload_and_preview()
    elif st.session_state.step == 2:
        step2_select_columns()
    elif st.session_state.step == 3:
        step3_create_and_export_graph()

def step1_upload_and_preview():
    st.header("Step 1: Upload CSV File")

    # File uploader and row skip option
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    skip_rows = st.number_input("Number of rows to skip", min_value=0, value=0, step=1)

    if uploaded_file is not None:
        try:
            # Read the first 50 lines for a preview, skipping any bad lines
            preview_df = pd.read_csv(
                StringIO(uploaded_file.getvalue().decode("utf-8")),
                skiprows=skip_rows,
                nrows=50,
                on_bad_lines='skip'
            )
            st.subheader("CSV Data Preview (first 50 rows)")
            st.write(preview_df)

            # Button to load the full CSV strictly
            if st.button("Load CSV"):
                st.session_state.df = pd.read_csv(
                    StringIO(uploaded_file.getvalue().decode("utf-8")),
                    skiprows=skip_rows
                )
                st.session_state.step = 2  # Move to the next step
        except Exception as e:
            st.warning("Error loading file. Try adjusting the rows to skip.")
            st.stop()

def step2_select_columns():
    st.header("Step 2: Select Columns for the Graph")
    
    # Ensure DataFrame is loaded
    if st.session_state.df is None:
        st.warning("No data loaded. Please go back to Step 1.")
        if st.button("Back"):
            st.session_state.step = 1
        return

    # Show available columns and select source/target columns
    columns = st.session_state.df.columns.tolist()
    st.write("Available Columns:", columns)  # Display available columns for debugging

    # Source and target column selection with validation
    st.session_state.source_column = st.selectbox("Select Source column", columns)
    st.session_state.target_column = st.selectbox("Select Target column", columns)

    # Check if the selected columns are valid and display a preview
    try:
        st.subheader("Preview of Selected Columns")
        preview_df = st.session_state.df[[st.session_state.source_column, st.session_state.target_column]].head(10)
        st.write(preview_df)
    except KeyError as e:
        st.error(f"Error: Selected columns not found. {e}")
        if st.button("Back to Upload"):
            st.session_state.step = 1
        return
    except ValueError as e:
        st.error(f"Error: {e}")
        if st.button("Back to Upload"):
            st.session_state.step = 1
        return

    # Navigation buttons
    if st.button("Back"):
        st.session_state.step = 1
    if st.button("Next"):
        st.session_state.step = 3

def step3_create_and_export_graph():
    st.header("Step 3: Create and Export Network Graph")

    # Ensure columns are selected
    if st.session_state.df is None or st.session_state.source_column is None or st.session_state.target_column is None:
        st.warning("No columns selected. Please go back to Step 2.")
        if st.button("Back"):
            st.session_state.step = 2
        return

    # Graph type selection
    graph_type = st.selectbox(
        "Select Graph Type",
        ["Directed", "Undirected", "Multi-Directed", "Multi-Undirected"],
        help=("Directed: One-way relationships.\n"
              "Undirected: Mutual relationships.\n"
              "Multi-Directed: Directed graph allowing multiple edges.\n"
              "Multi-Undirected: Undirected graph allowing multiple edges.")
    )

    # Button to create the network graph
    if st.button("Create Network Graph"):
        if graph_type == "Directed":
            G = nx.DiGraph()
        elif graph_type == "Undirected":
            G = nx.Graph()
        elif graph_type == "Multi-Directed":
            G = nx.MultiDiGraph()
        elif graph_type == "Multi-Undirected":
            G = nx.MultiGraph()

        edges = st.session_state.df[[st.session_state.source_column, st.session_state.target_column]].values.tolist()
        G.add_edges_from(edges)
        st.write(f"{graph_type} graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

        export_graph(G)

    # Navigation button
    if st.button("Back"):
        st.session_state.step = 2

def export_graph(G):
    st.subheader("Export Network Graph")

    # Function to convert NetworkX graph to CSVs or GEXF for download
    def to_csv(G):
        nodes_df = pd.DataFrame(G.nodes, columns=["Node"])
        edges_df = pd.DataFrame([(u, v) for u, v in G.edges], columns=["Source", "Target"])
        return nodes_df, edges_df

    def to_gexf(G):
        gexf_data = BytesIO()
        nx.write_gexf(G, gexf_data)
        gexf_data.seek(0)
        return gexf_data

    export_format = st.selectbox("Choose export format", ["CSV (Nodes and Edges)", "GEXF"])

    if export_format == "CSV (Nodes and Edges)":
        nodes_df, edges_df = to_csv(G)
        nodes_csv = nodes_df.to_csv(index=False).encode('utf-8')
        edges_csv = edges_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="Download Nodes CSV", data=nodes_csv, file_name="nodes.csv", mime="text/csv")
        st.download_button(label="Download Edges CSV", data=edges_csv, file_name="edges.csv", mime="text/csv")

    elif export_format == "GEXF":
        gexf_data = to_gexf(G)
        st.download_button(label="Download GEXF", data=gexf_data, file_name="network_graph.gexf", mime="application/gexf+xml")

if __name__ == "__main__":
    main()
