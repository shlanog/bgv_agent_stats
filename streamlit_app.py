import streamlit as st
import json
import pandas as pd
from datetime import datetime
import io

# Set page config
st.set_page_config(
    page_title="Onboarding Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# User ID to email mapping
USER_ID_MAP = {
    "514833": "Manish Bisht",
    "591950": "Vikram Thakur",
    "905072": "Vikash Singh",
    "1081989": "Sushma Negi",
    "1187116": "Sanchit Deshwal",
    "611429": "Deepak Chawla",
    "905037": "Diwakar Lohia",
    "1045453": "Tarun Chauniyal",
    "842566": "Ashfaq Alam",
    "710200": "Shivam Kumar",
    "358250": "Sonu Kumar",
    "605016": "Mohammad Sameen",
    "600438": "Pankaj Katyura",
    "699728": "Soral Singh",
    "397646": "Kuldeep Adhikari",
    "1484439": "Giridhar Chennuru",
    "1298474": "Yogesh Chaudhary",
    "858351": "Kajal Kumari",
    "699694": "Ranjan Sahu",
    "158897": "Mohammad Shebaz",
    "458444": "Farjul Islam",
    "465826": "Manish Kumar",
    "1013467": "Mohammad Aaqib",
    "327540": "Mohammed Shahrukh",
    "1009828": "Payal Negi",
}

def get_user_display_name(user_id):
    """Get the display name for a user ID (email if available, otherwise user ID)"""
    return USER_ID_MAP.get(str(user_id), str(user_id))

def format_verification_types(verification_types_count):
    """Format verification types count for display"""
    if not verification_types_count:
        return "None"
    
    # Sort by count (descending) then by type name
    sorted_verifications = sorted(verification_types_count.items(), key=lambda x: (-x[1], x[0]))
    
    # Format as "TYPE:count, TYPE:count"
    formatted = ", ".join([f"{vtype}:{count}" for vtype, count in sorted_verifications])
    return formatted

# Fixed column order for verification types in Excel export
# Any verification types not listed here will be appended after these, in alphabetical order
FIXED_VERIFICATION_ORDER = [
    "AV", "PANV", "DLV", "VIDV", "CCRV", "EDUV", "EMPV", "LAV", "PAV",
    "LAPV", "PAPV", "LADV", "PADV", "PRC", "PCC", "PVLF", "CC", "GDC",
    "BAV", "EREF", "EHC", "OFACC", "DRG", "PPV", "CVV", "XAV", "SMC"
]

def get_all_verification_types(date_data):
    """Extract all unique verification types from the data"""
    verification_types = set()
    for user_data in date_data.values():
        for process in user_data['processes']:
            verification_types.update(process.get('verification_types_count', {}).keys())
    return sorted(list(verification_types))

def create_excel_dataframe(date_data, selected_date):
    """Create a DataFrame for Excel export with users as rows and verification types as columns"""
    # Get all unique verification types
    all_verification_types = get_all_verification_types(date_data)

    # Build ordered list: always include the fixed list (even if absent in data),
    # then append any remaining unexpected types alphabetically
    remaining = sorted([v for v in all_verification_types if v not in FIXED_VERIFICATION_ORDER])
    ordered_verification_types = FIXED_VERIFICATION_ORDER + remaining
    
    # Prepare data for DataFrame - just user summary with verification types
    excel_data = []
    
    for user_id, user_data in date_data.items():
        user_name = get_user_display_name(user_id)
        
        # Start with basic user info
        row = {
            'Date': selected_date,
            'User': user_name
        }
        
        # Add verification type columns using summary data
        verification_counts = user_data['summary'].get('verification_types_count', {})
        for vtype in ordered_verification_types:
            count = verification_counts.get(vtype, 0)
            row[vtype] = count if count != 0 else 0
        
        excel_data.append(row)
    
    # Create DataFrame and enforce column order
    df = pd.DataFrame(excel_data)
    desired_columns = ['Date', 'User'] + ordered_verification_types
    # Ensure any accidental extra columns are preserved at the end (rare)
    extra_columns = [c for c in df.columns if c not in desired_columns]
    df = df.reindex(columns=desired_columns + extra_columns)
    return df

def create_excel_buffer(df):
    """Create an Excel file in memory and return the buffer"""
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Individual_Processes', index=False)
        
        # Auto-adjust column widths
        worksheet = writer.sheets['Individual_Processes']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    buffer.seek(0)
    return buffer

# Load data and convert format if needed
def load_data():
    try:
        with open('data_by_date_recent.json', 'r') as f:
            data = json.load(f)
        
        # Check if data needs conversion (old format detection)
        if data and isinstance(list(data.values())[0][list(list(data.values())[0].keys())[0]], list):
            # Convert to new format
            converted_data = {}
            for date_key, users_data in data.items():
                converted_data[date_key] = {}
                for user_id, processes in users_data.items():
                    # Calculate totals for this user on this date
                    total_individuals = sum(p.get('total_individuals', 0) for p in processes)
                    total_successful = sum(p.get('successful_onboardings', 0) for p in processes)
                    total_failed = sum(p.get('failed_onboardings', 0) for p in processes)
                    total_discarded = sum(p.get('discarded_candidates', 0) for p in processes)
                    total_verifications_initiated = sum(p.get('verifications_initiated', 0) for p in processes)
                    
                    # Aggregate verification types count for this user
                    user_verification_types = {}
                    for process in processes:
                        verification_types = process.get('verification_types_count', {})
                        for verification_type, count in verification_types.items():
                            user_verification_types[verification_type] = user_verification_types.get(verification_type, 0) + count
                    
                    # Create the new structure with processes and summary
                    converted_data[date_key][user_id] = {
                        'processes': processes,
                        'summary': {
                            'total_individuals': total_individuals,
                            'successful_onboardings': total_successful,
                            'failed_onboardings': total_failed,
                            'discarded_candidates': total_discarded,
                            'verifications_initiated': total_verifications_initiated,
                            'verification_types_count': user_verification_types
                        }
                    }
            return converted_data
        
        return data
    except FileNotFoundError:
        st.error("Data file 'data_by_date_recent.json' not found. Please run the query script first.")
        return {}

def load_monthly_data():
    try:
        with open('data_by_month_recent.json', 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        st.error("Monthly data file 'data_by_month_recent.json' not found. Please run the monthly query script first.")
        return {}

def main():
    
    # Sidebar for view selection
    st.sidebar.header("📊 View Selection")
    
    view_type = st.sidebar.radio(
        "Choose view type:",
        ["Daily Stats", "Monthly Stats"],
        index=0
    )
    
    if view_type == "Daily Stats":
        display_daily_stats()
    else:
        display_monthly_stats()

def display_daily_stats():
    # Load data
    data = load_data()
    
    if not data:
        st.stop()
    
    # Sidebar for date selection
    st.sidebar.header("📅 Select Date")
    
    # Get all available dates and sort them in descending order (latest first)
    available_dates = sorted(data.keys(), key=lambda x: datetime.strptime(x, '%d/%m/%Y'), reverse=True)
    
    if not available_dates:
        st.error("No data available.")
        return
    
    # Date selector
    selected_date = st.sidebar.selectbox(
        "Choose a date:",
        available_dates,
        index=0  # Default to first date (which is now the most recent)
    )
    
    # Display data for selected date
    if selected_date in data:
        st.header(f"📈 Daily Analytics for {selected_date}")
        
        date_data = data[selected_date]
        
        if not date_data:
            st.warning("No data available for this date.")
            return
        
        display_stats_content(date_data, selected_date, "daily")

def display_monthly_stats():
    # Load monthly data
    data = load_monthly_data()
    
    if not data:
        st.stop()
    
    # Sidebar for month selection
    st.sidebar.header("📅 Select Month")
    
    # Get all available months and sort them in descending order (latest first)
    available_months = sorted(data.keys(), key=lambda x: datetime.strptime(x, '%m/%Y'), reverse=True)
    
    if not available_months:
        st.error("No monthly data available.")
        return
    
    # Month selector
    selected_month = st.sidebar.selectbox(
        "Choose a month:",
        available_months,
        index=0  # Default to first month (which is now the most recent)
    )
    
    # Display data for selected month
    if selected_month in data:
        st.header(f"📈 Monthly Analytics for {selected_month}")
        
        month_data = data[selected_month]
        
        if not month_data:
            st.warning("No data available for this month.")
            return
        
        display_stats_content(month_data, selected_month, "monthly")

def calculate_excel_stats(period_data):
    """Calculate Excel-related statistics for the period"""
    total_processes_with_excel = 0
    total_individuals_with_excel = 0
    
    for user_data in period_data.values():
        for process in user_data['processes']:
            excel_document = process.get('excel_document', '')
            # Check if excel_document has a value (handle both dict with s3_url and string)
            has_excel = False
            if isinstance(excel_document, dict) and excel_document.get('s3_url'):
                has_excel = True
            elif isinstance(excel_document, str) and excel_document:
                has_excel = True
            
            if has_excel:
                total_processes_with_excel += 1
                total_individuals_with_excel += process.get('total_individuals', 0)
    
    return total_processes_with_excel, total_individuals_with_excel

def display_stats_content(period_data, selected_period, period_type):
    """Common function to display stats content for both daily and monthly views"""
    
    # Calculate overall totals for the period
    total_users = len(period_data)
    total_processes = sum(len(user_data['processes']) for user_data in period_data.values())
    overall_individuals = sum(user_data['summary']['total_individuals'] for user_data in period_data.values())
    overall_successful = sum(user_data['summary']['successful_onboardings'] for user_data in period_data.values())
    overall_failed = sum(user_data['summary']['failed_onboardings'] for user_data in period_data.values())
    overall_discarded = sum(user_data['summary']['discarded_candidates'] for user_data in period_data.values()) + overall_failed
    overall_verifications_initiated = sum(user_data['summary']['verifications_initiated'] for user_data in period_data.values())
    
    # Calculate Excel statistics
    total_processes_with_excel, total_individuals_with_excel = calculate_excel_stats(period_data)
    
    # Display overall metrics in three rows for better responsiveness
    # First row - main metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("👥 Total Users", total_users)    
    
    with col2:
        st.metric("👤 Total Individuals", overall_individuals)
    
    with col3:
        st.metric("🔍 Verifications Initiated", overall_verifications_initiated)
    
    # Second row - outcome metrics
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.metric("✅ Successful Onboardings", overall_successful)
    
    with col5:
        st.metric("🗑️ Discarded Candidates", overall_discarded)
    
    with col6:
        st.metric("📊 Total Processes", total_processes)
    
    st.markdown("---")
    
    # Single section with user summary and details
    st.subheader("👥 User Summary")
    
    # Prepare data for table
    table_data = []
    for user_id, user_data in period_data.items():    
        summary = user_data['summary']
        
        # Calculate Excel statistics for this user
        user_processes_with_excel = 0
        user_individuals_with_excel = 0
        user_successful_with_excel = 0
        user_discarded_with_excel = 0
        user_verifications_with_excel = 0
        
        for process in user_data['processes']:
            excel_document = process.get('excel_document', '')
            # Check if excel_document has a value (handle both dict with s3_url and string)
            has_excel = False
            if isinstance(excel_document, dict) and excel_document.get('s3_url'):
                has_excel = True
            elif isinstance(excel_document, str) and excel_document:
                has_excel = True
            
            if has_excel:
                user_processes_with_excel += 1
                user_individuals_with_excel += process.get('total_individuals', 0)
                user_successful_with_excel += process.get('successful_onboardings', 0)
                user_discarded_with_excel += process.get('discarded_candidates', 0) + process.get('failed_onboardings', 0)
                user_verifications_with_excel += process.get('verifications_initiated', 0)

        # Calculate documents-only statistics (total minus Excel)
        total_processes = len(user_data['processes'])
        total_individuals = summary['total_individuals']
        total_successful = summary['successful_onboardings']
        total_discarded = summary['discarded_candidates'] + summary['failed_onboardings']
        total_verifications = summary.get('verifications_initiated', 0)
        
        user_processes_documents_only = total_processes - user_processes_with_excel
        user_individuals_documents_only = total_individuals - user_individuals_with_excel
        user_successful_documents_only = total_successful - user_successful_with_excel
        user_discarded_documents_only = total_discarded - user_discarded_with_excel
        user_verifications_documents_only = total_verifications - user_verifications_with_excel

        table_data.append({
            'User': get_user_display_name(user_id),
            'Total Processes': total_processes,
            'Total Individuals': total_individuals,
            'Successful': total_successful,
            'Discarded': total_discarded,
            'Verifications Initiated': total_verifications,
            'Processes with Excel': user_processes_with_excel,
            'Individuals with Excel': user_individuals_with_excel,
            'Successful with Excel': user_successful_with_excel,
            'Discarded with Excel': user_discarded_with_excel,
            'Verifications Initiated with Excel': user_verifications_with_excel,
            'Processes with Documents Only': user_processes_documents_only,
            'Individuals with Documents Only': user_individuals_documents_only,
            'Successful with Documents Only': user_successful_documents_only,
            'Discarded with Documents Only': user_discarded_documents_only,
            'Verifications Initiated with Documents Only': user_verifications_documents_only
        })
    
    # Sort by total individuals (descending)
    table_data.sort(key=lambda x: x['Total Individuals'], reverse=True)
    
    # Display table
    df = pd.DataFrame(table_data)
    st.dataframe(df, width='stretch')
    
    # Compact verification types breakdown
    st.markdown("#### 🔍 Verification Types by User")
    
    # Sort users by the same order as the table (by total individuals)
    sorted_users = sorted(period_data.items(), key=lambda x: x[1]['summary']['total_individuals'], reverse=True)
    
    # Create compact verification display using Streamlit containers
    with st.container():
        st.markdown("""
        <style>
        .stContainer > div {
            background: linear-gradient(135deg, rgba(28, 131, 225, 0.08), rgba(28, 131, 225, 0.02));
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            border: 1px solid rgba(28, 131, 225, 0.1);
        }
        .verification-badge {
            background: rgba(255, 255, 255, 0.1);
            padding: 4px 8px;
            border-radius: 4px;
            margin: 2px;
            display: inline-block;
            font-size: 14px;
        }
        .total-badge {
            background: rgba(28, 131, 225, 0.3);
            padding: 4px 8px;
            border-radius: 4px;
            margin: 2px;
            display: inline-block;
            font-size: 14px;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Calculate total verification types across all users
        total_verification_types = {}
        for user_id, user_data in sorted_users:
            verification_types = user_data['summary'].get('verification_types_count', {})
            for verification_type, count in verification_types.items():
                total_verification_types[verification_type] = total_verification_types.get(verification_type, 0) + count
        
        # Display total row first
        if total_verification_types:
            sorted_total_verifications = sorted(total_verification_types.items(), key=lambda x: -x[1])
            
            col1, col2 = st.columns([1, 4])
            
            with col1:
                st.markdown("**📊 Total:**")
            
            with col2:
                total_text = ""
                for vtype, count in sorted_total_verifications:
                    total_text += f'<span class="total-badge">{vtype}: {count}</span> '
                
                st.markdown(total_text, unsafe_allow_html=True)
            
            # Add separator
            st.markdown("---")
        
        for user_id, user_data in sorted_users:
            user_name = get_user_display_name(user_id)
            verification_types = user_data['summary'].get('verification_types_count', {})
            
            if verification_types:
                sorted_verifications = sorted(verification_types.items(), key=lambda x: -x[1])
                
                # Create one row per user
                col1, col2 = st.columns([1, 4])
                
                with col1:
                    st.markdown(f"**{user_name}:**")
                
                with col2:
                    # Create verification badges
                    verification_text = ""
                    for vtype, count in sorted_verifications:
                        verification_text += f'<span class="verification-badge">{vtype}: {count}</span> '
                    
                    st.markdown(verification_text, unsafe_allow_html=True)
    
    # User selector for detailed process view
    st.markdown("---")
    st.markdown("### 🔍 Detailed Process Information")
    
    # Create a mapping for the selectbox (display name -> user_id)
    user_display_options = {get_user_display_name(user_id): user_id for user_id in period_data.keys()}
    
    selected_user_display = st.selectbox(
        "Select a user to view their individual processes:",
        list(user_display_options.keys()),
        key=f"user_selector_{period_type}"
    )
    
    if selected_user_display:
        selected_user_id = user_display_options[selected_user_display]
        user_data = period_data[selected_user_id]
        
        # Show individual processes
        if user_data['processes']:
            st.write(f"**Individual Processes for {selected_user_display}:**")
            
            # Format the processes data for better display
            formatted_processes = []
            for process in user_data['processes']:
                formatted_process = process.copy()
                # Combine failed onboardings with discarded candidates
                if 'failed_onboardings' in formatted_process and 'discarded_candidates' in formatted_process:
                    formatted_process['discarded_candidates'] = formatted_process['discarded_candidates'] + formatted_process['failed_onboardings']
                    # Remove the failed_onboardings field
                    del formatted_process['failed_onboardings']
                # Format verification types for better display
                if 'verification_types_count' in formatted_process:
                    verification_types = formatted_process['verification_types_count']
                    formatted_process['verification_types_count'] = format_verification_types(verification_types)
                # Extract s3_url from excel_document for better display
                if 'excel_document' in formatted_process:
                    excel_doc = formatted_process['excel_document']
                    if isinstance(excel_doc, dict) and 's3_url' in excel_doc:
                        formatted_process['Document URL'] = excel_doc['s3_url']
                    elif isinstance(excel_doc, str):
                        formatted_process['Document URL'] = excel_doc
                    else:
                        formatted_process['Document URL'] = ''
                    del formatted_process['excel_document']
                formatted_processes.append(formatted_process)
            
            process_df = pd.DataFrame(formatted_processes)
            st.dataframe(
                process_df, 
                width='stretch',
                column_config={
                    "verification_types_count": st.column_config.TextColumn(
                        "Verification Types",
                        width="large",
                        help="Types and counts of verifications for this process"
                    ),
                    "Document URL": st.column_config.TextColumn(
                        "Document URL",
                        width="medium",
                        help="URL link to the Excel document for this process"
                    )
                }
            )
        else:
            st.write("No processes found for this user.")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
             try:
                 # Create DataFrame for Excel export
                 excel_df = create_excel_dataframe(period_data, selected_period)
                 
                 if not excel_df.empty:
                     # Create Excel buffer
                     excel_buffer = create_excel_buffer(excel_df)
                     
                     # Direct download button
                     file_prefix = "monthly" if period_type == "monthly" else "daily"
                     st.download_button(
                         label="Download Excel",
                         data=excel_buffer,
                         file_name=f"{file_prefix}_initiation_portal_stats_{selected_period.replace('/', '_')}.xlsx",
                         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                         help="Click to download the Excel file",
                         type="primary"
                     )
                 else:
                     st.warning("No data available for Excel export.")
                     
             except Exception as e:
                 st.error(f"Error creating Excel file: {str(e)}")

    # Footer
    st.markdown("---")

if __name__ == "__main__":
    main() 