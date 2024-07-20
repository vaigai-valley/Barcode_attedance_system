import cv2
import numpy as np
import csv
import os
from datetime import date, datetime
import logging
import schedule
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to read student details from CSV file
def read_student_details(csv_file):
    student_details = {}
    try:
        with open(csv_file, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                student_details[row['ID']] = {'name': row['Name'], 'attendance': 'Absent'}
    except FileNotFoundError:
        logging.error(f"File not found: {csv_file}")
    except Exception as e:
        logging.error(f"Error reading {csv_file}: {e}")
    return student_details

# Function to create a new daily attendance CSV file
def create_daily_attendance_csv(csv_file):
    if not os.path.exists(csv_file):
        try:
            with open(csv_file, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Date', 'ID', 'Name', 'Attendance'])
        except Exception as e:
            logging.error(f"Error creating {csv_file}: {e}")

# Function to read the daily attendance to check for duplicates
def read_daily_attendance(csv_file):
    attendance_records = set()
    if os.path.exists(csv_file):
        try:
            with open(csv_file, mode='r', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    attendance_records.add(row['ID'])
        except Exception as e:
            logging.error(f"Error reading {csv_file}: {e}")
    return attendance_records

# Function to update attendance status in the daily attendance CSV
def update_daily_attendance(csv_file, student_id, student_name, status='Present'):
    try:
        attendance_records = read_daily_attendance(csv_file)
        if student_id not in attendance_records:
            with open(csv_file, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([date.today(), student_id, student_name, status])
            logging.info(f"Attendance recorded for {student_name} (ID: {student_id}) as {status}")
        else:
            logging.info(f"Attendance already recorded for {student_name} (ID: {student_id})")
    except Exception as e:
        logging.error(f"Error updating {csv_file}: {e}")

# Function to mark absences for students who did not scan by the specified time
def mark_absences(students_csv, daily_attendance_csv):
    student_details = read_student_details(students_csv)
    attendance_records = read_daily_attendance(daily_attendance_csv)
    
    for student_id, details in student_details.items():
        if student_id not in attendance_records:
            update_daily_attendance(daily_attendance_csv, student_id, details['name'], status='Absent')

    logging.info("Absences marked for students who did not scan by the specified time.")

# Function to capture barcode input and process attendance
def barcode_attendance(students_csv, daily_attendance_csv):
    student_details = read_student_details(students_csv)
    create_daily_attendance_csv(daily_attendance_csv)
    cap = cv2.VideoCapture(0)  # Adjust 0 to your camera index or video file
    barcode_reader = cv2.QRCodeDetector()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            logging.warning("Failed to capture frame from camera.")
            continue
        
        data, bbox, _ = barcode_reader.detectAndDecode(frame)
        
        if bbox is not None:
            bbox = np.array(bbox)  # Convert bbox to numpy array for easier indexing
            
            for i in range(len(bbox)):
                pt1 = tuple(bbox[i][0].astype(int))
                pt2 = tuple(bbox[(i + 1) % len(bbox)][0].astype(int))
                cv2.line(frame, pt1, pt2, color=(255, 0, 0), thickness=2)
                
            if data:
                student_id = data.strip()
                if student_id in student_details:
                    student_name = student_details[student_id]['name']
                    attendance_records = read_daily_attendance(daily_attendance_csv)
                    if student_id not in attendance_records:
                        update_daily_attendance(daily_attendance_csv, student_id, student_name)
                    else:
                        logging.info(f"Attendance already recorded for {student_name} (ID: {student_id})")
                else:
                    logging.warning("Student ID not found in the database.")
        
        cv2.imshow('Barcode Attendance System', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

# Main function
if __name__ == "__main__":
    students_csv = 'students.csv'  # Replace with your CSV file path
    daily_attendance_csv = f'daily_attendance_{date.today()}.csv'  # Daily attendance CSV filename
    
    # Schedule the absence marking function to run at 9:30 AM
    schedule.every().day.at("09:30").do(mark_absences, students_csv, daily_attendance_csv)
    
    # Start the barcode attendance system in a separate thread
    import threading
    attendance_thread = threading.Thread(target=barcode_attendance, args=(students_csv, daily_attendance_csv))
    attendance_thread.start()
    
    # Run the scheduler
    while True:
        schedule.run_pending()
        time.sleep(1)
