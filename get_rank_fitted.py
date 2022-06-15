#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  6 15:48:51 2022

@author: slcju
"""

# THE SCORING MODEL
# Extra params are for experiment
# I finally decide alpha=1, beta=1, mu(w)=50 (a_mu=0, b_mu=50)
# sigma_p and sigma(w) is fitted from historical data

# S = log2(1 + 2 ^ (t / alpha)) * p ^ (beta / sigma_p)
# t = (w - mu(w)) / sigma(w)
# mu(w) = a_mu * p + b_mu
# sigma(w) = a_w * p ^ b_w + c_w

import pandas as pd
import numpy as np
from bisect import bisect_left
from PIL import Image
import os
import imgkit
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

CWD = os.getcwd()
FONT = 'AaHanLinKai-2.ttf'

# CREDENTIALS FOR THE DATA API
# Register an account on pvp.91m.top/my, log on,
# and command 'document.cookie' in the console of development tools of your browser (F12).
openId = 'zzz'
accessToken = 'zzz'

# FOR PLOTTING
fprop = fm.FontProperties(fname=FONT)
y = np.linspace(44, 56, 101)
x = np.linspace(0, 40, 101)
x, y = np.meshgrid(x, y)

# GET HERO LIST
heros = pd.read_json(f'https://api.91m.top/hero/v1/app.php?type=getRanking&aid=0&bid=4&openId={openId}&accessToken={accessToken}')
heros = pd.DataFrame(heros.at['result', 'data']['rows'])
heros = heros[['id', 'name', 'allBanRate']]
heros.rename(columns={'id': 'heroId', 'name': 'heroName'}, inplace=True)
heros.set_index('heroId', inplace=True)
# drop potential new hero which hasn't been released
heros.drop(index=999, inplace=True, errors='ignore')
# heros.loc[heros['allBanRate'] < 0.01, 'allBanRate'] = 0
# heros['allBanRate'] = heros['allBanRate'] * 100

# GET HERO ICONS, RUN THIS WHEN NEW HERO IS RELEASED OR SOME HERO'S ICON IS UPDATED
# import requests
# from io import BytesIO

# for i in heros.index:
#     r = requests.get(f'https://game.gtimg.cn/images/yxzj/img201606/heroimg/{i}/{i}.jpg')
#     r = BytesIO(r.content)
#     r = Image.open(r)
#     r.save(f'hero_img/{i}.png')

################### 1350+ SECTION ####################

# PARAMS
ALPHA = 1
BETA = 1
SIGMA_P = 0.805
A_MU = 0
B_MU = 50
A_W = 0.201
B_W = -1.17
C_W = 1.659

def score(w, p):
    mu_w = A_MU * p + B_MU
    sigma_w = A_W * (p ** B_W) + C_W
    t = (w - mu_w) / sigma_w
    return np.log2(1 + 2 ** (t / ALPHA)) * (p ** (BETA / SIGMA_P))

cnt = 1
tot = len(heros.index)
for i in heros.index:
    print(f'{cnt}/{tot}')
    data = pd.read_json(f'https://api.91m.top/hero/v1/app.php?type=getHeroInfo&bid=4&id={i}').at['heroInfo', 'data']
    heros.loc[i, 'occupation'] = data['type'][0]
    try:
        p = float(data['pickRate'][1])
    except ValueError:
        p = 0
    heros.loc[i, 'pickRate1350'] = p
    try:
        b = float(data['banRate'][1])
    except ValueError:
        b = 0
    heros.loc[i, 'banRate1350'] = b
    try:
        w = float(data['winRate'][1])
    except ValueError:
        w = 0
    heros.loc[i, 'winRate1350'] = w
    #heros.loc[i, 'winScore1350'] = np.log2(1 + pow(2, (w - 50) / ALPHA))    #######
    heros.loc[i, 'pickScore1350'] = p / (100 - b)
    cnt += 1
c = heros['pickScore1350'].mean()   # mu_P_0 in doc v2
#heros.pickScore1350 = heros.pickScore1350 / c
heros = heros.assign(score1350 = score(heros.winRate1350, heros.pickScore1350 / c))  #######
heros.sort_values('score1350', ascending=False, inplace=True)
heros.reset_index(inplace=True)
heros.to_excel('1350res/1350.xlsx')

# threshes are in high-to-low order
threshes = (heros['score1350'].quantile(0.95), heros['score1350'].quantile(0.8), \
            1, heros['score1350'].quantile(0.3), heros['score1350'].quantile(0.1))
r_threshes = list(reversed(threshes))
names = ['对抗路', '中路', '', '打野', '发育路', '游走']
subsets = [heros[heros['occupation'] == i] for i in range(1, 7)]
for i in range(6):
    if i != 2:
        # REWRITE THIS IF YOUR SYSTEM DOES NOT SUPPORT THESE COMMANDS
        os.system(f'rm -rf temp/{names[i]}_1350')
        os.system(f'mkdir temp/{names[i]}_1350')
        for j in range(6):
            os.system(f'mkdir temp/{names[i]}_1350/T{j}')
        for row in subsets[i].itertuples():
            hero = Image.open(f'hero_img/{row.heroId}.png').convert('RGBA')
            t = 5 - bisect_left(r_threshes, row.score1350)
            hero.save(f'temp/{names[i]}_1350/T{t}/{row.Index}.png')

# RENDER
r_threshes.insert(0, 0); r_threshes.append(0)
hints = ['——版本答案', '——主流强势英雄', '——一般强势英雄', '——大众英雄', '——弱势英雄', '——边缘英雄']
c = heros['pickScore1350'].mean()
for i in range(6):
    if i != 2:
        z = score(y, x / c / 100)       ######
        r_threshes[-1] = np.amax(z)
        contour = plt.contourf(x, y, z, r_threshes, cmap='coolwarm', \
                               norm=LogNorm(vmin=r_threshes[1], vmax=r_threshes[-2], clip=True))  #####
        plt.axhline(50, color='k')
        plt.axvline(c * 100, color='k')
        p = plt.gca()
        p.set_title(names[i], fontproperties=fprop, fontsize=20)
        p.set_xlabel('bp率', fontproperties=fprop, fontsize=12)
        p.set_ylabel('胜率', fontproperties=fprop, fontsize=12)

        html = f'<html><head><style>@font-face{{font-family:myfont;src:url(\'{CWD}/{FONT}\');}}h1{{font-family:myfont;font-size:50px;}}</style></head><body>'
        html += '<style>img{width: 100px; height: 100px;}</style>'
        html += f'<h1>{names[i]}</h1>'
        html_ = f'<html><head><style>@font-face{{font-family:myfont;src:url(\'{CWD}/{FONT}\');}}h1{{font-family:myfont;}}</style></head><body>'
        html_ += f'<h1>{names[i]}</h1><table>'
        html_ += '<tr><th>英雄</th><th>胜率</th><th>选取率</th><th>禁用率</th><th>总分</th></tr>'
        for j in range(6):
            html += f'<p><h1>T{j}{hints[j]}</h1>'
            basepath = f'temp/{names[i]}_1350/T{j}/'
            files = [int(s.split('.')[0]) for s in os.listdir(basepath)]
            files.sort()
            for f in files:
                html += f'<img src="{CWD}/{basepath}{f}.png">&nbsp;&nbsp;&nbsp;&nbsp;'
                row = heros.loc[f]
                with Image.open(f"{CWD}/{basepath}{f}.png") as img:
                    img.putalpha(200)
                    im = OffsetImage(img, zoom=0.16)
                #im.set_width(40); im.set_height(40)
                    ab = AnnotationBbox(im, (row.pickScore1350 * 100, row.winRate1350), frameon=False)
                    p.add_artist(ab)
                html_ += f'<tr><td>{row.heroName}</td><td>{row.winRate1350:#.2f}</td><td>{row.pickRate1350:#.2f}</td><td>{row.banRate1350:#.2f}</td><td>{row.score1350:#.2f}</td></tr>'
            if j < 5:
                html_ += f'<tr style="background-color:#FFFF00"><td>T{j}线</td><td></td><td></td><td></td><td>{threshes[j]:#.2f}</td></tr>'
        plt.savefig(f'1350res/{names[i]}_1350_plot.png', dpi=300)
        plt.close()
        html_ += '</table></body></html>'
        imgkit.from_string(html_, f"1350res/{names[i]}_1350_.png")
        html += '</p></body></html>'
        imgkit.from_string(html, f"1350res/{names[i]}_1350.png")
        img = Image.open(f"1350res/{names[i]}_1350.png")
        width, height = img.size
        img = img.resize((width//2, height//2))
        img.save(f"1350res/{names[i]}_1350.png")

for i in range(6):
    if i != 2:
        img = Image.open(f'1350res/{names[i]}_1350_.png')
        width, height = img.size
        img = img.crop((0, 0, 280, height))
        img.save(f'1350res/{names[i]}_1350_.png')

################### PEAK SECTION ####################

# PARAMS
ALPHA = 1
BETA = 1
SIGMA_P = 1.173
A_MU = 0
B_MU = 50
A_W = 0.249
B_W = -0.926
C_W = 2.349

# READ SKILLS
skills = pd.read_excel('skills.xlsx', index_col=0)

# GET INFO
res = pd.read_json('https://api.91m.top/hero/v1/app/public/json/heroGenre.json?bid=4')
res = res[['heroId', 'skillId', 'positionId', 'pickTimes', 'winRate']]
res['winRate'] = res['winRate'] * 100
res = res[res['skillId'] != 0]
res['pickTimes'] = res['pickTimes'] / sum(res['pickTimes'])
res = res[res['pickTimes'] > 0.001]     # remove low pickRate entries
res['pickTimes'] = 1000 * res['pickTimes'] / sum(res['pickTimes'])
res.sort_values('positionId', inplace=True)
#res.to_excel('res.xlsx')
heros.set_index('heroId', inplace=True)

# CALC
res = res.join(heros, 'heroId')
res = res.join(skills, 'skillId')
#res = res.assign(winScore = lambda x: np.log2(1 + pow(2, (x.winRate - 50) / ALPHA)))  ######
res = res.assign(pickScore = lambda x: x.pickTimes / (100 - x.allBanRate))
subsets = [res[res['positionId'] == i] for i in range(5)]
c = [0] * 5
for i in range(5):
    c[i] = subsets[i]['pickScore'].mean()       # mu_P_0 in doc v2
    #subsets[i].pickScore = subsets[i].pickScore / c[i]
    subsets[i] = subsets[i].assign(totalScore = lambda x: score(x.winRate, x.pickScore / c[i]))   ###########
    subsets[i].sort_values('totalScore', ascending=False, inplace=True)
    subsets[i].reset_index(drop=True, inplace=True)
res = pd.concat(subsets)
res.to_excel('res/peak.xlsx')
# threshes are in high-to-low order
threshes = (res['totalScore'].quantile(0.95), res['totalScore'].quantile(0.8), \
            1, res['totalScore'].quantile(0.3), res['totalScore'].quantile(0.1))

# RENDER
r_threshes = list(reversed(threshes))
r_threshes.insert(0, 0); r_threshes.append(0)
names = ['对抗路', '中路', '发育路', '打野', '游走']
hints = ['——版本答案', '——主流强势英雄/玩法', '——一般强势英雄/玩法', '——大众英雄/玩法', \
         '——弱势英雄/玩法', '——边缘英雄/玩法']

for i in range(5):
    z = score(y, x / c[i] / 100)    ##########
    r_threshes[-1] = np.amax(z)
    contour = plt.contourf(x, y, z, r_threshes, cmap='coolwarm', \
                           norm=LogNorm(vmin=r_threshes[1], vmax=r_threshes[-2], clip=True))    #####
    q = np.max(subsets[i].totalScore)   # For some exceptionally high-ranking hero that scores higher than np.amax(z)
    if q > r_threshes[-1]:
        r_threshes[-1] = q
    plt.axhline(50, color='k')
    plt.axvline(c[i] * 100, color='k')
    p = plt.gca()
    p.set_title(names[i], fontproperties=fprop, fontsize=20)
    p.set_xlabel('bp率', fontproperties=fprop, fontsize=12)
    p.set_ylabel('胜率', fontproperties=fprop, fontsize=12)
    # CONTOUR LABELING, DISCARDED
    #fmt = {}
    #strs = ['', 'T3', 'T2', 'T1', 'T0', '']
    #for l, s in zip(contour.levels, strs):
    #    fmt[l] = s
    #p.clabel(contour, inline=True, fmt=fmt, fontsize=10, manual=True, color='k')

    html_ = f'<html><head><style>@font-face{{font-family:myfont;src:url(\'{CWD}/{FONT}\');}}h1{{font-family:myfont;}}</style></head><body>'
    html_ += f'<h1>{names[i]}</h1><table>'
    html_ += '<tr><th>英雄</th><th>技能</th><th>胜率</th><th>选取率</th><th>禁用率</th><th>总分</th></tr>'

    # REWRITE THIS IF YOUR SYSTEM DOES NOT SUPPORT THESE COMMANDS
    os.system(f'rm -rf temp/{names[i]}')
    os.system(f'mkdir temp/{names[i]}')
    flags = [False for i in range(5)]
    for j in range(6):
        os.system(f'mkdir temp/{names[i]}/T{j}')
    for row in subsets[i].itertuples():
        hero = Image.open(f'hero_img/{row.heroId}.png').convert('RGBA')
        if i != 3 and row.skillId != 80115:
            skill = Image.open(f'skill_img/{row.skillId}.png').convert('RGBA')
            hero.paste(skill, mask=skill)
        t = 6 - bisect_left(r_threshes, row.totalScore)
        hero.save(f'temp/{names[i]}/T{t}/{row.Index}.png')
        if t > 0 and not flags[t-1]:
            html_ += f'<tr style="background-color:#FFFF00"><td>T{t-1}线</td><td></td><td></td><td></td><td></td><td>{threshes[t-1]:#.2f}</td></tr>'
            flags[t-1] = True
        html_ += f'<tr><td>{row.heroName}</td><td>{row.name}</td><td>{row.winRate:#.2f}</td><td>{row.pickTimes:#.2f}</td><td>{row.allBanRate:#.2f}</td><td>{row.totalScore:#.2f}</td></tr>'
        hero.putalpha(200)
        #if row.pickScore <= 0.5 and row.winRate >= 45 and row.winRate <= 55:
        im = OffsetImage(hero, zoom=0.16)
        #im.set_width(40); im.set_height(40)
        ab = AnnotationBbox(im, (row.pickScore * 100, row.winRate), frameon=False)
        p.add_artist(ab)
    html_ += '</table></body></html>'

    plt.savefig(f'res/{names[i]}_plot.png', dpi=300)
    plt.close()
    imgkit.from_string(html_, f'res/{names[i]}_.png')

for i in range(5):
    html = f'<html><head><style>@font-face{{font-family:myfont;src:url(\'{CWD}/{FONT}\');}}h1{{font-family:myfont;font-size:50px;}}</style></head><body>'
    html += '<style>img{width: 100px; height: 100px;}</style>'
    html += f'<h1>{names[i]}</h1>'
    for j in range(6):
        html += f'<p><h1>T{j}{hints[j]}</h1>'
        basepath = f'temp/{names[i]}/T{j}/'
        files = [int(s.split('.')[0]) for s in os.listdir(basepath)]
        files.sort()
        for f in files:
            html += f'<img src="{CWD}/{basepath}{f}.png">&nbsp;&nbsp;&nbsp;&nbsp;'
    html += '</p></body></html>'
    imgkit.from_string(html, f'res/{names[i]}.png')
    img = Image.open(f'res/{names[i]}.png')
    width, height = img.size
    img = img.resize((width//2, height//2))
    img.save(f'res/{names[i]}.png')

for i in range(5):
    img = Image.open(f'res/{names[i]}_.png')
    width, height = img.size
    img = img.crop((0, 0, 320, height))
    img.save(f'res/{names[i]}_.png')
