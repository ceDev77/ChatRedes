#!/usr/bin/env python3
"""
Cliente de Chat - Trabalho de Redes
Executa a aplicação cliente com interface gráfica
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from cliente_app import ChatCliente

if __name__ == "__main__":
    print("Iniciando Cliente de Chat...")
    print("Certifique-se de que o servidor está rodando na porta 2004")
    print("=" * 50)
    
    try:
        app = ChatCliente()
        app.executar()
    except KeyboardInterrupt:
        print("\nCliente encerrado pelo usuário.")
    except Exception as e:
        print(f"Erro ao executar cliente: {e}") 