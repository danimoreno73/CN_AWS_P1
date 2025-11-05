#!/usr/bin/env python3
"""
Script para eliminar el stack de DynamoDB
Uso: python scripts/cleanup-dynamodb.py
"""

import boto3
import sys

STACK_NAME = "notes-dynamodb"
REGION = "us-east-1"

def main():
    print("ADVERTENCIA: Esto eliminará la tabla DynamoDB y todos los datos")
    confirm = input("¿Continuar? (si/no): ")
    
    if confirm.lower() != 'si':
        print("Cancelado")
        sys.exit(0)
    
    cf_client = boto3.client('cloudformation', region_name=REGION)
    
    try:
        print("Eliminando stack...")
        cf_client.delete_stack(StackName=STACK_NAME)
        
        print("Esperando eliminación...")
        waiter = cf_client.get_waiter('stack_delete_complete')
        waiter.wait(StackName=STACK_NAME)
        
        print("Stack eliminado")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()