#!/usr/bin/env python3
"""
Script para desplegar funciones Lambda (Opcion B)
Uso: python scripts/deploy-lambda.py
"""

import boto3
import os
import sys
import time

STACK_NAME = "notes-lambda-option-b"
TEMPLATE_FILE = "cloudformation/04-lambda-option-b.yml"
REGION = "us-east-1"
LAMBDA_PACKAGES_DIR = "lambda-packages"


def check_packages_exist():
    """Verificar que existen los paquetes Lambda"""
    functions = ["create_note", "get_note", "list_notes", "update_note", "delete_note"]
    
    if not os.path.exists(LAMBDA_PACKAGES_DIR):
        print(f"Error: Directorio {LAMBDA_PACKAGES_DIR}/ no existe")
        print("Ejecuta primero: python scripts/package-lambdas.py")
        sys.exit(1)
    
    for func in functions:
        zip_file = os.path.join(LAMBDA_PACKAGES_DIR, f"{func}.zip")
        if not os.path.exists(zip_file):
            print(f"Error: No se encuentra {zip_file}")
            print("Ejecuta primero: python scripts/package-lambdas.py")
            sys.exit(1)
    
    print("✓ Todos los paquetes Lambda encontrados\n")


def create_bucket_if_needed(s3_client, bucket_name):
    """Crear bucket S3 si no existe"""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✓ Bucket {bucket_name} ya existe\n")
    except:
        print(f"Creando bucket {bucket_name}...")
        s3_client.create_bucket(Bucket=bucket_name)
        print(f"✓ Bucket creado\n")


def upload_lambda_packages(bucket_name):
    """Subir paquetes Lambda a S3"""
    s3_client = boto3.client('s3', region_name=REGION)
    
    functions = ["create_note", "get_note", "list_notes", "update_note", "delete_note"]
    
    print("Subiendo paquetes Lambda a S3...")
    for func in functions:
        zip_file = os.path.join(LAMBDA_PACKAGES_DIR, f"{func}.zip")
        s3_key = f"functions/{func}.zip"
        
        print(f"  Subiendo {func}.zip...")
        s3_client.upload_file(zip_file, bucket_name, s3_key)
        print(f"  ✓ {s3_key}")
    
    print("\n✓ Todos los paquetes subidos\n")


