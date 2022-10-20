#!/usr/bin/env python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#
##################################################################
#     CLIMPORN
#
#  Plot only the trajectories of all the buoys, even those who disapear
#
#    L. Brodeau, August 2022
#
# TO DO: use `nemo_box = cp.nemo_hbox(CNEMO,CBOX)` !!!
##################################################################

from sys import argv, exit
from os import path, mkdir
import numpy as np

from re import split

from netCDF4 import Dataset

import csv

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as colors

from calendar import isleap
import datetime

import climporn as cp


i_field_plot = 7 ; # (C) column index of field to plot

idebug = 1

l_show_mod_field = False

color_top = 'w'
color_top_cb = 'k'
clr_yellow = '#ffed00'

rDPI = 200

# Defaults:
l_scientific_mode = False

l_show_msh = False

fig_type='png'

vmn = [ 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 ]
vml = [ 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 ]

CBOX = 'ALL' ; # what box of `CCONF` ???
#CBOX = 'EastArctic' ; # what box of `CCONF` ???


NbDays = np.sum(vmn[0:10]) ; #fixme: end of october !!!


narg = len(argv)
if not narg in [6,7]:
    print('Usage: '+argv[0]+' <CONF> <file_trj.npz> <file_mod,var> <name_fig> <LSM_file> (iTsubsampl)')
    exit(0)

CCONF  = argv[1]
cf_npz = argv[2]
vv = split(',',argv[3])
cf_mod = vv[0]
cv_mod = vv[1]
cnfig  = argv[4]
#
cf_lsm = argv[5]
#
# Subsampling in time...
itsubs = 1
if narg == 7 :
    itsubs = int(argv[6])

cp.chck4f(cf_mod)
cp.chck4f(cf_lsm)    

# Getting time info and time step from input model file:
vv = split('-|_', path.basename(cf_mod))

cyear = vv[-3] ; cyear = cyear[0:4]
cdt   = vv[-4]

print('\n *** Year = '+cyear)
print('\n *** time increment = '+cdt)

cyr0=cyear
yr0=int(cyear)
cmn0='01'
cdd0='01'

# Time step (h) as a string
if not len(cdt)==2:
    print('ERROR: something is wrong with the format of your time step => '+cdt+' !'); exit(0)
if cdt=='1d':
    dt = 24 ; ntpd = 1
elif cdt[1]=='h':
    dt = int(cdt[0]) ; ntpd = 24 / dt
else:
    print('ERROR: something is wrong with the format of your time step => '+cdt+' !'); exit(0)

vm = vmn
if isleap(yr0): vm = vml
#print(' year is ', vm, np.sum(vm)

jd = int(cdd0) - 1
jm = int(cmn0)

print('     ==> dt = ', dt,'h')


dir_conf = path.dirname(cf_npz)
if dir_conf == '':  dir_conf = '.'
print('\n *** dir_conf =',dir_conf,'\n')

if l_show_mod_field: print('\n Field to show in background: "'+cv_mod+'" of file "'+cf_mod+'" !\n')



# Getting setup for NEMO CONFIG/BOX:
HBX = cp.nemo_hbox(CCONF,CBOX)
(i1,j1,i2,j2) = HBX.idx()

# About fields:
l_log_field = False
l_pow_field = False
cextend='both'
l_hide_cb_ticks = False
tmin=0. ; tmax=1. ; df=0.01
cb_jump = 1

if l_show_mod_field: print('\n *** Model field to show in bacground: = '+cv_mod)

bgclr = 'w'   ; # background color for ocean in figure

if   cv_mod in ['sosstsst','tos']:
    cfield = 'SST'
    tmin=-3. ;  tmax=2.   ;  df = 0.1 ; # Arctic!
    #tmin=14. ;  tmax=26.   ;  df = 1.
    cpal_fld = 'inferno'
    cunit = r'SST ($^{\circ}$C)'

elif cv_mod in ['sosaline','sos']:
    cfield = 'SSS'
    tmin=32. ;  tmax=36.   ;  df = 1.
    cpal_fld = 'viridis'
    cunit = r'SSS (PSU)'

elif cv_mod in ['siconc']:
    cfield = 'siconc'
    tmin=0. ;  tmax=1.   ;  df = 0.1 ; # Arctic!
    #cpal_fld = 'ncview_ice'
    cpal_fld = 'viridis_r'
    cunit = 'Ice concentration'
    bgclr = 'k'   ; # background color for ocean in figure

elif cv_mod in ['duration']:
    cfield = 'duration'
    #fixme: end of october!
    tmin=0. ;  tmax=NbDays   ;  df = 30 ; # Arctic!
    #cpal_fld = 'ncview_ice'
    cpal_fld = 'viridis_r'
    cunit = 'Time from seed (days)'
    bgclr = 'w'   ; # background color for ocean in figure

