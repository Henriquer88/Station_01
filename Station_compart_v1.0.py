import serial
import minimalmodbus
import time
from datetime import datetime

# Configuração da porta serial
PORTA = 'COM19'
BAUDRATE = 4800

# IDs das estações conectadas
ESTACOES = [1, 2, 3, 4, 5]

# Cria objeto para comunicação
instrument = minimalmodbus.Instrument(PORTA, 1)
instrument.serial.baudrate = BAUDRATE
instrument.serial.bytesize = 8
instrument.serial.parity   = serial.PARITY_NONE
instrument.serial.stopbits = 1
instrument.serial.timeout  = 1

def ler_estacao(slave_id):
    try:
        instrument.address = slave_id
        # Leitura dos registros (tabela do manual)
        temperatura   = instrument.read_register(0x01F9, 1, functioncode=3, signed=True)   # °C
        umidade       = instrument.read_register(0x01F8, 1, functioncode=3, signed=False)  # %RH
        pressao_kpa   = instrument.read_register(0x01FD, 1, functioncode=3, signed=False)  # kPa
        ruido         = instrument.read_register(0x01FA, 1, functioncode=3, signed=False)  # dB
        iluminancia   = instrument.read_register(0x01FF, 0, functioncode=3, signed=False)  # Lux (16 bits low)
        chuva         = instrument.read_register(0x0201, 1, functioncode=3, signed=False)  # mm
        vento_raw     = instrument.read_register(0x01F4, 0, functioncode=3, signed=False)  # wind speed raw
        vento_dir     = instrument.read_register(0x01F7, 0, functioncode=3, signed=False)  # graus

        # Conversões
        pressao_hpa   = pressao_kpa * 10     # transforma kPa → hPa
        vento_vel_ms  = vento_raw * 0.01     # valor bruto → m/s
        vento_vel_kmh = vento_vel_ms * 3.6   # m/s → km/h

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

while True:
    print("\n📡 Leitura:", datetime.now())
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
                  f"C={dados['chuva']:.1f} mm  "
                  f"V={dados['vento_velocidade']:.1f} km/h  "
                  f"DV={dados['vento_direcao']}°")
    print("-" * 70)
    time.sleep(3)

