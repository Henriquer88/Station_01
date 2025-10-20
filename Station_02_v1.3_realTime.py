import serial
import time
from datetime import datetime

# Configurações da porta serial
PORTA = "COM15"      # No Linux: /dev/ttyUSB0
BAUDRATE = 4800
TIMEOUT = 1
SLAVE_ID = 1          # Altere para 2, 3, etc., conforme a estação

# Registradores da estação (endereço e fator de escala)
SENSORES = {
    "Wind speed (m/s)":        (0x1F4, 0.01),
    "Wind strength":           (0x1F5, 1),
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

    # 🌞 Novo sensor adicionado:
    "Solar irradiance (W/m²)": (0x204, 1),   # signed, escala 1
}

# Função para calcular CRC16 Modbus
def calcular_crc(data: bytes) -> bytes:
    crc = 0xFFFF
    for pos in data:
        crc ^= pos
        for _ in range(8):
            if crc & 1:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, byteorder="little")

# Monta comando Modbus RTU
def montar_comando(slave_id: int, addr: int, qtd: int = 1) -> bytes:
    msg = bytearray()
    msg.append(slave_id)
    msg.append(0x03)  # função: Read Holding Registers
    msg.append((addr >> 8) & 0xFF)
    msg.append(addr & 0xFF)
    msg.append(0x00)
    msg.append(qtd)
    crc = calcular_crc(msg)
    msg.extend(crc)
    return bytes(msg)

# Envia comando e lê resposta
def ler_registro(ser, slave_id: int, addr: int, scale: float, signed=False):
    cmd = montar_comando(slave_id, addr, 1)
    ser.reset_input_buffer()
    ser.write(cmd)
    resp = ser.read(7)
    if len(resp) == 7 and resp[0] == slave_id and resp[1] == 0x03:
        valor = int.from_bytes(resp[3:5], byteorder="big", signed=signed)
        return valor * scale
    return None

def main():
    with serial.Serial(port=PORTA, baudrate=BAUDRATE, timeout=TIMEOUT) as ser:
        while True:
            print(f"\n📡 Leitura: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            for nome, (addr, escala) in SENSORES.items():
                signed = True if nome == "Solar irradiance (W/m²)" else False
                valor = ler_registro(ser, SLAVE_ID, addr, escala, signed=signed)
                if valor is not None:
                    print(f"  {nome:<25}: {valor:.1f}")
                else:
                    print(f"  {nome:<25}: N/A")
            print("-" * 50)
            time.sleep(3)

if __name__ == "__main__":
    main()
