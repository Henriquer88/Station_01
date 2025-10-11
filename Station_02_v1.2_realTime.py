import serial
import time
from datetime import datetime

# Configurações da porta serial
PORTA = "COM15"
BAUDRATE = 4800
TIMEOUT = 1
SLAVE_ID = 1   # altere para 2 ou 3 dependendo da estação que quer ler

# Registradores da estação (endereço e fator de escala)
SENSORES = {
    "Wind speed (m/s)":        (0x1F4, 0.01),
    "Wind strength":           (0x1F5, 1),       # 0–7 direções discretas
    "Wind direction (0-7)":    (0x1F6, 1),
    "Wind direction (°)":      (0x1F7, 1),
    "Humidity (%)":            (0x1F8, 0.1),
    "Temperature (°C)":        (0x1F9, 0.1),
    "Noise (dB)":              (0x1FA, 0.1),
    "PM2.5 (µg/m3)":           (0x1FB, 1),
    "PM10 (µg/m3)":            (0x1FC, 1),
    "Pressure (kPa)":          (0x1FD, 0.1),
    "Illuminance High":        (0x1FE, 1),
    "Illuminance Low":         (0x1FF, 1),
    "Illuminance Extra":       (0x200, 100),
    "Rainfall (mm)":           (0x201, 0.1),
}

# Função para calcular CRC16 Modbus
def calcular_crc(data: bytes) -> bytes:
    crc = 0xFFFF
    for pos in data:
        crc ^= pos
        for _ in range(8):
            if (crc & 1) != 0:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, byteorder='little')

# Monta comando Modbus RTU
def montar_comando(slave_id: int, addr: int, qtd: int = 1) -> bytes:
    msg = bytearray()
    msg.append(slave_id)
    msg.append(0x03)  # função: read holding register
    msg.append((addr >> 8) & 0xFF)
    msg.append(addr & 0xFF)
    msg.append(0x00)
    msg.append(qtd)
    crc = calcular_crc(msg)
    msg.extend(crc)
    return bytes(msg)

# Envia comando e lê resposta
def ler_registro(ser, slave_id: int, addr: int, scale: float):
    cmd = montar_comando(slave_id, addr, 1)
    ser.write(cmd)
    resp = ser.read(7)  # resposta esperada = 7 bytes
    if len(resp) == 7 and resp[0] == slave_id and resp[1] == 0x03:
        valor = int.from_bytes(resp[3:5], byteorder="big")
        return valor * scale
    return None

def main():
    with serial.Serial(port=PORTA, baudrate=BAUDRATE, timeout=TIMEOUT) as ser:
        while True:
            print(f"\n📡 Leitura: {datetime.now()}")
            for nome, (addr, escala) in SENSORES.items():
                valor = ler_registro(ser, SLAVE_ID, addr, escala)
                if valor is not None:
                    print(f"  {nome:<20}: {valor}")
                else:
                    print(f"  {nome:<20}: N/A")
            print("-" * 40)
            time.sleep(3)

if __name__ == "__main__":
    main()
