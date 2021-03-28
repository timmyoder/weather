import serial
import datetime as dt

def _fmt(byte_str):
    """ This will format raw bytes into a string of space-delimited hex. """
    try:
        # Python 2
        return ' '.join(["%0.2X" % ord(c) for c in byte_str])
    except TypeError:
        # Python 3
        return ' '.join(["%.2X" % c for c in byte_str])


class Station(object):
    def __init__(self, address=1, port='/dev/ttyS0', baud=19200):
        self.terminator = b'\r\n'
        self.address = address
        self.port = port
        self.baudrate = baud
        self.timeout = 3  # seconds

        self.terminator = b'\r\n'
        self.device = None

    def open(self):
        print("open serial port %s" % self.port)
        self.device = serial.Serial(
            self.port, self.baudrate, timeout=self.timeout)

    def close(self):
        if self.device is not None:
            print("close serial port %s" % self.port)
            self.device.close()
            self.device = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, _, value, traceback):
        self.close()

    def send_cmd(self, cmd):
        cmd = b"%d%s%s" % (self.address, cmd, self.terminator)
        self.device.write(cmd)

    def get_data(self, cmd):
        self.send_cmd(cmd)
        line = self.device.readline()
        if line:
            line.replace(b'\x00', b'')  # eliminate any NULL characters
        return line

    def get_address(self):
        self.device.write(b'?%s' % self.terminator)
        return self.device.readline()

    def set_address(self, addr):
        self.send_cmd(b'A%d' % addr)

    def get_ack(self):
        return self.get_data(b'')

    def reset(self):
        self.send_cmd(b'XZ')

    def precip_counter_reset(self):
        self.send_cmd(b'XZRU')

    def precip_intensity_reset(self):
        self.send_cmd(b'XZRI')

    def measurement_reset(self):
        self.send_cmd(b'XZM')

    def set_automatic_mode(self):
        self.send_cmd(b'XU,M=R')

    def set_polled_mode(self):
        self.send_cmd(b'XU,M=P')

    def get_wind(self):
        return self.get_data(b'R1')

    def get_pth(self):
        return self.get_data(b'R2')

    def get_precip(self):
        return self.get_data(b'R3')

    def get_supervisor(self):
        return self.get_data(b'R5')

    def get_composite(self):
        return self.get_data(b'R0')

    OBSERVATIONS = {
        # aR1: wind message
        b'Dn': 'wind_dir_min',
        b'Dm': 'wind_dir_avg',
        b'Dx': 'wind_dir_max',
        b'Sn': 'wind_speed_min',
        b'Sm': 'wind_speed_avg',
        b'Sx': 'wind_speed_max',
        # aR2: pressure, temperature, humidity message
        b'Ta': 'temperature',
        b'Ua': 'humidity',
        b'Pa': 'pressure',
        # aR3: precipitation message
        b'Rc': 'rain',
        b'Rd': 'rain_duration',
        b'Ri': 'rain_intensity',
        b'Hc': 'hail',
        b'Hd': 'hail_duration',
        b'Hi': 'hail_intensity',
        b'Rp': 'rain_intensity_peak',
        b'Hp': 'hail_intensity_peak',
        # dR5: supervisor message
        b'Th': 'heating_temperature',
        b'Vh': 'heating_voltage',
        b'Vs': 'supply_voltage',
        b'Vr': 'reference_voltage',
        b'Id': 'information',
    }

    @staticmethod
    def parse(raw):
        # 0R0,Dn=000#,Dm=106#,Dx=182#,Sn=1.1#,Sm=4.0#,Sx=6.6#,Ta=16.0C,Ua=50.0P,Pa=1018.1H,Rc=0.00M,Rd=0s,Ri=0.0M,Hc=0.0M,Hd=0s,Hi=0.0M,Rp=0.0M,Hp=0.0M,Th=15.6C,Vh=0.0N,Vs=15.2V,Vr=3.498V,Id=Ant
        # 0R0,Dm=051D,Sm=0.1M,Ta=27.9C,Ua=39.4P,Pa=1003.2H,Rc=0.00M,Th=28.1C,Vh=0.0N
        # here is an unexpected result: no value for Dn!
        # 0R1,Dn=0m=032D,Sm=0.1M,Ta=27.9C,Ua=39.4P,Pa=1003.2H,Rc=0.00M,Th=28.3C,Vh=0.0N

        parsed = dict()
        for part in raw.strip().split(b','):
            cnt = part.count(b'=')
            if cnt == 0:
                # skip the leading identifier 0R0/0R1
                parsed['type'] = part
            elif cnt == 1:
                abbr, vstr = part.split(b'=')
                if abbr == b'Id':  # skip the information field
                    continue
                obs = Station.OBSERVATIONS.get(abbr)
                if obs:
                    value = None
                    unit = None
                    try:
                        # Get the last character as a byte-string
                        unit = vstr[-1:]
                        if unit != b'#':  # '#' indicates invalid data
                            value = float(vstr[:-1])
                    except ValueError as e:
                        print("parse failed for %s (%s):%s" % (abbr, vstr, e))
                    parsed[obs] = value
                else:
                    print("unknown sensor %s: %s" % (abbr, vstr))
            else:
                print("skip observation: '%s'" % part)

        parsed['datetime'] = dt.datetime.now()
        return parsed


if __name__ == '__main__':
    heritage = Station()

    with heritage as h:
        while True:
            data = h.get_composite().strip()
            parsed = Station.parse(data)
            if len(parsed) > 2:
                print("%s" % parsed)
