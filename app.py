import streamlit as st
import pandas as pd
import os
import requests
from datetime import date, datetime
from io import BytesIO, StringIO

# Set page config
st.set_page_config(page_title="Budget Tracker Filter", layout="wide")

def load_data(file_source):
    """Loads dataframe from specific file path or uploaded file object."""
    try:
        return pd.read_excel(file_source)
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

def update_master_from_uploaded(uploaded_file):
    """
    Saves uploaded file to data/ folder, updates master matrix, 
    and returns the merged dataframe.
    """
    # 1. Save uploaded file backup
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    
    # Use original filename
    file_path = os.path.join(data_dir, uploaded_file.name)
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    # 2. Load data
    new_data = pd.read_excel(file_path)
    if 'Period' not in new_data.columns:
        st.error("Uploaded file must have a 'Period' column for versioning.")
        return new_data

    # 3. Load or Create Master
    master_dir = "master"
    os.makedirs(master_dir, exist_ok=True)
    master_path = os.path.join(master_dir, "master.xlsx")
    
    if os.path.exists(master_path):
        master_df = pd.read_excel(master_path)
        # Ensure Period is datetime for comparison
        master_df['Period'] = pd.to_datetime(master_df['Period'])
        new_data['Period'] = pd.to_datetime(new_data['Period'])
        
        # Identify new rows (using Period as unique ID)
        existing_periods = set(master_df['Period'])
        # Filter new_data for rows where Period is NOT in existing_periods
        unique_new_data = new_data[~new_data['Period'].isin(existing_periods)]
        
        if not unique_new_data.empty:
            master_df = pd.concat([master_df, unique_new_data], ignore_index=True)
            # Save updated master
            master_df.to_excel(master_path, index=False)
            st.success(f"Master updated! Added {len(unique_new_data)} new records.")
    else:
        # Create new master
        master_df = new_data.copy()
        # Ensure Period is datetime
        master_df['Period'] = pd.to_datetime(master_df['Period'])
        master_df.to_excel(master_path, index=False)
        st.success("Master file created successfully!")

    return master_df


