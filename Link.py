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

    # Step 2.5: Process Columns
    if "source_column" in st.session_state and "target_column" in st.session_state:
        if st.button("Process Columns"):
            processed_df = process_columns(st.session_state.df, st.session_state.source_column, st.session_state.target_column)
            st.session_state.processed_df = processed_df  # Store the processed DataFrame
            st.success("Columns processed successfully!")
            # Display preview of the processed data
            st.subheader("Processed Data Preview for Network (first 50 rows)")
            st.write(processed_df[[st.session_state.source_column, st.session_state.target_column]].head(50))

    # Step 3: Create and Export Network Graph
    if "processed_df" in st.session_state:
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

                # Add edges to the graph from the processed DataFrame
                edges = st.session_state.processed_df[[st.session_state.source_column, st.session_state.target_column]].values.tolist()
                G.add_edges_from(edges)
                
                # Store the created graph in session state
                st.session_state.graph = G  
                
                # Save a success message in session state to persist across Step 3
                st.session_state.success_message = f"{graph_type} graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges."
                st.success(st.session_state.success_message)
            except Exception as e:
                st.error("Failed to create the network graph.")

        # Display the success message if the graph is already created
        if "success_message" in st.session_state:
            st.success(st.session_state.success_message)

        # Export options only if a graph has been created
        if "graph" in st.session_state:
            export_graph(st.session_state.graph, graph_type)

def process_columns(df, source_column, target_column):
    """Process data for network graph by exploding, dropping empty rows, and removing self-loops."""
    # Explode lists in the Source and Target columns if they contain lists
    if df[source_column].apply(lambda x: isinstance(x, list)).any():
        df = df.explode(source_column)
    if df[target_column].apply(lambda x: isinstance(x, list)).any():
        df = df.explode(target_column)

    # Drop rows where either Source or Target is empty (None or NaN)
    df = df.dropna(subset=[source_column, target_column])

    # Remove self-loops where Source == Target
    df = df[df[source_column] != df[target_column]]

    return df

def export_graph(G, graph_type):
    st.subheader("Export Network Graph")

    # to_csv function without "Key" column for Multi-graphs
    def to_csv(G, graph_type):
        nodes_df = pd.DataFrame(G.nodes, columns=["Node"]) if G.number_of_nodes() > 0 else pd.DataFrame(columns=["Node"])
        if "Multi" in graph_type:
            edges_df = pd.DataFrame([(u, v) for u, v, _ in G.edges(keys=True)], columns=["Source", "Target"])
        else:
            edges_df = pd.DataFrame([(u, v) for u, v in G.edges], columns=["Source", "Target"])
        return nodes_df, edges_df

    def to_gexf(G):
        if G.number_of_edges() > 0:
            gexf_data = BytesIO()
            nx.write_gexf(G, gexf_data)
            gexf_data.seek(0)
            return gexf_data
        else:
            st.warning("The graph has no edges to export in GEXF format.")
            return None

    # Set GEXF as the default export format
    export_format = st.selectbox("Choose export format", ["GEXF", "CSV (Nodes and Edges)"])

    if export_format == "CSV (Nodes and Edges)":
        nodes_df, edges_df = to_csv(G, graph_type)
        if not nodes_df.empty:
            nodes_csv = nodes_df.to_csv(index=False).encode('utf-8')
            st.download_button(label="Download Nodes CSV", data=nodes_csv, file_name="nodes.csv", mime="text/csv")
        if not edges_df.empty:
            edges_csv = edges_df.to_csv(index=False).encode('utf-8')
            st.download_button(label="Download Edges CSV", data=edges_csv, file_name="edges.csv")

    elif export_format == "GEXF":
        gexf_data = to_gexf(G)
        if gexf_data:
            st.download_button(label="Download GEXF", data=gexf_data, file_name="network_graph.gexf", mime="application/gexf+xml")

if __name__ == "__main__":
    main()
