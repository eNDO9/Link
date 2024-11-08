import streamlit as st
import pandas as pd
import networkx as nx
from io import StringIO, BytesIO

def main():
    st.title("Network Graph Creator")

    # Step 1: File Upload and Preview
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    skip_rows = st.number_input("Number of rows to skip", min_value=0, value=0, step=1)

    if uploaded_file is not None:
        # Displaying CSV preview immediately based on `skip_rows`
        preview_df = None
        try:
            preview_df = pd.read_csv(
                StringIO(uploaded_file.getvalue().decode("utf-8")),
                skiprows=skip_rows,
                nrows=50,
                on_bad_lines='skip'
            )
            st.subheader("CSV Data Preview (first 50 rows)")
            st.write(preview_df)
        except Exception as e:
            st.warning("Error loading file. Try adjusting the rows to skip.")

        # Full DataFrame loading on "Load CSV" button click
        if st.button("Load CSV"):
            try:
                st.session_state.df = pd.read_csv(
                    StringIO(uploaded_file.getvalue().decode("utf-8")),
                    skiprows=skip_rows,
                    on_bad_lines='skip'
                )
                st.success("CSV loaded successfully!")
            except Exception as e:
                st.error("Failed to load the full dataset. Please check the file format and try again.")

    # Step 2: Column Selection
    if "df" in st.session_state:
        st.subheader("Step 2: Select Columns for the Graph")
        columns = st.session_state.df.columns.tolist()
        source_column = st.selectbox("Select Source column", columns, index=0)
        target_column = st.selectbox("Select Target column", columns, index=1 if len(columns) > 1 else 0)

        # Display preview of selected columns
        st.subheader("Preview of Selected Columns for Network (first 50 rows)")
        st.write(st.session_state.df[[source_column, target_column]].head(50))

        # Save column selections in session state
        st.session_state.source_column = source_column
        st.session_state.target_column = target_column

    # Step 3: Create and Export Network Graph
    if "source_column" in st.session_state and "target_column" in st.session_state:
        st.subheader("Step 3: Create and Export Network Graph")

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
            try:
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
                edges = st.session_state.df[[st.session_state.source_column, st.session_state.target_column]].values.tolist()
                G.add_edges_from(edges)
                st.session_state.graph = G  # Store the created graph in session state
                st.success(f"{graph_type} graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
            except Exception as e:
                st.error("Failed to create the network graph.")

        # Export options only if a graph has been created
        if "graph" in st.session_state:
            export_graph(st.session_state.graph)

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

    # Show download buttons
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