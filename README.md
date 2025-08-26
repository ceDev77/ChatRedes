# Sistema de Chats

Sistema de chat em tempo real desenvolvido em Python com interface gráfica Tkinter.

## Instruções

### 1. Inicie o Servidor
```bash
python3 main.py
```
**Aguarde a mensagem:** `Servidor iniciado em 0.0.0.0:2004. Aguardando conexões...`

### 2. Abra o Primeiro Cliente
```bash
# Em um novo terminal
python3 cliente.cliente_app
```
- Digite um apelido (ex: "João")
- Clique em "Conectar"

### 3. Abra o Segundo Cliente
```bash
# Em outro terminal  
python3 cliente.cliente_app
```
- Digite outro apelido (ex: "José")
- Clique em "Conectar"

### 4. Teste o Chat
1. Selecione "José" na lista e clique "Iniciar Chat"
2. Digite uma mensagem e pressione Enter
3. No cliente "José": a janela de chat abrirá automaticamente
4. Agora os dois usuários podem se comunicar

---

## Estrutura do Projeto

```
ChatRedes/
├── main.py              # Servidor
├── servidor/            # Módulos do servidor
├── cliente/             # Módulos do cliente
└── imagens/            # Prints dos testes realizados
```

