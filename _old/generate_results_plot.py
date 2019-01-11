import os
import re
import argparse
from operator import itemgetter
import copy
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
# These are the colors that will be used in the plot
color_sequence = ['#1f77b4', '#aec7e8', '#ff7f0e', '#ffbb78', '#2ca02c',
                  '#98df8a', '#d62728', '#ff9896', '#9467bd', '#c5b0d5',
                  '#8c564b', '#c49c94', '#e377c2', '#f7b6d2', '#7f7f7f',
                  '#c7c7c7', '#bcbd22', '#dbdb8d', '#17becf', '#9edae5']




traces = [75,125,250,500,1000,2000,4000,8000,16000,32000,64000]

guesses_2v08 = [
173470139879964454693051405518974976000,
33600369853552520314221363419304960000,
10488522687341751341789071283712000000,
11129306152105468895230603100160000000,
579370412571567180263945784000000000,
12716764507217812263267741696000,
1015314300,
2245016736,
120]

guesses_mbedtls_1v2_dec1_external_supply = [
218892313431535447552157399789553254400,
43882301610898563886323913104519168000,
4395468563526016267311328484785889280,
463834524982016448000000,
23660000,
24786,
40587,
112,
98,
21,
1]

fig, (ax) = plt.subplots() # two axes on figure
#fig.set_size_inches(18.5, 10.5, forward=True)
plt.xscale('log', basex=2)
plt.yscale('log')
ax.get_xaxis().set_major_formatter(
    matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
ax.set_title(
	"Quality of traces in data set\n" + \
	"AES128 MBEDTLS\n" + \
	"1v2 external supply on DEC1")
ax.set(ylabel='Number of guesses')
ax.set(xlabel='Number of traces')
ax.grid()

#ax.plot(traces, guesses_2v08, label="MBEDTLS, 2v08 on VDD external supply")
ax.plot(traces, guesses_mbedtls_1v2_dec1_external_supply, label="MBEDTLS, 1v2 on DEC1 external supply")
#ax.set_xlim(left=0, right=1000000)
ax.legend(shadow=True, fancybox=True, loc='upper right')


#plt_name = args.input.replace(".log", "")
#plt.savefig(plt_name + '_correlation.pdf')

plt.show()


