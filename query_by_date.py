import pymongo
import os
from dotenv import load_dotenv
import json
from bson import ObjectId, json_util
from datetime import datetime
from collections import defaultdict

load_dotenv()

client = pymongo.MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DB_NAME")]
collection = db[os.getenv("MONGO_COLLECTION_NAME")]

# Query all documents sorted by created_at date
result = collection.find().sort("created_at", pymongo.ASCENDING)

# Dictionary to store data grouped by date, then by user_id
data_by_date = defaultdict(lambda: defaultdict(list))

for doc in result:
    # Extract date from created_at field
    created_at = doc.get('created_at')
    if created_at:
        # Convert to date string (YYYY-MM-DD format)
        if isinstance(created_at, dict) and '$date' in created_at:
            # Handle BSON date format
            date_obj = datetime.fromisoformat(created_at['$date'].replace('Z', '+00:00'))
        else:
            # Handle regular datetime object
            date_obj = created_at
        
        date_key = date_obj.strftime('%d/%m/%Y')
        user_id = doc.get('user_id')
        
        if user_id:
            # Get summary from the document
            summary = doc.get('summary', {})
            if summary:
                # Create a summary object with only the 4 required fields plus process_id
                user_summary = {
                    'process_id': str(doc.get('_id')),
                    'total_individuals': summary.get('total_individuals', 0),
                    'successful_onboardings': summary.get('successful_onboardings', 0),
                    'failed_onboardings': summary.get('failed_onboardings', 0),
                    'discarded_candidates': summary.get('discarded_candidates', 0)
                }
                
                # Add the summary to the user's array for this date
                data_by_date[date_key][user_id].append(user_summary)

# Convert defaultdict to regular dict and add user totals
final_data = {}
for date_key, users_data in data_by_date.items():
    final_data[date_key] = {}
    for user_id, summaries in users_data.items():
        # Calculate totals for this user on this date
        total_individuals = sum(s.get('total_individuals', 0) for s in summaries)
        total_successful = sum(s.get('successful_onboardings', 0) for s in summaries)
        total_failed = sum(s.get('failed_onboardings', 0) for s in summaries)
        total_discarded = sum(s.get('discarded_candidates', 0) for s in summaries)
        
        # Create the new structure with processes and summary
        final_data[date_key][user_id] = {
            'processes': summaries,
            'summary': {
                'total_individuals': total_individuals,
                'successful_onboardings': total_successful,
                'failed_onboardings': total_failed,
                'discarded_candidates': total_discarded
            }
        }

# Save the aggregated data to JSON file
output_file = 'data_by_date.json'
with open(output_file, 'w') as f:
    f.write(json_util.dumps(final_data, indent=4))

print(f"Date and user-grouped data saved to {output_file}")
print(f"Found data for {len(final_data)} unique dates")

# Print summary
total_documents = 0
for date_key in sorted(final_data.keys()):
    date_data = final_data[date_key]
    date_documents = sum(len(user_data['processes']) for user_data in date_data.values())
    total_documents += date_documents
    
    print(f"\nDate: {date_key}")
    print(f"  Users: {len(date_data)}")
    print(f"  Documents: {date_documents}")
    
    # Calculate totals for this date
    total_individuals = 0
    total_successful = 0
    total_failed = 0
    total_discarded = 0
    
    for user_id, user_data in date_data.items():
        user_summary = user_data['summary']
        user_individuals = user_summary['total_individuals']
        user_successful = user_summary['successful_onboardings']
        user_failed = user_summary['failed_onboardings']
        user_discarded = user_summary['discarded_candidates']
        
        total_individuals += user_individuals
        total_successful += user_successful
        total_failed += user_failed
        total_discarded += user_discarded
        
        print(f"    {user_id}: {len(user_data['processes'])} documents, {user_individuals} individuals")
    
    print(f"  Total Individuals: {total_individuals}")
    print(f"  Successful: {total_successful}, Failed: {total_failed}, Discarded: {total_discarded}")
    if total_individuals > 0:
        success_rate = (total_successful / total_individuals) * 100
        print(f"  Success Rate: {success_rate:.2f}%")

print(f"\nOverall Total Documents: {total_documents}") 