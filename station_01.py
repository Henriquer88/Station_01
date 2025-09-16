import serial
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import tkinter as tk
from tkinter import ttk, messagebox
import time

# Variáveis globais para armazenar dados das medições
dados_umidade = []
dados_temperatura = []
dados_pressao = []
dados_ruido = []
dados_iluminancia = []
dados_chuva = []
dados_vento_velocidade = []
dados_vento_direcao = []
tempos = []

# Função para enviar comando e tratar exceções de conexão serial
def enviar_comando(comando):
    try:
        comando_bytes = bytes.fromhex(comando)
        with serial.Serial(port='COM15', baudrate=4800, timeout=1) as ser:
            ser.write(comando_bytes)
            resposta = ser.read(7)
            return resposta
    except serial.SerialException as e:
        messagebox.showerror("Erro de Conexão Serial", f"Erro ao acessar a porta COM: {e}")
        return None

def interpretar_resposta(resposta, tipo):
    if resposta and len(resposta) == 7:
        valor_hex = resposta[3:5]
        valor_int = int.from_bytes(valor_hex, byteorder='big')
        if tipo in ['iluminancia', 'chuva', 'vento_direcao']:
            return valor_int
        elif tipo == 'vento_velocidade':
            return valor_int / 100  # Ajustar para a unidade correta
        else:
            return valor_int / 10
    return None

# Comandos
comandos = {
    'umidade': "01 03 01 f8 00 01 04 07",
    'temperatura': "01 03 01 f9 00 01 55 c7",
    'pressao': "01 03 01 fd 00 01 14 06",
    'ruido': "01 03 01 fa 00 01 a5 c7",
    'iluminancia': "01 03 02 00 00 01 85 b2",
    'chuva': "01 03 02 01 00 01 d4 72",
    'vento_velocidade': "01 03 01 f4 00 01 c4 04",
    'vento_direcao': "01 03 01 f5 00 01 95 c4"
}

def atualizar_medicoes(i):
    tempo_atual = time.strftime("%H:%M:%S")

    # Enviar comandos e obter medições, substituindo None por 0
    umidade = interpretar_resposta(enviar_comando(comandos['umidade']), 'umidade') or 0
    temperatura = interpretar_resposta(enviar_comando(comandos['temperatura']), 'temperatura') or 0
    pressao = interpretar_resposta(enviar_comando(comandos['pressao']), 'pressao') or 0
    ruido = interpretar_resposta(enviar_comando(comandos['ruido']), 'ruido') or 0
    iluminancia = interpretar_resposta(enviar_comando(comandos['iluminancia']), 'iluminancia') or 0
    chuva = interpretar_resposta(enviar_comando(comandos['chuva']), 'chuva') or 0
    vento_velocidade = interpretar_resposta(enviar_comando(comandos['vento_velocidade']), 'vento_velocidade') or 0
    vento_direcao = interpretar_resposta(enviar_comando(comandos['vento_direcao']), 'vento_direcao') or 0

    # Armazenar dados nas listas
    dados_umidade.append(umidade)
    dados_temperatura.append(temperatura)
    dados_pressao.append(pressao)
    dados_ruido.append(ruido)
    dados_iluminancia.append(iluminancia)
    dados_chuva.append(chuva)
    dados_vento_velocidade.append(vento_velocidade)
    dados_vento_direcao.append(vento_direcao)
    tempos.append(tempo_atual)

    # Limitar o tamanho dos dados para manter os gráficos "limpos"
    if len(tempos) > 20:
        dados_umidade.pop(0)
        dados_temperatura.pop(0)
        dados_pressao.pop(0)
        dados_ruido.pop(0)
        dados_iluminancia.pop(0)
        dados_chuva.pop(0)
        dados_vento_velocidade.pop(0)
        dados_vento_direcao.pop(0)
        tempos.pop(0)

    # Atualizar os gráficos
    ax1.clear()
    ax2.clear()
    ax3.clear()
    ax4.clear()
    ax5.clear()
    ax6.clear()
    ax7.clear()
    ax8.clear()

    # Gráficos com barras horizontais
    ax1.barh('Humidade (%)', dados_umidade[-1], color='skyblue', edgecolor='black')
    ax2.barh('Temperatura (°C)', dados_temperatura[-1], color='lightcoral', edgecolor='black')
    ax3.barh('Pressão (hPa)', dados_pressao[-1], color='lightgreen', edgecolor='black')
    ax4.barh('Ruído (dB)', dados_ruido[-1], color='plum', edgecolor='black')
    ax5.barh('Iluminância (lux)', dados_iluminancia[-1], color='lightgoldenrodyellow', edgecolor='black')
    ax6.barh('Chuva (mm)', dados_chuva[-1], color='lightskyblue', edgecolor='black')
    ax7.barh('Vento Velocidade (km/h)', dados_vento_velocidade[-1], color='lightseagreen', edgecolor='black')
    ax8.barh('Vento Direção (°)', dados_vento_direcao[-1], color='peachpuff', edgecolor='black')

    # Configuração dos gráficos
    for ax in [ax1, ax2, ax3, ax4, ax5, ax6, ax7, ax8]:
        ax.set_xlim(0, max(dados_umidade[-1], dados_temperatura[-1], dados_pressao[-1], dados_ruido[-1], dados_iluminancia[-1], dados_chuva[-1], dados_vento_velocidade[-1], dados_vento_direcao[-1]) + 10)
        ax.set_xlabel('', fontsize=12, weight='bold')
        ax.set_title(ax.get_label(), fontsize=14, weight='bold')
        ax.grid(True, linestyle='--', alpha=0.7)

    # Atualizar os labels dos dados na área esquerda
    label_umidade.config(text=f"Humidade: {umidade:.1f} %")
    label_temperatura.config(text=f"Temperatura: {temperatura:.1f} °C")
    label_pressao.config(text=f"Pressão: {pressao:.1f} hPa")
    label_ruido.config(text=f"Ruído: {ruido:.1f} dB")
    label_iluminancia.config(text=f"Iluminância: {iluminancia:.1f} lux")
    label_chuva.config(text=f"Chuva: {chuva:.1f} mm")
    label_vento_velocidade.config(text=f"Vento Velocidade: {vento_velocidade:.2f} km/h")
    label_vento_direcao.config(text=f"Vento Direção: {vento_direcao:.1f} °")

