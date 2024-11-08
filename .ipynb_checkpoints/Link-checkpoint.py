import streamlit as st
import pandas as pd
import networkx as nx
from io import StringIO, BytesIO

# Cache the CSV loading function to avoid reloading on reruns
@st.cache_data
def load_full_csv(file, skip_rows):
    return pd.read_csv(StringIO(file.getvalue().decode("utf-8")), skiprows=skip_rows, on_bad_lines='skip')

def main():
    st.title("Network Graph Creator")
    
    # Step 1: Upload and Preview CSV
    st.header("Step 1: Upload CSV File")
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

            # Proceed to Step 2 upon clicking "Load CSV"
            if st.button("Load CSV"):
                df = load_full_csv(uploaded_file, skip_rows)
                step2_select_columns(df)
        except Exception as e:
            st.warning("Error loading file. Try adjusting the rows to skip.")

def step2_select_columns(df):
    st.header("Step 2: Select Columns for the Graph")

    # Column selection
    columns = df.columns.tolist()
    source_column = st.selectbox("Select Source column", columns, index=0, key="source_column")
    target_column = st.selectbox("Select Target column", columns, index=1 if len(columns) > 1 else 0, key="target_column")

    # Display preview of selected columns as edges
    st.subheader("Preview of Selected Columns for Network (first 50 rows)")
    st.write(df[[source_column, target_column]].head(50))

    # Button to move to Step 3 and create the network graph
    if st.button("Create Network Graph"):
        create_and_export_graph(df, source_column, target_column)

def create_and_export_graph(df, source_column, target_column):
    st.header("Step 3: Create and Export Network Graph")

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