def deploy_stack():
    """Desplegar stack de CloudFormation"""
    print("Desplegando funciones Lambda (Opción B)...")
    print(f"Stack: {STACK_NAME}")
    print(f"Region: {REGION}\n")
    
    cf_client = boto3.client('cloudformation', region_name=REGION)
    
    # Leer template
    try:
        with open(TEMPLATE_FILE, 'r') as f:
            template_body = f.read()
    except FileNotFoundError:
        print(f"Error: No se encuentra {TEMPLATE_FILE}")
        sys.exit(1)
    
    # Validar template
    print("Validando template...")
    try:
        cf_client.validate_template(TemplateBody=template_body)
        print("✓ Template válido\n")
    except Exception as e:
        print(f"Error: Template inválido - {e}")
        sys.exit(1)
    
    # Obtener el Account ID para el nombre del bucket
    print("Obteniendo Account ID de AWS...")
    try:
        sts_client = boto3.client('sts', region_name=REGION)
        account_id = sts_client.get_caller_identity().get('Account')
        if not account_id:
            raise Exception("No se pudo obtener Account ID")
        print(f"✓ Account ID: {account_id}\n")
    except Exception as e:
        print(f"Error obteniendo Account ID: {e}")
        print("Asegúrate de que tus credenciales de AWS son correctas.")
        sys.exit(1)
        
    # Subir ZIPs a S3
    print("\nSubiendo código Lambda a S3...")
    s3_client = boto3.client('s3', region_name=REGION)
    
    # Nombre del bucket (debe coincidir con el CloudFormation)
    bucket_name = f'notes-lambda-deployment-{account_id}'
    
    # Crear bucket si no existe
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"  Bucket {bucket_name} ya existe")
    except:
        print(f"  Creando bucket {bucket_name}...")
        s3_client.create_bucket(Bucket=bucket_name)
    
    # Subir cada ZIP
    lambda_packages_dir = os.path.join(os.path.dirname(__file__), '..', 'lambda-packages')
    functions = ['create_note', 'get_note', 'list_notes', 'update_note', 'delete_note']
    
    for func in functions:
        zip_file = os.path.join(lambda_packages_dir, f'{func}.zip')
        s3_key = f'functions/{func}.zip'
        
        print(f"  Subiendo {func}.zip...")
        s3_client.upload_file(zip_file, bucket_name, s3_key)
    
    print("✓ Código Lambda subido a S3\n")

    # Verificar si stack existe
    stack_exists = False
    try:
        cf_client.describe_stacks(StackName=STACK_NAME)
        stack_exists = True
    except:
        pass
    
    # Parámetros
    parameters = [
        {'ParameterKey': 'TableName', 'ParameterValue': 'Notes'}
    ]
    
    try:
        if not stack_exists:
            # Crear stack
            print("Creando stack (esto puede tardar 3-5 minutos)...")
            cf_client.create_stack(
                StackName=STACK_NAME,
                TemplateBody=template_body,
                Parameters=parameters,
                Capabilities=['CAPABILITY_NAMED_IAM']
            )
            
            print("Esperando creación del stack...")
            waiter = cf_client.get_waiter('stack_create_complete')
            waiter.wait(StackName=STACK_NAME)
            print("✓ Stack creado exitosamente!\n")
        else:
            # Actualizar stack
            print("Stack existe, actualizando...")
            try:
                cf_client.update_stack(
                    StackName=STACK_NAME,
                    TemplateBody=template_body,
                    Parameters=parameters,
                    Capabilities=['CAPABILITY_NAMED_IAM']
                )
                
                print("Esperando actualización...")
                waiter = cf_client.get_waiter('stack_update_complete')
                waiter.wait(StackName=STACK_NAME)
                print("✓ Stack actualizado!\n")
            except Exception as e:
                if 'No updates are to be performed' in str(e):
                    print("⚠ No hay cambios para aplicar\n")
                else:
                    raise
        
        # Mostrar outputs
        print("=" * 60)
        print("INFORMACIÓN IMPORTANTE")
        print("=" * 60)
        response = cf_client.describe_stacks(StackName=STACK_NAME)
        outputs = response['Stacks'][0].get('Outputs', [])
        
        api_url = None
        api_key = None
        bucket_name = None
        
        for output in outputs:
            print(f"{output['OutputKey']}: {output['OutputValue']}")
            if output['OutputKey'] == 'ApiUrl':
                api_url = output['OutputValue']
            elif output['OutputKey'] == 'ApiKey':
                api_key = output['OutputValue']
            elif output['OutputKey'] == 'DeploymentBucket':
                bucket_name = output['OutputValue']
        
        # Ahora subir los paquetes Lambda
        if bucket_name:
            print(f"\n{'=' * 60}")
            print("SUBIENDO CÓDIGO LAMBDA")
            print("=" * 60)
            upload_lambda_packages(bucket_name)
            
            # Actualizar código de las funciones
            print("Actualizando código de las funciones Lambda...")
            lambda_client = boto3.client('lambda', region_name=REGION)
            
            functions = {
                'CreateNoteFunction': 'create_note',
                'GetNoteFunction': 'get_note',
                'ListNotesFunction': 'list_notes',
                'UpdateNoteFunction': 'update_note',
                'DeleteNoteFunction': 'delete_note'
            }
            
            for func_name, zip_name in functions.items():
                print(f"  Actualizando {func_name}...")
                lambda_client.update_function_code(
                    FunctionName=func_name,
                    S3Bucket=bucket_name,
                    S3Key=f"functions/{zip_name}.zip"
                )
            
            print("\n✓ Código actualizado en todas las funciones\n")
        
        # Mostrar ejemplo de uso
        print("=" * 60)
        print("PRUEBA LA API")
        print("=" * 60)
        
        if api_url and api_key:
            # Obtener valor de API Key
            apigw = boto3.client('apigateway', region_name=REGION)
            key_value = apigw.get_api_key(apiKey=api_key, includeValue=True)['value']
            
            print(f"\nURL: {api_url}")
            print(f"API Key: {key_value}")
            print(f"\nEjemplo:")
            print(f'curl -X POST {api_url}/notes \\')
            print(f'  -H "x-api-key: {key_value}" \\')
            print(f'  -H "Content-Type: application/json" \\')
            print(f'  -d \'{{"title": "Test Lambda", "content": "Desde Lambda!", "tags": ["lambda"]}}\'')
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    print("=" * 60)
    print("DESPLIEGUE DE LAMBDA (OPCIÓN B)")
    print("=" * 60)
    print()
    
    # Verificar que existen los paquetes
    check_packages_exist()
    
    # Desplegar stack
    deploy_stack()


if __name__ == '__main__':
    main()