# MongoQueryBGV

A MongoDB analytics dashboard that automatically updates daily using GitHub Actions.

## Project Structure

- `query_by_date.py` - Script that queries MongoDB and generates analytics data
- `data_by_date.json` - Generated analytics data file
- `streamlit_app.py` - Streamlit frontend dashboard
- `.github/workflows/daily_data_update.yml` - GitHub Actions workflow for daily updates

## Setup Instructions

### 1. Repository Setup

1. Push this code to your GitHub repository
2. Go to your repository settings → Secrets and variables → Actions
3. Add the following repository secrets:
   - `MONGO_URI` - Your MongoDB connection string
   - `MONGO_DB_NAME` - Your MongoDB database name
   - `MONGO_COLLECTION_NAME` - Your MongoDB collection name

### 2. GitHub Actions Configuration

The workflow is configured to:
- Run daily at 6:00 AM UTC (modify the cron schedule in `.github/workflows/daily_data_update.yml` if needed)
- Execute the query script with your MongoDB credentials
- Commit updated data back to the repository
- Can be manually triggered via the "Actions" tab

### 3. Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables (create .env file)
MONGO_URI=your_mongo_connection_string
MONGO_DB_NAME=your_database_name
MONGO_COLLECTION_NAME=your_collection_name

# Run the query script
python query_by_date.py

# Run the Streamlit dashboard
streamlit run streamlit_app.py
```

### 4. Frontend Deployment

#### Option A: Streamlit Community Cloud (Recommended)
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click "New app" and fill in:
   - Repository: `your-username/MongoQueryBGV`
   - Branch: `main`
   - Main file path: `streamlit_app.py`
4. Click "Deploy!" 
5. Your app will auto-update when GitHub Actions commits new data

#### Option B: Heroku
```bash
# Install Heroku CLI, then:
heroku create your-app-name
git push heroku main
```

#### Option C: Railway
1. Connect your GitHub repo to [Railway](https://railway.app)
2. It will automatically detect and deploy your Streamlit app

#### Option D: Docker
```bash
# Build and run locally
docker build -t mongo-analytics .
docker run -p 8501:8501 mongo-analytics
```

#### Option E: Other platforms
- **Render**: Connect GitHub repo, set build command to `pip install -r requirements.txt`
- **DigitalOcean App Platform**: Deploy directly from GitHub
- **AWS/GCP/Azure**: Use their container services with the provided Dockerfile

## How It Works

1. **Daily Automation**: GitHub Actions runs the query script daily
2. **Data Generation**: Script queries MongoDB and generates `data_by_date.json`
3. **Auto-commit**: Updated data is automatically committed to the repository
4. **Frontend Access**: Streamlit app reads the latest data from the JSON file
5. **Real-time Dashboard**: Users see up-to-date analytics without manual intervention

## Customization

- **Schedule**: Modify the cron expression in the workflow file to change run frequency
- **Timezone**: Adjust the cron schedule for your timezone
- **Data Processing**: Modify `query_by_date.py` to change data aggregation logic
- **Dashboard**: Customize `streamlit_app.py` to modify the UI and visualizations 