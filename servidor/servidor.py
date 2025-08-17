import socket
import threading
import json
from cliente.cliente import Cliente

class chat_servidor:
    def __init__(self, host='0.0.0.0', porta=2004):
        self.host = host
        self.porta = porta
        self.socket_servidor = None
        self.lock = threading.Lock()
        self.clientes = {}  # apelido -> Cliente

    def iniciar(self):
        self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.socket_servidor.bind((self.host, self.porta))
        self.socket_servidor.listen(5)
        print(f"Servidor iniciado em {self.host}:{self.porta}. Aguardando conexões...")

        while True:
            socket_cliente, end_cliente = self.socket_servidor.accept()
            threading.Thread(target=self.conectar_cliente, args=(socket_cliente, end_cliente)).start()

    def broadcast(self, mensagem):
        """Envia uma mensagem para todos os clientes conectados"""
        with self.lock:
            for cliente in self.clientes.values():
                cliente.enviar(mensagem)

    def conectar_cliente(self, socket_cliente, end):
        apelido = None
        buffer = ""
        try:
            print(f"\n--- Nova conexão de {end} ---")

            while True:
                dados = socket_cliente.recv(1024)
                if not dados:
                    break

                buffer += dados.decode('utf-8', errors='ignore')

                while "\n" in buffer:
                    linha, buffer = buffer.split("\n", 1)
                    comando = linha.strip()
                    print(f"Dados recebidos: '{comando}'")
                    apelido = self.processar_comando(comando, apelido, socket_cliente, end)

        except Exception as e:
            print(f"ERRO com {end}: {e}")
        finally:
            if apelido:
                with self.lock:
                    if apelido in self.clientes:
                        self.clientes[apelido].desconectar()
                        del self.clientes[apelido]
                self.broadcast(f"SERVIDOR: {apelido} saiu do chat!")
                lista_msg = json.dumps({
                    "command": "UPDATE_LIST",
                    "client_list": list(self.clientes.keys())
                }) + "\n"
                self.broadcast(lista_msg)

            socket_cliente.close()
            print(f"Conexão encerrada: {end}")

    def processar_comando(self, comando, apelido, socket_cliente, end):
        if comando.startswith("REGISTER"):
            try:
                apelido = comando.split()[1]
                cliente = Cliente(apelido, socket_cliente, end)

                with self.lock:
                    self.clientes[apelido] = cliente

                resposta = json.dumps({
                    "status": "OK",
                    "client_list": list(self.clientes.keys())
                }) + "\n"
                cliente.enviar(resposta)

                self.broadcast(f"SERVIDOR: {apelido} entrou no chat!")
                lista_msg = json.dumps({
                    "command": "UPDATE_LIST",
                    "client_list": list(self.clientes.keys())
                }) + "\n"
                self.broadcast(lista_msg)

            except IndexError:
                socket_cliente.sendall("Formato inválido. Use: REGISTER apelido\n".encode('utf-8'))

        elif comando.startswith("MSG"):
            try:
                _, destino, mensagem = comando.split(" ", 2)
                with self.lock:
                    if destino in self.clientes:
                        self.clientes[destino].enviar(f"{apelido}: {mensagem}")
                    else:
                        socket_cliente.sendall("ERRO: Destino não encontrado\n".encode('utf-8'))
            except Exception as e:
                socket_cliente.sendall(f"ERRO: {e}\n".encode('utf-8'))

        return apelido
