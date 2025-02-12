import os
import boto3
import boto3.session
from dotenv import load_dotenv

def connect_s3_client():
    # Load environment variables from .env file
    load_dotenv()

    # Get secrets from environment
    ACCESS_KEY = os.getenv("WAS_ACCESS_KEY_ID")
    SECRET_KEY = os.getenv("WAS_SECRET_ACCESS_KEY")
    REGION = os.getenv("SPACES_REGION")
    BUCKET_NAME = os.getenv("SPACES_BUCKET_NAME")

    session = boto3.session.Session()
    client = session.client('s3',
                            region_name=REGION,
                            endpoint_url='https://sfo3.digitaloceanspaces.com',
                            aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY)
    return client, BUCKET_NAME

client, BUCKET_NAME = connect_s3_client()

def upload_image_to_s3(client, BUCKET_NAME, path_to_raster, date):
    region = "missoula" # missoula county is hard coded for now
    
    # Collect raster layer type
    raster_name = path_to_raster.split("/")[-1]
    layer = raster_name.split("_")[0]
    
    # Collect year, month, and day from date
    year, month, day = date.split("-")
    
    # Set the destination in the bucket
    S3_OBJECT_KEY = f"montana/{year}/{month}/{day}/{layer}-{region}-{date}.tif"  # Destination in bucket
    
    # Upload the file
    try:
        client.upload_file(
        Filename=path_to_raster,
        Bucket=BUCKET_NAME,
        Key=S3_OBJECT_KEY,
        ExtraArgs={'ACL': 'public-read', 'ContentType': 'image/tiff'}  # Keep it private unless public access is needed
    )
        print(f"Successfully uploaded {S3_OBJECT_KEY}")
    except Exception as e:
        print(f"Error uploading {S3_OBJECT_KEY}: {e}")



# ### Example usage ###
# local_file_path = '/Volumes/Drew_ext_drive/NDVI_Proj/historic_rasters/2024/July/26/RGB_mosaic.tif'
# S3_OBJECT_KEY = f"montana/2024/07/28/RGB-missoula-2024-01-15.tif"  # Destination in bucket


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
# response = client.list_objects_v2(Bucket=BUCKET_NAME, Prefix="montana/2024/07/28/")
# if "Contents" in response:
#     print(f"Objects in {BUCKET_NAME}:")
#     for obj in response["Contents"]:
#         print(f"- {obj['Key']} ({obj['Size']} bytes)")
# else:
#     print("No objects found or permission denied.")

