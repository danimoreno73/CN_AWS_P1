#!/usr/bin/env python3
"""
Script para desplegar la tabla DynamoDB
Uso: python scripts/deploy-dynamodb.py
"""

import boto3
import sys
import time

STACK_NAME = "notes-dynamodb"
TEMPLATE_FILE = "cloudformation/01-dynamodb.yml"
REGION = "us-east-1"

def main():
    print("Desplegando tabla DynamoDB...")
    print(f"Stack: {STACK_NAME}")
    print(f"Region: {REGION}\n")
    
    cf_client = boto3.client('cloudformation', region_name=REGION)
    
    # Leer template
    try:
        with open(TEMPLATE_FILE, 'r') as f:
            template_body = f.read()
    except FileNotFoundError:
        print(f"Error: No se encuentra el archivo {TEMPLATE_FILE}")
        sys.exit(1)
    
    # Validar template
    print("Validando template...")
    try:
        cf_client.validate_template(TemplateBody=template_body)
        print("Template válido\n")
    except Exception as e:
        print(f"Error: Template inválido - {e}")
        sys.exit(1)
    
    # Verificar si el stack existe
    stack_exists = False
    try:
        cf_client.describe_stacks(StackName=STACK_NAME)
        stack_exists = True
    except cf_client.exceptions.ClientError:
        pass
    
    try:
        if not stack_exists:
            # Crear stack
            print("Creando stack...")
            cf_client.create_stack(
                StackName=STACK_NAME,
                TemplateBody=template_body
            )
            
            print("Esperando a que se complete...")
            waiter = cf_client.get_waiter('stack_create_complete')
            waiter.wait(StackName=STACK_NAME)
            print("Stack creado exitosamente!\n")
        else:
            # Actualizar stack
            print("Stack existe, actualizando...")
            try:
                cf_client.update_stack(
                    StackName=STACK_NAME,
                    TemplateBody=template_body
                )
                
                print("Esperando actualización...")
                waiter = cf_client.get_waiter('stack_update_complete')
                waiter.wait(StackName=STACK_NAME)
                print("Stack actualizado!\n")
            except cf_client.exceptions.ClientError as e:
                if 'No updates are to be performed' in str(e):
                    print("No hay cambios para aplicar\n")
                else:
                    raise
        
        # Mostrar outputs
        print("Outputs:")
        response = cf_client.describe_stacks(StackName=STACK_NAME)
        outputs = response['Stacks'][0].get('Outputs', [])
        for output in outputs:
            print(f"  {output['OutputKey']}: {output['OutputValue']}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()