import streamlit as st
import pandas as pd
import networkx as nx
from io import StringIO, BytesIO
import re
from urllib.parse import urlparse

def main():
    st.title("Link")
    st.markdown("<p style='font-size:20px'>This tool creates a network graph from imported CSVs.</p>", unsafe_allow_html=True)

    # Step 1: Upload Multiple Files
    uploaded_files = st.file_uploader("Upload CSV files", type="csv", accept_multiple_files=True)

    if uploaded_files:
        st.subheader("Adjust Settings and Preview Data")
        rows_to_skip = {}  # Store rows-to-skip values for each file
        previews = {}      # Store dynamic previews for each file

        # Step 1.1: Iterate through files to allow individual adjustments
        for file in uploaded_files:
            # User input for rows to skip
            rows_to_skip[file.name] = st.number_input(
                f"Rows to skip for {file.name}", min_value=0, value=0, step=1, key=f"skip_{file.name}"
            )

            # Dynamic preview based on rows-to-skip
            try:
                preview_df = pd.read_csv(
                    StringIO(file.getvalue().decode("utf-8")),
                    skiprows=rows_to_skip[file.name],
                    nrows=10,  # Only preview the first 10 rows
                    on_bad_lines="skip"
                )
                previews[file.name] = preview_df
            except Exception as e:
                previews[file.name] = None
                st.warning(f"Error loading preview for {file.name}. Adjust rows to skip.")

            # Display preview or error message
            #st.write(f"Preview of {file.name} (adjusted for {rows_to_skip[file.name]} rows skipped):")
            if previews[file.name] is not None:
                with st.expander("Click to preview merged data (first 50 rows)", expanded=False):
                    st.write(previews[file.name])
            else:
                st.error("Unable to preview data. Adjust rows to skip or check the file format.")

        # Step 1.2: Process all files and merge when the user clicks "Process All and Merge"
        if st.button("Process All and Merge"):
            processed_csvs = []
            for file in uploaded_files:
                try:
                    # Load full file based on rows-to-skip
                    df = pd.read_csv(
                        StringIO(file.getvalue().decode("utf-8")),
                        skiprows=rows_to_skip[file.name],
                        on_bad_lines="skip"
                    )
                    processed_csvs.append(df)
                except Exception as e:
                    st.error(f"Failed to process {file.name}: {e}")

            # Merge processed DataFrames
            if processed_csvs:
                merged_df = pd.concat(processed_csvs, ignore_index=True)
                st.session_state.df = merged_df  # Store the merged DataFrame in session_state
                st.success("All files processed and merged successfully!")
                st.write("CSV preview (first 25 rows and last 25 rows)")
                if len(merged_df) > 50:
                    preview_df = pd.concat([merged_df.head(25), merged_df.tail(25)])
                else:
                    preview_df = merged_df  # Show all rows if there are fewer than 50
                st.write(preview_df)

    # Step 2: Column Selection
    if "df" in st.session_state:
        st.subheader("Step 2: Select Columns and Processing Method")
        columns = st.session_state.df.columns.tolist()
        source_column = st.selectbox("Select Source column", columns, index=0)
        target_column = st.selectbox("Select Target column", columns, index=1 if len(columns) > 1 else 0)

        # Processing options for each column
        processing_options = [
            "No Processing", 
            "Hashtags - Free Text", 
            "Domains - Free Text", 
            "Mentioned Users - Free Text", 
            "Hashtags - Comma Separated List", 
            "Domains - Comma Separated List", 
            "Mentioned Users - Comma Separated List"
        ]

        source_processing = st.selectbox("Select Processing for Source column", processing_options)
        target_processing = st.selectbox("Select Processing for Target column", processing_options)

        # Save selections in session state
        st.session_state.source_column = source_column
        st.session_state.target_column = target_column
        st.session_state.source_processing = source_processing
        st.session_state.target_processing = target_processing

        # Display preview of selected columns
        st.subheader("Preview of Selected Columns for Network (first 50 rows)")
        st.write(st.session_state.df[[source_column, target_column]].head(50))

    # Step 2.5: Process Columns
    if "source_column" in st.session_state and "target_column" in st.session_state:
        if st.button("Process Columns"):
            processed_df = process_columns(
                st.session_state.df, 
                st.session_state.source_column, 
                st.session_state.target_column, 
                st.session_state.source_processing, 
                st.session_state.target_processing
            )
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

                # Only save the success message once
                st.session_state.success_message = f"{graph_type} graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges."
            except Exception as e:
                st.error("Failed to create the network graph.")

        # Display the success message once, only when the graph is created
        if "success_message" in st.session_state and st.session_state.success_message:
            st.success(st.session_state.success_message)
            # Clear the success message after displaying it once
            st.session_state.success_message = None

        # Export options only if a graph has been created
        if "graph" in st.session_state:
            export_graph(st.session_state.graph, graph_type)

def process_columns(df, source_column, target_column, source_processing, target_processing):
    """Process data for network graph by applying specified processing options, exploding lists, dropping empty rows, and removing self-loops."""
    df[source_column] = apply_processing(df[source_column], source_processing)
    df[target_column] = apply_processing(df[target_column], target_processing)

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

def apply_processing(column, processing_type):
    """Apply the selected processing type to a column."""
    column = column.str.lower()  # Convert all text to lowercase by default

    if processing_type == "No Processing":
        return column
    elif processing_type == "Hashtags - Free Text":
        return column.str.findall(r"#\w+").apply(lambda x: [tag.lower() for tag in x] if isinstance(x, list) else x)    
    elif processing_type == "Domains - Free Text":
        return column.apply(lambda x: urlparse(x).netloc if pd.notnull(x) else None).str.lower()    
    elif processing_type == "Mentioned Users - Free Text":
        return column.str.findall(r"@(\w+)").apply(lambda x: [mention.lower() for mention in x] if isinstance(x, list) else x)    
    elif processing_type == "Hashtags - Comma Separated List":
        return column.str.split(",").apply(lambda x: [tag.strip().lower() for tag in x if tag.strip().startswith("#")] if isinstance(x, list) else x)    
    elif processing_type == "Domains - Comma Separated List":
        return column.str.split(",").apply(lambda x: [urlparse(domain.strip()).netloc.lower() for domain in x if pd.notnull(domain)] if isinstance(x, list) else x)    
    elif processing_type == "Mentioned Users - Comma Separated List":
        return column.str.split(",").apply(lambda x: [mention.strip().lstrip("@").lower() for mention in x if mention.strip().startswith("@")] if isinstance(x, list) else x)
    
    return column

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
