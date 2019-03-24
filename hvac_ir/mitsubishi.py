#!/usr/bin/env python3

import datetime


class MitsubishiCommand_W001CP(object):

    _header = '00100011' + '11001011' + '00100110' + '00100001' + '00000000'

    # protocol informations
    protocol_bytes = 17
    protocol_repeats = 1
    protocol_parameters = {'power': (True, False),
                           'hvac_mode': ('heat', 'dry', 'cold', 'auto', 'fan'),
                           'temperature': tuple(range(16, 32)),
                           'fan': (1, 2, 3, 4),
                           'vane': ('auto', 0, 1, 2, 3),
                          }

    # pyslinger settings
    pyslinger_protocol = "NEC"
    pyslinger_protocol_config = dict(frequency=38000,
                                     duty_cycle=0.5,
                                     leading_pulse_duration=3245,
                                     leading_gap_duration=1590,
                                     one_pulse_duration=400,
                                     one_gap_duration=1210,
                                     zero_pulse_duration=400,
                                     zero_gap_duration=425,
                                     trailing_pulse_duration=440,
                                     trailing_gap_duration=17100)

    def __init__(self, power=False, hvac_mode='auto', temperature=24,
                 fan=1, vane='auto', timer='timer_off', timer_on=0, timer_off=0):
        self.power = power
        self.hvac_mode = hvac_mode
        self.temperature = temperature
        self.fan = fan
        self.vane = vane
        self.timer = timer
        self.timer_on = timer_on
        self.timer_off = timer_off

    def __str__(self):
        parms = ['power=%s' % self.power,
                 'hvac_mode=%s' % self.hvac_mode,
                 'temperature=%s' % self.temperature,
                 'fan=%s' % self.fan,
                 'vane=%s' % self.vane]
        my_str = '<MitsubishiCommand_W001CP(' + ', '.join(parms) + ')>'
        return my_str

    def encode(self, lsb=True):
        # bytes 0~4: constant header
        bitstring = self._header
        # byte 5: power status on / off
        bitstring += self.encode_power()
        # byte 6: temperature + HVAC mode
        bitstring += self.encode_temperature()  # 4 bits
        bitstring += self.encode_hvac_mode()    # 4 bits
        # byte 7: FAN & vanne
        bitstring += self.encode_vane()         # 4 bits
        bitstring += self.encode_fan()          # 4 bits
        # byte 8: timer mode
        bitstring += '00000100' # not yet implemented
        # byte 9: PowerOff countdown (in 1/6th hours)
        bitstring += '0' * 8    # not yet implemented
        # byte 10: PowerOn  countdown (in 1/6th hours)
        bitstring += '0' * 8    # not yet implemented
        # bytes 11~16: XOR of bytes 5~10
        bitstring += self.checksum(bitstring)
        # reverse to Least Significant Bit first if required
        if lsb:
            reversed_bitstring = ''
            for _ in range(0, len(bitstring), 8):
                reversed_bitstring += bitstring[_:_+8][::-1]
            bitstring = reversed_bitstring
        # sanity check and we're done
        if len(bitstring) != 136:
            raise RuntimeError('bitstring should be 136 bits but it is %d' % len(bitstring))
        return bitstring

    def encode_power(self):
        if self.power is True:
            return '01000000'
        elif self.power is False:
            return '00000000'
        else:
            raise ValueError

    def encode_temperature(self):
        if not 16 <= self.temperature <= 31:
            raise ValueError
        temp = self.temperature - 16
        bitstring = "{0:04b}".format(temp)
        return bitstring

    def encode_hvac_mode(self):
        if self.hvac_mode == 'fan':
            return '0000'
        elif self.hvac_mode == 'cold':
            return '0001'
        elif self.hvac_mode == 'heat':
            return '0010'
        elif self.hvac_mode == 'auto':
            return '0011'
        elif self.hvac_mode == 'dry':
            return '0101'
        else:
            raise ValueError

    def encode_vane(self):
        if self.vane not in self.protocol_parameters['vane']:
            raise ValueError('wrong vane value %s' % repr(self.vane))
        vane = 12 if self.vane == 'auto' else self.vane
        bitstring = "{0:04b}".format(vane)
        return bitstring

    def encode_fan(self):
        bitstring = '0'
        if isinstance(self.fan, int) and 0 < self.fan < 5:
            bitstring += "{0:02b}".format(self.fan - 1)
        else:
            raise ValueError('invalid fan value %s' % repr(self.fan))
        bitstring += '1'
        return bitstring

    @staticmethod
    def checksum(bitstring):
        if len(bitstring) != 88:
            raise ValueError('bitstring to checksum is %d bits' % len(bitstring))
        if isinstance(bitstring, tuple):
            bitstring = ''.join(bitstring)
        # calculate checksum
        checksum_bitstring = ''
        for pos in range(5, 11):
            my_byte = bitstring[8*pos:8*pos+8]
            my_value = int("".join(str(i) for i in my_byte), 2)
            xor_value = 255 ^ my_value
            checksum_bitstring += "{0:08b}".format(xor_value)
        return checksum_bitstring

    @classmethod
    def from_dump(cls, binary_dump):
        # https://github.com/r45635/HVAC-IR-Control/blob/master/Protocol/Mitsubishi_W001CP_IR_Packet_Data_v1.0-FULL.pdf
        binary_dump = tuple([int(_) for _ in binary_dump])
        # bytes 0~4: constant header
        header = ''.join(str(_) for _ in binary_dump[0:40])
        if header != cls._header:
            raise ValueError('wrong header: %s' % header)
        # byte 5: power status on / off
        if binary_dump[40:48] == (0, 0, 0, 0, 0, 0, 0, 0):
            power = False
        elif binary_dump[40:48] == (0, 1, 0, 0, 0, 0, 0, 0):
            power = True
        else:
            raise ValueError('wrong power byte: ' + repr(binary_dump[40:48]))
        # byte 6: temperature + HVAC mode
        temperature = 16 + int("".join(str(i) for i in binary_dump[48:52]), 2)
        if binary_dump[52:56] == (0, 0, 0, 0):
            hvac_mode = 'fan'
        elif binary_dump[52:56] == (0, 0, 0, 1):
            hvac_mode = 'cold'
        elif binary_dump[52:56] == (0, 0, 1, 0):
            hvac_mode = 'heat'
        elif binary_dump[52:56] == (0, 0, 1, 1):
            hvac_mode = 'auto'
        elif binary_dump[52:56] == (0, 1, 0, 1):
            hvac_mode = 'dry'
        else:
            raise ValueError('wrong HVAC mode (%s)' % repr(binary_dump[52:56]))
        # byte 7: FAN & vanne
        my_byte = binary_dump[56:64]
        fan = int("".join(str(i) for i in my_byte[4:7]), 2) + 1
        if not 0 < fan < 5:
            raise ValueError('wrong fan speed %d: %s' % (fan, repr(my_byte[4:8])))
        vane = int("".join(str(i) for i in my_byte[0:4]), 2)
        if vane == 12:
            vane = 'auto'
        # byte  8: timer mode
        my_byte = binary_dump[64:72]
        if my_byte[0:6] != (0, 0, 0, 0, 0, 1):
            raise ValueError('wrong timer mode byte: ' + repr(my_byte))
        if my_byte[6:8] == (0, 0):
            timer_mode = 'timer_off'
        elif my_byte[6:8] == (0, 1):
            timer_mode = 'timer_powreoff'
        elif my_byte[6:8] == (1, 0):
            timer_mode = 'timer_poweron'
        elif my_byte[6:8] == (1, 1):
            timer_mode = 'timer_poweronoff'
        else:
            raise ValueError('wrong timer mode byte: ' + repr(my_byte))
        # byte  9: PowerOff countdown (in 1/6th hours)
        my_byte = binary_dump[72:80]
        timer_on = int(''.join(str(i) for i in my_byte), 2)
        # byte 10: PowerOn  countdown (in 1/6th hours)
        my_byte = binary_dump[80:88]
        timer_off = int(''.join(str(i) for i in my_byte), 2)
        # bytes 11~16: XOR of bytes 5~10
        checksum = 'check_OK'
        for pos in range(5, 11):
            my_byte = binary_dump[8*pos:8*pos+8]
            my_value = int("".join(str(i) for i in my_byte), 2)
            xor_byte = binary_dump[8*pos+48:8*pos+56]
            xor_value = int("".join(str(i) for i in xor_byte), 2)
            if xor_value != (255 ^ my_value):
                checksum = 'check_BAD'
        return {'power': power, 'hvac_mode': hvac_mode, 'temperature': temperature, 'fan': fan,
                'vane': vane, 'timer_mode': timer_mode, 'timer_on': timer_on,
                'timer_off': timer_off, 'checksum': checksum}

