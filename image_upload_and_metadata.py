"""
image_upload_and_metadata.py

This script combines the functionalities of metadata extraction and image uploading to Google Cloud Storage (GCS).

Features:
- Extracts metadata (latitude, longitude, date, time) from images in a specified folder.
- Uploads images to a specified GCS bucket.
- Generates a CSV file called  `gcs_image_metadata_with_links.csv` containing the extracted metadata and public URLs of the uploaded images.

Usage:
- Run the script and input the folder path containing the images when prompted.
- Ensure that Google Cloud authentication is set up correctly (service account key and environment variable).
- Replace 'your-bucket-name' in the script with the actual name of your GCS bucket.
- Set the GOOGLE_APPLICATION_CREDENTIALS environment variable to point to your service account key JSON file
     `export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"`

Prerequisites:
- Python 3.x
- Libraries: os, csv, datetime, PIL (Pillow), google-cloud-storage
- Google Cloud SDK and a GCS bucket with appropriate permissions.

Author: Rene Montelongo
"""

import os
import csv
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from google.cloud import storage

def dms_to_decimal(dms, ref):
    """
    Converts GPS coordinates from degrees, minutes, seconds format to decimal format.

    Parameters:
    - dms: Tuple containing degrees, minutes, and seconds.
    - ref: Reference hemisphere ('N', 'S', 'E', 'W').

    Returns:
    - Decimal representation of the coordinate.
    """
    degrees, minutes, seconds = dms
    decimal = float(degrees) + float(minutes)/60 + float(seconds)/3600
    if ref in ['S', 'W']:
        decimal = -decimal
    return decimal

def extract_image_metadata(image_path, filename):
    """
    Extracts metadata (latitude, longitude, date, time) from an image file.

    Parameters:
    - image_path: Full path to the image file.
    - filename: Name of the image file.

    Returns:
    - Dictionary containing extracted metadata.
    """
    try:
        with Image.open(image_path) as image:
            exif_data = image._getexif()
            metadata = {'Filename': filename}
            latitude = None
            longitude = None
            date = None
            time_value = None

            if exif_data:
                gps_info = {}

                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)

                    if tag == 'GPSInfo':
                        for key in value:
                            decode = GPSTAGS.get(key, key)
                            gps_info[decode] = value[key]

                        # Extract latitude and longitude
                        gps_latitude = gps_info.get('GPSLatitude')
                        gps_latitude_ref = gps_info.get('GPSLatitudeRef')
                        gps_longitude = gps_info.get('GPSLongitude')
                        gps_longitude_ref = gps_info.get('GPSLongitudeRef')

                        if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
                            latitude = dms_to_decimal(gps_latitude, gps_latitude_ref)
                            longitude = dms_to_decimal(gps_longitude, gps_longitude_ref)

                    elif tag in ('DateTime', 'DateTimeOriginal', 'DateTimeDigitized'):
                        # Value is in the format 'YYYY:MM:DD HH:MM:SS'
                        try:
                            date_time_obj = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                            date = date_time_obj.strftime('%m/%d/%Y')
                            time_value = date_time_obj.strftime('%H:%M:%S')
                        except ValueError:
                            date = None
                            time_value = None

            metadata['Latitude'] = latitude
            metadata['Longitude'] = longitude
            metadata['Date'] = date
            metadata['Time'] = time_value

            return metadata
    except Exception as e:
        error_message = f"Error extracting metadata from {filename}: {e}"
        print(error_message)
        return {'Filename': filename}
    
def log_errors(error_log):
    """
    Writes the list of errors to an error log file.

    Parameters:
    - error_log: List of tuples containing error messages and timestamps.
    """
    if error_log:
        log_file = 'error_log.txt'
        with open(log_file, 'w', encoding='utf-8') as f:
            for timestamp, error in error_log:
                f.write(f"[{timestamp}] {error}\n")
        print(f"Errors were encountered. Details are logged in {log_file}.")

def upload_images_to_gcs_with_metadata(folder_path, bucket_name):
    """
    Uploads images from a specified folder to a GCS bucket and extracts metadata.

    Parameters:
    - folder_path: Path to the folder containing images.
    - bucket_name: Name of the GCS bucket.

    Actions:
    - Iterates over image files in the folder.
    - Extracts metadata from each image.
    - Uploads each image to GCS.
    - Generates a CSV file with metadata and image URLs.
    - Logs any errors encountered during processing.
    """
    # Initialize the GCS client
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    # Lists to hold metadata and errors
    metadata_list = []
    error_log = []

    # Counters for success and failure
    success_count = 0
    failure_count = 0

    # Iterate over files in the folder
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.tiff', '.tif')):
            image_path = os.path.join(folder_path, filename)
            print(f"Processing {filename}...")

            # Initialize metadata dictionary
            metadata = {'Filename': filename, 'Latitude': None, 'Longitude': None, 'Date': None, 'Time': None, 'ImageURL': None}

            # Extract image metadata
            try:
                extracted_metadata = extract_image_metadata(image_path, filename)
                metadata.update(extracted_metadata)
            except Exception as e:
                error_message = f"Error extracting metadata from {filename}: {e}"
                print(error_message)
                error_log.append((datetime.now().strftime('%Y-%m-%d %H:%M:%S'), error_message))

            # Upload the image to GCS
            try:
                blob = bucket.blob(filename)
                blob.upload_from_filename(image_path)
                public_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"
                metadata['ImageURL'] = public_url
                success_count += 1
                print(f"Uploaded {filename} to GCS.")
            except Exception as e:
                error_message = f"Error uploading {filename} to GCS: {e}"
                print(error_message)
                error_log.append((datetime.now().strftime('%Y-%m-%d %H:%M:%S'), error_message))
                failure_count += 1

            # Add metadata to the list (even if upload failed)
            metadata_list.append(metadata)
        else:
            print(f"Skipping non-image file: {filename}")

    # Write metadata to CSV
    if metadata_list:
        csv_file = 'gcs_image_metadata_with_links.csv'
        fieldnames = ['Filename', 'Latitude', 'Longitude', 'Date', 'Time', 'ImageURL']
        with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for data in metadata_list:
                writer.writerow(data)
        print(f"Metadata extraction and upload complete. Data saved to {csv_file}.")
    else:
        print("No images were processed.")

    # Log errors if any
    log_errors(error_log)

    # Print summary
    print(f"\nProcessing complete: {success_count} images uploaded successfully, {failure_count} images failed.")

if __name__ == '__main__':
    # Prompt user for folder path
    folder_path = input('Enter the folder path containing the images: ').strip()
    if not os.path.isdir(folder_path):
        print("The specified folder does not exist.")
    else:
        # Specify your GCS bucket name
        bucket_name = 'your-bucket-name'  # Replace with your GCS bucket name

        # Inform user about public access requirement
        print("\nNote: Ensure that your GCS bucket has public read access for the images to be accessible via URLs.\n")

        # Call the main function to process images
        upload_images_to_gcs_with_metadata(folder_path, bucket_name)