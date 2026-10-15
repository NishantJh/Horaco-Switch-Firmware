import sys
# compact 8051 disassembler
OPS={}
def reg(n):return 'R%d'%n
def build():
    t=[None]*256
    # ops by pattern: (mnemonic format, length)
    # formats: {a}=addr11 ... handle in decode
    return t
SFR={0x80:'P0',0x81:'SP',0x82:'DPL',0x83:'DPH',0x87:'PCON',0x88:'TCON',0x89:'TMOD',0x90:'P1',0x98:'SCON',0x99:'SBUF',0xA0:'P2',0xA8:'IE',0xB0:'P3',0xB8:'IP',0xD0:'PSW',0xE0:'ACC',0xF0:'B'}
def d(a):return SFR.get(a,'%02Xh'%a)
def dec(m,pc):
    o=m[pc]; b1=m[pc+1] if pc+1<len(m) else 0; b2=m[pc+2] if pc+2<len(m) else 0
    lo=o&0xF; hi=o>>4
    rel=lambda n,x:(pc+n+(x-256 if x>127 else x))&0xFFFF
    if lo==1: # ajmp/acall
        a=((o>>5)<<8)|b1
        return 2,('ACALL' if o&0x10 else 'AJMP'),'%04X'%(((pc+2)&0xF800)|a)
    if o==0:return 1,'NOP',''
    if o==2:return 3,'LJMP','%04X'%((b1<<8)|b2)
    if o==0x12:return 3,'LCALL','%04X'%((b1<<8)|b2)
    if o==0x22:return 1,'RET',''
    if o==0x32:return 1,'RETI',''
    if o==0x80:return 2,'SJMP','%04X'%rel(2,b1)
    if o==0x40:return 2,'JC','%04X'%rel(2,b1)
    if o==0x50:return 2,'JNC','%04X'%rel(2,b1)
    if o==0x60:return 2,'JZ','%04X'%rel(2,b1)
    if o==0x70:return 2,'JNZ','%04X'%rel(2,b1)
    if o==0x73:return 1,'JMP','@A+DPTR'
    if o==0x90:return 3,'MOV','DPTR,#%04Xh'%((b1<<8)|b2)
    if o==0xA3:return 1,'INC','DPTR'
    if o==0xE0:return 1,'MOVX','A,@DPTR'
    if o==0xF0:return 1,'MOVX','@DPTR,A'
    if o==0x93:return 1,'MOVC','A,@A+DPTR'
    if o==0x83:return 1,'MOVC','A,@A+PC'
    if o==0xE4:return 1,'CLR','A'
    if o==0xF4:return 1,'CPL','A'
    if o==0x04:return 1,'INC','A'
    if o==0x14:return 1,'DEC','A'
    if o==0x03:return 1,'RR','A'
    if o==0x13:return 1,'RRC','A'
    if o==0x23:return 1,'RL','A'
    if o==0x33:return 1,'RLC','A'
    if o==0xC4:return 1,'SWAP','A'
    if o==0xD4:return 1,'DA','A'
    if o==0xA4:return 1,'MUL','AB'
    if o==0x84:return 1,'DIV','AB'
    if o==0x05:return 2,'INC',d(b1)
    if o==0x15:return 2,'DEC',d(b1)
    if o==0x10:return 3,'JBC','%02Xh,%04X'%(b1,rel(3,b2))
    if o==0x20:return 3,'JB','%02Xh,%04X'%(b1,rel(3,b2))
    if o==0x30:return 3,'JNB','%02Xh,%04X'%(b1,rel(3,b2))
    if o==0xB3:return 1,'CPL','C'
    if o==0xC3:return 1,'CLR','C'
    if o==0xD3:return 1,'SETB','C'
    if o==0xC2:return 2,'CLR','%02Xh'%b1
    if o==0xD2:return 2,'SETB','%02Xh'%b1
    if o==0xB2:return 2,'CPL','%02Xh'%b1
    if o==0x82:return 2,'ANL','C,%02Xh'%b1
    if o==0xB0:return 2,'ANL','C,/%02Xh'%b1
    if o==0x72:return 2,'ORL','C,%02Xh'%b1
    if o==0xA0:return 2,'ORL','C,/%02Xh'%b1
    if o==0xA2:return 2,'MOV','C,%02Xh'%b1
    if o==0x92:return 2,'MOV','%02Xh,C'%b1
    if o==0xC0:return 2,'PUSH',d(b1)
    if o==0xD0:return 2,'POP',d(b1)
    if o==0x75:return 3,'MOV','%s,#%02Xh'%(d(b1),b2)
    if o==0x85:return 3,'MOV','%s,%s'%(d(b2),d(b1))
    if o==0xE5:return 2,'MOV','A,'+d(b1)
    if o==0xF5:return 2,'MOV',d(b1)+',A'
    if o==0x74:return 2,'MOV','A,#%02Xh'%b1
    if o==0xB4:return 3,'CJNE','A,#%02Xh,%04X'%(b1,rel(3,b2))
    if o==0xB5:return 3,'CJNE','A,%s,%04X'%(d(b1),rel(3,b2))
    if o==0xD5:return 3,'DJNZ','%s,%04X'%(d(b1),rel(3,b2))
    if o==0xC5:return 2,'XCH','A,'+d(b1)
    if o==0xA5:return 1,'DB','A5'
    if o in(0x42,0x52,0x62):
        n={0x42:'ORL',0x52:'ANL',0x62:'XRL'}[o];return 2,n,d(b1)+',A'
    if o in(0x43,0x53,0x63):
        n={0x43:'ORL',0x53:'ANL',0x63:'XRL'}[o];return 3,n,'%s,#%02Xh'%(d(b1),b2)
    names={0x2:'ADD',0x3:'ADDC',0x4:'ORL',0x5:'ANL',0x6:'XRL',0x9:'SUBB'}
    if hi in names and lo>=4:
        n=names[hi]
        if lo==4:return 2,n,'A,#%02Xh'%b1
        if lo==5:return 2,n,'A,'+d(b1)
        if lo in(6,7):return 1,n,'A,@R%d'%(lo-6)
        return 1,n,'A,R%d'%(lo-8)
    if lo>=6 and hi==0 : return 1,'INC','@R%d'%(lo-6) if lo<8 else 'R%d'%(lo-8)
    if lo>=6 and hi==1 : return 1,'DEC','@R%d'%(lo-6) if lo<8 else 'R%d'%(lo-8)
    if hi==7 and lo>=8:return 2,'MOV','R%d,#%02Xh'%(lo-8,b1)
    if hi==7 and lo in(6,7):return 2,'MOV','@R%d,#%02Xh'%(lo-6,b1)
    if hi==8 and lo>=8:return 2,'MOV','%s,R%d'%(d(b1),lo-8)
    if hi==8 and lo in(6,7):return 2,'MOV','%s,@R%d'%(d(b1),lo-6)
    if hi==0xA and lo>=8:return 2,'MOV','R%d,%s'%(lo-8,d(b1))
    if hi==0xA and lo in(6,7):return 2,'MOV','@R%d,%s'%(lo-6,d(b1))
    if hi==0xF and lo>=8:return 1,'MOV','R%d,A'%(lo-8)
    if hi==0xF and lo in(6,7):return 1,'MOV','@R%d,A'%(lo-6)
    if hi==0xE and lo>=8:return 1,'MOV','A,R%d'%(lo-8)
    if hi==0xE and lo in(6,7):return 1,'MOV','A,@R%d'%(lo-6)
    if hi==0xE and lo in(2,3):return 1,'MOVX','A,@R%d'%(lo-2)
    if hi==0xF and lo in(2,3):return 1,'MOVX','@R%d,A'%(lo-2)
    if hi==0xB and lo>=8:return 3,'CJNE','R%d,#%02Xh,%04X'%(lo-8,b1,rel(3,b2))
    if hi==0xB and lo in(6,7):return 3,'CJNE','@R%d,#%02Xh,%04X'%(lo-6,b1,rel(3,b2))
    if hi==0xD and lo>=8:return 2,'DJNZ','R%d,%04X'%(lo-8,rel(2,b1))
    if hi==0xC and lo>=8:return 1,'XCH','A,R%d'%(lo-8)
    if hi==0xC and lo in(6,7):return 1,'XCH','A,@R%d'%(lo-6)
    if hi==0xD and lo in(6,7):return 1,'XCHD','A,@R%d'%(lo-6)
    return 1,'DB','%02X'%o
def disasm(m,start,end,base=0):
    pc=start
    while pc<end:
        n,mn,op=dec(m,pc)
        print('%05X: %-14s %s %s'%(pc+base,m[pc:pc+n].hex(' '),mn,op))
        pc+=n
if __name__=='__main__':
    m=open(sys.argv[1],'rb').read()
    disasm(m,int(sys.argv[2],0),int(sys.argv[3],0))
