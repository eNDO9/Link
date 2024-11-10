import streamlit as st
import pandas as pd
import networkx as nx
from io import StringIO, BytesIO
import re

def main():
    st.title("Network Graph Creator")

    # Step 1: File Upload and Preview
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    skip_rows = st.number_input("Number of rows to skip", min_value=0, value=0, step=1)

    if uploaded_file is not None:
        # Displaying CSV preview immediately based on `skip_rows`
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

        # Load CSV on button click
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

        # Save column selections in session state
        st.session_state.source_column = source_column
        st.session_state.target_column = target_column

        # Step 3a: Process Columns
        st.subheader("Step 3a: Process Columns")

        def process_column(df, column, method):
            """Process a column based on the selected method."""
            if method == "No Processing":
                return df[column].str.lower()
            elif method == "Comma-Separated List":
                return df[column].str.lower().str.split(',')
            elif method == "Free Text - Hashtags":
                return df[column].str.lower().apply(lambda x: re.findall(r"#\w+", str(x)))
            elif method == "Free Text - Mentions":
                # Extract mentions without the '@' symbol
                return df[column].str.lower().apply(lambda x: [mention[1:] for mention in re.findall(r"@\w+", str(x))])
            elif method == "Free Text - URLs":
                # Extract domains only from URLs
                return df[column].str.lower().apply(lambda x: re.findall(r"https?://(?:www\.)?([^/]+)", str(x)))
            else:
                return df[column].str.lower()

        # Processing options
        source_processing = st.selectbox("Process Source Column", ["No Processing", "Comma-Separated List", "Free Text - Hashtags", "Free Text - Mentions", "Free Text - URLs"])
        target_processing = st.selectbox("Process Target Column", ["No Processing", "Comma-Separated List", "Free Text - Hashtags", "Free Text - Mentions", "Free Text - URLs"])

        # Apply processing and show preview
        processed_source = process_column(st.session_state.df, source_column, source_processing)
        processed_target = process_column(st.session_state.df, target_column, target_processing)
        
        # Display processed preview
        st.subheader("Preview of Processed Columns for Network (first 50 rows)")
        st.write(pd.DataFrame({source_column: processed_source, target_column: processed_target}).head(50))

        # Step 3b: Create and Export Network Graph
        st.subheader("Step 3b: Create and Export Network Graph")
        
        # Graph type selection
        graph_type = st.selectbox("Select Graph Type", ["Directed", "Undirected", "Multi-Directed", "Multi-Undirected"])

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

                # Add edges from processed columns
                for source, target in zip(processed_source, processed_target):
                    if isinstance(source, list) and isinstance(target, list):
                        for s in source:
                            for t in target:
                                G.add_edge(s, t)
                    elif isinstance(source, list):
                        for s in source:
                            G.add_edge(s, target)
                    elif isinstance(target, list):
                        for t in target:
                            G.add_edge(source, t)
                    else:
                        G.add_edge(source, target)

                # Display graph summary
                st.success(f"{graph_type} graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
                st.session_state.graph = G
            except Exception as e:
                st.error("Failed to create the network graph.")

        # Export options (similar to before)
        if "graph" in st.session_state:
            export_graph(st.session_state.graph, graph_type)

def export_graph(G, graph_type):
    st.subheader("Export Network Graph")
    def to_csv(G, graph_type):
        nodes_df = pd.DataFrame(G.nodes, columns=["Node"]) if G.number_of_nodes() > 0 else pd.DataFrame(columns=["Node"])
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

    export_format = st.selectbox("Choose export format", ["GEXF", "CSV (Nodes and Edges)"])

    if export_format == "CSV (Nodes and Edges)":
        nodes_df, edges_df = to_csv(G, graph_type)
        nodes_csv = nodes_df.to_csv(index=False).encode('utf-8')
        edges_csv = edges_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="Download Nodes CSV", data=nodes_csv, file_name="nodes.csv", mime="text/csv")
        st.download_button(label="Download Edges CSV", data=edges_csv, file_name="edges.csv")
    elif export_format == "GEXF":
        gexf_data = to_gexf(G)
        if gexf_data:
            st.download_button(label="Download GEXF", data=gexf_data, file_name="network_graph.gexf", mime="application/gexf+xml")

if __name__ == "__main__":
    main()
