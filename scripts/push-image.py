#!/usr/bin/env python3
"""
Script para construir y subir imagen Docker a ECR
Uso: python scripts/push-image.py
"""

import boto3
import subprocess
import sys
import base64

REGION = "us-east-1"
STACK_NAME = "notes-ecr"
IMAGE_TAG = "latest"

def run_command(command, shell=False):
    """Ejecutar comando y mostrar output"""
    print(f"Ejecutando: {command if isinstance(command, str) else ' '.join(command)}")
    result = subprocess.run(
        command,
        shell=shell,
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    if result.returncode != 0:
        print(f"Error: Comando falló con código {result.returncode}")
        sys.exit(1)
    
    return result

def main():
    print("Construyendo y subiendo imagen Docker a ECR...\n")
    
    # Obtener URI del repositorio desde CloudFormation
    cf_client = boto3.client('cloudformation', region_name=REGION)
    
    try:
        response = cf_client.describe_stacks(StackName=STACK_NAME)
        outputs = response['Stacks'][0]['Outputs']
        
        repo_uri = None
        for output in outputs:
            if output['OutputKey'] == 'RepositoryUri':
                repo_uri = output['OutputValue']
                break
        
        if not repo_uri:
            print("Error: No se encontró el URI del repositorio")
            sys.exit(1)
        
        print(f"Repositorio ECR: {repo_uri}\n")
        
    except Exception as e:
        print(f"Error obteniendo información del stack: {e}")
        print("Asegúrate de haber desplegado el stack ECR primero (deploy-ecr.py)")
        sys.exit(1)
    
    # Autenticarse en ECR
    print("Autenticando con ECR...")
    ecr_client = boto3.client('ecr', region_name=REGION)
    
    try:
        token_response = ecr_client.get_authorization_token()
        token = token_response['authorizationData'][0]['authorizationToken']
        endpoint = token_response['authorizationData'][0]['proxyEndpoint']
        
        # Decodificar token
        decoded_token = base64.b64decode(token).decode('utf-8')
        username, password = decoded_token.split(':')
        
        # Login docker
        login_cmd = f'echo {password} | docker login --username {username} --password-stdin {endpoint}'
        run_command(login_cmd, shell=True)
        print("Autenticación exitosa\n")
        
    except Exception as e:
        print(f"Error en autenticación: {e}")
        sys.exit(1)
    
    # Construir imagen
    print("Construyendo imagen Docker...")
    image_name = f"{repo_uri}:{IMAGE_TAG}"
    
    run_command(['docker', 'build', '-t', image_name, 'app-ecs/'])
    print("Imagen construida exitosamente\n")
    
    # Subir imagen
    print("Subiendo imagen a ECR...")
    run_command(['docker', 'push', image_name])
    print("\nImagen subida exitosamente!")
    print(f"URI completa: {image_name}")

if __name__ == '__main__':
    main()