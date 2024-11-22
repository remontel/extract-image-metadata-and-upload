# This program extracts metadata (latitude, longitude, date, time) from images in a specified folder
# and saves the data to a CSV file. The metadata is extracted from the EXIF data embedded in the images.
# 
# Python Imaging Library (PIL) is used to read the image files and extract the metadata.
# Extracted metadata is then written to a CSV file using the csv module.
#
# dms_to_decimal function converts the GPS coordinates from degrees, minutes, seconds format to decimal format.
# extract_metadata function processes each image file in the specified folder, extracts the metadata, and saves it to a CSV file.
# main function prompts the user to enter the folder path containing the images and calls the extract_metadata function.
# 
# The program can be run from the command line or an IDE, and it will prompt the user to enter the folder path.
# The extracted metadata is saved to a file named image_metadata.csv in the same directory as the script.

import os
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import csv
from datetime import datetime

def dms_to_decimal(dms, ref):
    degrees, minutes, seconds = dms
    decimal = float(degrees) + float(minutes)/60 + float(seconds)/3600
    if ref in ['S', 'W']:
        decimal = -decimal
    return decimal

def extract_metadata(folder_path):
    metadata_list = []

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.jpg', '.jpeg', '.tiff', '.tif')):
            image_path = os.path.join(folder_path, filename)
            print(f"Processing {filename}...")
            try:
                image = Image.open(image_path)
                exif_data = image._getexif()
                exif_dict = {'Filename': filename}

                if exif_data:
                    gps_info = {}
                    date = None
                    time = None
                    latitude = None
                    longitude = None

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
                            # value is in the format 'YYYY:MM:DD HH:MM:SS'
                            try:
                                date_time_obj = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                                date = date_time_obj.strftime('%m/%d/%Y')
                                time = date_time_obj.strftime('%H:%M:%S')
                            except ValueError:
                                date = None
                                time = None

                    exif_dict['Latitude'] = latitude
                    exif_dict['Longitude'] = longitude
                    exif_dict['Date'] = date
                    exif_dict['Time'] = time
                else:
                    exif_dict['Latitude'] = None
                    exif_dict['Longitude'] = None
                    exif_dict['Date'] = None
                    exif_dict['Time'] = None

                metadata_list.append(exif_dict)
            except Exception as e:
                print(f"Error processing {filename}: {e}")

    # Write metadata to CSV
    with open('image_metadata.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Filename', 'Latitude', 'Longitude', 'Date', 'Time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for metadata in metadata_list:
            row = {
                'Filename': metadata['Filename'],
                'Latitude': metadata['Latitude'],
                'Longitude': metadata['Longitude'],
                'Date': metadata['Date'],
                'Time': metadata['Time']
            }
            writer.writerow(row)

    print("Metadata extraction complete. Data saved to image_metadata.csv.")

if __name__ == '__main__':
    folder_path = input('Enter the folder path containing the photos: ')
    if not os.path.isdir(folder_path):
        print("The specified folder does not exist.")
    else:
        extract_metadata(folder_path)