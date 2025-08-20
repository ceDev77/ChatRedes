import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import socket
import threading
import json
import time
from datetime import datetime

class ChatCliente:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Chat Cliente")
        self.root.geometry("800x600")
        
        # Configurações de conexão
        self.servidor_host = "localhost"
        self.servidor_porta = 2004
        self.socket_servidor = None
        self.apelido = None
        self.endereco_ip = self.get_local_ip()
        
        # Lista de usuários online
        self.usuarios_online = []
        
        # Janelas de chat ativas
        self.janelas_chat = {}
        
        # Thread de escuta do servidor
        self.thread_servidor = None
        
        # Lock para operações thread-safe
        self.lock = threading.Lock()
        
        self.criar_interface()
    
    def get_local_ip(self):
        """Obtém o IP local da máquina"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    

    
    def criar_interface(self):
        """Cria a interface principal do cliente"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configuração de grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Título
        titulo = ttk.Label(main_frame, text="Chat Cliente", font=("Arial", 16, "bold"))
        titulo.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Frame de conexão
        conexao_frame = ttk.LabelFrame(main_frame, text="Conexão com Servidor", padding="10")
        conexao_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Apelido
        ttk.Label(conexao_frame, text="Apelido:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.entry_apelido = ttk.Entry(conexao_frame, width=20)
        self.entry_apelido.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        # Botão conectar
        self.btn_conectar = ttk.Button(conexao_frame, text="Conectar", command=self.conectar_servidor)
        self.btn_conectar.grid(row=0, column=2, padx=(0, 10))
        
        # Botão atualizar
        self.btn_atualizar = ttk.Button(conexao_frame, text="Atualizar Lista", command=self.atualizar_lista, state="disabled")
        self.btn_atualizar.grid(row=0, column=3)
        
        # Status de conexão
        self.label_status = ttk.Label(conexao_frame, text="Desconectado", foreground="red")
        self.label_status.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))
        
        # Frame de usuários online
        usuarios_frame = ttk.LabelFrame(main_frame, text="Usuários Online", padding="10")
        usuarios_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Lista de usuários
        self.lista_usuarios = tk.Listbox(usuarios_frame, height=8)
        self.lista_usuarios.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Scrollbar para lista
        scrollbar = ttk.Scrollbar(usuarios_frame, orient=tk.VERTICAL, command=self.lista_usuarios.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.lista_usuarios.configure(yscrollcommand=scrollbar.set)
        
        # Botão para iniciar chat
        self.btn_chat = ttk.Button(usuarios_frame, text="Iniciar Chat", command=self.iniciar_chat, state="disabled")
        self.btn_chat.grid(row=0, column=2, padx=(10, 0))
        
        # Configurar grid do frame de usuários
        usuarios_frame.columnconfigure(0, weight=1)
        usuarios_frame.rowconfigure(0, weight=1)
        
        # Frame de mensagens do servidor
        msg_frame = ttk.LabelFrame(main_frame, text="Mensagens do Servidor", padding="10")
        msg_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Área de mensagens
        self.area_mensagens = scrolledtext.ScrolledText(msg_frame, height=10, state="disabled")
        self.area_mensagens.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid do frame de mensagens
        msg_frame.columnconfigure(0, weight=1)
        msg_frame.rowconfigure(0, weight=1)
        
        # Bind duplo clique na lista
        self.lista_usuarios.bind("<Double-Button-1>", lambda e: self.iniciar_chat())
    
    def conectar_servidor(self):
        """Conecta ao servidor e registra o usuário"""
        apelido = self.entry_apelido.get().strip()
        if not apelido:
            messagebox.showerror("Erro", "Digite um apelido!")
            return
        
        try:
            # Conectar ao servidor
            self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_servidor.connect((self.servidor_host, self.servidor_porta))
            
            # Registrar no servidor
            comando = f"REGISTER {apelido}\n"
            self.socket_servidor.sendall(comando.encode('utf-8'))
            
            self.apelido = apelido
            
            # Atualizar interface
            self.btn_conectar.config(state="disabled")
            self.entry_apelido.config(state="disabled")
            self.btn_atualizar.config(state="normal")
            self.btn_chat.config(state="normal")
            self.label_status.config(text="Conectado", foreground="green")
            
            # Iniciar thread de escuta do servidor
            self.thread_servidor = threading.Thread(target=self.escutar_servidor, daemon=True)
            self.thread_servidor.start()
            
            self.adicionar_mensagem("Sistema", f"Conectado ao servidor como '{apelido}'")
            
        except Exception as e:
            messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao servidor: {e}")
    
    def escutar_servidor(self):
        """Escuta mensagens do servidor"""
        buffer = ""
        try:
            while True:
                dados = self.socket_servidor.recv(1024)
                if not dados:
                    break
                
                buffer += dados.decode('utf-8', errors='ignore')
                
                while "\n" in buffer:
                    linha, buffer = buffer.split("\n", 1)
                    self.processar_mensagem_servidor(linha.strip())
                    
        except Exception as e:
            print(f"Erro na conexão com servidor: {e}")
        finally:
            self.desconectar_servidor()
    
    def processar_mensagem_servidor(self, mensagem):
        """Processa mensagens recebidas do servidor"""
        try:
            if mensagem.startswith("SERVIDOR:"):
                # Mensagem de broadcast do servidor
                self.adicionar_mensagem("Servidor", mensagem[9:])
            elif mensagem.startswith("{"):
                # Mensagem JSON
                dados = json.loads(mensagem)
                if dados.get("command") == "UPDATE_LIST":
                    self.atualizar_lista_usuarios(dados.get("client_list", []))
                elif dados.get("status") == "OK":
                    self.atualizar_lista_usuarios(dados.get("client_list", []))
            else:
                # Verificar se é uma mensagem de chat (formato: "remetente: mensagem")
                if ":" in mensagem and not mensagem.startswith("MSG_OK") and not mensagem.startswith("ERRO"):
                    # É uma mensagem de chat de outro usuário
                    self.processar_mensagem_chat(mensagem)
                else:
                    # Outras mensagens
                    self.adicionar_mensagem("Servidor", mensagem)
                
        except json.JSONDecodeError:
            self.adicionar_mensagem("Servidor", mensagem)
        except Exception as e:
            print(f"Erro ao processar mensagem: {e}")
    
    def processar_mensagem_chat(self, mensagem):
        """Processa mensagem de chat recebida do servidor"""
        try:
            # Extrair remetente e texto da mensagem
            if ":" in mensagem:
                remetente, texto = mensagem.split(":", 1)
                remetente = remetente.strip()
                texto = texto.strip()
                
                print(f"Mensagem de chat recebida de {remetente}: {texto}")
                
                # Abrir janela de chat automaticamente
                self.root.after(0, lambda: self.abrir_chat_automatico(remetente, texto))
        except Exception as e:
            print(f"Erro ao processar mensagem de chat: {e}")
    
    def atualizar_lista(self):
        """Solicita atualização da lista de usuários"""
        if self.socket_servidor:
            try:
                # Enviar comando para atualizar lista
                comando = "UPDATE_LIST\n"
                self.socket_servidor.sendall(comando.encode('utf-8'))
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao atualizar lista: {e}")
    
    def atualizar_lista_usuarios(self, usuarios):
        """Atualiza a lista de usuários na interface"""
        self.usuarios_online = [u for u in usuarios if u != self.apelido]
        
        # Atualizar interface na thread principal
        self.root.after(0, self._atualizar_lista_interface)
    
    def _atualizar_lista_interface(self):
        """Atualiza a interface da lista de usuários (deve ser chamada na thread principal)"""
        self.lista_usuarios.delete(0, tk.END)
        for usuario in self.usuarios_online:
            self.lista_usuarios.insert(tk.END, usuario)
    
    def iniciar_chat(self):
        """Inicia uma conversa com o usuário selecionado"""
        selecao = self.lista_usuarios.curselection()
        if not selecao:
            messagebox.showwarning("Aviso", "Selecione um usuário para conversar!")
            return
        
        usuario_destino = self.lista_usuarios.get(selecao[0])
        if usuario_destino == self.apelido:
            messagebox.showwarning("Aviso", "Você não pode conversar consigo mesmo!")
            return
        
        # Verificar se o usuário está online
        if usuario_destino not in self.usuarios_online:
            messagebox.showwarning("Aviso", "Usuário não está mais online!")
            return
        
        # Verificar se já existe uma janela de chat
        if usuario_destino in self.janelas_chat:
            self.janelas_chat[usuario_destino].deiconify()
            self.janelas_chat[usuario_destino].lift()
        else:
            # Criar nova janela de chat
            janela_chat = JanelaChat(self, usuario_destino)
            self.janelas_chat[usuario_destino] = janela_chat
    
    def adicionar_mensagem(self, remetente, mensagem):
        """Adiciona uma mensagem na área de mensagens"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        texto = f"[{timestamp}] {remetente}: {mensagem}\n"
        
        # Atualizar interface na thread principal
        self.root.after(0, lambda: self._adicionar_mensagem_interface(texto))
    
    def _adicionar_mensagem_interface(self, texto):
        """Adiciona mensagem na interface (deve ser chamada na thread principal)"""
        self.area_mensagens.config(state="normal")
        self.area_mensagens.insert(tk.END, texto)
        self.area_mensagens.see(tk.END)
        self.area_mensagens.config(state="disabled")
    

    
    def abrir_chat_automatico(self, remetente, mensagem):
        """Abre automaticamente uma janela de chat quando recebe mensagem"""
        if remetente not in self.janelas_chat:
            janela_chat = JanelaChat(self, remetente)
            self.janelas_chat[remetente] = janela_chat
        
        # Adicionar mensagem na janela
        self.janelas_chat[remetente].adicionar_mensagem_recebida(mensagem)
        self.janelas_chat[remetente].deiconify()
        self.janelas_chat[remetente].lift()
    
    def enviar_mensagem_servidor(self, destino, mensagem):
        """Envia mensagem via servidor para outro cliente"""
        try:
            if self.socket_servidor:
                # Enviar mensagem para o servidor
                comando = f"MSG {destino} {mensagem}\n"
                self.socket_servidor.sendall(comando.encode('utf-8'))
                
                print(f"Mensagem enviada para {destino} via servidor")
                return True
                
        except Exception as e:
            print(f"Erro ao enviar mensagem para {destino}: {e}")
            return False
    
    def desconectar_servidor(self):
        """Desconecta do servidor"""
        if self.socket_servidor:
            self.socket_servidor.close()
            self.socket_servidor = None
        
        # Atualizar interface
        self.btn_conectar.config(state="normal")
        self.entry_apelido.config(state="normal")
        self.btn_atualizar.config(state="disabled")
        self.btn_chat.config(state="disabled")
        self.label_status.config(text="Desconectado", foreground="red")
        
        self.adicionar_mensagem("Sistema", "Desconectado do servidor")
    
    def executar(self):
        """Executa a aplicação"""
        self.root.mainloop()


class JanelaChat:
    def __init__(self, cliente_principal, usuario_destino):
        self.cliente_principal = cliente_principal
        self.usuario_destino = usuario_destino
        
        # Criar janela
        self.janela = tk.Toplevel(cliente_principal.root)
        self.janela.title(f"Chat com {usuario_destino}")
        self.janela.geometry("500x400")
        
        # Configurar protocolo de fechamento
        self.janela.protocol("WM_DELETE_WINDOW", self.fechar_janela)
        
        # Variáveis para mover a janela
        self.x_offset = 0
        self.y_offset = 0
        self.dragging = False
        
        self.criar_interface()
        self.configurar_movimento()
        self.posicionar_janela()
    
    def criar_interface(self):
        """Cria a interface da janela de chat"""
        # Frame principal
        main_frame = ttk.Frame(self.janela, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.janela.columnconfigure(0, weight=1)
        self.janela.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)  # Mudou de 1 para 2
        
        # Barra de título personalizada
        titulo_frame = ttk.Frame(main_frame)
        titulo_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        titulo_frame.columnconfigure(0, weight=1)
        
        # Título com ícone de movimento
        titulo = ttk.Label(titulo_frame, text=f"💬 Chat com {self.usuario_destino}", 
                          font=("Arial", 12, "bold"), foreground="blue")
        titulo.grid(row=0, column=0, sticky=tk.W)
        
        # Dica de movimento
        dica = ttk.Label(titulo_frame, text="(Arraste para mover • Ctrl+C para centralizar manualmente)", 
                        font=("Arial", 8), foreground="gray")
        dica.grid(row=1, column=0, sticky=tk.W, pady=(2, 0))
        
        # Área de mensagens
        self.area_mensagens = scrolledtext.ScrolledText(main_frame, height=15, state="disabled")
        self.area_mensagens.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Frame de entrada
        entrada_frame = ttk.Frame(main_frame)
        entrada_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        entrada_frame.columnconfigure(0, weight=1)
        
        # Campo de mensagem
        self.entry_mensagem = ttk.Entry(entrada_frame)
        self.entry_mensagem.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Botão enviar
        btn_enviar = ttk.Button(entrada_frame, text="Enviar", command=self.enviar_mensagem)
        btn_enviar.grid(row=0, column=1)
        
        # Bind Enter para enviar
        self.entry_mensagem.bind("<Return>", lambda e: self.enviar_mensagem())
        
        # Bind Ctrl+C para centralizar janela
        self.janela.bind("<Control-c>", lambda e: self.centralizar_janela())
        
        # Focar no campo de mensagem
        self.entry_mensagem.focus()
    
    def configurar_movimento(self):
        """Configura os eventos para mover a janela"""
        # Bind eventos de mouse na janela inteira
        self.janela.bind("<Button-1>", self.iniciar_arraste)
        self.janela.bind("<B1-Motion>", self.arrastar_janela)
        self.janela.bind("<ButtonRelease-1>", self.parar_arraste)
        
        # Bind eventos específicos na área de título
        self.janela.bind("<Enter>", self.on_enter)
        self.janela.bind("<Leave>", self.on_leave)
        
        # Configurar cursor para indicar que pode mover
        self.janela.config(cursor="fleur")  # Cursor de movimento
    
    def enviar_mensagem(self):
        """Envia uma mensagem"""
        mensagem = self.entry_mensagem.get().strip()
        if not mensagem:
            return
        
        # Verificar se o destinatário ainda está online
        if self.usuario_destino not in self.cliente_principal.usuarios_online:
            messagebox.showerror("Erro", "Usuário não está mais online!")
            return
        
        # Adicionar mensagem na área
        self.adicionar_mensagem_enviada(mensagem)
        
        # Enviar via servidor
        if self.cliente_principal.enviar_mensagem_servidor(self.usuario_destino, mensagem):
            self.entry_mensagem.delete(0, tk.END)
        else:
            messagebox.showerror("Erro", "Não foi possível enviar a mensagem!")
    
    def adicionar_mensagem_enviada(self, mensagem):
        """Adiciona uma mensagem enviada na área"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        texto = f"[{timestamp}] Você: {mensagem}\n"
        
        self.area_mensagens.config(state="normal")
        self.area_mensagens.insert(tk.END, texto)
        self.area_mensagens.see(tk.END)
        self.area_mensagens.config(state="disabled")
    
    def adicionar_mensagem_recebida(self, mensagem):
        """Adiciona uma mensagem recebida na área"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        texto = f"[{timestamp}] {self.usuario_destino}: {mensagem}\n"
        
        self.area_mensagens.config(state="normal")
        self.area_mensagens.insert(tk.END, texto)
        self.area_mensagens.see(tk.END)
        self.area_mensagens.config(state="disabled")
    
    def fechar_janela(self):
        """Fecha a janela de chat"""
        self.janela.withdraw()  # Esconde em vez de destruir
    
    def iniciar_arraste(self, event):
        """Inicia o arraste da janela"""
        # Permitir arraste clicando em qualquer lugar da janela
        self.dragging = True
        self.x_offset = event.x
        self.y_offset = event.y
    
    def arrastar_janela(self, event):
        """Arrasta a janela durante o movimento do mouse"""
        if self.dragging:
            x = self.janela.winfo_x() + (event.x - self.x_offset)
            y = self.janela.winfo_y() + (event.y - self.y_offset)
            self.janela.geometry(f"+{x}+{y}")
    
    def parar_arraste(self, event):
        """Para o arraste da janela"""
        self.dragging = False
    
    def on_enter(self, event):
        """Quando o mouse entra na janela"""
        # Mudar cursor para indicar que pode mover
        self.janela.config(cursor="fleur")
    
    def on_leave(self, event):
        """Quando o mouse sai da janela"""
        # Restaurar cursor padrão
        self.janela.config(cursor="")
    
    def posicionar_janela(self):
        """Posiciona a janela de forma inteligente para evitar sobreposição"""
        # Obter posição da janela principal
        main_x = self.cliente_principal.root.winfo_x()
        main_y = self.cliente_principal.root.winfo_y()
        
        # Calcular posição para a nova janela (deslocada)
        offset_x = 50
        offset_y = 50
        
        # Contar quantas janelas já existem para posicionar adequadamente
        num_janelas = len(self.cliente_principal.janelas_chat)
        offset_x += (num_janelas * 30)
        offset_y += (num_janelas * 30)
        
        # Posicionar a janela
        nova_x = main_x + offset_x
        nova_y = main_y + offset_y
        
        # Garantir que a janela não saia da tela
        screen_width = self.janela.winfo_screenwidth()
        screen_height = self.janela.winfo_screenheight()
        
        if nova_x + 500 > screen_width:
            nova_x = screen_width - 520
        if nova_y + 400 > screen_height:
            nova_y = screen_height - 420
        
        self.janela.geometry(f"500x400+{nova_x}+{nova_y}")
            
    def centralizar_janela(self):
        """Centraliza a janela na tela"""
        # Obter dimensões da tela
        screen_width = self.janela.winfo_screenwidth()
        screen_height = self.janela.winfo_screenheight()
        
        # Calcular posição central
        x = (screen_width - 500) // 2
        y = (screen_height - 400) // 2
        
        # Posicionar a janela
        self.janela.geometry(f"500x400+{x}+{y}")


if __name__ == "__main__":
    app = ChatCliente()
    app.executar() 