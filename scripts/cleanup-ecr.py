#!/usr/bin/env python3
"""
Script para eliminar el stack de ECR
Uso: python scripts/cleanup-ecr.py
"""

import boto3
import sys

STACK_NAME = "notes-ecr"
REGION = "us-east-1"
REPOSITORY_NAME = "notes-app"

def main():
    print("ADVERTENCIA: Esto eliminará el repositorio ECR y todas las imágenes")
    confirm = input("¿Continuar? (si/no): ")
    
    if confirm.lower() != 'si':
        print("Cancelado")
        sys.exit(0)
    
    ecr_client = boto3.client('ecr', region_name=REGION)
    cf_client = boto3.client('cloudformation', region_name=REGION)
    
    try:
        # Primero eliminar todas las imágenes del repositorio
        print("Eliminando imágenes del repositorio...")
        try:
            images = ecr_client.list_images(repositoryName=REPOSITORY_NAME)
            image_ids = images.get('imageIds', [])
            
            if image_ids:
                ecr_client.batch_delete_image(
                    repositoryName=REPOSITORY_NAME,
                    imageIds=image_ids
                )
                print(f"Eliminadas {len(image_ids)} imágenes")
            else:
                print("No hay imágenes para eliminar")
        except ecr_client.exceptions.RepositoryNotFoundException:
            print("Repositorio no existe")
        
        # Eliminar stack
        print("\nEliminando stack...")
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