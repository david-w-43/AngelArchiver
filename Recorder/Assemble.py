import os
import subprocess
from datetime import datetime, timedelta

import mysql.connector

# Database configuration
DB_CONFIG = {
    'host': '172.19.0.2',
    'user': 'root',
    'password': 'example',
    'database': 'angel'
}

# Directory where the source MP3 files are stored
SOURCE_DIR = '/home/david/Documents/Angel/Recorder/Recordings'

# Directory where the output MP3 files will be stored
OUTPUT_DIR = '/home/david/Documents/Angel/Recorder/Output'

def fetch_timestamps(connection):
    # Fetch start and end timestamps along with programme names from the MySQL database.
    cursor = connection.cursor()
    cursor.execute("""
                   SELECT id, name, start_time 
                   FROM programmes 
                   WHERE 
                    filepath IS NULL 
                    AND start_time < NOW() + INTERVAL 1 HOUR
                    AND start_time > NOW() - INTERVAL 1 DAY
                   ORDER BY start_time ASC
                   """)
    rows = cursor.fetchall()
    cursor.close()
    return rows

def generate_file_list(start_time, end_time):
    # Generate a list of MP3 files whose timestamps fall within the given range.
    file_list = []
    for filename in sorted(os.listdir(SOURCE_DIR)):
        if filename.endswith('.mp3'):
            try:
                file_timestamp = datetime.strptime(filename[:12], '%Y%m%d%H%M')
                if start_time <= file_timestamp < end_time:
                    file_list.append(os.path.join(SOURCE_DIR, filename))
            except ValueError:
                print(f"Skipping file with invalid timestamp format: {filename}")
    return file_list

def concatenate_files(file_list, output_file):
    # Concatenate MP3 files using ffmpeg.
    if os.path.exists(output_file):
        print(f"Output file {output_file} already exists. Skipping.")
        return

    with open('file_list.txt', 'w') as f:
        for file_path in file_list:
            f.write(f"file '{file_path}'\n")

    try:
        subprocess.run(
            ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'file_list.txt', '-c', 'copy', output_file],
            check=True
        )
        print(f"Created {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error during concatenation: {e}")
    finally:
        os.remove('file_list.txt')

def assemble():
    # Connect to database
    connection = mysql.connector.connect(**DB_CONFIG)

    # Main function to process all timestamps and create output files.
    timestamps = fetch_timestamps(connection)
    
    # Debugging: Using hardcoded timestamps instead of fetching from DB
    # timestamps = [{"record_id": 1, 
    #                "name": "Debug Show1", 
    #                "start_time": "2025-10-14 19:06:30"},
    #                {"record_id": 2, 
    #                "name": "Debug Show2", 
    #                "start_time": "2025-10-14 19:12:30"},
    #                {"record_id": 2, 
    #                "name": "Debug Show3", 
    #                "start_time": "2025-10-14 19:16:30"},
    #                ]
    
    for i in range(len(timestamps) - 1):
        record_id, name, start_time = timestamps[i]
        end_time = timestamps[i + 1][2]
        # record_id = timestamps[i]["record_id"]
        # name = timestamps[i]["name"]
        # start_time = timestamps[i]["start_time"]
        
        #start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')

        # Get the end time from the next entry's start time
        #end_time = datetime.strptime((timestamps[i+1])["start_time"], '%Y-%m-%d %H:%M:%S')

        # Ensure the output file name is unique and includes the programme name
        sanitized_name = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in name)
        output_file = os.path.join(OUTPUT_DIR, f"{start_time.strftime("%Y_%m_%d_%H_%M")}_{sanitized_name}.mp3")

        # Generate the list of files to concatenate
        file_list = generate_file_list(start_time, end_time)
        if not file_list:
            print(f"No files found for programme {name} from {start_time} to {end_time}. Skipping.")
            continue

        # Concatenate the files
        concatenate_files(file_list, output_file)

        # Update the database with the output file path
        cursor = connection.cursor()
        try:
            cursor.execute(
            "UPDATE programmes SET filepath = %s WHERE id = %s",
            (output_file, record_id)
            )
            connection.commit()
        except mysql.connector.Error as err:
            print(f"Error updating database: {err}")
        finally:
            cursor.close()
        
    connection.close()

def cleanup(daysOld=2):
    for filename in os.listdir(SOURCE_DIR):
        file_path = os.path.join(SOURCE_DIR, filename)
        if filename.endswith('.mp3') and os.path.isfile(file_path):
            try:
                file_timestamp = datetime.strptime(filename[:12], '%Y%m%d%H%M')
                if file_timestamp < datetime.now() - timedelta(days=daysOld):
                    os.remove(file_path)
                    print(f"Deleted old recording: {filename}")
            except ValueError:
                print(f"Skipping file with invalid timestamp format: {filename}")

def main():
    # Process recordings
    assemble()

    # Clean up old recordings (older than 2 days)
    cleanup(2)

if __name__ == '__main__':
    main()