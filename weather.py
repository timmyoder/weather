import serial

port = input("Enter the port name: ")
baud = int(input('Enter baudrate: '))

if baud == "":
    baud = None

ser = serial.Serial(port=port, baudrate=baud)
ser.reset_input_buffer()

while True:
    try:
        bytesToRead = ser.inWaiting()
        decoded_bytes = ser.read(bytesToRead).decode("utf-8")
        print(decoded_bytes)
        with open('output.txt', 'a') as out_file:
            out_file.write(decoded_bytes)
    except KeyboardInterrupt:
        print("Keyboard Interrupt")
        break
