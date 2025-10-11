import serial

def modbus_crc(data: bytes) -> bytes:
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

ser = serial.Serial(port="COM15", baudrate=4800, bytesize=8, parity="N", stopbits=1, timeout=1)

# Frame base: [FF][03][07][D0][00][01]
frame = bytes([0xFF, 0x03, 0x07, 0xD0, 0x00, 0x01])
cmd = frame + modbus_crc(frame)

print("🔎 Enviando comando broadcast para ler Slave ID...")
ser.write(cmd)

resp = ser.read(7)  # deve vir 7 bytes de resposta
if resp:
    slave_id = resp[0]
    print(f"✅ Dispositivo respondeu com Slave ID = {slave_id}, resposta bruta: {resp.hex()}")
else:
    print("❌ Nenhuma resposta recebida.")

ser.close()
