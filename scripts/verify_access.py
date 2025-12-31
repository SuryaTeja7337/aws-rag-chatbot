import boto3
from src.common.settings import AWS_REGION

def main():
    print("Checking AWS access...")

    sts = boto3.client("sts", region_name=AWS_REGION)
    identity = sts.get_caller_identity()

    print("✅ AWS access verified")
    print(f"Account: {identity['Account']}")
    print(f"ARN: {identity['Arn']}")

if __name__ == "__main__":
    main()
