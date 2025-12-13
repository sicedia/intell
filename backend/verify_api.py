import requests
import json

try:
    # URL for Job 20 (from user logs)
    url = 'http://127.0.0.1:8000/api/jobs/20/'
    print(f"Fetching {url}...")
    
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("Success! Response keys:", data.keys())
        
        events = data.get('events', [])
        print(f"Event count: {len(events)}")
        
        if events:
            first_event = events[0]
            print("Sample event keys:", first_event.keys())
            print("Sample event progress:", first_event.get('progress'))
            
        # Check image tasks
        image_tasks = data.get('image_tasks', [])
        print(f"Image tasks: {len(image_tasks)}")
        if image_tasks:
            print("First image task status:", image_tasks[0].get('status'))
            print("First image task PNG URL:", image_tasks[0].get('artifact_png_url'))
            
    else:
        print("Error response:", response.text)

except Exception as e:
    print(f"Script failed: {e}")
