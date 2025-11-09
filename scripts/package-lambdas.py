#!/usr/bin/env python3
"""
Script para empaquetar las funciones Lambda en archivos ZIP
Uso: python scripts/package-lambdas.py
"""

import os
import shutil
import zipfile
import subprocess
import sys

LAMBDA_DIR = "app-lambda"
OUTPUT_DIR = "lambda-packages"
FUNCTIONS = ["create_note", "get_note", "list_notes", "update_note", "delete_note"]


def create_output_dir():
    """Crear directorio de salida"""
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)
    print(f"Directorio {OUTPUT_DIR}/ creado\n")


def install_dependencies(function_name, temp_dir):
    """Instalar dependencias en un directorio temporal"""
    requirements_file = os.path.join(LAMBDA_DIR, function_name, "requirements.txt")
    
    if os.path.exists(requirements_file):
        print(f"  Instalando dependencias...")
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "-r", requirements_file,
            "-t", temp_dir,
            "--quiet"
        ], check=True)


def copy_shared_code(temp_dir):
    """Copiar código compartido"""
    shared_src = os.path.join(LAMBDA_DIR, "shared")
    shared_dst = os.path.join(temp_dir, "shared")
    
    if os.path.exists(shared_src):
        shutil.copytree(shared_src, shared_dst)


def create_zip(function_name):
    """Crear archivo ZIP para una función Lambda"""
    print(f"Empaquetando {function_name}...")
    
    # Directorio temporal
    temp_dir = os.path.join(OUTPUT_DIR, f"{function_name}_temp")
    os.makedirs(temp_dir)
    
    # Instalar dependencias
    install_dependencies(function_name, temp_dir)
    
    # Copiar código compartido
    copy_shared_code(temp_dir)
    
    # Copiar handler
    handler_src = os.path.join(LAMBDA_DIR, function_name, "handler.py")
    handler_dst = os.path.join(temp_dir, "handler.py")
    shutil.copy(handler_src, handler_dst)
    
    # Crear ZIP
    zip_path = os.path.join(OUTPUT_DIR, f"{function_name}.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)
    
    # Limpiar directorio temporal
    shutil.rmtree(temp_dir)
    
    # Mostrar tamaño
    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"  ✓ Creado: {zip_path} ({size_mb:.2f} MB)\n")


def main():
    print("=" * 60)
    print("EMPAQUETADO DE FUNCIONES LAMBDA")
    print("=" * 60)
    print()
    
    # Crear directorio de salida
    create_output_dir()
    
    # Empaquetar cada función
    for function in FUNCTIONS:
        create_zip(function)
    
    print("=" * 60)
    print("EMPAQUETADO COMPLETADO")
    print("=" * 60)
    print(f"\nArchivos ZIP creados en: {OUTPUT_DIR}/")
    print("\nPróximo paso:")
    print("  python scripts/deploy-lambda.py")


if __name__ == '__main__':
    main()