# Configuração da janela principal com tkinter
root = tk.Tk()
root.title("Monitor de Medições")
root.geometry("1400x800")  # Ajustar o tamanho da janela

# Configuração dos frames
frame_dados = tk.Frame(root, padx=20, pady=20, bg='#f0f0f0')
frame_dados.pack(side=tk.LEFT, fill=tk.Y)

frame_graficos = tk.Frame(root, padx=20, pady=20)
frame_graficos.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# Configuração dos labels de dados
label_umidade = tk.Label(frame_dados, text="Umidade: -- %", font=('Arial', 14, 'bold'), bg='#f0f0f0')
label_umidade.pack(anchor='w', pady=5)
label_temperatura = tk.Label(frame_dados, text="Temperatura: -- °C", font=('Arial', 14, 'bold'), bg='#f0f0f0')
label_temperatura.pack(anchor='w', pady=5)
label_pressao = tk.Label(frame_dados, text="Pressão: -- hPa", font=('Arial', 14, 'bold'), bg='#f0f0f0')
label_pressao.pack(anchor='w', pady=5)
label_ruido = tk.Label(frame_dados, text="Ruído: -- dB", font=('Arial', 14, 'bold'), bg='#f0f0f0')
label_ruido.pack(anchor='w', pady=5)
label_iluminancia = tk.Label(frame_dados, text="Iluminância: -- lux", font=('Arial', 14, 'bold'), bg='#f0f0f0')
label_iluminancia.pack(anchor='w', pady=5)
label_chuva = tk.Label(frame_dados, text="Chuva: -- mm", font=('Arial', 14, 'bold'), bg='#f0f0f0')
label_chuva.pack(anchor='w', pady=5)
label_vento_velocidade = tk.Label(frame_dados, text="Vento Velocidade: -- km/h", font=('Arial', 14, 'bold'), bg='#f0f0f0')
label_vento_velocidade.pack(anchor='w', pady=5)
label_vento_direcao = tk.Label(frame_dados, text="Vento Direção: -- °", font=('Arial', 14, 'bold'), bg='#f0f0f0')
label_vento_direcao.pack(anchor='w', pady=5)

# Configuração dos gráficos
fig, (ax1, ax2, ax3, ax4, ax5, ax6, ax7, ax8) = plt.subplots(8, 1, figsize=(12, 16))
plt.tight_layout(pad=4.0)

# Configurar animação para atualizar os gráficos a cada 500 ms
ani = FuncAnimation(fig, atualizar_medicoes, interval=500, cache_frame_data=False)

# Adicionar gráficos ao tkinter
canvas = FigureCanvasTkAgg(fig, master=frame_graficos)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
canvas.draw()

# Iniciar a aplicação tkinter
root.mainloop()