class MitsubishiCommand_SG14D(object):
    '''Mitsubishi SG14D remote control
    off       --> heat_17_1: rimane almeno 35min <50W
    heat_17_1 --> heat_28_1: ~ 1 minuto ramp up fino a ~600W, poi fino a 1300W
    heat_28_1 --> off      : consumi zero in <30s
    '''
    _header = '00100011' + '11001011' + '00100110' + '00000001' + '00000000'
    _footer = '00010' + '00000000' + '00000000'

    # protocol informations
    protocol_bytes = 18
    protocol_repeats = 2
    protocol_parameters = {'power': (True, False),
                           'hvac_mode': ('heat', 'dry', 'cold', 'auto', 'fan'),
                           'isee': (True, False),
                           'temperature': tuple(range(16, 32)),
                           'fan': ('auto', 'quiet', 1, 2, 3, 4),
                           'vane': ('auto', 1, 2, 3, 4, 5, 'move'),
                           'econocool': (True, False)
                          }

    # pyslinger settings
    pyslinger_protocol = "NEC"
    # see https://github.com/r45635/HVAC-IR-Control/blob/master/python/hvac_ircontrol/mitsubishi.py
    pyslinger_protocol_config = dict(frequency=38000,
                                     duty_cycle=0.5,
                                     leading_pulse_duration=3500,   # 3400
                                     leading_gap_duration=1600,     # 1750
                                     one_pulse_duration=400,        #  450
                                     one_gap_duration=1300,         # 1300
                                     zero_pulse_duration=400,       #  450
                                     zero_gap_duration=450,         #  420
                                     trailing_pulse_duration=440,
                                     trailing_gap_duration=17100)

    def __init__(self, power=False, hvac_mode='cold', isee=False,
                 temperature=24, fan='auto', vane='auto', econocool=False):
        self.power = power
        self.hvac_mode = hvac_mode
        self.isee = isee
        self.temperature = temperature
        self.fan = fan
        self.vane = vane
        self.econocool = econocool

    def __str__(self):
        parms = ['power=%s' % self.power,
                 'hvac_mode=%s' % self.hvac_mode,
                 'temperature=%s' % self.temperature,
                 'fan=%s' % self.fan,
                 'vane=%s' % self.vane,
                 'econocool=%s' % self.econocool,
                 'isee=%s' % self.isee]
        my_str = '<MitsubishiCommand_SG14D(' + ', '.join(parms) + ')>'
        return my_str

    def encode(self, lsb=True):
        # bytes 0~4: constant header
        bitstring = self._header
        # byte 5: power status
        bitstring += self.encode_power()
        # byte 6: HVAC mode
        bitstring += self.encode_hvac_mode()
        # byte 7: temperature
        bitstring += self.encode_temperature()
        # byte 8: HVAC mode (again)
        bitstring += self.encode_hvac_again()
        # byte 9: fan & vanne
        bitstring += self.encode_fan_vanne()
        # byte 10: clock
        bitstring += self.encode_timeofday(datetime.datetime.now())
        # bytes 11, 12: start and end clock (to be done)
        bitstring += '0' * 8 * 2
        # byte 13: timer mode (to be done)
        # ...and possibly Area Mode?
        bitstring += '0' * 8
        # byte 14: econocool
        bitstring += self.encode_econocool()
        # byte 15 & 16: constant
        bitstring += self._footer
        # byte 17: checksum
        bitstring += self.checksum(bitstring)
        # reverse to Least Significant Bit first if required
        if lsb:
            reversed_bitstring = ''
            for _ in range(0, len(bitstring), 8):
                reversed_bitstring += bitstring[_:_+8][::-1]
            bitstring = reversed_bitstring
        # sanity check and we're done
        if len(bitstring) != 144:
            raise RuntimeError
        return bitstring

    @staticmethod
    def checksum(bitstring):
        if len(bitstring) != 136:
            raise ValueError('expected string of 136 bits but received a %d bits one' %
                             len(bitstring))
        if isinstance(bitstring, tuple):
            bitstring = ''.join(bitstring)
        # calculate checksum
        checksum = 0
        for _ in range(17):
            byte_value = int(bitstring[_*8:_*8+8], 2)
            checksum += byte_value
        checksum %= 256
        # bring it back to binary string representation
        return "{0:08b}".format(checksum)

    def encode_power(self):
        if self.power is True:
            return '00100000'
        elif self.power is False:
            return '00000000'
        else:
            raise ValueError

    def encode_hvac_mode(self):
        bitstring = '0'
        if self.isee is True:
            bitstring += '1'
        elif self.isee is False:
            bitstring += '0'
        else:
            raise ValueError
        if self.hvac_mode == 'auto':
            bitstring += '100'
        elif self.hvac_mode == 'heat':
            bitstring += '001'
        elif self.hvac_mode == 'dry':
            bitstring += '010'
        elif self.hvac_mode == 'cold':
            bitstring += '011'
        elif self.hvac_mode == 'fan':
            bitstring += '111'
        else:
            raise ValueError
        bitstring += '000'
        return bitstring

    def encode_temperature(self):
        bitstring = '0000'
        if not 16 <= self.temperature <= 31:
            raise ValueError
        temp = self.temperature - 16
        bitstring += "{0:04b}".format(temp)
        return bitstring

    def encode_hvac_again(self):
        bitstring = '00110'
        if self.hvac_mode == 'auto':
            bitstring += '110'
        elif self.hvac_mode == 'heat':
            bitstring += '000'
        elif self.hvac_mode == 'dry':
            bitstring += '010'
        elif self.hvac_mode == 'cold':
            bitstring += '110'
        elif self.hvac_mode == 'fan':
            bitstring += '000'
        else:
            raise ValueError
        return bitstring

    def encode_fan_vanne(self):
        '''encode byte 9 (fan & vanne parameters)'''
        # first two bits *seem* to command the HVAC unit beeper
        # 01 = single standard beep
        # 10 = double short beep
        #       |- used when switching to temperature extremes (16 & 31 C)
        #       |- used when switching from manual to auto fan
        #       \- used when switching from manual to auto vane
        if self.temperature in (16, 31):
            bitstring = '10'
        else:
            bitstring = '01'
        # the following 3 bits are the vane setting: 0=auto, N=fixed position, -1=move
        if self.vane == 'auto':
            bitstring += '000'
        elif self.vane == 1:
            bitstring += '001'
        elif self.vane == 2:
            bitstring += '010'
        elif self.vane == 3:
            bitstring += '011'
        elif self.vane == 4:
            bitstring += '100'
        elif self.vane == 5:
            bitstring += '101'
        elif self.vane == 'move':
            bitstring += '111'
        else:
            raise ValueError
        # the following 3 bits are the fan settings: 0=auto, N=fixed speed, -2=quiet
        if self.fan == 'auto':
            bitstring += '000'
        elif self.fan == 1:
            bitstring += '001'
        elif self.fan == 2:
            bitstring += '010'
        elif self.fan == 3:
            bitstring += '011'
        elif self.fan == 4:
            bitstring += '100'
        elif self.fan == 'quiet':
            bitstring += '101'
        else:
            raise ValueError
        return bitstring

    def encode_timeofday(self, time_of_day):
        # time is represented as the count of 10-minute intervals from midnight
        # eg. 15:53 is 15*60 + 5
        time_counter = time_of_day.hour * 6
        time_counter += time_of_day.minute // 10
        bitstring = "{0:08b}".format(time_counter)
        return bitstring

    def encode_econocool(self):
        if self.econocool is True:
            return '001'
        elif self.econocool is False:
            return '000'
        else:
            raise ValueError

    @classmethod
    def from_dump(cls, binary_dump):
        # https://github.com/r45635/HVAC-IR-Control/tree/master/Protocol
        binary_dump = tuple([int(_) for _ in binary_dump])
        # check length
        if len(binary_dump) != cls.protocol_bytes * 8:
            raise ValueError('length of %d bits does not match protocol length %d bits' %
                             (len(binary_dump), cls.protocol_bytes * 8))
        # bytes 0~4: constant
        header = ''.join(str(_) for _ in binary_dump[0:40])
        if header != cls._header:
            raise ValueError('wrong header: %s instead of %s' % (header, cls._header))
        # byte 5: power status on / off
        if binary_dump[40:48] == (0, 0, 0, 0, 0, 0, 0, 0):
            power = False
        elif binary_dump[40:48] == (0, 0, 1, 0, 0, 0, 0, 0):
            power = True
        else:
            raise ValueError('wrong power byte: ' + repr(binary_dump[40:48]))
        # byte 6: HVAC mode + iSee
        if binary_dump[48] != 0 or binary_dump[53:56] != (0, 0, 0):
            raise ValueError('wrong HVAC mode')
        isee = bool(binary_dump[49])
        if binary_dump[50:53] == (1, 0, 0):
            hvac_mode = 'auto'
        elif binary_dump[50:53] == (0, 0, 1):
            hvac_mode = 'heat'
        elif binary_dump[50:53] == (0, 1, 0):
            hvac_mode = 'dry'
        elif binary_dump[50:53] == (0, 1, 1):
            hvac_mode = 'cold'
        elif binary_dump[50:53] == (1, 1, 1):
            hvac_mode = 'fan'
        else:
            raise ValueError('wrong HVAC mode (%s)' % repr(binary_dump[49:53]))
        # byte 7: temperature
        if binary_dump[56:60] != (0, 0, 0, 0):
            raise ValueError('wrong temperature byte')
        #temperature = 'temp_%d' % (16 + int("".join(str(i) for i in binary_dump[60:64]), 2))
        temperature = 16 + int("".join(str(i) for i in binary_dump[60:64]), 2)
        # byte 8: HVAC mode, again
        # TBD: we currently ignore this one
        # byte 9: FAN & vanne
        byte9 = binary_dump[72:80]
        fan = int("".join(str(i) for i in binary_dump[77:80]), 2)
        if 0 < fan < 5:
            pass
        elif fan == 0:
            fan = 'auto'
        elif fan == 5:
            fan = 'quiet'
        else:
            raise ValueError('wrong fan speed %d (0=%s, 5-7=%s)' %
                             (fan, byte9[0], repr(byte9[5:8])))
        if byte9[2:5] == (1, 1, 1):
            vane = 'move'
        else:
            vane = int("".join(str(i) for i in byte9[2:5]), 2)
            if vane == 0:
                vane = 'auto'
        # byte 10: clock
        # byte 11: end time
        # byte 12: start time
        # byte 13: timer mode
        # byte 14: constants + econocool (bits 112 -> 120)
        econocool = bool(binary_dump[114])                  # third bit is econocool
        # bytes 14x & 15~16: constants                      # fourth bit of byte 14 and onwards
        footer = ''.join(str(_) for _ in binary_dump[115:136])
        if footer != cls._footer:
            raise ValueError('wrong header: %s instead of %s' % (footer, cls._footer))
        # byte 17: checksum
        checksum = 0
        for _ in range(17):
            byte_value = int("".join(str(i) for i in binary_dump[_*8:_*8+8]), 2)
            checksum += byte_value
        checksum %= 256
        pkt_checksum = int("".join(str(i) for i in binary_dump[136:144]), 2)
        if checksum != pkt_checksum:
            checksum = 'check_BAD'
        else:
            checksum = 'check_OK'
        return {'power': power, 'isee': isee, 'hvac_mode': hvac_mode, 'temperature': temperature,
                'fan': fan, 'vane': vane, 'econocool': econocool, 'checksum': checksum}
