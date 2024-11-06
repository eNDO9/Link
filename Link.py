import streamlit as st
import pandas as pd
import networkx as nx
from io import BytesIO

def main():
    st.title("Network Graph Creator")

    # Step tracking in session state
    if "step" not in st.session_state:
        st.session_state.step = "upload"  # Initial step

    # Step 1: Upload and Adjust Rows to Skip
    if st.session_state.step == "upload":
        st.header("Upload CSV File")
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

        # Display guidance message if there was a loading error
        if "load_error" in st.session_state and st.session_state.load_error:
            st.info("This file may contain extra rows or inconsistent formatting at the beginning, likely from BrandWatch. "
                    "**Try increasing the 'Number of rows to skip' option and click 'Load CSV' again.**")

        if uploaded_file is not None:
            # Option to skip rows
            skip_rows = st.number_input("Number of rows to skip", min_value=0, value=0, step=1)

            # Button to confirm and load CSV
            if st.button("Load CSV"):
                try:
                    # Attempt to read the CSV with the specified number of rows to skip
                    df = pd.read_csv(uploaded_file, skiprows=skip_rows)
                    st.session_state.df = df  # Store the dataframe in session state
                    st.session_state.load_error = False  # No error
                    st.session_state.step = "preview"  # Move to the next step

                except Exception:
                    # Set load error flag and show guidance
                    st.session_state.load_error = True
                    st.warning("This file may contain extra rows or inconsistent formatting. "
                               "Adjust the 'Number of rows to skip' option and try loading again.")

    # Step 2: Preview and Column Selection
    if st.session_state.step == "preview":
        st.header("CSV Preview and Column Selection")

        # Display the preview of the loaded CSV
        st.subheader("Preview of CSV (first 50 rows)")
        st.write(st.session_state.df.head(50))

        # Select Source and Target columns
        columns = st.session_state.df.columns.tolist()
        source_column = st.selectbox("Select **Source** column", columns)
        target_column = st.selectbox("Select **Target** column", columns)

        # Step 3: Choose Graph Type
        st.subheader("Choose Graph Type")
        graph_type = st.selectbox(
            "Select the type of network graph",
            ["Directed", "Undirected", "Multi-Directed", "Multi-Undirected"],
            help=("Directed: One-way relationships.\n"
                  "Undirected: Mutual relationships.\n"
                  "Multi-Directed: Directed graph allowing multiple edges between nodes.\n"
                  "Multi-Undirected: Undirected graph allowing multiple edges between nodes.")
        )

        # Button to create the network graph
        if st.button("Create Network Graph"):
            # Initialize graph based on selection
            if graph_type == "Directed":
                G = nx.DiGraph()
            elif graph_type == "Undirected":
                G = nx.Graph()
            elif graph_type == "Multi-Directed":
                G = nx.MultiDiGraph()
            elif graph_type == "Multi-Undirected":
                G = nx.MultiGraph()

            # Add edges to the graph
            edges = st.session_state.df[[source_column, target_column]].values.tolist()
            G.add_edges_from(edges)
            st.write(f"{graph_type} graph created successfully with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

            # Export options for the graph
            export_graph(G)

def export_graph(G):
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