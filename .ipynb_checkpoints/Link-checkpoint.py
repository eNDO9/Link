import streamlit as st
import pandas as pd
import networkx as nx
from io import BytesIO

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
            st.error(f"An unexpected error occurred: {e}")
            return

        # Preview first 50 rows
        st.subheader("Preview of CSV (first 50 rows)")
        st.write(df.head(50))

        # Select Source and Target columns
        columns = df.columns.tolist()
        source_column = st.selectbox("Select Source column", columns)
        target_column = st.selectbox("Select Target column", columns)

        # Step 1: Preview Source and Target columns
        st.subheader("Preview of Source and Target Columns")
        st.write(df[[source_column, target_column]].head(10))  # Show first 10 rows of Source and Target columns

        # Step 2: Choose Graph Type
        st.subheader("Choose Graph Type")
        graph_type = st.selectbox(
            "Select the type of network graph",
            ["Directed", "Undirected", "Multi-Directed", "Multi-Undirected"],
            help=("Directed: One-way relationships.\n"
                  "Undirected: Mutual relationships.\n"
                  "Multi-Directed: Directed graph allowing multiple edges between nodes.\n"
                  "Multi-Undirected: Undirected graph allowing multiple edges between nodes.")
        )

        # Step 3: Create Network Graph
        if st.button("Create Network Graph"):
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
            st.write(f"{graph_type} graph created successfully with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

        # Step 4: Export Options
        st.subheader("Export Network Graph")
        
        # Function to convert NetworkX graph to CSVs for download
        def to_csv(G):
            nodes_df = pd.DataFrame(G.nodes, columns=["Node"])
            edges_df = pd.DataFrame([(u, v) for u, v in G.edges], columns=["Source", "Target"])
            return nodes_df, edges_df
        
        # Function to convert NetworkX graph to GEXF for download
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