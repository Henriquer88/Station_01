import serial
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Circle
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import time
import threading
import queue
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
    """Classe responsável pela comunicação serial"""

    def __init__(self, port: str = 'COM15', baudrate: int = 4800, timeout: int = 1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.connection = None
        self.is_connected = False
        self.simulation_mode = True

        # Valores iniciais estáveis
        self.stable_values = {
            'temperatura': 23.5,
            'umidade': 58.2,
            'pressao': 1013.25,
            'ruido': 45.0,
            'iluminancia': 32000.0,
            'chuva': 0.0,
            'vento_velocidade': 12.8,
            'vento_direcao': 235.0
        }

        print("Weather System Ready")

    def connect(self) -> bool:
        """Conecta sistema"""
        print("Starting simulation...")
        self.is_connected = True
        self.simulation_mode = True
        return True

    def disconnect(self):
        """Desconecta sistema"""
        self.is_connected = False
        print("System stopped")

    def generate_data(self) -> SensorReading:
        """Gera dados realistas"""
        now = datetime.now()
        hour = now.hour

        # Variações muito pequenas para estabilidade
        # Temperatura
        self.stable_values['temperatura'] += random.uniform(-0.1, 0.1)
        self.stable_values['temperatura'] = max(20.0, min(28.0, self.stable_values['temperatura']))

        # Umidade
        self.stable_values['umidade'] += random.uniform(-0.5, 0.5)
        self.stable_values['umidade'] = max(40.0, min(80.0, self.stable_values['umidade']))

        # Pressão
        self.stable_values['pressao'] += random.uniform(-0.05, 0.05)
        self.stable_values['pressao'] = max(1005.0, min(1025.0, self.stable_values['pressao']))

        # Ruído
        self.stable_values['ruido'] += random.uniform(-1.0, 1.0)
        self.stable_values['ruido'] = max(35.0, min(65.0, self.stable_values['ruido']))

        # Iluminância
        if 6 <= hour <= 18:
            base_light = 40000
        else:
            base_light = 500
        self.stable_values['iluminancia'] += (base_light - self.stable_values['iluminancia']) * 0.1
        self.stable_values['iluminancia'] = max(0, min(50000, self.stable_values['iluminancia']))

        # Chuva
        if random.random() < 0.01:
            self.stable_values['chuva'] = random.uniform(0, 2.0)
        else:
            self.stable_values['chuva'] *= 0.99

        # Vento
        self.stable_values['vento_velocidade'] += random.uniform(-0.5, 0.5)
        self.stable_values['vento_velocidade'] = max(0, min(30.0, self.stable_values['vento_velocidade']))

        self.stable_values['vento_direcao'] += random.uniform(-2.0, 2.0)
        self.stable_values['vento_direcao'] = self.stable_values['vento_direcao'] % 360

        return SensorReading(
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

    def ler_todos_sensores(self) -> SensorReading:
        """Lê todos os sensores"""
        return self.generate_data()


class DataManager:
    """Gerenciador de dados"""

    def __init__(self, max_points: int = 30):
        self.max_points = max_points
        self.readings: List[SensorReading] = []
        self.lock = threading.Lock()

    def add_reading(self, reading: SensorReading):
        with self.lock:
            self.readings.append(reading)
            if len(self.readings) > self.max_points:
                self.readings.pop(0)

    def get_latest_reading(self) -> Optional[SensorReading]:
        with self.lock:
            return self.readings[-1] if self.readings else None

    def get_all_readings(self) -> List[SensorReading]:
        with self.lock:
            return self.readings.copy()


class CompactWeatherDashboard:
    """Dashboard meteorológico compacto e funcional"""

    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()

        # Componentes
        self.communicator = SerialCommunicator()
        self.data_manager = DataManager()
        self.data_queue = queue.Queue()

        # Threading
        self.running = False
        self.data_thread = None

        # Widgets
        self.value_widgets = {}

        # Configurar interface
        self.setup_dashboard()

        # Iniciar automaticamente
        self.auto_start()

        print("Dashboard Initialized")

    def setup_window(self):
        """Configuração de janela otimizada"""
        self.root.title("Weather Station")
        self.root.geometry("1000x700")  # Tamanho menor para caber na tela
        self.root.configure(bg='#f0f0f0')
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.resizable(True, True)  # Permitir redimensionamento

    def create_sensor_card(self, parent, title, key, unit, color, row, col):
        """Cria card de sensor compacto"""
        # Card frame
        card = tk.Frame(parent, bg='white', relief='solid', borderwidth=1, padx=15, pady=10)
        card.grid(row=row, column=col, padx=8, pady=8, sticky='ew')
        parent.grid_columnconfigure(col, weight=1)

        # Título
        title_label = tk.Label(card, text=title, font=('Segoe UI', 12, 'bold'),
                               bg='white', fg='#333333')
        title_label.pack()

        # Valor
        value_label = tk.Label(card, text="--", font=('Segoe UI', 24, 'normal'),
                               bg='white', fg=color)
        value_label.pack(pady=(5, 0))

        # Unidade
        unit_label = tk.Label(card, text=unit, font=('Segoe UI', 10, 'normal'),
                              bg='white', fg='#666666')
        unit_label.pack()

        self.value_widgets[key] = value_label

        return card

    def setup_dashboard(self):
        """Configura dashboard compacto"""
        # Header compacto
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=50)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        # Título
        title_label = tk.Label(header_frame, text="Weather Station Dashboard",
                               font=('Segoe UI', 16, 'bold'), bg='#2c3e50', fg='white')
        title_label.pack(side=tk.LEFT, padx=20, pady=12)

        # Status
        self.status_label = tk.Label(header_frame, text="● Offline",
                                     font=('Segoe UI', 12, 'bold'), bg='#2c3e50', fg='#e74c3c')
        self.status_label.pack(side=tk.RIGHT, padx=20, pady=12)

        # Container principal
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Grid de sensores (3x3)
        sensors_frame = tk.Frame(main_frame, bg='#f0f0f0')
        sensors_frame.pack(fill=tk.X, pady=(0, 10))

        # Linha 1
        self.create_sensor_card(sensors_frame, "Temperature", "temperatura", "°C", "#e74c3c", 0, 0)
        self.create_sensor_card(sensors_frame, "Humidity", "umidade", "%", "#3498db", 0, 1)
        self.create_sensor_card(sensors_frame, "Pressure", "pressao", "hPa", "#2ecc71", 0, 2)

        # Linha 2
        self.create_sensor_card(sensors_frame, "Air Quality", "ruido", "dB", "#9b59b6", 1, 0)
        self.create_sensor_card(sensors_frame, "Light", "iluminancia", "lux", "#f39c12", 1, 1)
        self.create_sensor_card(sensors_frame, "Rainfall", "chuva", "mm", "#1abc9c", 1, 2)

        # Linha 3 - Bússola e gráfico
        bottom_frame = tk.Frame(main_frame, bg='#f0f0f0')
        bottom_frame.pack(fill=tk.BOTH, expand=True)

        # Bússola (esquerda)
        compass_frame = tk.Frame(bottom_frame, bg='white', relief='solid', borderwidth=1)
        compass_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        compass_title = tk.Label(compass_frame, text="Wind Direction",
                                 font=('Segoe UI', 14, 'bold'), bg='white', fg='#333333')
        compass_title.pack(pady=10)

        # Matplotlib para bússola
        self.fig_compass, self.ax_compass = plt.subplots(figsize=(4, 4), facecolor='white')
        self.ax_compass.set_facecolor('white')

        self.compass_canvas = FigureCanvasTkAgg(self.fig_compass, master=compass_frame)
        self.compass_widget = self.compass_canvas.get_tk_widget()
        self.compass_widget.pack(padx=10, pady=10)

        # Gráfico (direita)
        chart_frame = tk.Frame(bottom_frame, bg='white', relief='solid', borderwidth=1)
        chart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        chart_title = tk.Label(chart_frame, text="Temperature Trend",
                               font=('Segoe UI', 14, 'bold'), bg='white', fg='#333333')
        chart_title.pack(pady=10)

        # Matplotlib para gráfico
        self.fig_chart, self.ax_chart = plt.subplots(figsize=(5, 4), facecolor='white')
        self.ax_chart.set_facecolor('white')

        self.chart_canvas = FigureCanvasTkAgg(self.fig_chart, master=chart_frame)
        self.chart_widget = self.chart_canvas.get_tk_widget()
        self.chart_widget.pack(padx=10, pady=10)

        # Controles
        controls_frame = tk.Frame(main_frame, bg='#f0f0f0')
        controls_frame.pack(fill=tk.X, pady=(10, 0))

        self.start_button = tk.Button(controls_frame, text="▶ Start", command=self.start_monitoring,
                                      bg='#27ae60', fg='white', font=('Segoe UI', 12, 'bold'),
                                      padx=20, pady=8, relief='flat', cursor='hand2')
        self.start_button.pack(side=tk.LEFT)

        self.stop_button = tk.Button(controls_frame, text="⏸ Stop", command=self.stop_monitoring,
                                     bg='#e74c3c', fg='white', font=('Segoe UI', 12, 'bold'),
                                     padx=20, pady=8, relief='flat', cursor='hand2', state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(10, 0))

        # Inicializar visualizações
        self.update_compass(235, 12.8)
        self.setup_chart()

    def update_compass(self, direction, speed):
        """Atualiza bússola"""
        self.ax_compass.clear()
        self.ax_compass.set_xlim(-1.2, 1.2)
        self.ax_compass.set_ylim(-1.2, 1.2)
        self.ax_compass.set_aspect('equal')
        self.ax_compass.axis('off')

        # Círculo
        circle = Circle((0, 0), 1, fill=False, edgecolor='#34495e', linewidth=2)
        self.ax_compass.add_patch(circle)

        # Pontos cardeais
        points = {'N': (0, 1.1), 'E': (1.1, 0), 'S': (0, -1.1), 'W': (-1.1, 0)}
        for point, (x, y) in points.items():
            color = '#e74c3c' if point == 'N' else '#7f8c8d'
            self.ax_compass.text(x, y, point, ha='center', va='center',
                                 fontsize=12, color=color, fontweight='bold')

        # Seta
        wind_rad = math.radians(direction - 90)
        arrow_x = 0.8 * math.cos(wind_rad)
        arrow_y = 0.8 * math.sin(wind_rad)

        self.ax_compass.arrow(0, 0, arrow_x, arrow_y, head_width=0.15, head_length=0.1,
                              fc='#3498db', ec='#3498db', linewidth=3)

        # Centro
        center = Circle((0, 0), 0.1, fill=True, facecolor='#2c3e50')
        self.ax_compass.add_patch(center)

        # Info
        self.ax_compass.text(0, -1.4, f'{direction:.0f}° • {speed:.1f} km/h', ha='center',
                             fontsize=11, color='#2c3e50', fontweight='bold')

        plt.tight_layout()
        self.compass_canvas.draw()

    def setup_chart(self):
        """Configura gráfico inicial"""
        self.ax_chart.clear()
        self.ax_chart.set_facecolor('white')
        self.ax_chart.set_title('Waiting for data...', fontsize=12, color='#7f8c8d')
        self.ax_chart.grid(True, alpha=0.3)
        plt.tight_layout()
        self.chart_canvas.draw()

    def update_chart(self):
        """Atualiza gráfico"""
        readings = self.data_manager.get_all_readings()
        if len(readings) < 2:
            return

        self.ax_chart.clear()
        self.ax_chart.set_facecolor('white')

        # Dados de temperatura
        recent_readings = readings[-20:]
        temps = [r.temperatura for r in recent_readings]
        times = range(len(temps))

        # Plotar
        self.ax_chart.plot(times, temps, color='#e74c3c', linewidth=2, marker='o', markersize=4)
        self.ax_chart.fill_between(times, temps, alpha=0.3, color='#e74c3c')

        # Estilo
        self.ax_chart.set_title('Temperature (°C)', fontsize=12, color='#2c3e50', fontweight='bold')
        self.ax_chart.grid(True, alpha=0.3)
        self.ax_chart.tick_params(colors='#7f8c8d')

        # Labels do tempo
        if len(recent_readings) > 5:
            step = max(1, len(recent_readings) // 5)
            positions = range(0, len(recent_readings), step)
            labels = [recent_readings[i].timestamp.strftime('%H:%M') for i in positions]
            self.ax_chart.set_xticks(positions)
            self.ax_chart.set_xticklabels(labels, rotation=45)

        plt.tight_layout()
        self.chart_canvas.draw()

    def data_collection_thread(self):
        """Thread de coleta"""
        while self.running:
            try:
                reading = self.communicator.ler_todos_sensores()
                self.data_queue.put(reading)
                self.data_manager.add_reading(reading)
                time.sleep(3)  # A cada 3 segundos
            except Exception as e:
                print(f"Erro: {e}")
                time.sleep(3)

    def update_display(self):
        """Atualiza display"""
        try:
            while not self.data_queue.empty():
                reading = self.data_queue.get_nowait()
                self.update_values(reading)
        except queue.Empty:
            pass

        if self.running:
            self.root.after(1000, self.update_display)

    def update_values(self, reading: SensorReading):
        """Atualiza valores na interface"""
        # Sensores
        sensors = {
            'temperatura': reading.temperatura,
            'umidade': reading.umidade,
            'pressao': reading.pressao,
            'ruido': reading.ruido,
            'iluminancia': reading.iluminancia,
            'chuva': reading.chuva
        }

        for key, value in sensors.items():
            if key in self.value_widgets:
                if key == 'iluminancia' and value >= 1000:
                    self.value_widgets[key].config(text=f"{value / 1000:.1f}k")
                else:
                    self.value_widgets[key].config(text=f"{value:.1f}")

        # Bússola
        self.update_compass(reading.vento_direcao, reading.vento_velocidade)

        # Gráfico
        self.update_chart()

    def auto_start(self):
        """Inicia automaticamente após 1 segundo"""
        self.root.after(1000, self.start_monitoring)

    def start_monitoring(self):
        """Inicia monitoramento"""
        if self.communicator.connect():
            self.running = True
            self.data_thread = threading.Thread(target=self.data_collection_thread, daemon=True)
            self.data_thread.start()

            self.start_button.config(state=tk.DISABLED, bg='#95a5a6')
            self.stop_button.config(state=tk.NORMAL, bg='#e74c3c')
            self.status_label.config(text="● Online", fg='#27ae60')

            self.update_display()
            print("Monitoring started")

    def stop_monitoring(self):
        """Para monitoramento"""
        self.running = False
        if self.data_thread:
            self.data_thread.join(timeout=2)

        self.communicator.disconnect()

        self.start_button.config(state=tk.NORMAL, bg='#27ae60')
        self.stop_button.config(state=tk.DISABLED, bg='#95a5a6')
        self.status_label.config(text="● Offline", fg='#e74c3c')

        print("Monitoring stopped")

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
        dashboard = CompactWeatherDashboard()
        dashboard.run()
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()