else:
    print('ERROR: variable '+cv_mod+' is not known yet...'); exit(0)

if not path.exists("figs"): mkdir("figs")



if not path.exists(cf_npz):    
    print('\n *** '+cf_npz+' NOT found !!!   :(  ')
    exit(0)

else:
    print('\n *** '+cf_npz+' was found !!!   :D  ')



#############################3
print('\n *** Reading into '+cf_npz+' !!!')
with np.load(cf_npz) as data:
    NrTraj = data['NrTraj']
    xmask   = data['mask']
    xIDs    = data['IDs']
    xJIs    = data['JIs']
    xJJs    = data['JJs']
    xFFs    = data['FFs']

    

print('\n\n *** Trajectories contain '+str(NrTraj)+' records each in CSV file')

if l_show_mod_field:
    print('   => and '+str(Nt_mod)+' records of field '+cv_mod+' in NEMO file '+cf_mod+' !')
    if not NrTraj%Nt_mod == 0:
        print('==> ERROR: they are not a multiple of each other!'); exit(0)
    nsubC = NrTraj//Nt_mod
    print('    ==> number of subcycles for trajectories w.r.t model data =>', nsubC)

else:
    Nt_mod = NrTraj
    nsubC  = 1


cnmsk = 'tmask'
print('\n *** Reading "'+cnmsk+'" in meshmask file...')
id_lsm = Dataset(cf_lsm)
nb_dim = len(id_lsm.variables[cnmsk].dimensions)
Ni = id_lsm.dimensions['x'].size
Nj = id_lsm.dimensions['y'].size
#if i2 == 0: i2 = Ni
#if j2 == 0: j2 = Nj
if nb_dim == 4: XMSK  = id_lsm.variables[cnmsk][0,0,j1:j2,i1:i2] ; # t, y, x
if nb_dim == 3: XMSK  = id_lsm.variables[cnmsk][0,  j1:j2,i1:i2] ; # t, y, x
if nb_dim == 2: XMSK  = id_lsm.variables[cnmsk][    j1:j2,i1:i2] ; # t, y, x
if l_show_msh:
    Xlon = id_lsm.variables['glamu'][0,j1:j2,i1:i2]
    Xlat = id_lsm.variables['gphiv'][0,j1:j2,i1:i2]
id_lsm.close()
print('      done.')

print('\n The shape of the domain is Ni, Nj =', Ni, Nj)


# Stuff for size of figure respecting pixels...
print('  *** we are going to show: i1,i2,j1,j2 =>', i1,i2,j1,j2, '\n')
nx_res = i2-i1
ny_res = j2-j1
yx_ratio = float(ny_res)/float(nx_res)
#
nxr = int(HBX.rfact_zoom*nx_res) ; # widt image (in pixels)
nyr = int(HBX.rfact_zoom*ny_res) ; # height image (in pixels)
rh  = float(nxr)/float(rDPI) ; # width of figure as for figure...

print('\n *** width and height of image to create:', nxr, nyr, '\n')

pmsk    = np.ma.masked_where(XMSK[:,:] > 0.2, XMSK[:,:]*0.+40.)
idx_oce = np.where(XMSK[:,:] > 0.5)

#font_rat
#params = { 'font.family':'Ubuntu',
params = { 'font.family':'Open Sans',
           'font.weight':    'normal',
           'font.size':       int(12.*HBX.font_rat),
           'legend.fontsize': int(22.*HBX.font_rat),
           'xtick.labelsize': int(18.*HBX.font_rat),
           'ytick.labelsize': int(18.*HBX.font_rat),
           'axes.labelsize':  int(15.*HBX.font_rat) }
mpl.rcParams.update(params)
cfont_clb   = { 'fontname':'Open Sans',   'fontweight':'medium', 'fontsize':int(18.*HBX.font_rat), 'color':color_top_cb }
cfont_cnfn  = { 'fontname':'Open Sans',   'fontweight':'light' , 'fontsize':int(35.*HBX.font_rat), 'color':color_top }
cfont_axis  = { 'fontname':'Open Sans',   'fontweight':'medium', 'fontsize':int(18.*HBX.font_rat), 'color':color_top }
cfont_ttl   = { 'fontname':'Open Sans',   'fontweight':'medium', 'fontsize':int(25.*HBX.font_rat), 'color':color_top }
cfont_clock = { 'fontname':'Ubuntu Mono', 'fontweight':'normal', 'fontsize':int(19.*HBX.font_rat), 'color':color_top }