def main():
    st.title("Monthly Budget Data Filter")

    # Generate timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # --- File Loading ---
    # Sidebar Header
    st.sidebar.header("Data Source")
    uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx"])

    if uploaded_file:
        # Update Master and Load Data
        df = update_master_from_uploaded(uploaded_file)
    else:
        st.info("Please upload an Excel file to proceed.")
        st.stop()

    if df is not None:
        # Ensure 'Period' or similar date columns are datetime objects if possible
        # Heuristic: Convert columns with 'date' or 'period' in name, or check dtype
        for col in df.columns:
            if pd.api.types.is_object_dtype(df[col]):
                try:
                    df[col] = pd.to_datetime(df[col])
                except (ValueError, TypeError):
                    pass # Keep as is if not parseable

        # --- Dynamic Filters ---
        st.sidebar.header("Filters")
        
        # EXCLUDED COLUMNS
        EXCLUDED_COLS = ['Note', 'LKR', 'Description', 'Amount', 'Currency', 'Accounts.1', 'Accounts']
        
        # --- Favorites Logic ---
        def apply_favorites():
            # Hardcoded favorites per user request
            st.session_state['multi_Category'] = ['Borrow', 'Borrows', 'Household']
            st.session_state['multi_Subcategory'] = ['Dada Borrowing', 'Dada Borrows', 'Grocery']
            st.session_state['multi_Income/Expense'] = ['Exp.']

        if st.sidebar.button("Apply Favorites"):
            apply_favorites()
            # We don't need st.rerun() if we rely on the widget picking up the session state 
            # on the NEXT interaction, but for immediate effect we might want it.
            # However, since the widgets are rendered below, they should pick up the NEW session state immediately.
        
        # Create a copy which we will progressively filter (Cascading effect)
        df_filtered = df.copy()

        # 1. Handle Date Columns FIRST (Global filter)
        date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
        for col in date_cols:
            if col in EXCLUDED_COLS: continue
            
            min_date = df[col].min()
            max_date = df[col].max()
            
            if pd.isna(min_date) or pd.isna(max_date):
                continue


            # Split Date Input to separate Start/End for better visibility
            d_col1, d_col2 = st.sidebar.columns(2)
            
            start_date_input = d_col1.date_input(
                f"{col} Start",
                value=min_date,
                key=f"start_{col}"
            )
            
            end_date_input = d_col2.date_input(
                f"{col} End",
                value=max_date,
                key=f"end_{col}"
            )
            
            if start_date_input and end_date_input:
                df_filtered = df_filtered[
                    (df_filtered[col].dt.date >= start_date_input) & 
                    (df_filtered[col].dt.date <= end_date_input)
                ]

        # 2. Handle Categorical Columns SEQUENTIALLY (Waterfall/Cascading)
        # Options for Col B depend on selection in Col A
        other_cols = [c for c in df.columns if c not in date_cols and c not in EXCLUDED_COLS]
        
        for col in other_cols:
            # GET OPTIONS FROM CURRENTLY FILTERED DATA
            unique_values = df_filtered[col].dropna().unique()
            
            try:
                unique_values = sorted(unique_values)
            except TypeError:
                unique_values = sorted(unique_values, key=str)
            
            selected_values = st.sidebar.multiselect(
                f"{col}",
                options=unique_values,
                key=f"multi_{col}"
            )
            
            if selected_values:
                df_filtered = df_filtered[df_filtered[col].isin(selected_values)]

        # --- Total Row Logic ---
        if st.checkbox("Show Total Row", key="show_total"):
            if 'Amount' in df_filtered.columns:
                # Create a total row
                total_data = {col: '' for col in df_filtered.columns}
                total_data['Amount'] = df_filtered['Amount'].sum()
                
                # Label the first available column as TOTAL
                for label_col in ['Period', 'Accounts', 'Category']:
                    if label_col in df_filtered.columns:
                        total_data[label_col] = 'TOTAL'
                        break
                
                # Append to df_filtered
                df_filtered = pd.concat([df_filtered, pd.DataFrame([total_data])], ignore_index=True)

        # --- Main Display ---
        # Hide specific columns from view as requested
        cols_to_hide = ['LKR', 'Accounts.1', 'Description', 'Currency']
        df_display = df_filtered.drop(columns=cols_to_hide, errors='ignore')
        st.dataframe(df_display, use_container_width=True)



        import hashlib

        # --- Translation Logic (Free - deep-translator) ---
        # Initialize session state for translation
        if 'translated_df' not in st.session_state:
            st.session_state['translated_df'] = None
        if 'last_filtered_hash' not in st.session_state:
            st.session_state['last_filtered_hash'] = None

        # Compute hash of current filtered data to detect changes
        # We use a simple string representation hash for efficiency
        current_hash = hashlib.md5(pd.util.hash_pandas_object(df_display).values).hexdigest()

        # If data changed, reset translation
        if st.session_state['last_filtered_hash'] != current_hash:
             st.session_state['translated_df'] = None
             st.session_state['last_filtered_hash'] = current_hash

        if st.button("Translate to Sinhala (Free)"):
            from deep_translator import GoogleTranslator
            
            with st.spinner(f"Translating {len(df_display)} rows... This may take a moment."):
                try:
                    df_translated = df_display.copy()
                    
                    # Identify string columns to translate
                    text_cols = []
                    for col in df_translated.columns:
                        if pd.api.types.is_object_dtype(df_translated[col]) or pd.api.types.is_string_dtype(df_translated[col]):
                            text_cols.append(col)
                    
                    # Optimization: Translate unique values only
                    translator = GoogleTranslator(source='auto', target='si')
                    
                    progress_bar = st.progress(0)
                    total_cols = len(text_cols)
                    
                    for i, col in enumerate(text_cols):
                        # Get unique values
                        unique_vals = df_translated[col].dropna().unique()
                        unique_vals = [str(x) for x in unique_vals if str(x).strip() != '']
                        
                        if not unique_vals:
                            continue
                            
                        # Custom Corrections/Context
                        REPLACEMENTS = {
                            "Dada": "Father",
                            "dada": "father"
                        }

                        translation_map = {}
                        for val in unique_vals:
                            try:
                                # Pre-process
                                val_to_translate = str(val)
                                for k, v in REPLACEMENTS.items():
                                    val_to_translate = val_to_translate.replace(k, v)

                                translated = translator.translate(val_to_translate)
                                translation_map[val] = translated
                            except Exception:
                                translation_map[val] = val
                        
                        # Apply mapping
                        df_translated[col] = df_translated[col].astype(str).map(lambda x: translation_map.get(x, x))
                        progress_bar.progress((i + 1) / total_cols)
                        
                    # Translate Column Headers
                    translated_cols = {}
                    for col in df_translated.columns:
                        try:
                            translated_col = translator.translate(col)
                            translated_cols[col] = translated_col
                        except Exception:
                            translated_cols[col] = col
                    
                    df_translated.rename(columns=translated_cols, inplace=True)

                    # Save to session state
                    st.session_state['translated_df'] = df_translated
                    st.success("Translation Complete!")
                    
                except Exception as e:
                    st.error(f"An error occurred: {e}")

        import textwrap

        def wrap_text(text):
            return textwrap.fill(str(text), width=20)

        # --- Display Translated Output & Downloads ---
        if st.session_state['translated_df'] is not None:
            st.divider()
            st.subheader("Translated Data (Sinhala)")
            st.dataframe(st.session_state['translated_df'], use_container_width=True)
            
            t_col1, t_col2 = st.columns(2)
            
            # 1. Download Translated Excel
            with t_col1:
                output_si = BytesIO()
                with pd.ExcelWriter(output_si, engine='openpyxl') as writer:
                    st.session_state['translated_df'].to_excel(writer, index=False, sheet_name='Sinhala Data')
                processed_data_si = output_si.getvalue()

                st.download_button(
                    label="Download Translated Excel",
                    data=processed_data_si,
                    file_name=f"translated_data_{timestamp}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_excel_si"
                )
            
            # 2. Download Translated Image
            with t_col2:
                import matplotlib.pyplot as plt
                
                # Set Font to Nirmala UI for Sinhala support (Windows)
                plt.rcParams['font.family'] = 'Nirmala UI'
                
                df_si_img = st.session_state['translated_df'].head(50) # Limit for image
                
                # Wrap text
                cell_text = []
                for row in df_si_img.values:
                    cell_text.append([wrap_text(x) for x in row])
                
                buf_si = BytesIO()
                # Dynamic height based on row count
                # Multiplier increased for better vertical spacing
                row_heights = [max([str(x).count('\n') + 1 for x in row]) for row in cell_text]
                total_height = sum(row_heights) * 0.6 + 2 
                
                fig_si, ax_si = plt.subplots(figsize=(20, total_height)) # Width increased
                ax_si.axis('tight')
                ax_si.axis('off')
                table_si = ax_si.table(cellText=cell_text, colLabels=df_si_img.columns, loc='center', cellLoc='center')
                
                # Auto-adjust column widths
                table_si.auto_set_column_width(col=list(range(len(df_si_img.columns))))
                
                table_si.auto_set_font_size(False)
                table_si.set_fontsize(10)
                table_si.scale(1.0, 1.5) # Increased vertical scale
                
                plt.savefig(buf_si, format='png', bbox_inches='tight', dpi=150)
                plt.close(fig_si)
                img_data_si = buf_si.getvalue()
                
                st.download_button(
                    label="Download Translated Image",
                    data=img_data_si,
                    file_name=f"translated_table_{timestamp}.png",
                    mime="image/png",
                    key="download_img_si"
                )

        # --- Download Buttons (Excel & Image) ---
        d_col1, d_col2 = st.columns([1, 1])
        
        with d_col1:
            # Generate Excel in memory
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_filtered.to_excel(writer, index=False, sheet_name='Filtered Data')
            processed_data = output.getvalue()

            st.download_button(
                label="Download Filtered Excel",
                data=processed_data,
                file_name=f"filtered_data_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with d_col2:
            # Generate Image in memory (Matplotlib)
            import matplotlib.pyplot as plt
            
            # Set Font to Nirmala UI for Sinhala support (Windows)
            plt.rcParams['font.family'] = 'Nirmala UI'
            
            # Limit rows for image download to avoid massive images
            MAX_ROWS_IMG = 50
            if len(df_filtered) > MAX_ROWS_IMG:
                 st.caption(f"Image download limited to first {MAX_ROWS_IMG} rows.")
                 df_img = df_display.head(MAX_ROWS_IMG)
            else:
                 df_img = df_display

            # Wrap text
            cell_text = []
            for row in df_img.values:
                cell_text.append([wrap_text(x) for x in row])

            buf = BytesIO()
            # Dynamic height
            row_heights = [max([str(x).count('\n') + 1 for x in row]) for row in cell_text]
            total_height = sum(row_heights) * 0.6 + 2
            
            fig, ax = plt.subplots(figsize=(20, total_height)) # Wider figure
            ax.axis('tight')
            ax.axis('off')
            table = ax.table(cellText=cell_text, colLabels=df_img.columns, loc='center', cellLoc='center')
            
            # Auto-adjust column widths
            table.auto_set_column_width(col=list(range(len(df_img.columns))))
            
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1.0, 1.5) # Increased vertical scale
            
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
            plt.close(fig)
            img_data = buf.getvalue()
            
            st.download_button(
                label="Download as Image (PNG)",
                data=img_data,
                file_name=f"table_image_{timestamp}.png",
                mime="image/png"
            )

if __name__ == "__main__":
    main()
