:SEL:CH1 ON;:CH1:PRO:GAIN 1.0;:CH1:SCA 0.5;
:SEL:CH2 ON;:CH2:PRO:GAIN 1.0;:CH2:SCA 0.5;
:SEL:CH3 ON;:CH3:PRO:GAIN 1.0;:CH3:SCA 0.5;
:SEL:CH4 ON;:CH4:PRO:GAIN 1.0;:CH4:SCA 0.05;
:HOR:SCA 400e-9;:HOR:RESO 200000;:HOR:TRIG:POS 80;
:WFMI:NR_P 10000;
:TRIG:A:EDGE:SLO FALL;:TRIG:A:EDGE:SOU CH1;:TRIG:A:LEV -0.4;:TRIG:A:MOD NORM;
:ACQ:MOD SAM;:ACQ:STOPA SEQ;
WFMO:ENC BIN
ACQ:STOPA SEQ
