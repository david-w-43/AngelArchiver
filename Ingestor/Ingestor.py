import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import mysql.connector

class Programme:
    def __init__(self, start_time, end_time, title, subtitle):
        self.start_time = start_time
        self.end_time = end_time
        self.title = title
        self.subtitle = subtitle

def extract_regex_matches(url, regex_pattern):
    """
    Extracts a list of regex matches from the HTML content of a website.

    Args:
        url (str): The URL of the website to scrape.
        regex_pattern (str): The regex pattern to match.

    Returns:
        list: A list of strings that match the regex pattern.
    """
    try:
        # Fetch the website content
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract all text from the HTML
        text_content = soup.get_text()

        # Find all matches using the regex pattern
        matches = re.findall(regex_pattern, text_content)

        return matches
    except requests.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return []
    except re.error as e:
        print(f"Error with regex pattern: {e}")
        return []

def convert_time_to_hours_minutes(time_str):
    """
    Converts a time string in the format "H:MM" or "HH:MM" to hours and minutes.

    Args:
        time_str (str): The time string to convert.

    Returns:
        tuple: A tuple containing hours and minutes as integers.
    """
    try:
        hours, minutes = map(int, time_str.replace(".", ":").split(":"))
        return hours, minutes
    except ValueError:
        print(f"Invalid time format: {time_str}")
        return None
    
def parse_entries(entries, date):
    # Create empty list of Programme objects
    programmes = []

    # Variables to keep track of times
    pm = False
    next_day = False
    previous_time = (0, 0)
    for i, (time, title, subtitle) in enumerate(entries):
        # Detect next day, with bodge for out of order times
        if pm and (time[0] <= previous_time[0] - 12) and (previous_time[0] in [10, 11, 12]):
            next_day = True
        # Detect change to pm
        if (time[0] < previous_time[0]):
            pm = True

        # If the time is in the afternoon, adjust the hour
        if pm and not next_day and time[0] < 12:
            time = (time[0] + 12, time[1])
        
        # Create a Programme object, using the current year and the date from the website
        # Month comes through as a string, so we need to use strptime!
        start_time = datetime.strptime(f"{datetime.now().year}-{date[1]}-{date[0]} {time[0]}:{time[1]}", "%Y-%B-%d %H:%M")
        start_time = start_time.astimezone()  # Ensure the time is in local timezone

        # If next_day is True, add one day
        if next_day:
            start_time += timedelta(days=1)

        # Add programme to list
        programmes.append(Programme(start_time, start_time + timedelta(hours=1), title, subtitle))

        # Update previous time
        previous_time = time

    # REMOVED END TIMES AS THIS IS HANDLED IN ASSEMBLE.PY
    # # Run through and update the end times
    # for i in range(len(programmes)):
    #     if i < len(programmes) - 1:
    #         programmes[i].end_time = programmes[i + 1].start_time
    #     else:
    #         # If it's the last programme, set the end time to one hour after the start time
    #         # We'll go back and update this later
    #         programmes[i].end_time = programmes[i].start_time + timedelta(hours=1)

    return programmes

def upload_programmes_to_database(programmes):
    """
    Uploads the programme schedule to a MySQL database.

    Args:
        programmes (list): A list of Programme objects to upload.
    """
    # Connect to the MySQL database
    try:
        connection = mysql.connector.connect(
            host="db",
            user="root",
            password="example"
        )
        cursor = connection.cursor()

        # Check if the "angel" database exists
        cursor.execute("SHOW DATABASES")
        databases = [db[0] for db in cursor.fetchall()]
        if "angel" not in databases:
            # Create the "angel" database if it doesn't exist
            cursor.execute("CREATE DATABASE angel")

        # Connect to the "angel" database
        connection.database = "angel"

        # Check if the "programmes" table exists
        cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'angel'
        AND table_name = 'programmes'
        """)
        if cursor.fetchone()[0] == 0:
            # Create the "programmes" table if it doesn't exist
            create_table_query = """
            CREATE TABLE `programmes` (
                `id` int NOT NULL AUTO_INCREMENT COMMENT 'Primary Key',
                `start_time` datetime NOT NULL COMMENT 'Start Time',
                `name` varchar(255) NOT NULL,
                `subtitle` varchar(255) DEFAULT NULL,
                `filepath` varchar(255) DEFAULT NULL,
                PRIMARY KEY (`id`),
                UNIQUE KEY `start_time` (`start_time`)
            )
            """
            cursor.execute(create_table_query)
        
        # Insert each programme into the "programmes" table
        for programme in programmes:
            try:
                insert_query = """
                INSERT INTO programmes (start_time, name, subtitle)
                VALUES (%s, %s, %s)
                """
                cursor.execute(insert_query, (programme.start_time, programme.title, programme.subtitle))
            except mysql.connector.Error as err:
                print(f"Error inserting {programme.title}: {err.msg}")
            
        
        # Commit the transaction
        connection.commit()
        print("Programmes successfully added to the database.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if connection.is_connected():
            cursor.close()
        connection.close()

def upload_programmes_for_day(day):
    url = "https://www.angelradio.co.uk/" + day.lower()
    
    # Get programme times and titles from the Angel Radio website
    programme_pattern = r"([0-9]{1,2}[:\.][0-9]{2})(?:\s+)([\w'’&() ]*)(?:[-–] (.*))?"
    matches = extract_regex_matches(url, programme_pattern)

    # Convert the matches' time format and clean up titles
    matches = [(convert_time_to_hours_minutes(time), title.strip().replace("TOMORROW", ""), subtitle.strip().replace("TOMORROW", "")) for time, title, subtitle in matches]

    # Get date from the website
    date_pattern = r"\w*day\D+(\d+)(?:st|nd|rd|th)\W+([A-Z][a-z]+)"
    date = extract_regex_matches(url, date_pattern)[0]

    programmes = parse_entries(matches, date)
    for programme in programmes:
        print(f"{programme.start_time.strftime('%Y-%m-%d %H:%M')} - {programme.title} - {programme.subtitle}")
    # Upload the programme schedule to the database
    upload_programmes_to_database(programmes)

def ingest_all():
    # List of days to upload programmes for
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    for day in days:
        print(f"Uploading programmes for {day}...")
        upload_programmes_for_day(day)
        print(f"Finished uploading programmes for {day}.")

# Main execution
if __name__ == "__main__":
    ingest_all()
