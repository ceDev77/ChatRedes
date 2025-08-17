import threading


class Cliente:
    def __init__(self, apelido, socket, endereco):
        self.apelido = apelido
        self.socket = socket
        self.endereco = endereco
        self.lock = threading.Lock()

    def enviar(self, mensagem):
        """Envia uma mensagem para este cliente"""
        try:
            with self.lock:
                self.socket.sendall((mensagem + "\n").encode('utf-8'))
        except:
            pass

    def desconectar(self):
        """Fecha a conexão do cliente"""
        try:
            self.socket.close()
        except:
            pass
