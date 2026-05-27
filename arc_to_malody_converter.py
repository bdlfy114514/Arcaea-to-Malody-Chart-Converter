#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import numpy as np

def xtrans(x):                      #将arcaea中从-0.5到1.5的坐标映射到malody的0到256内以确保x=0或1的mote不会超界
    return int(x * 128 + 64)

def xtrans_rel(x):                  #用于处理slide中seg的相对坐标，将0~1的相对坐标值映射到0~128
    return int(x * 128)

def ttrans(t):                      #将arcaea的绝对时间转化为malody的节拍表示（[a,b,c]），并且统一设定bpm=120，c=96
    a = int(t // 500)
    b = int((t % 500) / (500 / 96))
    return f'[{a},{b},96]'

def cal_tap(t,key):                 #转换地键
    return '{' + f'"beat":{ttrans(t)},"x":{int(64*key - 32)},"w":60' + '},'

def cal_hold(t1,t2,key):            #转换hold
    return '{' + f'"beat":{ttrans(t1)},"x":{int(64*key - 32)},"w":60,"seg":[' + '{' + f'"beat":{ttrans(t2-t1)},"x":0' + '}]},'

def cal_slide(x1,t1,x2,t2,type):    #转换arc，绘制slide
    x1_m = xtrans(x1)
    t1_m = ttrans(t1)
    ts = np.linspace(0,t2 - t1,int((t2 - t1)/(500 / 8)) + 1)
    def trans_to_sld(ts,xs,x1_m,t1_m):  #将生成slide文本的过程封装为函数
        sld = '{' + f'"beat":{t1_m},"x":{x1_m},"w":50,"seg":['
        tlst = ts.tolist()
        xlst = xs.tolist()
        xlst = [int(x) for x in xlst]
        for i in range (1,len(tlst)):
            sld += '{' + f'"beat":{ttrans(tlst[i])},"x":{xlst[i]}' + '},'
        sld = sld.rstrip(',')
        sld += ']},'
        return sld
    if type == 's':                     #处理"s"型arc，即直线
        return '{' + f'"beat":{t1_m},"x":{x1_m},"w":50,"seg":[' + '{' +f'"beat":{ttrans(t2-t1)},"x":{xtrans_rel(x2-x1)}' +'}]},'
    elif type == 'si' or type == 'sisi' or type == 'siso':                  #处理"si"型arc，即sin in，正弦曲线的1/4周期
        xs = xtrans_rel(x2 - x1) * np.sin(((2 * np.pi) / (4 * (t2 - t1))) * ts)
        sld = trans_to_sld(ts,xs,x1_m,t1_m)
        return sld
    elif type == 'so' or type == 'soso' or type == 'sosi':                  #处理"so"型arc，即sine out，也是正弦曲线的1/4周期
        xs = xtrans_rel(x2 - x1) - xtrans_rel(x2 - x1) * np.cos(((2 * np.pi) / (4 * (t2 - t1))) * ts)
        sld = trans_to_sld(ts,xs,x1_m,t1_m)
        return sld
    elif type == 'b':                   #处理"b"型曲线，近似处理为正弦曲线的1/2周期
        xs = xtrans_rel(x2 - x1) / 2 - (xtrans_rel(x2 - x1) / 2) * np.cos(((2 * np.pi) / (2 * (t2 - t1))) * ts)
        sld = trans_to_sld(ts,xs,x1_m,t1_m)
        return sld

def cal_arctap(x1,x2,t1,t2,t,type):         #转换天键
    t_rel = t - t1
    if type == 's':                         #将天键所在的黑线始末位置和时间、天键自身时间带入黑线的方程中算出其坐标
        x = (t_rel / (t2 - t1)) * (x2-x1) + x1
    elif type == 'si' or type == 'sisi' or type == 'siso':
        x = (x2 - x1) * np.sin(((2 * np.pi) / (4 * (t2 - t1))) * t_rel) + x1
    elif type == 'so' or type == 'soso' or type == 'sosi':
        x = (x2 - x1) - (x2 - x1) * np.cos(((2 * np.pi) / (4 * (t2 - t1))) * t_rel) + x1
    elif type == 'b':
        x = (x2 - x1) / 2 - ((x2 - x1) / 2) * np.cos(((2 * np.pi) / (2 * (t2 - t1))) * t_rel) + x1
    return '{' + f'"beat":{ttrans(t)},"x":{xtrans(x)},"w":60,"type":4' + '},'

filepath = input('请输入aff格式谱面文件路径：')
if filepath[0] == '"' or filepath[0] == "'":
    d = filepath[0]
    filepath_ = filepath.strip(d)
else:
    filepath_ = filepath
aff_content = []
with open (filepath_, 'r', encoding = 'utf-8') as aff:     #读取aff文件
    while True:
        line = aff.readline()
        if line == '':
            break
        else:
            aff_content.append(line.lstrip().rstrip('\n').rstrip(';'))

#编辑写入mc文件的文本
mc_content = '{"meta":{"$ver":0,"creator":"","background":"","version":"","id":0,"mode":7,"time":1779352022,"song":{"title":"1","artist":"Unknown","id":0},"mode_ext":{}},"time":[{"beat":[0,0,1],"bpm":120.0}],"effect":[],"note":['
for lines in aff_content:
    if 'AudioOffset' in lines:                            #读取offset数据
        offset = -int(lines.split(':')[1])
    elif lines[0] == '(':                                 #读取地键数据
        tap_lst = lines.lstrip('(').rstrip(')').split(',')
        mc_content += cal_tap(int(tap_lst[0]),int(tap_lst[1]))
    elif 'hold' in lines:                                 #读取hold数据
        hold_lst = lines.lstrip('hold(').rstrip(')').split(',')
        mc_content += cal_hold(int(hold_lst[0]),int(hold_lst[1]),int(hold_lst[2]))
    elif 'arc' in lines and 'false' in lines:             #读取arc数据
        arc_lst = lines.lstrip('arc(').rstrip(')').split(',')
        mc_content += cal_slide(float(arc_lst[2]),int(arc_lst[0]),float(arc_lst[3]),int(arc_lst[1]),arc_lst[4])
    elif 'arc' in lines and 'true' in lines:              #读取黑线数据
        if 'arctap' in lines:                             #若黑线上带有arctap，带入函数进行转换
            arctap_lst = lines.lstrip('arc(').rstrip(']').split('[')
            arctap_lst1 = arctap_lst[0].split(',')
            arctap_lst2 = arctap_lst[1].split(',')
            arctap_lst2 = [int(i.lstrip('arctap(').rstrip(')')) for i in arctap_lst2]
            for arctap in arctap_lst2:
                mc_content += cal_arctap(float(arctap_lst1[2]),float(arctap_lst1[3]),int(arctap_lst1[0]),int(arctap_lst1[1]),arctap,arctap_lst1[4])
        else: 
            continue                                      #无arctap附着的黑线直接跳过
    else:
        continue                                          #忽略其余所有信息
mc_content += '{"beat":[0,0,1],"sound":"1.ogg","vol":100,"offset":' + str(offset) + ',"type":1}],"extra":{"test":{"divide":4,"speed":100,"save":0,"lock":0,"edit_mode":0}}}'

with open ('1.mc', 'w', encoding = 'utf-8') as mc:        #写入mc文件
    mc.write(mc_content)

end = input("生成完毕！按enter退出")


# In[ ]:




