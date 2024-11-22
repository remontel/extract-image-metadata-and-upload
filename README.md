# Image Upload and Metadata Extraction Scripts

## Overview

This Python scripts combine metadata extraction and image uploading functionalities. They extracts metadata from images in a specified folder and uploads them to Google Cloud Storage (GCS), generating a CSV file containing the metadata and public URLs of the uploaded images.

This was written for a client who wanted an "art map" of murals they had painted around the world. A shopify app called Progus Store Locator was used to host the map. But there were about 2150 murals that needed to be process. To expedite the process, this script was written to take the location data from the image of the mural, upload the image to a GCS bucket accessible by Progus, and generate a CSV file with the associated location and url address.

## Features

- Extracts EXIF metadata (latitude, longitude, date, time) from images.
- Uploads images to a specified GCS bucket.
- Generates a CSV file (`gcs_image_metadata_with_links.csv`) with metadata and image URLs.
- Logs errors encountered during processing to `error_log.txt`.

## Prerequisites

- **Python 3.x**
- **Google Cloud Platform (GCP) Account**
- **Google Cloud SDK**



## Setup Instructions



### 1. Clone the Repository

```bash
git clone https://github.com/your-username/image-upload-metadata-extraction.git
cd image-upload-metadata-extraction
```



### 2. Set Up a Virtual Environment (Recommended)

```
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```



### 3. Install Dependencies

```
pip install -r requirements.txt
```



### 4. Setup Google Cloud Storage

#### 1. Create a GCS Bucket

- Log in to your GCP Console.
- Create a new bucket (ensure the name is globally unique).

#### 2. Configure Bucket Permissions

- Set the bucket to **Uniform Bucket-Level Access**.
- Grant `Storage Object Viewer` role to `allUsers`for public read access.

#### 3. Create A Service Account

- Navigate to **IAM & Admin > Service Accounts**.
- Create a new service account with **Storage Object Admin** role.
- Generate a key in JSON format and download it.



### 5. Setup Google SDK



## Usage Instructions



**Set the GOOGLE_APPLICATION_CREDENTIALS Environment Variable**

Set the environment variable to point to your service account key JSON file:

`export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"`



**Update the Script**

In `image_upload_and_metadata.py`, update the following:

- Replace `your-bucket-name` with your actual GCS bucket name.



**Run the Script**

`python image_upload_and_metadata.py`

- When prompted, enter the folder path containing your images.



## Notes

- **Input**: The script processes image files with extensions .jpg, .jpeg, .png, .gif, .tiff, .tif.
- **Output**:
  - gcs_image_metadata_with_links.csv: Contains metadata and image URLs.
  - error_log.txt: Logs any errors encountered during processing.
- Ensure images have EXIF metadata for accurate extraction.
- The script skips files that are not images or do not have the supported extensions.
- Be careful with public access to your GCS bucket; only store data intended for public access.