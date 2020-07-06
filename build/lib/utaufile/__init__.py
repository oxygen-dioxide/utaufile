__version__='0.0.3'

import math
import numpy as np

#UTAU
class Ustnote():
    '''
    ust音符类
    length:时长，480为一拍，int
    lyric:歌词，str
    notenum:音高,C4为60，int
    properties:其他所有数据，dict
    properties中，以"_"开头的键被视为临时变量，不被写入UST文件
    '''
    def __init__(self,length:int,
                 lyric:str,
                 notenum:int,
                 properties:dict={}):
        if(properties=={}):
            properties={}
        self.length=length
        self.lyric=lyric
        self.notenum=notenum 
        self.properties=properties
        
    def __str__(self):
        s="Length={}\nLyric={}\nNoteNum={}\n".format(self.length,self.lyric,self.notenum)
        for i in self.properties.keys():
            if(not i.startswith("_")):
                s+="{}={}\n".format(i,self.properties[i])
        return s
    
    def isR(self)->bool:
        '''
        判断音符是否为休止符(“r”,“R”,“”,“ ”)
        '''
        return (self.lyric in [""," ","r","R"])

    def to_music21_note(self):
        import music21
        if(self.isR()):
            n=music21.note.Rest()
        else:
            n=music21.note.Note(self.notenum)
            n.lyric=self.lyric
        n.duration=music21.duration.Duration(self.length/480)
        return n

class Ustfile():
    '''
    ust文件类
    properties:工程整体属性(即[#SETTING]块),dict
    note:音符，list                    
    '''
    def __init__(self,properties:dict={},note:list=[]):
        if(note==[]):
            note=[]
        if(properties=={}):
            properties={}
        self.properties=properties
        self.note=note
        
    def __str__(self):
        s='[#SETTING]\n'
        for i in self.properties.keys():
            s+="{}={}\n".format(i,self.properties[i])
        for i in range(0,len(self.note)):
            s+='[#{:0>4}]\n'.format(i)
            s+=str(self.note[i])
        s+="[#TRACKEND]\n"
        return s
    
    def save(self,filename:str):
        '''
        保存UST文件
        '''
        with open(filename,"w",encoding='utf8') as file:
            file.write("[#VERSION]\nUST Version1.2\nCharset=UTF-8\n")
            file.write(str(self))
        
    def getlyric(self,start:int=0,end:int=0,ignoreR:bool=True)->list:
        '''
        获取歌词,返回歌词列表
        start：指定获取歌词区间的起点
        end：指定获取歌词区间的终点
        ignoreR：忽略休止符
        '''
        if(end==0):
            end=len(self.note)
        lyric=[]
        if(ignoreR):
            for i in self.note[start:end]:
                if(not i.isR()):
                    lyric+=[i.lyric]
        else:
            for i in self.note[start:end]:
                lyric+=[i.lyric]
        return lyric
    
    def replacelyric(self,dictionary:dict,start:int=0,end:int=0):
        '''
        按字典替换歌词
        start：指定替换歌词区间的起点
        end：指定替换歌词区间的终点
        '''
        if(end==0):
            end=len(self.note)
        for i in range(0,len(self.note))[start:end]:
            self.note[i].lyric=dictionary.get(self.note[i].lyric,self.note[i].lyric)
        return self
    
    def setlyric(self,lyrics:list,start:int=0,end:int=0,ignoreR:bool=True):
        '''
        批量输入歌词
        lyrics:输入歌词列表
        start：指定输入歌词区间的起点
        end：指定输入歌词区间的终点
        ignoreR：忽略休止符
        如果输入歌词列表的长度大于输入歌词区间的有效音符数，则多出的歌词将不会被使用
        如果输入歌词列表的长度小于输入歌词区间的有效音符数，则多出的音符歌词不变
        '''
        if(end==0):
            end=len(self.note)
        if(ignoreR):
            j=0
            l=len(lyrics)
            for i in range(0,len(self.note))[start:end]:
                if(not self.note[i].isR()):
                    if(j>=l):
                        break
                    self.note[i].lyric=lyrics[j]
                    j=j+1
        else:
            j=0
            l=len(lyrics)
            for i in range(0,len(self.note))[start:end]:
                if(j>=l):
                    break
                self.note[i].lyric=lyrics[j]
                j=j+1
        return self
    
    def nrange(self)->tuple:
        '''
        获取ust工程的音域
        返回元组：(最低音,最高音+1)
        '''
        notenums=[i.notenum for i in self.note if (not i.isR())]
        return (min(notenums),max(notenums)+1)
    
    def length(self)->int:
        '''
        获取ust工程的总长度
        '''
        return sum([i.length for i in self.note])
    
    def quantize(self,d:int):
        '''
        将UST工程按照给定的分度值（四分音符为480）量化。
        将所有音符的边界四舍五入到d的整数倍，过短的音符将被删除。
        例如，如果需要量化到八分音符，请使用f.quantize(240)
        '''
        note_new=[]
        tick=0
        for i in self.note:
            tick_c=int(round((tick+i.length)/d))*d
            i.length=tick_c-tick
            if(i.length>0):
                note_new+=[i]
            tick=tick_c
        self.note=note_new
        return self
        
    def to_midi_track(self):
        '''
        将ust文件对象转换为mido.MidiTrack对象
        '''
        import mido
        track=mido.MidiTrack()
        tick=0
        for note in self.note:
            if(note.isR()):
                tick+=note.length
            else:
                track.append(mido.MetaMessage('lyrics',text=note.lyric,time=tick))
                tick=0
                track.append(mido.Message('note_on', note=note.notenum,velocity=64,time=0))
                track.append(mido.Message('note_off',note=note.notenum,velocity=64,time=note.length))
        track.append(mido.MetaMessage('end_of_track'))
        return(track)
    
    def to_midi_file(self,filename:str=""):
        '''
        将ust文件对象转换为mid文件和mido.MidiFile对象
        '''
        import mido
        mid = mido.MidiFile()
        ctrltrack=mido.MidiTrack()
        ctrltrack.append(mido.MetaMessage('track_name',name='Control',time=0))
        ctrltrack.append(mido.MetaMessage('set_tempo',tempo=mido.bpm2tempo(self.properties.get("Tempo",120)),time=0))
        mid.tracks.append(ctrltrack)
        mid.tracks.append(self.to_midi_track())
        if(filename!=""):
            mid.save(filename)
        return mid
    
    def to_nn_file(self):
        '''
        将ust文件对象转换为nn文件对象
        '''
        nn=Nnfile(tempo=self.properties.get("Tempo",120))
        time=0
        for i in self.note:
            starttime=time
            time+=i.length
            if(not i.isR()):
                nn.note+=[Nnnote(hanzi=i.lyric,
                                pinyin=i.lyric,
                                start=starttime//60,
                                length=time//60-starttime//60,
                                notenum=i.notenum)]
        return nn

    def to_music21_stream(self):
        '''
        将ust文件对象转换为music21 stream，并自动判断调性
        '''
        #其他文件转music21 stream，将一律先转UST，再转music21 stream
        #因为UST将音轨描述为音符和休止符组成，这与music21不谋而合
        import music21
        st=music21.stream.Stream()
        for n in self.note:
            st.append(n.to_music21_note())
        st.insert(0,st.analyze("key"))
        ks=st.keySignature
        #由于music21音符默认带有还原符号，需要一个个消除
        for n in st.notes:
            if(ks.getScaleDegreeAndAccidentalFromPitch(n.pitch)[1]==None and n.pitch.accidental==music21.pitch.Accidental(0)):
                n.pitch.accidental=None
        return st

