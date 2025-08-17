from servidor.servidor import chat_servidor


server = chat_servidor()
try:
    server.iniciar()
except KeyboardInterrupt:
    print("\nServidor encerrado.")