# Colormaps for fields:
pal_fld = cp.chose_colmap(cpal_fld)
if l_log_field:
    norm_fld = colors.LogNorm(  vmin = tmin, vmax = tmax, clip = False)
if l_pow_field:
    norm_fld = colors.PowerNorm(gamma=pow_field, vmin = tmin, vmax = tmax, clip = False)
else:
    norm_fld = colors.Normalize(vmin = tmin, vmax = tmax, clip = False)

pal_lsm = cp.chose_colmap('land')
norm_lsm = colors.Normalize(vmin = 0., vmax = 1., clip = False)

#pal_filled = cp.chose_colmap('gray_r')
#norm_filled = colors.Normalize(vmin = 0., vmax = 0.1, clip = False)

vc_fld = np.arange(tmin, tmax + df, df)





# Only 1 figure
cfig = './figs/'+cnfig+'.'+fig_type


fig = plt.figure(num=1, figsize=(rh,rh*yx_ratio), dpi=rDPI, facecolor='k', edgecolor='k')
    
if l_scientific_mode:
    ax1 = plt.axes([0.09, 0.09, 0.9, 0.9], facecolor = 'r')
else:
    ax1 = plt.axes([0., 0., 1., 1.],     facecolor = bgclr)



    
#cm = plt.imshow(pmsk, cmap=pal_lsm, norm=norm_lsm, interpolation='none')
cm = plt.pcolormesh( pmsk, cmap=pal_lsm, norm=norm_lsm )
    
plt.axis([ 0,i2-i1,0,j2-j1])




# If we show backward:
#print(xJIs[:,NrTraj-1])
#exit(0)
    
# Loop over time records:
icpt = -1
for jtt in range(NrTraj):
    #for jtt in np.arange(NrTraj-1,0,-1):
    icpt = icpt+1
    #    if jtt%itsubs == 0:
    print('jtt =',jtt)

    rfade = float(icpt)/float(NrTraj-1)*NbDays
    
    # Showing trajectories:
    ct = plt.scatter(xJIs[:,jtt]-i1, xJJs[:,jtt]-j1, c=xJIs[:,jtt]*0.+rfade, cmap=pal_fld , norm=norm_fld, marker='o', s=0.01) ; #, alpha=rfade ) ;#s=HBX.pt_sz_track ) ; # c=xFFs[:,jtt], 





        
if l_scientific_mode:
    plt.xlabel('i-points', **cfont_axis)
    plt.ylabel('j-points', **cfont_axis)
    
if HBX.l_show_cb:
    ax2 = plt.axes(HBX.vcb)
    if l_pow_field or l_log_field:
        clb = mpl.colorbar.ColorbarBase(ax=ax2,               cmap=pal_fld, norm=norm_fld, orientation='horizontal', extend='neither')
    else:
        clb = mpl.colorbar.ColorbarBase(ax=ax2, ticks=vc_fld, cmap=pal_fld, norm=norm_fld, orientation='horizontal', extend=cextend)
    if cb_jump > 1:
        cb_labs = [] ; cpt = 0
        for rr in vc_fld:
            if cpt % cb_jump == 0:
                if df >= 1.: cb_labs.append(str(int(rr)))
                if df <  1.: cb_labs.append(str(rr))
            else:
                cb_labs.append(' ')
            cpt = cpt + 1
        clb.ax.set_xticklabels(cb_labs)
    clb.set_label(cunit, **cfont_clb)
    clb.ax.yaxis.set_tick_params(color=color_top_cb) ; # set colorbar tick color
    #clb.outline.set_edgecolor(color_top_cb) ; # set colorbar edgecolor
    if l_hide_cb_ticks: clb.ax.tick_params(axis=u'both', which=u'both',length=0) ; # remove ticks!
    plt.setp(plt.getp(clb.ax.axes, 'xticklabels'), color=color_top_cb) ; # set colorbar ticklabels


if HBX.l_show_name:  ax1.annotate(CCONF,          xy=(1, 4), xytext=HBX.name,  **cfont_cnfn)

if HBX.l_show_exp:   ax1.annotate(CCONF,          xy=(1, 4), xytext=HBX.exp,   **cfont_ttl)

#if HBX.l_show_clock: ax1.annotate('Date: '+cdats, xy=(1, 4), xytext=HBX.clock, **cfont_clock)
    
        
    
    
#plt.savefig(cfig, dpi=rDPI, orientation='portrait', facecolor='b', transparent=True)
plt.savefig(cfig, dpi=rDPI, orientation='portrait') #, transparent=True)
print(cfig+' created!\n')
plt.close(1)
        


    
    ### if jtt%itsubs == 0


### for jtt in range(NrTraj)