def ustvaluetyper(key,value):#根据ust中的键决定值的类型
    types={
        "Length":int,
        "NoteNum":int,
        "Tempo":float,
        "Tracks":int,
        "Mode2":bool,
        "PreUtterance":float,
        "VoiceOverlap":int,
        "Velocity":int,
        "Intensity":int,
        "Modulation":int,
        "$direct":bool}
    str2bool={"True":True,"true":True,"False":False,"false":False}
    valuetype=types.get(key,str)
    if(valuetype==bool):
        return str2bool[value]
    elif(valuetype==str):
        return value
    else:
        return valuetype(value)

def openust(filename:str):
    '''
    打开ust文件，返回Ustfile对象
    '''
    #读ust文件
    with open(filename,'rb') as f:
        file=f.read()

    #读取编码
    if(b"Charset=UTF-8" in file):
        encoding="utf-8"
    else:
        encoding="shift-JIS"
    #分块
    blocks=[]
    block=[]
    for line in file.split(b"\n"):
        line=line.strip(b"\r")
        #逐行解码
        try:
            line=str(line,encoding=encoding)
        except:
            #如果某行编码与其他行不同，则尝试各种编码
            for i in ["gbk","utf-8","shift-JIS"]:
                try:
                    line=str(line,encoding=i)
                except:
                    pass
        if(line.startswith("[")):
            blocks+=[block]
            block=[]
        block+=[line]
    #读文件头
    fileproperties={}
    for line in blocks[2]:
        if("=" in line):
            [key,value]=line.split("=")
            if(value!=""):
                fileproperties[key]=ustvaluetyper(key,value)
    #读音符
    notes=[]
    for block in blocks[3:]:
        noteproperties={}
        for line in block:
            if("=" in line):
                [key,value]=line.split("=")
                if(value!=""):
                    noteproperties[key]=ustvaluetyper(key,value)
        length=noteproperties.pop("Length")
        notenum=noteproperties.pop("NoteNum")
        lyric=noteproperties.pop("Lyric")
        notes+=[Ustnote(length,lyric,notenum,noteproperties)]
    return Ustfile(fileproperties,notes)

