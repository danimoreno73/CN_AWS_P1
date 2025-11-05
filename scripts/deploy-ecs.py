#!/usr/bin/env python3
"""
Script para desplegar ECS Fargate (Opcion A)
Uso: python scripts/deploy-ecs.py
"""

import boto3
import sys

STACK_NAME = "notes-ecs-option-a"
TEMPLATE_FILE = "cloudformation/03-ecs-option-a.yml"
REGION = "us-east-1"

def get_default_vpc_and_subnets():
    """Obtener VPC por defecto y sus subnets"""
    ec2 = boto3.client('ec2', region_name=REGION)
    
    # Obtener VPC por defecto
    vpcs = ec2.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])
    if not vpcs['Vpcs']:
        print("Error: No se encontró VPC por defecto")
        sys.exit(1)
    
    vpc_id = vpcs['Vpcs'][0]['VpcId']
    
    # Obtener subnets de la VPC
    subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    subnet_ids = [subnet['SubnetId'] for subnet in subnets['Subnets']]
    
    if len(subnet_ids) < 2:
        print("Error: Se necesitan al menos 2 subnets")
        sys.exit(1)
    
    return vpc_id, subnet_ids[:2]

def get_ecr_image_uri():
    """Obtener URI de la imagen en ECR"""
    cf_client = boto3.client('cloudformation', region_name=REGION)
    
    try:
        response = cf_client.describe_stacks(StackName='notes-ecr')
        outputs = response['Stacks'][0]['Outputs']
        
        for output in outputs:
            if output['OutputKey'] == 'RepositoryUri':
                return f"{output['OutputValue']}:latest"
        
        print("Error: No se encontró URI del repositorio ECR")
        sys.exit(1)
        
    except Exception as e:
        print(f"Error: Primero debes desplegar ECR (deploy-ecr.py)")
        print(f"Detalle: {e}")
        sys.exit(1)

def main():
    print("Desplegando ECS Fargate (Opción A)...")
    print(f"Stack: {STACK_NAME}")
    print(f"Region: {REGION}\n")
    
    # Obtener VPC y subnets
    print("Obteniendo VPC y subnets...")
    vpc_id, subnet_ids = get_default_vpc_and_subnets()
    print(f"VPC: {vpc_id}")
    print(f"Subnets: {', '.join(subnet_ids)}\n")
    
    # Obtener imagen ECR
    print("Obteniendo imagen ECR...")
    image_uri = get_ecr_image_uri()
    print(f"Imagen: {image_uri}\n")
    
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
    
    # Parámetros
    parameters = [
        {'ParameterKey': 'VpcId', 'ParameterValue': vpc_id},
        {'ParameterKey': 'SubnetIds', 'ParameterValue': ','.join(subnet_ids)},
        {'ParameterKey': 'ImageUri', 'ParameterValue': image_uri},
        {'ParameterKey': 'TableName', 'ParameterValue': 'Notes'}
    ]
    
    try:
        if not stack_exists:
            # Crear stack
            print("Creando stack (esto puede tardar 5-10 minutos)...")
            cf_client.create_stack(
                StackName=STACK_NAME,
                TemplateBody=template_body,
                Parameters=parameters,
                Capabilities=['CAPABILITY_IAM']
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
                    TemplateBody=template_body,
                    Parameters=parameters,
                    Capabilities=['CAPABILITY_IAM']
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
        print("=" * 60)
        print("INFORMACIÓN IMPORTANTE")
        print("=" * 60)
        response = cf_client.describe_stacks(StackName=STACK_NAME)
        outputs = response['Stacks'][0].get('Outputs', [])
        
        api_url = None
        api_key = None
        
        for output in outputs:
            print(f"{output['OutputKey']}: {output['OutputValue']}")
            if output['OutputKey'] == 'ApiUrl':
                api_url = output['OutputValue']
            elif output['OutputKey'] == 'ApiKey':
                api_key = output['OutputValue']
        
        print("\n" + "=" * 60)
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
            print(f'  -d \'{{"title": "Test", "content": "Prueba ECS", "tags": ["test"]}}\'')
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()