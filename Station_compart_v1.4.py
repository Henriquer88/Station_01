import serial
import minimalmodbus
import time
from datetime import datetime
import requests

# ================================
# CONFIGURAÇÕES GERAIS
# ================================
PORTA = 'COM15'        # porta serial
BAUDRATE = 4800        # baud rate da estação
ESTACOES = [1, 2, 3, 4, 5]  # IDs das estações conectadas
ENDPOINT = "https://iothub.eletromidia.com.br/api/v1/estacoes_mets/storeOrUpdate"

# ================================
# CONFIGURAÇÃO MODBUS
# ================================
instrument = minimalmodbus.Instrument(PORTA, 1)
instrument.serial.baudrate = BAUDRATE
instrument.serial.bytesize = 8
instrument.serial.parity   = serial.PARITY_NONE
instrument.serial.stopbits = 1
instrument.serial.timeout  = 1

# ================================
# FUNÇÃO DE LEITURA
# ================================
def ler_estacao(slave_id):
    """Lê todos os sensores da estação especificada"""
    try:
        instrument.address = slave_id

        temperatura   = instrument.read_register(0x01F9, 1, functioncode=3, signed=True)
        umidade       = instrument.read_register(0x01F8, 1, functioncode=3, signed=False)
        pressao_kpa   = instrument.read_register(0x01FD, 1, functioncode=3, signed=False)
        ruido         = instrument.read_register(0x01FA, 1, functioncode=3, signed=False)
        iluminancia   = instrument.read_register(0x01FF, 0, functioncode=3, signed=False)
        chuva         = instrument.read_register(0x0201, 1, functioncode=3, signed=False)
        vento_raw     = instrument.read_register(0x01F4, 0, functioncode=3, signed=False)
        vento_dir     = instrument.read_register(0x01F7, 0, functioncode=3, signed=False)
        pm25          = instrument.read_register(0x01FB, 0, functioncode=3, signed=False)
        pm10          = instrument.read_register(0x01FC, 0, functioncode=3, signed=False)

        # Conversões
        pressao_hpa   = pressao_kpa * 10
        vento_vel_ms  = vento_raw * 0.01
        vento_vel_kmh = vento_vel_ms * 3.6

        return {
            "temperatura": temperatura,
            "umidade": umidade,
            "pressao": pressao_hpa,
            "ruido": ruido,
            "iluminancia": iluminancia,
            "chuva": chuva,
            "vento_velocidade": vento_vel_kmh,
            "vento_direcao": vento_dir,
            "pm25": pm25,
            "pm10": pm10
        }

    except Exception as e:
        return {"erro": str(e)}

# ================================
# FUNÇÕES DE CALIBRAÇÃO
# ================================
def inverter_direcao_vento(slave_id, inverter=True):
    """
    Define offset da direção do vento:
    inverter=False → normal (0)
    inverter=True  → invertido (180°)
    """
    try:
        instrument.address = slave_id
        valor = 1 if inverter else 0
        instrument.write_register(0x6000, valor, functioncode=6)
        print(f"🌪️ Estação {slave_id}: Direção do vento ajustada para {'invertida' if inverter else 'normal'}.")
    except Exception as e:
        print(f"⚠️ Erro ao calibrar direção do vento: {e}")

def zerar_velocidade_vento(slave_id):
    """Zera o valor do vento após 10 segundos"""
    try:
        instrument.address = slave_id
        instrument.write_register(0x6001, 0xAA, functioncode=6)
        print(f"💨 Estação {slave_id}: Comando de zerar vento enviado (aguarde 10s).")
    except Exception as e:
        print(f"⚠️ Erro ao zerar vento: {e}")

def zerar_chuva(slave_id):
    """Zera o acumulado de chuva"""
    try:
        instrument.address = slave_id
        instrument.write_register(0x6002, 0x5A, functioncode=6)
        print(f"🌧️ Estação {slave_id}: Chuva acumulada zerada.")
    except Exception as e:
        print(f"⚠️ Erro ao zerar chuva: {e}")

# ================================
# FUNÇÃO DE ENVIO PARA API
# ================================
def enviar_para_api(nome, dados):
    """Envia os dados formatados para o endpoint HTTP"""
    try:
        payload = {
            "nome": nome,
            "sensores": (
                f"T:{dados['temperatura']:.1f}|"
                f"H:{dados['umidade']:.1f}|"
                f"P:{dados['pressao']:.1f}|"
                f"R:{dados['ruido']:.1f}|"
                f"L:{dados['iluminancia']:.1f}|"
                f"CH:{dados['chuva']:.1f}|"
                f"VV:{dados['vento_velocidade']:.1f}|"
                f"DV:{dados['vento_direcao']:.1f}|"
                f"PM25:{dados['pm25']:.0f}|"
                f"PM10:{dados['pm10']:.0f}"
            )
        }

        response = requests.post(ENDPOINT, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"  ✅ Enviado para API: {payload['nome']}")
        else:
            print(f"  ⚠️ Falha ao enviar {payload['nome']} -> {response.status_code} {response.text}")

    except Exception as e:
        print(f"  ❌ Erro no envio para API: {e}")

# ================================
# LOOP PRINCIPAL
# ================================
print("🚀 Iniciando leituras e envio a cada 60 segundos...\n")

while True:
    print(f"\n📡 Leitura: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    for estacao in ESTACOES:
        dados = ler_estacao(estacao)

        if "erro" in dados:
            print(f"  Estação {estacao}: ⚠️ Erro -> {dados['erro']}")
        else:
            print(
                f"  Estação {estacao}: "
                f"T={dados['temperatura']:.1f}°C  "
                f"H={dados['umidade']:.1f}%  "
                f"P={dados['pressao']:.1f}hPa  "
                f"R={dados['ruido']:.1f}dB  "
                f"L={dados['iluminancia']} lx  "
                f"CH={dados['chuva']:.1f} mm  "
                f"VV={dados['vento_velocidade']:.1f} km/h  "
                f"DV={dados['vento_direcao']:.1f}°  "
                f"PM2.5={dados['pm25']} µg/m³  "
                f"PM10={dados['pm10']} µg/m³"
            )

            enviar_para_api(f"Estação {estacao}", dados)

    print("-" * 90)
    time.sleep(60)

    # Exemplo: comandos de calibração (pode chamar manualmente se quiser)
    # inverter_direcao_vento(1, inverter=True)
    # zerar_velocidade_vento(1)
    # zerar_chuva(1)
