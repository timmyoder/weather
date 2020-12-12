import serial

port = input("Enter the port name: ")

ser = serial.Serial(port=port)
ser.flushInput()

while True:
    try:
        ser_bytes = ser.readline()
        decoded_bytes = ser_bytes.decode("utf-8")
        print(decoded_bytes)
    except KeyboardInterrupt:
        print("Keyboard Interrupt")
        break
