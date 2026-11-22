#!/usr/bin/env python3

"""
📚 Deploy Documentation to AWS S3
No CLI required - uses boto3 Python SDK
"""

import os
import sys
import json
from pathlib import Path

def deploy_to_s3():
    """Deploy documentation to AWS S3"""
    
    print("""
╔════════════════════════════════════════════════════╗
║                                                    ║
║      📚 Deploy Documentation to AWS S3             ║
║                                                    ║
╚════════════════════════════════════════════════════╝
    """)
    
    # Check if boto3 is installed
    try:
        import boto3
        print("✅ boto3 is installed")
    except ImportError:
        print("❌ boto3 is not installed")
        print("\n📦 Install with:")
        print("   pip install boto3 --break-system-packages")
        sys.exit(1)
    
    # Get configuration
    print("\n📝 Configuration")
    print("=" * 50)
    
    bucket_name = input("📦 S3 bucket name (or press Enter for 'escrow-docs'): ").strip() or "escrow-docs"
    region = input("🌍 AWS region (or press Enter for 'us-east-1'): ").strip() or "us-east-1"
    access_key = input("🔑 AWS Access Key ID: ").strip()
    secret_key = input("🔐 AWS Secret Access Key: ").strip()
    
    if not access_key or not secret_key:
        print("❌ AWS credentials are required")
        sys.exit(1)
    
    print(f"\n✅ Using configuration:")
    print(f"   Bucket: {bucket_name}")
    print(f"   Region: {region}")
    
    # Initialize S3 client
    try:
        s3 = boto3.client(
            's3',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        print("✅ Connected to AWS")
    except Exception as e:
        print(f"❌ Failed to connect to AWS: {e}")
        sys.exit(1)
    
    # Create bucket
    print(f"\n📦 Creating S3 bucket: {bucket_name}")
    try:
        if region == 'us-east-1':
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        print(f"✅ Bucket created: {bucket_name}")
    except Exception as e:
        if 'BucketAlreadyOwnedByYou' in str(e):
            print(f"✅ Bucket already exists: {bucket_name}")
        else:
            print(f"⚠️  {e}")
    
    # Configure bucket as static website
    try:
        s3.put_bucket_website(
            Bucket=bucket_name,
            WebsiteConfiguration={
                'IndexDocument': {'Suffix': 'index.html'},
                'ErrorDocument': {'Key': 'index.html'}
            }
        )
        print("✅ Configured bucket for static website hosting")
    except Exception as e:
        print(f"⚠️  Could not configure website hosting: {e}")
    
    # Make bucket public
    try:
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/*"
                }
            ]
        }
        s3.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))
        print("✅ Made bucket public (readable)")
    except Exception as e:
        print(f"⚠️  Could not set bucket policy: {e}")
    
    # Upload files
    docs_dir = Path(__file__).parent / "docs"
    
    if not docs_dir.exists():
        print(f"❌ Documentation directory not found: {docs_dir}")
        sys.exit(1)
    
    print(f"\n📤 Uploading files from: {docs_dir}")
    
    files_uploaded = 0
    for file_path in docs_dir.glob("*"):
        if file_path.is_file():
            # Determine content type
            if file_path.suffix == '.html':
                content_type = 'text/html'
            elif file_path.suffix == '.css':
                content_type = 'text/css'
            elif file_path.suffix == '.js':
                content_type = 'application/javascript'
            else:
                content_type = 'application/octet-stream'
            
            try:
                with open(file_path, 'rb') as f:
                    s3.put_object(
                        Bucket=bucket_name,
                        Key=file_path.name,
                        Body=f,
                        ContentType=content_type
                    )
                print(f"   ✅ {file_path.name}")
                files_uploaded += 1
            except Exception as e:
                print(f"   ❌ {file_path.name}: {e}")
    
    # Success!
    print(f"\n✅ Successfully uploaded {files_uploaded} files!")
    
    # Display URLs
    print(f"\n🌐 Your documentation is now live!")
    print(f"\nAccess at:")
    print(f"   S3 Website:  http://{bucket_name}.s3-website-{region}.amazonaws.com/")
    print(f"   S3 Direct:   http://{bucket_name}.s3.amazonaws.com/index.html")
    
    print(f"\n💡 Next steps:")
    print(f"   1. Test the URL in your browser")
    print(f"   2. (Optional) Set up CloudFront for HTTPS and custom domain")
    print(f"   3. Share the URL with your team")
    
    print(f"\n📚 For custom domain (docs.eascrow.io):")
    print(f"   1. Create CloudFront distribution pointing to {bucket_name}.s3.amazonaws.com")
    print(f"   2. Point your DNS CNAME to CloudFront")
    print(f"   3. Enable HTTPS in CloudFront settings")

if __name__ == "__main__":
    try:
        deploy_to_s3()
    except KeyboardInterrupt:
        print("\n\n❌ Deployment cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
