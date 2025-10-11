import serial
import minimalmodbus
import time
from datetime import datetime
import requests

# Configuração da porta serial
PORTA = 'COM15'
BAUDRATE = 4800

# IDs das estações conectadas
ESTACOES = [1, 2, 3, 4, 5]

# Endpoint da API
ENDPOINT = "https://iothub.eletromidia.com.br/api/v1/estacoes_mets/storeOrUpdate"

# Cria objeto para comunicação
instrument = minimalmodbus.Instrument(PORTA, 1)
instrument.serial.baudrate = BAUDRATE
instrument.serial.bytesize = 8
instrument.serial.parity   = serial.PARITY_NONE
instrument.serial.stopbits = 1
instrument.serial.timeout  = 1

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
            "vento_direcao": vento_dir
        }
    except Exception as e:
        return {"erro": str(e)}

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
                f"DV:{dados['vento_direcao']:.1f}"
            )
        }
        response = requests.post(ENDPOINT, json=payload, timeout=5)
        if response.status_code == 200:
            print(f"  ✅ Enviado para API: {payload['nome']}")
        else:
            print(f"  ⚠️ Falha ao enviar {payload['nome']} -> {response.status_code} {response.text}")
    except Exception as e:
        print(f"  ❌ Erro no envio para API: {e}")

# Loop principal
while True:
    print(f"\n📡 Leitura: {datetime.now()}")
    for estacao in ESTACOES:
        dados = ler_estacao(estacao)
        if "erro" in dados:
            print(f"  Estação {estacao}: ⚠️ Erro -> {dados['erro']}")
        else:
            print(f"  Estação {estacao}: "
                  f"T={dados['temperatura']:.1f}°C  "
                  f"H={dados['umidade']:.1f}%  "
                  f"P={dados['pressao']:.1f}hPa  "
                  f"R={dados['ruido']:.1f}dB  "
                  f"L={dados['iluminancia']} lx  "
                  f"CH={dados['chuva']:.1f} mm  "
                  f"VV={dados['vento_velocidade']:.1f} km/h  "
                  f"DV={dados['vento_direcao']:.1f}°")

            #
            enviar_para_api(f"Estação {estacao}", dados)

    print("-" * 80)
    time.sleep(60)
