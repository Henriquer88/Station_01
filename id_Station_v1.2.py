import serial

def modbus_crc(data: bytes) -> bytes:
    """Calcula CRC16 Modbus (Lo, Hi)"""
    crc = 0xFFFF
    for pos in data:
        crc ^= pos
        for _ in range(8):
            if crc & 1:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return bytes([crc & 0xFF, (crc >> 8) & 0xFF])

# Porta serial
ser = serial.Serial(port="COM15", baudrate=4800, bytesize=8, parity="N", stopbits=1, timeout=1)

OLD_ID = 2   # ID atual do dispositivo
NEW_ID = 5   # Novo ID que você quer configurar
REGISTER_ADDR = 0x07D0  # Endereço do registrador de Slave ID

# Monta frame para Write Single Register (0x06)
frame = bytes([
    OLD_ID,     # endereço atual do escravo
    0x06,       # função: Write Single Register
    (REGISTER_ADDR >> 8) & 0xFF,  # endereço alto
    REGISTER_ADDR & 0xFF,         # endereço baixo
    (NEW_ID >> 8) & 0xFF,         # valor alto
    NEW_ID & 0xFF                 # valor baixo
])
cmd = frame + modbus_crc(frame)

print(f"🔧 Alterando Slave ID de {OLD_ID} para {NEW_ID}...")
ser.write(cmd)

resp = ser.read(8)  # resposta do dispositivo deve ecoar o comando
if resp:
    print(f"✅ ID alterado com sucesso! Resposta: {resp.hex()}")
else:
    print("❌ Nenhuma resposta recebida.")

ser.close()
