import pyvisa
import array
import time
import ROOT
import signal


class waveform:
    data = array.array('b')
    vscale = 0.0
    hscale = 0.0
    sampling_rate = 0.0

    def __init__(self):
        data = array.array('b')
        vscale = 0.0
        hscale = 0.0
        sampling_rate = 0.0

    def len(self):
        return len(self.data)

    def print(self):
        print('npoint : ', self.len())
        print('vscale / hscale : ', self.vscale, ' / ', self.hscale)
        print('sampling_rate : ', self.sampling_rate)
        # print('data : ', self.data)

    def parse_waveform(self, wfmdata):

        def get_vhscale(d: str):
            d = d.replace(' ', '')
            val = float("".join([(x if x.isdigit() or x == '.' else '') for x in d]))
            unit = "".join([(x if not (x.isdigit() or x == '.') else '') for x in d]).replace('/div', '')
            return val, unit

        channel_header = wfmdata.split(b';')[5].decode('ascii')
        self.vscale, _ = get_vhscale(channel_header.split(',')[2])
        self.hscale, _ = get_vhscale(channel_header.split(',')[3])
        self.sampling_rate = 1.0 / float(wfmdata.split(b';')[9].decode('ascii'))

        bdata = wfmdata.split(b';')[18]

        def check_firstchar(d):
            return d[0] == ord('#')

        def check_nnpoint(d):
            return int(chr(d[1]))

        def check_npoint(d):
            return int(d[2:2 + check_nnpoint(d)].decode('ascii'))

        def conv_binary(d):
            buf = array.array('b')
            for i in range(check_npoint(d)):
                buf.append(int.from_bytes(d[3 + check_nnpoint(d) + i: 3 + check_nnpoint(d) + i + 1], signed=True))
            return buf

        if not (check_firstchar(bdata)):
            print('ERR: invalid wfm data')
            return {}

        self.data = conv_binary(bdata)

    def convert_float(self):
        buf = []
        for i in range(self.len()):
            buf.append((i / self.sampling_rate, float(self.data[i]) * self.vscale * 10 / 256.0))
        return buf

    def find_edge(self, thr: 0.0, is_falling=True):
        p_pre = 0.0
        v_pre = 0.0
        for p, v in self.convert_float():
            if v < thr and v_pre >= thr:
                return (p - p_pre) / (v - v_pre) * (thr - v_pre) + p_pre
            p_pre = p
            v_pre = v

        return -99999999

    def integral(self, start: float, stop: float):
        sum = 0.0
        for t, v in self.convert_float():
            if (t >= start and t < stop):
                sum = sum + v / self.sampling_rate
        return sum

flag_to_exit_sigint = False