def readint(flag):
    for i in range(0,len(flag)):
        if(not flag[i] in ("+","-","1","2","3","4","5","6","7","8","9","0")):
            break
    else:
        i+=1
    value=int(flag[0:i])
    flag=flag[i:]
    return(flag,value)
    
def parseflag(flag:str,flagtype:set,usedefault=False)->dict:
    '''
    解析flag，返回字典
    flagtype：由元组组成的集合，每个元组第0项为字符串,例如"b","g","Mt"等，第1项为默认值。可参考utaufile.flag库
    usedefault：如果为True，则返回的字典会包含输入flag中没有的条目，且代入默认值
    '''
    if(usedefault):
        flagdict={i[0]:i[1] for i in flagtype}
    else:
        flagdict={}
    while(flag!=""):
        for i in flagtype:
            if(flag.startswith(i[0])):
                flag=flag[len(i)-1:]
                if(type(i[1])==int):
                    (flag,value)=readint(flag)
                    flagdict[i[0]]=value
                elif(type(i[1])==bool):
                    flagdict[i[0]]=True
                break
        else:
            flag=flag[1:]
    return flagdict

def dumpflag(flagdict:dict)->str:
    '''
    将flag字典转换为字符串
    '''
    flag=""
    for (key,value) in flagdict.items():
        if(value==True):
            flag+=key
        elif(type(value)==int):
            flag+=key+str(value)
    return flag
#NN
class Nnnote():
    '''
    nn音符类
    hanzi:歌词汉字，str
    pinyin:歌词拼音，str
    start:起点，以32分音符为单位（四分音符为8），int
    length:长度，以32分音符为单位，int
    notenum:音高，与midi及ust相同，即C4为60，音高越高，数值越大，int
    注意：该notenum的表示法与nn文件不同，nn文件中音高的表示方法为B5为0，音高越低，数值越大
    83-notenum
    cle:清晰度，int
    vel:急促度，int
    por:滑音起始，int
    viblen:颤音长度，int
    vibdep:颤音幅度，int
    vibrat:颤音速率，int
    dyn:音量曲线，取值范围0~100，numpy.ndarray
    pit:音高曲线，以50为基准，取值范围0~100，numpy.ndarray
    pbs:音高弯曲灵敏度，取值范围是0至11，但实际上表示1至12，int
    '''
    def __init__(self,hanzi:str,pinyin:str,start:int,length:int,
            notenum:int,cle:int=50,vel:int=50,por:int=0,
            viblen:int=0,vibdep:int=0,vibrat:int=0,dyn=np.ones(100)*50,
            pit=np.ones(100)*50,pbs:int=0):
        self.hanzi=hanzi
        self.pinyin=pinyin
        self.start=start
        self.length=length
        self.notenum=notenum
        self.cle=cle
        self.vel=vel
        self.por=por
        self.viblen=viblen
        self.vibdep=vibdep
        self.vibrat=vibrat
        self.dyn=dyn
        self.pit=pit
        self.pbs=pbs

    def __str__(self):
        s=" ".join(["",self.hanzi,
            self.pinyin,
            str(self.start),
            str(self.length),
            str(83-self.notenum),
            str(self.cle),
            str(self.vel),
            str(self.por),
            str(self.viblen),
            str(self.vibdep),
            str(self.vibrat),
            ",".join(["100"]+[str(int(i)) for i in self.dyn]),
            ",".join(["100"]+[str(int(i)) for i in self.pit]),
            str(self.pbs)])+"\n"
        return s
    def getpitbend(self):
        '''
        获得音符的pit参数对音符的作用量（pit*pbs）,单位为半音，返回numpy.ndarray
        '''
        return (self.pit-50)*(self.pbs+1)/50
    
    def setpitbend(self,pitbend):
        '''
        设置音符的pit参数对音符的作用量（pit*pbs）,单位为半音，输入类型为长度100的numpy.ndarray
        '''
        self.pbs=min(math.ceil(max(abs(pitbend))),12)-1
        self.pit=(pitbend/(self.pbs+1)*50+50)
        
