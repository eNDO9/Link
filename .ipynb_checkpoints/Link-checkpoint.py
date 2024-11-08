import streamlit as st
import pandas as pd
import networkx as nx
from io import StringIO, BytesIO

def main():
    st.title("Network Graph Creator")

    # Step 1: Upload and Preview CSV
    st.header("Step 1: Upload CSV File")
    
    # Check if the CSV has already been loaded into session_state
    if "df" not in st.session_state:
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        skip_rows = st.number_input("Number of rows to skip", min_value=0, value=0, step=1)
        
        # Display the CSV preview as part of Step 1
        if uploaded_file is not None:
            try:
                # Load and display a preview of the first 50 rows
                preview_df = pd.read_csv(
                    StringIO(uploaded_file.getvalue().decode("utf-8")),
                    skiprows=skip_rows,
                    nrows=50,
                    on_bad_lines='skip'
                )
                st.subheader("CSV Data Preview (first 50 rows)")
                st.write(preview_df)

                # Load full CSV and save it in session_state when "Load CSV" is clicked
                if st.button("Load CSV"):
                    st.session_state.df = pd.read_csv(
                        StringIO(uploaded_file.getvalue().decode("utf-8")),
                        skiprows=skip_rows,
                        on_bad_lines='skip'
                    )
                    st.session_state.step = 2  # Proceed to Step 2
            except Exception as e:
                st.warning("Error loading file. Try adjusting the rows to skip.")
    else:
        # Proceed to Step 2 if the DataFrame is already loaded
        step2_select_columns()

def step2_select_columns():
    st.header("Step 2: Select Columns for the Graph")
    
    # Ensure DataFrame is loaded
    df = st.session_state.get("df")
    if df is None:
        st.warning("No data loaded. Please go back to Step 1.")
        return

    # Column selection
    columns = df.columns.tolist()
    source_column = st.selectbox("Select Source column", columns, index=0, key="source_column")
    target_column = st.selectbox("Select Target column", columns, index=1 if len(columns) > 1 else 0, key="target_column")

    # Display preview of selected columns as edges
    st.subheader("Preview of Selected Columns for Network (first 50 rows)")
    st.write(df[[source_column, target_column]].head(50))

    # Button to move to Step 3 and create the network graph
    if st.button("Create Network Graph"):
        # Set `session_state` values after confirming selections, minimizing errors
        st.session_state.step = 3
        st.session_state.source_column = source_column
        st.session_state.target_column = target_column
        step3_create_and_export_graph()  # Directly call the next step function

def step3_create_and_export_graph():
    st.header("Step 3: Create and Export Network Graph")
    
    # Ensure columns are selected
    df = st.session_state.get("df")
    source_column = st.session_state.get("source_column")
    target_column = st.session_state.get("target_column")
    
    if df is None or source_column is None or target_column is None:
        st.warning("No columns selected. Please go back to Step 2.")
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
