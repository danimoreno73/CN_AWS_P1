#!/usr/bin/env python3
"""
Script para eliminar el stack de ECS
Uso: python scripts/cleanup-ecs.py
"""

import boto3
import sys

STACK_NAME = "notes-ecs-option-a"
REGION = "us-east-1"

def main():
    print("ADVERTENCIA: Esto eliminará el stack de ECS Fargate")
    confirm = input("¿Continuar? (si/no): ")
    
    if confirm.lower() != 'si':
        print("Cancelado")
        sys.exit(0)
    
    cf_client = boto3.client('cloudformation', region_name=REGION)
    
    try:
        print("Eliminando stack (puede tardar 5-10 minutos)...")
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