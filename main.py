import streamlit as st
import pandas as pd
import json
import base64
from io import StringIO
import time

def get_download_link(json_data, filename="data.json"):
    """Generate a download link for the JSON data"""
    json_str = json.dumps(json_data, indent=2)
    b64 = base64.b64encode(json_str.encode()).decode()
    href = f'<a href="data:file/json;base64,{b64}" download="{filename}">Download JSON file</a>'
    return href

# Page config
st.set_page_config(
    page_title="CSV to JSON Converter", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("CSV to JSON Converter")
st.write("Upload a CSV file and convert it to JSON format")

# File uploader
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    # Display file details
    file_details = {"Filename": uploaded_file.name, "FileType": uploaded_file.type, "FileSize": f"{uploaded_file.size / 1024:.2f} KB"}
    st.write("File Details:")
    st.json(file_details)
    
    # Check file size and warn if large
    if uploaded_file.size > 5 * 1024 * 1024:  # 5MB
        st.warning("Large file detected. Conversion might take some time.")
    
    # Load the CSV data with progress
    with st.spinner("Loading CSV data..."):
        try:
            # For large files, consider chunk processing
            if uploaded_file.size > 10 * 1024 * 1024:  # 10MB
                chunk_size = 100000  # Adjust based on your needs
                chunks = pd.read_csv(uploaded_file, chunksize=chunk_size)
                df_list = []
                for chunk in chunks:
                    df_list.append(chunk)
                df = pd.concat(df_list)
            else:
                df = pd.read_csv(uploaded_file)
            
            # Show sample rows instead of the whole preview
            st.subheader("CSV Data Preview")
            st.dataframe(df.head(5))
            st.info(f"Total rows: {len(df)}, Total columns: {len(df.columns)}")
            
            # Conversion options
            st.subheader("Conversion Options")
            orientation = st.radio(
                "JSON Structure",
                ["Records", "Split", "Index"],
                help="Records: list of dictionaries, Split: keys and values separate, Index: dictionary with index as key"
            )
            
            # Add option for handling large datasets
            sample_size = None
            if len(df) > 1000:
                use_full_dataset = st.checkbox("Use full dataset", value=True)
                if not use_full_dataset:
                    sample_size = st.slider("Sample size", min_value=100, max_value=min(10000, len(df)), value=1000)
            
            # Convert to JSON
            if st.button("Convert to JSON"):
                # Process the data
                with st.spinner("Converting data to JSON..."):
                    # Use a sample if specified
                    df_to_convert = df if sample_size is None else df.sample(sample_size)
                    
                    orient_map = {
                        "Records": "records",
                        "Split": "split", 
                        "Index": "index"
                    }
                    
                    # Progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Convert in chunks for index orientation to prevent freezing
                    if orientation == "Index" and len(df_to_convert) > 5000:
                        status_text.text("Processing large dataset in chunks...")
                        chunks = []
                        chunk_size = 1000
                        total_chunks = (len(df_to_convert) + chunk_size - 1) // chunk_size
                        
                        for i in range(0, len(df_to_convert), chunk_size):
                            chunk = df_to_convert.iloc[i:i+chunk_size]
                            chunk_json = json.loads(chunk.to_json(orient=orient_map[orientation]))
                            chunks.append(chunk_json)
                            progress = (i + chunk_size) / len(df_to_convert)
                            progress_bar.progress(min(progress, 1.0))
                            status_text.text(f"Processing chunk {i//chunk_size + 1}/{total_chunks}...")
                            time.sleep(0.1)  # Give UI time to update
                        
                        # Combine chunks
                        json_data = {}
                        for chunk in chunks:
                            json_data.update(chunk)
                    else:
                        # Standard conversion for smaller datasets
                        json_data = json.loads(df_to_convert.to_json(orient=orient_map[orientation]))
                        progress_bar.progress(1.0)
                    
                    status_text.text("Conversion complete!")
                    time.sleep(0.5)
                    progress_bar.empty()
                    status_text.empty()
                
                # Display JSON
                st.subheader("JSON Output")
                
                # For large outputs, show truncated version
                json_str = json.dumps(json_data, indent=2)
                if len(json_str) > 500000:  # ~500KB of text
                    st.warning("JSON output is very large. Showing truncated preview.")
                    with st.expander("JSON Preview (truncated)", expanded=True):
                        st.code(json_str[:500000] + "\n... (truncated)")
                else:
                    with st.expander("View JSON", expanded=True):
                        st.json(json_data)
                
                # Generate download link
                st.markdown(get_download_link(json_data, f"{uploaded_file.name.split('.')[0]}.json"), unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"Error: {e}")
            st.write("Please ensure your CSV file is properly formatted.")

st.markdown("---")
st.markdown("Made with ❤️ using Streamlit")
