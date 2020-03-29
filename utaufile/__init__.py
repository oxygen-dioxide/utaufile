from mido import Message, MidiFile, MidiTrack, MetaMessage, bpm2tempo
class Ustnote():
    #length:时长，480为一拍，整数
    #lyric:歌词，字符串
    #notenum:音高
    #properties:其他所有数据
    def __init__(self,length:int,lyric:str,notenum:int,properties={}):
        self.length=length
        self.lyric=lyric
        self.notenum=notenum 
        self.properties=properties
    def __str__(self):
        s="Length={}\nLyrics={}\nNoteNum={}\n".format(self.length,self.lyric,self.notenum)
        for i in self.properties.keys():
            s+="{}={}\n".format(i,self.properties[i])
        return s
    def isR(self)->bool:
        return (self.lyric in [""," ","r","R"])

class Ustfile():
    def __init__(self,properties={},notes=[]):
        self.properties=properties
        self.note=notes
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
        file=open(filename,"w",encoding='utf8')
        file.write("[#VERSION]\nUST Version1.2\nCharset=UTF-8\n")
        file.write(str(self))
    def getlyric(self,start:int=0,end:int=0,ignoreR:bool=True):
        #获取歌词
        #ignoreR：忽略休止符
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
        return(lyric)
    def replacelyric(self,dictionary:dict,start:int=0,end:int=0):
        #按字典替换歌词
        if(end==0):
            end=len(self.note)
        for i in range(start,end):
            self.note[i].lyric=dictionary.get(self.note[i].lyric,default=self.note[i].lyric)
    def setlyric(self,lyrics:list,start:int=0,end:int=0,ignoreR:bool=True):
        #批量输入歌词
        #ignoreR：忽略休止符
        if(end==0):
            end=len(self.note)
        if(ignoreR):
            j=0
            l=len(lyrics)
            for i in range(start,end):
                if(not self.note[i].isR()):
                    if(j>=l):
                        break
                    self.note[i].lyric=lyrics[j]
                    j=j+1
        else:
            j=0
            l=len(lyrics)
            for i in range(start,end):
                if(j>=l):
                    break
                self.note[i].lyric=lyrics[j]
                j=j+1
    def to_midi_track(self):
        track=MidiTrack()
        tick=0
        for note in self.note:
            if(note.isR()):
                tick+=note.length
            else:
                track.append(MetaMessage('lyrics',text=note.lyric,time=tick))
                tick=0
                track.append(Message('note_on', note=note.notenum,velocity=64,time=0))
                track.append(Message('note_off',note=note.notenum,velocity=64,time=note.length))
        track.append(MetaMessage('end_of_track'))
        return(track)
    def to_midi_file(self,filename:str=""):
        mid = MidiFile()
        ctrltrack=Miditrack()
        ctrltrack.append(MetaMessage('track_name',name='Control',time=0))
        ctrltrack.append(MetaMessage('set_tempo',tempo=bpm2tempo(self.tempo),time=0))
        mid.tracks.append(ctrltrack)
        mid.tracks.append(self.to_midi_track())
        if(filename!=""):
            mid.save(filename)
        return mid    
    
def ustvaluetyper(key,value):#根据ust中的键决定值的类型
    types={
        "Tempo":float,
        "Tracks":int,
        "Mode2":bool,
        "PreUtterance":int,
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

def openust(filename:str):#打开ust文件，返回Ustfile对象
    encoding='utf8'
    #读ust文件
    file=open(filename,'r',encoding=encoding)
    #分块
    blocks=[]
    block=[]
    for line in file.readlines():
        line=line.strip("\n")
        if(line[0]=="["):
            blocks+=[block]
            block=[]
        block+=[line]
    file.close()    
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
        if(not flag[i].isdigit()):
            break
    else:
        i+=1
    value=int(flag[0:i])
    flag=flag[i:]
    return(flag,value)
    
def parseflag(flag:str,flagtype,usedefault=False):
    #解析flag，返回字典
    #flagtype为由元组组成的集合
    #每个元组第0项为字符串,例如"b","g","Mt"等，第1项为默认值
    #如果usedefault=True，则返回字典会包含输入flag中没有的条目，且代入默认值
    if(usedefault):
        flagdict={i[0]:i[1] for i in flagtype}
    else:
        flagdict={}
    while(flag!=""):
        for i in flagtype:
            if(flag.startswith(i[0])):
                flag=flag[len(i):]
                if(type(i[1])==int):
                    (flag,value)=readint(flag)
                    flagdict[i[0]]=value
                elif(type(i[1])==bool):
                    flagdict[i[0]]=True
                break
        else:
            flag=flag[1:]
    return flagdict