import streamlit as st
import pandas as pd
import networkx as nx
from io import StringIO, BytesIO
import re
from urllib.parse import urlparse

def main():
    st.title("Link")
    # Add a logo
    st.logo("logo.png", size='large')
    
    st.markdown("<p style='font-size:20px; font-style: italic;'>This tool creates a network graph from imported CSVs.</p>", unsafe_allow_html=True)
    st.write("")
    
    # Custom CSS for footer
    footer = """
        <style>
            .footer {
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100%;
                background-color: #0E1117; /* Matches the dark mode */
                color: white;
                text-align: center;
                padding: 10px 0;
                font-size: 18px;
            }
            .footer a {
                color: #0068B2; /* Matches your organization's color palette */
                text-decoration: none;
                font-weight: bold;
            }
            .footer a:hover {
                text-decoration: underline;
            }
        </style>
        <div class="footer">
            Need help? <a href="https://github.com/eNDO9/Link/blob/main/Overview%20-%20Link.pdf" target="_blank">View the User Guide</a>
        </div>
    """
    st.markdown(footer, unsafe_allow_html=True)
    
    st.subheader("Step 1: Upload and Process CSVs")

    # Step 1: Upload and Process CSVs
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

            # Collapsible preview for each file
            try:
                preview_df = pd.read_csv(
                    StringIO(file.getvalue().decode("utf-8")),
                    skiprows=rows_to_skip[file.name],
                    nrows=10,  # Only preview the first 10 rows
                    on_bad_lines="skip"
                )
                previews[file.name] = preview_df
                with st.expander(f"Preview of {file.name} (first 10 rows)", expanded=False):
                    st.write(preview_df)
            except Exception as e:
                previews[file.name] = None
                st.warning(f"Error loading preview for {file.name}. Adjust rows to skip.")

        # Step 1.2: Process all files and merge when the user clicks the button
        button_label = "Process CSV" if len(uploaded_files) == 1 else "Process and Merge"
        if st.button(button_label):  # Dynamically update button label
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

    # Step 2: Column Selection
    if "df" in st.session_state:
        st.subheader("Step 2: Select Columns and Processing Method")

        # Unified Preview
        st.subheader("CSV Preview (first 25 rows and last 25 rows)")
        if len(st.session_state.df) > 50:
            preview_df = pd.concat([st.session_state.df.head(25), st.session_state.df.tail(25)])
        else:
            preview_df = st.session_state.df
        st.write(preview_df)

        # Subsection 1: Source and Target Columns
        st.markdown("#### Source and Target Columns")
        source_column = st.selectbox("Select Source column", st.session_state.df.columns.tolist(), index=0)
        target_column = st.selectbox("Select Target column", st.session_state.df.columns.tolist(), index=1)

        # Restored processing options for each column
        processing_options = [
            "No Processing",
            "Free Text - Hashtags",
            "Free Text - Domains",
            "Free Text - Mentioned Users",
            "Comma Separated List - Hashtags",
            "Comma Separated List - Domains",
            "Comma Separated List - Mentioned Users"
        ]

        source_processing = st.selectbox("Select Processing for Source column", processing_options)
        target_processing = st.selectbox("Select Processing for Target column", processing_options)

        # Save Source and Target selections in session state
        st.session_state.source_column = source_column
        st.session_state.target_column = target_column
        st.session_state.source_processing = source_processing
        st.session_state.target_processing = target_processing

        # Subsection 2: Additional Attributes
        st.markdown("#### Optional Attributes")
        attribute_columns = st.multiselect(
            "Select additional columns as attributes (optional)",
            st.session_state.df.columns.tolist(),
            default=[]
        )
        st.session_state.attribute_columns = attribute_columns

    # Step 2.5: Process Columns
    if "source_column" in st.session_state and "target_column" in st.session_state:
        if st.button("Process Columns"):
            # Include Source, Target, and Attributes for processing
            columns_to_process = [st.session_state.source_column, st.session_state.target_column] + st.session_state.attribute_columns
            processed_df = st.session_state.df[columns_to_process].copy()

            # Apply processing to Source and Target columns
            processed_df[st.session_state.source_column] = apply_processing(
                processed_df[st.session_state.source_column],
                st.session_state.source_processing
            )
            processed_df[st.session_state.target_column] = apply_processing(
                processed_df[st.session_state.target_column],
                st.session_state.target_processing
            )

            # Explode lists in the Source and Target columns
            if processed_df[st.session_state.source_column].apply(lambda x: isinstance(x, list)).any():
                processed_df = processed_df.explode(st.session_state.source_column).reset_index(drop=True)
            if processed_df[st.session_state.target_column].apply(lambda x: isinstance(x, list)).any():
                processed_df = processed_df.explode(st.session_state.target_column).reset_index(drop=True)

            # Remove rows with empty Source or Target
            processed_df = processed_df.dropna(subset=[st.session_state.source_column, st.session_state.target_column])

            # Remove self-loops
            processed_df = processed_df[processed_df[st.session_state.source_column] != processed_df[st.session_state.target_column]]

            # Save the processed DataFrame
            st.session_state.processed_df = processed_df

            st.success("Columns processed successfully!")

            # Unified preview: Source, Target, and Attributes
            st.subheader("Processed Data Preview for Network (first 50 rows)")
            st.write(processed_df.head(50))

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

                # Add edges to the graph
                edges = st.session_state.processed_df[
                    [st.session_state.source_column, st.session_state.target_column]
                ].values.tolist()
                G.add_edges_from(edges)

                # Add attributes (if any) to nodes
                if st.session_state.attribute_columns:
                    for col in st.session_state.attribute_columns:
                        for idx, row in st.session_state.processed_df.iterrows():
                            G.nodes[row[st.session_state.source_column]][col] = row[col]

                # Store the created graph in session state
                st.session_state.graph = G  

                # Success message
                st.success(f"{graph_type} graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
            except Exception as e:
                st.error(f"Failed to create the network graph: {e}")

        # Export options only if a graph has been created
        if "graph" in st.session_state:
            export_graph(st.session_state.graph, graph_type)

def apply_processing(column, processing_type):
    """Apply the selected processing type to a column."""
    column = column.str.lower()  # Convert all text to lowercase by default

    if processing_type == "No Processing":
        return column
    elif processing_type == "Free Text - Hashtags":
        return column.str.findall(r"#\w+").apply(lambda x: [tag.lower() for tag in x] if isinstance(x, list) else x)
    elif processing_type == "Free Text - Domains":
        return column.apply(lambda x: urlparse(x).netloc if pd.notnull(x) else None).str.lower()
    elif processing_type == "Free Text - Mentioned Users":
        return column.str.findall(r"@(\w+)").apply(lambda x: [mention.lower() for mention in x] if isinstance(x, list) else x)
    elif processing_type == "Comma Separated List - Hashtags":
        return column.str.split(",").apply(lambda x: [tag.strip().lower() for tag in x if tag.strip().startswith("#")] if isinstance(x, list) else x)
    elif processing_type == "Comma Separated List - Domains":
        return column.str.split(",").apply(lambda x: [urlparse(domain.strip()).netloc.lower() for domain in x if pd.notnull(domain)] if isinstance(x, list) else x)
    elif processing_type == "Comma Separated List - Mentioned Users":
        return column.str.split(",").apply(lambda x: [mention.strip().lstrip("@").lower() for mention in x if mention.strip().startswith("@")] if isinstance(x, list) else x)
    return column

def export_graph(G, graph_type):
    st.subheader("Export Network Graph")

    def to_csv(G, graph_type):
        # Extract nodes with attributes into a DataFrame
        if G.number_of_nodes() > 0:
            nodes_data = [
                {"Id": node, "Label": node, **data} for node, data in G.nodes(data=True)
            ]
            nodes_df = pd.DataFrame(nodes_data)
        else:
            nodes_df = pd.DataFrame(columns=["Id", "Label"])

        # Extract edges with attributes into a DataFrame
        if "Multi" in graph_type:
            edges_data = [
                {"Source": u, "Target": v, **data} for u, v, _, data in G.edges(data=True, keys=True)
            ]
        else:
            edges_data = [
                {"Source": u, "Target": v, **data} for u, v, data in G.edges(data=True)
            ]
        edges_df = pd.DataFrame(edges_data)

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
