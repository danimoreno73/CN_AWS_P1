#!/usr/bin/env python3
"""
Script para eliminar el stack de Lambda
Uso: python scripts/cleanup-lambda.py
"""

import boto3
import sys

STACK_NAME = "notes-lambda-option-b"
REGION = "us-east-1"


def empty_bucket(bucket_name):
    """Vaciar bucket S3 antes de eliminar"""
    s3 = boto3.resource('s3', region_name=REGION)
    bucket = s3.Bucket(bucket_name)
    
    print(f"Vaciando bucket {bucket_name}...")
    bucket.objects.all().delete()
    bucket.object_versions.all().delete()
    print("✓ Bucket vaciado")


def main():
    print("ADVERTENCIA: Esto eliminará el stack de Lambda")
    confirm = input("¿Continuar? (si/no): ")
    
    if confirm.lower() != 'si':
        print("Cancelado")
        sys.exit(0)
    
    cf_client = boto3.client('cloudformation', region_name=REGION)
    
    try:
        # Obtener nombre del bucket
        response = cf_client.describe_stacks(StackName=STACK_NAME)
        outputs = response['Stacks'][0].get('Outputs', [])
        
        bucket_name = None
        for output in outputs:
            if output['OutputKey'] == 'DeploymentBucket':
                bucket_name = output['OutputValue']
                break
            # Vaciar bucket antes de eliminar
        if bucket_name:
            empty_bucket(bucket_name)
        
        print("\nEliminando stack...")
        cf_client.delete_stack(StackName=STACK_NAME)
        
        print("Esperando eliminación...")
        waiter = cf_client.get_waiter('stack_delete_complete')
        waiter.wait(StackName=STACK_NAME)
        
        print("✓ Stack eliminado")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
    