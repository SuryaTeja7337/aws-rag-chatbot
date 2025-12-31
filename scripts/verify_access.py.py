# scripts/verify_access.py
from pathlib import Path
import sys

# Add project root to Python path so `import src...` works reliably
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

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