def main():
    global flag_to_exit_sigint
    num_take_data = -1

    def sig_handler(sig, frame):
        if sig == signal.SIGINT:
            global flag_to_exit_sigint
            flag_to_exit_sigint = True


    ofile = ROOT.TFile('osc_data.root', 'RECREATE')
    ntuple = ROOT.TTree('osc_data', 'osc data')
    global_counter = array.array('I', [0])
    epoch = array.array('I', [0])
    ch1 = array.array('f', [-9999999.])
    ch2 = array.array('f', [-9999999.])
    ch3 = array.array('f', [-9999999.])
    ch4 = array.array('f', [-9999999.])
    ch4q = array.array('f', [-9999999.])
    size_obuf = 200000
    waveform_ch4_v = array.array('f', size_obuf * [-9999999999.0])
    waveform_ch4_t = array.array('f', size_obuf * [-9999999999.0])
    ntuple.Branch('Cnt', global_counter, 'Cnt/i')
    ntuple.Branch('epoch', epoch, 'epoch/i')
    ntuple.Branch('Ch1', ch1, 'Ch1/F')
    ntuple.Branch('Ch2', ch2, 'Ch2/F')
    ntuple.Branch('Ch3', ch3, 'Ch3/F')
    ntuple.Branch('Ch4', ch4, 'Ch4/F')
    ntuple.Branch('Ch4Q', ch4q, 'Ch4Q/F')
    ntuple.Branch('Ch4WFM_T', waveform_ch4_t, 'Ch4WFM_T[' + str(size_obuf) + ']/F')
    ntuple.Branch('Ch4WFM_V', waveform_ch4_v, 'Ch4WFM_V[' + str(size_obuf) + ']/F')



    rm = pyvisa.ResourceManager()

    print(rm.list_resources('?*'))

    osc = rm.open_resource('TCPIP::127.0.0.1::4000::SOCKET')
    print(osc)
    osc.read_termination = '\n'
    osc.write_termination = '\n'
    osc.write('*RST')
    time.sleep(1)
    idn = osc.query('*IDN?')
    print(idn)

    filename = '../src/init.cmd'
    with open(filename, 'r') as file:
        lines = file.readlines()
        for line in lines:
            osc.write(line.strip())

    #with open('../src/load.cmd', 'r') as file:
    #    lines = file.readlines()
    #    for line in lines:
    #        osc.write(line.strip())



    def read_waveforms(inst):
        def read_waveform(inst):
            inst.write('WAVF?')
            data = inst.read_raw()
            # print(data)
            wfmdata = waveform()
            wfmdata.parse_waveform(data)

            # wfmdata.print()
            return wfmdata

        data = {}
        for i in range(1, 5):
            buf = 'DAT:SOU CH' + str(i)
            inst.write(buf)
            data[i] = read_waveform(inst)
        return data


    time.sleep(1)

    # print(osc.query('DATA:START?'))
    # print(osc.query('DATA:STOP?'))
    osc.write('DATA:START 0')
    osc.write('DATA:STOP 200000')
    smpl_rate = float(osc.query('HOR:SAMPLER?'))
    print('Sampling rate: ', smpl_rate)

    cnt = 0
    signal.signal(signal.SIGINT, sig_handler)
    load_max = num_take_data if num_take_data > 0 else 10000000000000
    print('Started DAQ...')
    for i in range(load_max):
        if flag_to_exit_sigint:
            print('Exit from loop...')
            break
        try:
            osc.write('*CLS')
            osc.write('ACQ:STATE ON')
            while 1:
                time.sleep(0.0001)
                opc = int(osc.query('*OPC?'))
                # print(opc)
                if opc == 1: break;
            epoch[0] = int(time.time())
            data = read_waveforms(osc)
        except Exception as e:
            print('Exception ', e)
            wait_time = 30
            print('Restart after ',wait_time, ' sec')
            time.sleep(wait_time)
            continue

        edge = {}
        for c in range(1, 5):
            #print('CH' + str(c), len(data[c]))
            # print(data[c])

            # for p, v in data[c]:
            #     print(v, ' ')

            edge[c] = data[c].find_edge( -400, True)
        print('cnt ', global_counter[0], ' ', epoch[0], ' ', edge[1], ' ', edge[2], ' ', edge[3], ' ', edge[4])
        cnt = cnt + 1

        ch1[0] = edge[1]
        ch2[0] = edge[2]
        ch3[0] = edge[3]
        ch4[0] = edge[4]
        wfmbuf = data[4].convert_float()
        for i in range( len(wfmbuf)):
            t,v = wfmbuf[i]
            waveform_ch4_v[i] = v
            waveform_ch4_t[i] = t
        if ch2[0] > 0 :
            ch4q[0] = data[4].integral(-50.0e-9 + edge[2], 200e-9 + edge[2])
        else:
            ch4q[0] = -9999999

        if ch2[0] >= 0:
            ntuple.Fill()
        global_counter[0] = global_counter[0] + 1

    ntuple.Write()
    print('ROOT file saved: ', ofile.GetName())
    ofile.Save()
    ofile.Close()


if __name__ == '__main__':
    main()