class Nnfile():
    '''
    nn文件类
    tempo:曲速，float
    beats:节拍，元组，第0项为每小节拍数，第1项为以X分音符为1拍
    note:音符，Nnnote的列表
    '''
    def __init__(self,tempo:int=120,beats:tuple=(4,4),note:list=[]):
        if(note==[]):
            note=[]
        self.tempo=tempo
        self.beats=beats
        self.note=note
            
    def sort(self):
        '''
        音符按开始时间排序
        '''
        def sortkey(note):
            return note.start
        self.note=sorted(self.note,key=sortkey)
        return self
    
    def __str__(self):
        self.sort()
        nbars=int((self.note[-1].start+self.note[-1].length)/(32*self.beats[0]/self.beats[1]))+1
        s="{:.1f} {} {} {} 19 0 0 0 0 0\n{}\n".format(
            self.tempo,
            self.beats[0],
            self.beats[1],
            nbars,
            len(self.note))
        for i in self.note:
            s+=str(i)
        return s
    
    def save(self,filename:str):
        '''
        保存nn文件
        '''
        with open(filename,encoding="utf8",mode="w") as file:
            file.write(str(self))
    
    def to_ust_file(self,use_hanzi:bool=False):
        '''
        将nn文件对象转换为ust文件对象
        默认使用nn文件中的拼音，如果需要使用汉字，use_hanzi=True
        '''
        ust=Ustfile(properties={'Tempo':self.tempo})
        time=0
        for note in self.note:
            if(note.start>time):
                ust.note+=[Ustnote(length=(note.start-time)*60,lyric="R",notenum=60)]
            if(use_hanzi):
                lyric=note.hanzi
            else:
                lyric=note.pinyin
            ust.note+=[Ustnote(length=note.length*60,lyric=lyric,notenum=note.notenum)]
            time=note.length+note.start
        return ust
    
    def to_midi_track(self,use_hanzi:bool=False):
        '''
        将nn文件对象转换为mido.MidiTrack对象
        默认使用nn文件中的拼音，如果需要使用汉字，use_hanzi=True
        '''
        import mido
        track=mido.MidiTrack()
        time=0
        for note in self.note:
            if(use_hanzi):
                track.append(mido.MetaMessage('lyrics',text=note.hanzi,time=(note.start-time)*60))
            else:
                track.append(mido.MetaMessage('lyrics',text=note.pinyin,time=(note.start-time)*60))
            track.append(mido.Message('note_on', note=note.notenum,velocity=64,time=0))
            track.append(mido.Message('note_off',note=note.notenum,velocity=64,time=note.length*60))
            time=note.start+note.length
        track.append(mido.MetaMessage('end_of_track'))
        return track
    
    def to_midi_file(self,filename:str="",use_hanzi:bool=False):
        '''
        将nn文件对象转换为mid文件与mido.MidiFile对象
        默认使用nn文件中的拼音，如果需要使用汉字，use_hanzi=True
        '''
        import mido
        mid = mido.MidiFile()
        ctrltrack=mido.MidiTrack()
        ctrltrack.append(mido.MetaMessage('track_name',name='Control',time=0))
        ctrltrack.append(mido.MetaMessage('set_tempo',tempo=mido.bpm2tempo(self.tempo),time=0))
        mid.tracks.append(ctrltrack)
        mid.tracks.append(self.to_midi_track(use_hanzi))
        if(filename!=""):
            mid.save(filename)
        return mid
        pass
            
    def to_music21_stream(self,use_hanzi:bool=False):
        '''
        将nn文件对象转换为music21 stream
        '''
        return self.to_ust_file(use_hanzi=use_hanzi).to_music21_stream()
    
def opennn(filename:str):
    '''
    打开nn文件，返回Nnfile对象
    '''
    with open(filename,"r",encoding="utf8") as file:
        line=file.readline().split(" ")
        tempo=float(line[0])
        beats=(int(line[1]),int(line[2]))
        file.readline()
        note=[]
        for i in file.readlines():
            line=i.strip(" \n").split(" ")
            hanzi=line[0]
            pinyin=line[1]
            start=int(line[2])
            length=int(line[3])
            notenum=83-int(line[4])
            cle=int(line[5])
            vel=int(line[6])
            por=int(line[7])
            viblen=int(line[8])
            vibdep=int(line[9])
            vibrat=int(line[10])
            dyn=np.array([int(i) for i in line[11].split(",")[1:]])
            pit=np.array([int(i) for i in line[12].split(",")[1:]])
            pbs=int(line[13])
            note+=[Nnnote(hanzi,pinyin,start,length,notenum,cle,vel,por,viblen,vibdep,vibrat,dyn,pit,pbs)]
    return Nnfile(tempo=tempo,beats=beats,note=note)
