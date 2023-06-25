from flask import Flask, jsonify, request
from bs4 import BeautifulSoup
from google_play_scraper import app
from apscheduler.schedulers.background import BackgroundScheduler
import sqlite3
import requests

app = Flask(__name__)

# Create a database connection
conn = sqlite3.connect('playstore_data.db')
cursor = conn.cursor()

# Create a table to store the scraped data
cursor.execute('''CREATE TABLE IF NOT EXISTS apps
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   package_name TEXT,
                   title TEXT,
                   description TEXT)''')
conn.commit()

# Function to scrape the data from the provided URL
def scrape_data():
    url = 'https://play.google.com/store/games?hl=en&gl=US'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    package_names = []

    # Extract package names from the scraped data
    tr = soup.find_all('div', {'class': 'ULeU3b neq64b'})
    package_names = []
    for i in tr:
        t = i.find('a', {'class': 'Si6A0c Gy4nib'})
        if t:
            package_name = t.get('href').split('=')[-1]
            package_names.append(package_name)
        else:
            print("Package name not found.")
    # Schedule the scraping tasks for package details
    for package_name in package_names:
        scheduler.add_job(scrape_playstore, args=[package_name])

# Function to scrape package details from the Play Store
def scrape_playstore(package_name):
    try:
        result = app(package_name)
        title = result['title']
        description = result['description']
        
        # Store the scraped data in the database
        cursor.execute("INSERT INTO apps (package_name, title, description) VALUES (?, ?, ?)",
                       (package_name, title, description))
        conn.commit()
    except Exception as e:
        print(f"Error scraping package {package_name}: {str(e)}")

# Create a background scheduler
scheduler = BackgroundScheduler()

# API endpoint for triggering the scraping event
@app.route('/scrape', methods=['POST'])
def trigger_scraping():
    # Trigger the scraping event
    scheduler.add_job(scrape_data)
    scheduler.start()
    return jsonify({'message': 'Scraping triggered successfully'})

# API endpoint for fetching the Play Store details
@app.route('/details', methods=['GET'])
def get_details():
    # Retrieve the stored data from the database
    cursor.execute("SELECT package_name, title, description FROM apps")
    data = cursor.fetchall()
    apps = []
    for row in data:
        package_name, title, description = row
        apps.append({'package_name': package_name, 'title': title, 'description': description})
    return jsonify(apps)

if __name__ == '__main__':
    app.run(debug=True)
