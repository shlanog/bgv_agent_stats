import streamlit as st
import json
import pandas as pd
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Onboarding Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# Load data and convert format if needed
def load_data():
    try:
        with open('data_by_date.json', 'r') as f:
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
                    
                    # Create the new structure with processes and summary
                    converted_data[date_key][user_id] = {
                        'processes': processes,
                        'summary': {
                            'total_individuals': total_individuals,
                            'successful_onboardings': total_successful,
                            'failed_onboardings': total_failed,
                            'discarded_candidates': total_discarded
                        }
                    }
            return converted_data
        
        return data
    except FileNotFoundError:
        st.error("Data file 'data_by_date.json' not found. Please run the query script first.")
        return {}

def main():
    
    # Load data
    data = load_data()
    
    if not data:
        st.stop()
    
    # Sidebar for date selection
    st.sidebar.header("📅 Select Date")
    
    # Get all available dates and sort them
    available_dates = sorted(data.keys(), key=lambda x: datetime.strptime(x, '%d/%m/%Y'))
    
    if not available_dates:
        st.error("No data available.")
        return
    
    # Date selector
    selected_date = st.sidebar.selectbox(
        "Choose a date:",
        available_dates,
        index=len(available_dates)-1  # Default to most recent date
    )
    
    # Display data for selected date
    if selected_date in data:
        st.header(f"📈 Analytics for {selected_date}")
        
        date_data = data[selected_date]
        
        if not date_data:
            st.warning("No data available for this date.")
            return
        
        # Calculate overall totals for the date
        total_users = len(date_data)
        total_processes = sum(len(user_data['processes']) for user_data in date_data.values())
        overall_individuals = sum(user_data['summary']['total_individuals'] for user_data in date_data.values())
        overall_successful = sum(user_data['summary']['successful_onboardings'] for user_data in date_data.values())
        overall_failed = sum(user_data['summary']['failed_onboardings'] for user_data in date_data.values())
        overall_discarded = sum(user_data['summary']['discarded_candidates'] for user_data in date_data.values())
        overall_verifications_initiated = sum(user_data['summary']['verifications_initiated'] for user_data in date_data.values())
        
        # Display overall metrics in two rows for better responsiveness
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
            st.metric("❌ Failed Onboardings", overall_failed)

        with col6:
            st.metric("🗑️ Discarded Candidates", overall_discarded)
            
        st.markdown("---")
        
        # Single section with user summary and details
        st.subheader("👥 User Summary")
        
        # Prepare data for table
        table_data = []
        for user_id, user_data in date_data.items():    
            summary = user_data['summary']

            table_data.append({
                'User ID': user_id,
                'Processes': len(user_data['processes']),
                'Total Individuals': summary['total_individuals'],
                'Successful': summary['successful_onboardings'],
                'Failed': summary['failed_onboardings'],
                'Discarded': summary['discarded_candidates'],
                'Verifications Initiated': summary.get('verifications_initiated', 0)
            })
        
        # Sort by total individuals (descending)
        table_data.sort(key=lambda x: x['Total Individuals'], reverse=True)
        
        # Display table
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)
        
        # User selector for detailed process view
        st.markdown("### 🔍 Detailed Process Information")
        selected_user = st.selectbox(
            "Select a user to view their individual processes:",
            list(date_data.keys()),
            key="user_selector"
        )
        
        if selected_user:
            user_data = date_data[selected_user]
            
            # Show individual processes
            if user_data['processes']:
                st.write(f"**Individual Processes for {selected_user}:**")
                process_df = pd.DataFrame(user_data['processes'])
                st.dataframe(process_df, use_container_width=True)
            else:
                st.write("No processes found for this user.")
    
    # Footer
    st.markdown("---")
    st.markdown("*Data updated from MongoDB collection*")

if __name__ == "__main__":
    main() 