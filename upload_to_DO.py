"""
This script provides functionality to connect to a DigitalOcean Spaces S3-compatible storage service 
and upload raster images to a specified bucket.

1. **connect_s3_client()**: This function loads AWS credentials and configuration from environment variables 
   and establishes a connection to the S3 client using the `boto3` library. It returns the client object 
   and the bucket name for further operations.

2. **upload_image_to_s3()**: This function takes the S3 client, bucket name, local file path of the raster image, 
   and the date as parameters. It constructs the S3 object key based on the provided date and raster layer type, 
   and uploads the image to the specified S3 bucket. The upload is done with public-read access by default.


These functions can be optionally included in the main.py script to handle the upload of raster images to the
DigitalOcean Spaces bucket.
"""

import os
import boto3
import boto3.session

from dotenv import load_dotenv


def connect_s3_client():
    # Load environment variables from .env file
    load_dotenv()

    # Get secrets from environment
    ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
    SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    REGION = os.getenv("SPACES_REGION")
    BUCKET_NAME = os.getenv("SPACES_BUCKET_NAME")

    session = boto3.session.Session()
    client = session.client('s3',
                            region_name=REGION,
                            endpoint_url='https://sfo3.digitaloceanspaces.com',
                            aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY)
    return client, BUCKET_NAME

# client, BUCKET_NAME = connect_s3_client()


def upload_image_to_s3(client, BUCKET_NAME, path_to_raster, date):
    """
    Uploads a raster image to a specified S3 bucket.

    Parameters:
    - client: The S3 client object.
    - BUCKET_NAME: The name of the S3 bucket.
    - path_to_raster: The local path to the raster image file.
    - date: The date of the raster image in YYYY-MM-DD format.
    """
    region = "missoula"  # Missoula county is hard coded for now

    # Collect raster layer type
    raster_name = path_to_raster.split("/")[-1]
    layer = raster_name.split("_")[0]

    # Set the destination in the bucket
    # Destination in bucket
    S3_OBJECT_KEY = f"montana/{region}/{date}/{layer}.tif"

    # Upload the file
    try:
        client.upload_file(
            Filename=path_to_raster,
            Bucket=BUCKET_NAME,
            Key=S3_OBJECT_KEY,
            # Keep it private unless public access is needed
            ExtraArgs={'ACL': 'public-read', 'ContentType': 'image/tiff'}
        )
        print(f"Successfully uploaded {S3_OBJECT_KEY}")
    except Exception as e:
        print(f"Error uploading {S3_OBJECT_KEY}: {e}")


### Example usage ###
# local_file_path = '/Volumes/Drew_ext_drive/NDVI_Proj/historic_rasters/2024/July/26/RGB_mosaic.tif'
# S3_OBJECT_KEY = f"montana/2024/07/28/RGB-missoula-2024-01-.tif"  # Destination in bucket


# # Upload the file
# client.upload_file(
#     Filename=local_file_path,
#     Bucket=BUCKET_NAME,
#     Key=S3_OBJECT_KEY,
#     ExtraArgs={'ACL': 'private', 'ContentType': 'image/tiff'}  # Keep it private unless public access is needed
# )


# # Delete the file
# client.delete_object(Bucket=BUCKET_NAME, Key=S3_OBJECT_KEY)

# Check for objects in the bucket
# client, BUCKET_NAME = connect_s3_client()
# response = client.list_objects_v2(Bucket=BUCKET_NAME, Prefix="montana/")
# if "Contents" in response:
#     print(f"Objects in {BUCKET_NAME}:")
#     for obj in response["Contents"]:
#         for key, value in obj.items():
#             print(f"{key}: {value}")
#         print(f"- {obj['Key']} ({obj['Size']} bytes)")
# else:
#     print("No objects found or permission denied.")