import csv
import qrcode
import os

# Function to read student IDs from CSV file
def read_student_ids(csv_file):
    student_ids = []
    with open(csv_file, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            student_ids.append(row['ID'])
    return student_ids

# Function to generate QR codes for each student ID
def generate_qr_codes(csv_file, output_folder):
    student_ids = read_student_ids(csv_file)
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    for student_id in student_ids:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(student_id)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(f"{output_folder}/qr_{student_id}.png")
        print(f"QR code generated for student ID: {student_id}")

# Main function
if __name__ == "__main__":
    students_csv = 'students.csv'  # Replace with your CSV file path
    output_folder = 'qr_codes'  # Folder where QR codes will be saved
    generate_qr_codes(students_csv, output_folder)
