import serial
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import time
import threading
import queue
import csv
import random
import math
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@dataclass
class SensorReading:
    """Classe para armazenar uma leitura de sensor"""
    timestamp: datetime
    umidade: float = 0.0
    temperatura: float = 0.0
    pressao: float = 0.0
    ruido: float = 0.0
    iluminancia: float = 0.0
    chuva: float = 0.0
    vento_velocidade: float = 0.0
    vento_direcao: float = 0.0


class SerialCommunicator:
    """Classe responsável pela comunicação serial com os sensores"""

    def __init__(self, port: str = 'COM19', baudrate: int = 4800, timeout: int = 1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.connection = None
        self.is_connected = False
        self.simulation_mode = True

        # Comandos Modbus para cada sensor
        self.comandos = {
            'umidade': "01 03 01 f8 00 01 04 07",
            'temperatura': "01 03 01 f9 00 01 55 c7",
            'pressao': "01 03 01 fd 00 01 14 06",
            'ruido': "01 03 01 fa 00 01 a5 c7",
            'iluminancia': "01 03 02 00 00 01 85 b2",
            'chuva': "01 03 02 01 00 01 d4 72",
            'vento_velocidade': "01 03 01 f4 00 01 c4 04",
            'vento_direcao': "01 03 01 f5 00 01 95 c4"
        }

        # Valores ESTÁVEIS para simulação gradual (iniciais realistas)
        self.stable_values = {
            'temperatura': 22.0,
            'umidade': 65.0,
            'pressao': 1013.2,
            'ruido': 45.0,
            'iluminancia': 25000.0,
            'chuva': 0.0,
            'vento_velocidade': 12.0,
            'vento_direcao': 180.0
        }

        print("SerialCommunicator inicializado em modo simulação estável")

    def connect(self) -> bool:
        """Estabelece conexão serial ou ativa modo simulação"""
        # FORÇAR MODO SIMULAÇÃO por enquanto para garantir valores corretos
        print("Modo simulação ativado (valores realistas)")
        self.is_connected = True
        self.simulation_mode = True
        return True

        # Código real comentado por enquanto:
        # try:
        #     self.connection = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
        #     self.is_connected = True
        #     self.simulation_mode = False
        #     print(f"Conectado à porta {self.port}")
        #     return True
        # except Exception as e:
        #     print(f"Erro ao conectar à porta {self.port}: {e}")
        #     print("Ativando modo simulação")
        #     self.is_connected = True
        #     self.simulation_mode = True
        #     return True

    def disconnect(self):
        """Fecha conexão serial"""
        if self.connection and hasattr(self.connection, 'is_open') and self.connection.is_open:
            self.connection.close()
        self.is_connected = False
        print("Conexão fechada")

    def generate_realistic_data(self) -> SensorReading:
        """Gera dados realistas com MUDANÇAS GRADUAIS (como na realidade)"""
        now = datetime.now()
        hour = now.hour
        minute = now.minute

        print(f"Gerando dados graduais para {hour:02d}:{minute:02d}")

        # TEMPERATURA: mudança muito gradual (±0.3°C por leitura no máximo)
        hour_factor = math.sin(2 * math.pi * (hour - 6) / 24)  # Ciclo diário
        target_temp = 22.0 + 4.0 * hour_factor  # Varia entre 18°C e 26°C ao longo do dia

        # Aproximar gradualmente do valor alvo
        temp_diff = target_temp - self.stable_values['temperatura']
        self.stable_values['temperatura'] += temp_diff * 0.1 + random.uniform(-0.3, 0.3)
        self.stable_values['temperatura'] = max(15.0, min(35.0, self.stable_values['temperatura']))

        # UMIDADE: inversamente relacionada à temperatura, mudança gradual
        target_humidity = 75.0 - (self.stable_values['temperatura'] - 20.0) * 1.5
        humidity_diff = target_humidity - self.stable_values['umidade']
        self.stable_values['umidade'] += humidity_diff * 0.1 + random.uniform(-1.5, 1.5)
        self.stable_values['umidade'] = max(30.0, min(85.0, self.stable_values['umidade']))

        # PRESSÃO: mudança muito lenta (±0.2 hPa por leitura)
        self.stable_values['pressao'] += random.uniform(-0.2, 0.2)
        self.stable_values['pressao'] = max(1000.0, min(1025.0, self.stable_values['pressao']))

        # RUÍDO: varia com a hora do dia, mudança gradual
        if 7 <= hour <= 22:  # Dia - mais ruído
            target_noise = 50.0
        else:  # Noite - menos ruído
            target_noise = 35.0

        noise_diff = target_noise - self.stable_values['ruido']
        self.stable_values['ruido'] += noise_diff * 0.1 + random.uniform(-2.0, 2.0)
        self.stable_values['ruido'] = max(25.0, min(70.0, self.stable_values['ruido']))

        # ILUMINÂNCIA: baseada na hora do dia
        if 6 <= hour <= 18:
            sun_angle = math.sin(math.pi * (hour - 6) / 12)
            target_illuminance = 50000 * sun_angle
        else:
            target_illuminance = random.uniform(50, 200)  # Luz artificial

        ill_diff = target_illuminance - self.stable_values['iluminancia']
        self.stable_values['iluminancia'] += ill_diff * 0.2 + random.uniform(-1000, 1000)
        self.stable_values['iluminancia'] = max(0.0, min(60000.0, self.stable_values['iluminancia']))

        # CHUVA: mudança muito gradual (raramente muda)
        if random.random() < 0.02:  # 2% chance de mudança
            self.stable_values['chuva'] = max(0.0, random.uniform(-0.5, 2.0))
        else:
            self.stable_values['chuva'] *= 0.95  # Decai gradualmente
        self.stable_values['chuva'] = max(0.0, min(5.0, self.stable_values['chuva']))

        # VENTO VELOCIDADE: mudança gradual (±1 km/h por leitura)
        self.stable_values['vento_velocidade'] += random.uniform(-1.0, 1.0)
        self.stable_values['vento_velocidade'] = max(0.0, min(40.0, self.stable_values['vento_velocidade']))

        # VENTO DIREÇÃO: rotação gradual (±5° por leitura)
        self.stable_values['vento_direcao'] += random.uniform(-5.0, 5.0)
        while self.stable_values['vento_direcao'] < 0:
            self.stable_values['vento_direcao'] += 360
        while self.stable_values['vento_direcao'] >= 360:
            self.stable_values['vento_direcao'] -= 360

        # Criar leitura com valores estáveis
        reading = SensorReading(
            timestamp=now,
            temperatura=round(self.stable_values['temperatura'], 1),
            umidade=round(self.stable_values['umidade'], 1),
            pressao=round(self.stable_values['pressao'], 1),
            ruido=round(self.stable_values['ruido'], 1),
            iluminancia=round(self.stable_values['iluminancia'], 0),
            chuva=round(self.stable_values['chuva'], 1),
            vento_velocidade=round(self.stable_values['vento_velocidade'], 1),
            vento_direcao=round(self.stable_values['vento_direcao'], 0)
        )

        print(f"Dados graduais: T={reading.temperatura:.1f}°C, H={reading.umidade:.1f}%, P={reading.pressao:.1f}hPa")
        return reading

    def interpretar_resposta(self, resposta: bytes, tipo: str) -> Optional[float]:
        """Interpreta resposta do sensor (para modo real)"""
        if not resposta or len(resposta) != 7:
            return None

        try:
            valor_hex = resposta[3:5]
            valor_int = int.from_bytes(valor_hex, byteorder='big')

            if tipo in ['iluminancia', 'chuva', 'vento_direcao']:
                return float(valor_int)
            elif tipo == 'vento_velocidade':
                return valor_int / 100.0
            else:
                return valor_int / 10.0
        except Exception as e:
            print(f"Erro ao interpretar resposta para {tipo}: {e}")
            return None

    def ler_sensor(self, tipo: str) -> Optional[float]:
        """Lê valor de um sensor específico (para modo real)"""
        if self.simulation_mode or tipo not in self.comandos or not self.connection:
            return None

        try:
            comando_bytes = bytes.fromhex(self.comandos[tipo])
            self.connection.write(comando_bytes)
            resposta = self.connection.read(7)
            return self.interpretar_resposta(resposta, tipo)
        except Exception as e:
            print(f"Erro ao ler sensor {tipo}: {e}")
            return None

    def ler_todos_sensores(self) -> SensorReading:
        """Lê todos os sensores (FORÇANDO simulação por enquanto)"""
        # SEMPRE usar simulação para garantir valores corretos
        print("Usando simulação (valores garantidos)")
        return self.generate_realistic_data()

        # Código real comentado:
        # if self.simulation_mode:
        #     return self.generate_realistic_data()
        #
        # # Modo real
        # reading = SensorReading(timestamp=datetime.now())
        # for sensor in ['umidade', 'temperatura', 'pressao', 'ruido',
        #               'iluminancia', 'chuva', 'vento_velocidade', 'vento_direcao']:
        #     valor = self.ler_sensor(sensor)
        #     setattr(reading, sensor, valor if valor is not None else 0.0)
        #
        # return reading


class DataManager:
    """Classe para gerenciar dados históricos"""

    def __init__(self, max_points: int = 25):
        self.max_points = max_points
        self.readings: List[SensorReading] = []
        self.lock = threading.Lock()

    def add_reading(self, reading: SensorReading):
        """Adiciona nova leitura"""
        with self.lock:
            self.readings.append(reading)
            if len(self.readings) > self.max_points:
                self.readings.pop(0)
            print(f"Dados adicionados. Total: {len(self.readings)} leituras")

    def get_latest_reading(self) -> Optional[SensorReading]:
        """Retorna última leitura"""
        with self.lock:
            return self.readings[-1] if self.readings else None

    def get_all_readings(self) -> List[SensorReading]:
        """Retorna todas as leituras"""
        with self.lock:
            return self.readings.copy()

    def export_to_csv(self, filename: str):
        """Exporta dados para CSV"""
        with self.lock:
            if not self.readings:
                return False

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([
                    'Timestamp', 'Temperatura (°C)', 'Umidade (%)', 'Pressão (hPa)',
                    'Ruído (dB)', 'Iluminância (lux)', 'Chuva (mm)',
                    'Vento Velocidade (km/h)', 'Vento Direção (°)'
                ])

                for reading in self.readings:
                    writer.writerow([
                        reading.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        reading.temperatura, reading.umidade, reading.pressao,
                        reading.ruido, reading.iluminancia, reading.chuva,
                        reading.vento_velocidade, reading.vento_direcao
                    ])
            return True
        except Exception as e:
            print(f"Erro ao exportar CSV: {e}")
            return False


class WeatherMonitorApp:
    """Aplicação do monitor meteorológico"""

    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()

        # Configurações dos sensores
        self.sensor_configs = {
            'temperatura': {'unit': '°C', 'color': '#2c3e50', 'min': 0, 'max': 40},
            'umidade': {'unit': '%', 'color': '#34495e', 'min': 0, 'max': 100},
            'pressao': {'unit': 'hPa', 'color': '#2c3e50', 'min': 980, 'max': 1040},
            'ruido': {'unit': 'dB', 'color': '#34495e', 'min': 20, 'max': 100},
            'iluminancia': {'unit': 'lux', 'color': '#2c3e50', 'min': 0, 'max': 80000},
            'chuva': {'unit': 'mm', 'color': '#34495e', 'min': 0, 'max': 10},
            'vento_velocidade': {'unit': 'km/h', 'color': '#2c3e50', 'min': 0, 'max': 50},
            'vento_direcao': {'unit': '°', 'color': '#34495e', 'min': 0, 'max': 360}
        }

        # Componentes
        self.communicator = SerialCommunicator()
        self.data_manager = DataManager()
        self.data_queue = queue.Queue()

        # Threading
        self.running = False
        self.data_thread = None

        # Widgets de dados
        self.data_widgets = {}

        # Interface
        self.setup_interface()
        self.setup_charts()

        print("Aplicação inicializada")

    def setup_window(self):
        """Configura janela principal"""
        self.root.title("Monitor Meteorológico")
        self.root.geometry("1600x900")
        self.root.configure(bg='#ecf0f1')
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_interface(self):
        """Configura interface"""
        # Header
        header_frame = tk.Frame(self.root, bg='#34495e', height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        # Título
        title_label = tk.Label(header_frame, text="Monitor Meteorológico",
                               font=('Segoe UI', 18, 'bold'), bg='#34495e', fg='white')
        title_label.pack(side=tk.LEFT, padx=20, pady=15)

        # Controles
        controls_frame = tk.Frame(header_frame, bg='#34495e')
        controls_frame.pack(side=tk.RIGHT, padx=20, pady=10)

        self.start_button = tk.Button(controls_frame, text="Iniciar", command=self.start_monitoring,
                                      bg='#27ae60', fg='white', font=('Segoe UI', 10, 'bold'),
                                      padx=15, pady=6, relief='flat', cursor='hand2')
        self.start_button.pack(side=tk.LEFT, padx=3)

        self.stop_button = tk.Button(controls_frame, text="Parar", command=self.stop_monitoring,
                                     bg='#e74c3c', fg='white', font=('Segoe UI', 10, 'bold'),
                                     padx=15, pady=6, relief='flat', cursor='hand2', state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=3)

        self.export_button = tk.Button(controls_frame, text="Exportar", command=self.export_data,
                                       bg='#3498db', fg='white', font=('Segoe UI', 10, 'bold'),
                                       padx=15, pady=6, relief='flat', cursor='hand2')
        self.export_button.pack(side=tk.LEFT, padx=3)

        # Status
        self.status_label = tk.Label(controls_frame, text="Desconectado",
                                     font=('Segoe UI', 11, 'bold'), bg='#34495e', fg='#e74c3c')
        self.status_label.pack(side=tk.RIGHT, padx=15)

        # Container principal
        main_container = tk.Frame(self.root, bg='#ecf0f1')
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Frame de dados (esquerda)
        self.cards_frame = tk.Frame(main_container, bg='#ecf0f1', width=300)
        self.cards_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        self.cards_frame.pack_propagate(False)

        # Frame de gráficos (direita)
        self.charts_frame = tk.Frame(main_container, bg='white', relief='solid', borderwidth=1)
        self.charts_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Criar cards de dados
        self.create_data_cards()

    def create_data_cards(self):
        """Cria cards para cada sensor"""
        sensors = list(self.sensor_configs.keys())

        for sensor in sensors:
            config = self.sensor_configs[sensor]

            # Card
            card = tk.Frame(self.cards_frame, bg='white', relief='solid', borderwidth=1)
            card.pack(fill=tk.X, pady=4, padx=5, ipady=8)

            # Nome do sensor
            name_label = tk.Label(card, text=sensor.replace('_', ' ').title(),
                                  font=('Segoe UI', 11, 'bold'), bg='white', fg='#2c3e50')
            name_label.pack(pady=(5, 0))

            # Container do valor
            value_frame = tk.Frame(card, bg='white')
            value_frame.pack(pady=5)

            # Valor
            value_label = tk.Label(value_frame, text="--",
                                   font=('Segoe UI', 20, 'bold'), bg='white', fg=config['color'])
            value_label.pack(side=tk.LEFT)

            # Unidade
            unit_label = tk.Label(value_frame, text=config['unit'],
                                  font=('Segoe UI', 12), bg='white', fg='#7f8c8d')
            unit_label.pack(side=tk.LEFT, padx=(3, 0), anchor='s', pady=(0, 2))

            # Armazenar referência
            self.data_widgets[sensor] = {
                'value': value_label,
                'config': config
            }

    def setup_charts(self):
        """Configura gráficos"""
        plt.style.use('default')

        # Criar figura
        self.fig, self.axes = plt.subplots(2, 4, figsize=(14, 7))
        self.fig.patch.set_facecolor('white')
        self.fig.suptitle('Tendências dos Sensores', fontsize=16, fontweight='bold', color='#2c3e50')

        # Canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.charts_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Configurar gráficos
        sensors = list(self.sensor_configs.keys())
        for i, sensor in enumerate(sensors):
            row, col = i // 4, i % 4
            ax = self.axes[row, col]
            config = self.sensor_configs[sensor]

            ax.set_title(sensor.replace('_', ' ').title(), fontweight='bold', fontsize=11, color='#2c3e50')
            ax.set_facecolor('#f8f9fa')
            ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, color='#bdc3c7')

            for spine in ax.spines.values():
                spine.set_color('#bdc3c7')
                spine.set_linewidth(0.8)

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    def data_collection_thread(self):
        """Thread para coleta de dados"""
        print("Thread de coleta iniciada")
        while self.running:
            try:
                print("Coletando dados...")
                reading = self.communicator.ler_todos_sensores()
                self.data_queue.put(reading)
                self.data_manager.add_reading(reading)
                print(f"Dados coletados: T={reading.temperatura}°C")
                time.sleep(5)  # Atualização a cada 5 segundos
            except Exception as e:
                print(f"Erro na coleta de dados: {e}")
                time.sleep(5)
        print("Thread de coleta finalizada")

    def update_display(self):
        """Atualiza display"""
        try:
            # Processar dados da queue
            updated = False
            while not self.data_queue.empty():
                reading = self.data_queue.get_nowait()
                self.update_cards(reading)
                self.update_charts()
                updated = True
                print("Display atualizado")
        except queue.Empty:
            pass

        # Reagendar atualização
        if self.running:
            self.root.after(1000, self.update_display)

    def update_cards(self, reading: SensorReading):
        """Atualiza cards com dados"""
        print("Atualizando cards...")
        for sensor, widget in self.data_widgets.items():
            value = getattr(reading, sensor)

            if sensor == 'iluminancia':
                widget['value'].config(text=f"{value:.0f}")
            elif sensor == 'vento_direcao':
                widget['value'].config(text=f"{value:.0f}")
            else:
                widget['value'].config(text=f"{value:.1f}")

            print(f"Card {sensor} atualizado: {value}")

    def update_charts(self):
        """Atualiza gráficos"""
        readings = self.data_manager.get_all_readings()
        if not readings:
            print("Nenhum dado para gráficos")
            return

        print(f"Atualizando gráficos com {len(readings)} pontos")

        # Dados dos últimos 15 pontos
        recent_readings = readings[-15:] if len(readings) > 15 else readings
        time_labels = [r.timestamp.strftime('%H:%M') for r in recent_readings]

        sensors = list(self.sensor_configs.keys())
        for i, sensor in enumerate(sensors):
            row, col = i // 4, i % 4
            ax = self.axes[row, col]
            config = self.sensor_configs[sensor]

            # Dados do sensor
            values = [getattr(r, sensor) for r in recent_readings]

            # Limpar e plotar
            ax.clear()

            # Linha simples
            if len(values) > 0:
                ax.plot(range(len(values)), values, color=config['color'],
                        linewidth=2, marker='o', markersize=4, markerfacecolor='white',
                        markeredgecolor=config['color'], markeredgewidth=1.5)

            # Configuração
            ax.set_title(sensor.replace('_', ' ').title(), fontweight='bold', fontsize=11, color='#2c3e50')
            ax.set_facecolor('#f8f9fa')
            ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, color='#bdc3c7')

            # Bordas
            for spine in ax.spines.values():
                spine.set_color('#bdc3c7')
                spine.set_linewidth(0.8)

            # Eixos
            if len(values) > 0:
                ax.set_ylim(config['min'], config['max'])
                if len(values) > 1:
                    ax.set_xlim(0, len(values) - 1)

                # Labels do eixo x
                if len(time_labels) > 3:
                    step = max(1, len(time_labels) // 3)
                    positions = range(0, len(time_labels), step)
                    ax.set_xticks(positions)
                    ax.set_xticklabels([time_labels[i] for i in positions],
                                       fontsize=9, color='#7f8c8d')

                ax.tick_params(axis='y', labelsize=9, colors='#7f8c8d')

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        self.canvas.draw()
        print("Gráficos atualizados")

    def start_monitoring(self):
        """Inicia monitoramento"""
        print("Iniciando monitoramento...")
        if self.communicator.connect():
            self.running = True
            self.data_thread = threading.Thread(target=self.data_collection_thread, daemon=True)
            self.data_thread.start()

            self.start_button.config(state=tk.DISABLED, bg='#95a5a6')
            self.stop_button.config(state=tk.NORMAL, bg='#e74c3c')

            # Status sempre será simulação por enquanto
            self.status_label.config(text="Simulação Estável", fg='#27ae60')

            # Iniciar atualização da interface
            self.update_display()
            print("Monitoramento iniciado com sucesso")

    def stop_monitoring(self):
        """Para monitoramento"""
        print("Parando monitoramento...")
        self.running = False
        if self.data_thread:
            self.data_thread.join(timeout=3)

        self.communicator.disconnect()

        self.start_button.config(state=tk.NORMAL, bg='#27ae60')
        self.stop_button.config(state=tk.DISABLED, bg='#95a5a6')
        self.status_label.config(text="Desconectado", fg='#e74c3c')

        print("Monitoramento parado")

    def export_data(self):
        """Exporta dados"""
        if not self.data_manager.readings:
            messagebox.showwarning("Aviso", "Não há dados para exportar")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Exportar dados meteorológicos"
        )

        if filename:
            if self.data_manager.export_to_csv(filename):
                messagebox.showinfo("Sucesso", f"Dados exportados para:\n{filename}")
            else:
                messagebox.showerror("Erro", "Erro ao exportar dados")

    def on_closing(self):
        """Fecha aplicação"""
        if self.running:
            self.stop_monitoring()
        self.root.destroy()

    def run(self):
        """Executa aplicação"""
        self.root.mainloop()


def main():
    """Função principal"""
    try:
        app = WeatherMonitorApp()
        app.run()
    except Exception as e:
        print(f"Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("Erro Fatal", f"Erro na aplicação: {e}")


if __name__ == "__main__":
    main()