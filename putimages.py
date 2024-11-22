import os
import boto3

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
rekognition_client = boto3.client('rekognition')

# Define your S3 bucket name and DynamoDB table
bucket_name = 'famouspersonsimages-atharva-123'
table = dynamodb.Table('face_recognition')
collection_id = 'my-face-collection'

# Create the Rekognition collection
try:
    rekognition_client.create_collection(CollectionId=collection_id)
    print(f"Collection '{collection_id}' created successfully.")
except rekognition_client.exceptions.ResourceAlreadyExistsException:
    print(f"Collection '{collection_id}' already exists.")

# List of images and their associated names
images_info = [
    (r"C:\Users\hp\aws_recognition\code\image1.jpeg", 'Person1_Name'),
    (r"C:\Users\hp\aws_recognition\code\image2.jpeg", 'Elon_Musk'),
    (r"C:\Users\hp\aws_recognition\code\image3.jpeg", 'Bill_Gates'),
    (r"C:\Users\hp\aws_recognition\code\image4.jpeg", 'Bill_Gates'),
    (r"C:\Users\hp\aws_recognition\code\image5.jpeg", 'Sundar_Pichai'),
    (r"C:\Users\hp\aws_recognition\code\image6.jpeg", 'Sundar_Pichai')
]

for file_path, full_name in images_info:
    # Sanitize the ExternalImageId by replacing spaces with underscores
    sanitized_name = full_name.replace(" ", "_")

    if os.path.exists(file_path):
        try:
            # Extract filename and S3 key
            file_name = os.path.basename(file_path)
            s3_key = f'images/{file_name}'

            # Upload image to S3
            s3_client.upload_file(file_path, bucket_name, s3_key)
            print(f"Uploaded {file_name} to S3 bucket {bucket_name}")

            # Index face in Rekognition collection
            with open(file_path, 'rb') as image_file:
                response = rekognition_client.index_faces(
                    CollectionId=collection_id,
                    Image={'Bytes': image_file.read()},
                    ExternalImageId=sanitized_name,  # Use sanitized name
                    DetectionAttributes=['ALL']
                )

            # Extract the FaceId from the response
            if response['FaceRecords']:
                face_id = response['FaceRecords'][0]['Face']['FaceId']
                print(f"FaceId for {sanitized_name}: {face_id}")

                # Add information to DynamoDB
                response = table.put_item(
                    Item={
                        'RekognitionId': face_id,  # Use the unique FaceId
                        'FullName': full_name,     # Person's full name
                        'S3Path': f's3://{bucket_name}/{s3_key}'
                    }
                )
                print(f"Inserted {full_name} into DynamoDB with RekognitionId: {face_id}")

            else:
                print(f"No faces detected in {file_name}")

        except Exception as e:
            print(f"Error processing {file_name}: {e}")
    else:
        print(f"File not found: {file_path}")
