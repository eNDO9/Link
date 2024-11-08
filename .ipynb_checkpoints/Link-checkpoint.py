import streamlit as st
import pandas as pd
import networkx as nx
from io import StringIO, BytesIO

def main():
    st.title("Network Graph Creator")

    # Initialize session state variables
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    if 'skip_rows' not in st.session_state:
        st.session_state.skip_rows = 0
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'source_column' not in st.session_state:
        st.session_state.source_column = None
    if 'target_column' not in st.session_state:
        st.session_state.target_column = None

    # Step 1: Upload and Preview CSV
    st.header("Step 1: Upload CSV File")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file
    elif st.session_state.uploaded_file is not None:
        uploaded_file = st.session_state.uploaded_file

    skip_rows = st.number_input("Number of rows to skip", min_value=0, value=st.session_state.skip_rows, step=1)
    st.session_state.skip_rows = skip_rows

    # Proceed if a file has been uploaded
    if uploaded_file is not None:
        try:
            # Display preview of the first 50 rows
            preview_df = pd.read_csv(
                StringIO(uploaded_file.getvalue().decode("utf-8")),
                skiprows=skip_rows,
                nrows=50,
                on_bad_lines='skip'
            )
            st.subheader("CSV Data Preview (first 50 rows)")
            st.write(preview_df)

            # Button to proceed to column selection
            if st.button("Load CSV"):
                # Load the full DataFrame and store in session state
                df = pd.read_csv(
                    StringIO(uploaded_file.getvalue().decode("utf-8")),
                    skiprows=skip_rows,
                    on_bad_lines='skip'
                )
                st.session_state.df = df
                step2_select_columns()
            elif st.session_state.df is not None:
                # If DataFrame is already loaded, proceed to Step 2
                step2_select_columns()
        except Exception as e:
            st.warning("Error loading file. Try adjusting the rows to skip.")
    elif st.session_state.df is not None:
        # If DataFrame is already loaded, proceed to Step 2
        step2_select_columns()

def step2_select_columns():
    st.header("Step 2: Select Columns for the Graph")

    df = st.session_state.df

    if df is None:
        st.error("Dataframe not loaded. Please upload and load a CSV file first.")
        return

    # Column selection
    columns = df.columns.tolist()
    source_column = st.selectbox("Select Source column", columns, index=0, key="source_column")
    target_column = st.selectbox("Select Target column", columns, index=1 if len(columns) > 1 else 0, key="target_column")

    st.session_state.source_column = source_column
    st.session_state.target_column = target_column

    # Display preview of selected columns
    st.subheader("Preview of Selected Columns for Network (first 50 rows)")
    st.write(df[[source_column, target_column]].head(50))

    # Button to proceed to graph creation
    if st.button("Create Network Graph"):
        create_and_export_graph()

def create_and_export_graph():
    st.header("Step 3: Create and Export Network Graph")

    df = st.session_state.df
    source_column = st.session_state.source_column
    target_column = st.session_state.target_column

    if df is None or source_column is None or target_column is None:
        st.error("Please complete the previous steps.")
        return

    # Graph type selection
    graph_type = st.selectbox(
        "Select Graph Type",
        ["Directed", "Undirected", "Multi-Directed", "Multi-Undirected"],
        key="graph_type",
        help=("Directed: One-way relationships.\n"
              "Undirected: Mutual relationships.\n"
              "Multi-Directed: Directed graph allowing multiple edges.\n"
              "Multi-Undirected: Undirected graph allowing multiple edges.")
    )

    # Button to generate the graph
    if st.button("Generate Graph"):
        # Initialize the appropriate NetworkX graph
        if graph_type == "Directed":
            G = nx.DiGraph()
        elif graph_type == "Undirected":
            G = nx.Graph()
        elif graph_type == "Multi-Directed":
            G = nx.MultiDiGraph()
        elif graph_type == "Multi-Undirected":
            G = nx.MultiGraph()

        # Add edges to the graph
        edges = df[[source_column, target_column]].values.tolist()
        G.add_edges_from(edges)
        st.write(f"{graph_type} graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

        # Export options
        export_graph(G)

def export_graph(G):
    st.subheader("Export Network Graph")

    # Functions to export the graph
    def to_csv(G):
        nodes_df = pd.DataFrame(G.nodes, columns=["Node"])
        edges_df = pd.DataFrame(list(G.edges), columns=["Source", "Target"])
        return nodes_df, edges_df

    def to_gexf(G):
        gexf_data = BytesIO()
        nx.write_gexf(G, gexf_data)
        gexf_data.seek(0)
        return gexf_data

    # Export format selection
    export_format = st.selectbox("Choose export format", ["CSV (Nodes and Edges)", "GEXF"], key="export_format")

    # Download buttons for the selected format
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
