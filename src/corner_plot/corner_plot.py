from __future__ import division, print_function

import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import sys
import matplotlib.cm as cm
import matplotlib.colors as colors 

from matplotlib.ticker import MaxNLocator, FuncFormatter
from matplotlib.colors import LogNorm

__all__ = ["corner_plot"]


def confidence_2d(xsamples,ysamples,ax=None,intervals=None,nbins=20,linecolor='k',histunder=False,cmap="Blues",filled=False,linewidth=1.):
    """Draw confidence intervals at the levels asked from a 2d sample of points (e.g. 
        output of MCMC)"""

    if intervals is None:
        intervals  = 1.0 - np.exp(-0.5 * np.array([0., 1., 2.]) ** 2)
    H,yedges,xedges = np.histogram2d(ysamples,xsamples,bins=nbins)

    #get the contour levels
    h = H.flatten()[np.argsort(H.flatten())[::-1]]
    cdf = np.cumsum(h)/np.cumsum(h)[-1]
    v = np.array([h[ cdf<=li ][-1] for li in intervals[1:]])[::-1]
    v = np.append(v,h[0])

    xc = np.array([.5*(xedges[i]+xedges[i+1]) for i in np.arange(nbins)]) #bin centres
    yc = np.array([.5*(yedges[i]+yedges[i+1]) for i in np.arange(nbins)])

    xx,yy = np.meshgrid(xc,yc)

    if ax is None:
        if histunder:
            plt.hist2d(xsamples,ysamples,bins=nbins,cmap=cmap)
            plt.contour(xx,yy,H,levels=v,colors=linecolor,extend='max',linewidths=linewidth)
        elif filled:
            plt.contourf(xx,yy,H,levels=v,cmap=cmap)
        else:
            plt.contour(xx,yy,H,levels=v,colors=linecolor,linewidths=linewidth)
    else:
        if histunder:
            ax.hist2d(xsamples,ysamples,bins=nbins,cmap=cmap)
            ax.contour(xx,yy,H,levels=v,colors=linecolor,extend='max',linewidths=linewidth)
        elif filled:
            ax.contourf(xx,yy,H,levels=v,cmap=cmap)
            ax.contour(xx,yy,H,levels=v,colors=linecolor,extend='max',linewidths=linewidth)
        else:
            ax.contour(xx,yy,H,levels=v,colors=linecolor,linewidths=linewidth)        

    return None

def my_formatter(x, pos):
    """Format 1 as 1, 0 as 0, and all values whose absolute values is between
    0 and 1 without the leading "0." (e.g., 0.7 is formatted as .7 and -0.4 is
    formatted as -.4)."""
    val_str = '${:g}$'.format(x)
    if np.abs(x) > 0 and np.abs(x) < 1:
        return val_str.replace("0", "", 1)
    else:
        return val_str

def corner_plot( chain, axis_labels=None, fname = None, nbins=40, figsize = (15.,15.), filled=True, cmap="Blues", truths = None,\
                        fontsize=20 , tickfontsize=15, nticks=4, linewidth=1., wspace=0.5, hspace=0.5 ):

    """
    Make a corner plot from MCMC output.
    Parameters
    ----------
    chain : array_like[nsamples, ndim]
        Samples from an MCMC chain. ndim should be >= 2.
    axis_labels : array_like[ndim]
        Strings corresponding to axis labels.
    fname : str 
        The name of the file to save the figure to.
    nbins : int 
        The number of bins to use in each dimension for the histograms.
    figsize : tuple
        The height and width of the plot in inches.
    filled : bool
        If True, the histograms will be filled.
    cmap : str
        Name of the colormap to use.
    truths : array_like[ndim]
    	A list of true values. These are marked on the 2D and 1D histograms. If None, none are added.
   	fontsize : float
   		The size font to use for axis labels.
   	tickfontsize : float
   	    The size font to use for tick labels.
   	nticks : int
   	    The number of ticks to use on each axis.
   	linewidth: float
   	    The width of the lines surrounding the contours and histograms.
   	wspace : float
   	    The amount of whitespace to place vertically between subplots.
   	hspace : float
   		The amount of whitespace to place horizontally between subplots.
    """

    major_formatter = FuncFormatter(my_formatter)
        
    traces = chain.T

    if axis_labels is None:
        axis_labels = ['']*len(traces)

    #Defines the widths of the plots in inches
    plot_width = 15.
    plot_height = 15.

    if len(traces) != len(axis_labels):
        print("There must be the same number of axis labels as traces",file=sys.stderr)

    if truths != None and ( len(truths) != len(traces) ):
        print("There must be the same number of true values as traces",file=sys.stderr)

    num_samples = min([ len(trace) for trace in traces])
    n_traces = len(traces)


    #Set up the figure
    fig = plt.figure( num = None, figsize = figsize)

    dim = 2*n_traces - 1

    gs = gridspec.GridSpec(dim+1,dim+1)
    gs.update(wspace=wspace,hspace=hspace)

    hist_2d_axes = {}

    #Create axes for 2D histograms
    for x_pos in xrange( n_traces - 1 ):
        for y_pos in range( n_traces - 1 - x_pos  ):
            x_var = x_pos
            y_var = n_traces - 1 - y_pos

            hist_2d_axes[(x_var, y_var)] = fig.add_subplot( \
                                           gs[ -1-(2*y_pos):-1-(2*y_pos), \
                                               2*x_pos:(2*x_pos+2) ] )
            hist_2d_axes[(x_var, y_var)].xaxis.set_major_formatter(major_formatter)
            hist_2d_axes[(x_var, y_var)].yaxis.set_major_formatter(major_formatter)

    #Create axes for 1D histograms
    hist_1d_axes = {}
    for var in xrange( n_traces -1 ):
        hist_1d_axes[var] = fig.add_subplot( gs[ (2*var):(2*var+2), 2*var:(2*var+2) ] )
        hist_1d_axes[var].xaxis.set_major_formatter(major_formatter)
        hist_1d_axes[var].yaxis.set_major_formatter(major_formatter)
    hist_1d_axes[n_traces-1] = fig.add_subplot( gs[-2:, -2:] )
    hist_1d_axes[n_traces-1].xaxis.set_major_formatter(major_formatter)
    hist_1d_axes[n_traces-1].yaxis.set_major_formatter(major_formatter)



    #Remove the ticks from the axes which don't need them
    for x_var in xrange( n_traces -1 ):
        for y_var in xrange( 1, n_traces - 1):
            try:
                hist_2d_axes[(x_var,y_var)].xaxis.set_visible(False)
            except KeyError:
                continue
    for var in xrange( n_traces - 1 ):
        hist_1d_axes[var].set_xticklabels([])
        hist_1d_axes[var].xaxis.set_major_locator(MaxNLocator(nticks))
        hist_1d_axes[var].yaxis.set_visible(False)

    for y_var in xrange( 1, n_traces ):
        for x_var in xrange( 1, n_traces - 1):
            try:
                hist_2d_axes[(x_var,y_var)].yaxis.set_visible(False)
            except KeyError:
                continue

    #Do the plotting
    #Firstly make the 1D histograms
    vals, walls = np.histogram(traces[-1][:num_samples], bins=nbins, normed = True)

    xplot = np.zeros( nbins*2 + 2 )
    yplot = np.zeros( nbins*2 + 2 )
    for i in xrange(1, nbins * 2 + 1 ):
        xplot[i] = walls[int((i-1)/2)]
        yplot[i] = vals[int((i-2)/2)]

    xplot[0] = walls[0]
    xplot[-1] = walls[-1]
    yplot[0] = yplot[1]
    yplot[-1] = yplot[-2]

    Cmap = colors.Colormap(cmap)
    cNorm = colors.Normalize(vmin=0.,vmax=1.)
    scalarMap = cm.ScalarMappable(norm=cNorm,cmap=cmap)
    cVal = scalarMap.to_rgba(0.65)

    #this one's special, so do it on it's own
    hist_1d_axes[n_traces - 1].plot(xplot, yplot, color = 'k', lw=linewidth)
    if filled: hist_1d_axes[n_traces - 1].fill_between(xplot,yplot,color=cVal)
    hist_1d_axes[n_traces - 1].set_xlim( walls[0], walls[-1] )
    hist_1d_axes[n_traces - 1].set_xlabel(axis_labels[-1],fontsize=fontsize)
    hist_1d_axes[n_traces - 1].tick_params(labelsize=tickfontsize)
    hist_1d_axes[n_traces - 1].xaxis.set_major_locator(MaxNLocator(nticks))
    hist_1d_axes[n_traces - 1].yaxis.set_visible(False)
    plt.setp(hist_1d_axes[n_traces - 1].xaxis.get_majorticklabels(), rotation=45)
    if truths is not None:
        xlo,xhi = hist_1d_axes[n_traces-1].get_xlim()
        if truths[n_traces-1]<xlo:
            dx = xlo-truths[n_traces-1]
            hist_1d_axes[n_traces-1].set_xlim((xlo-dx-0.05*(xhi-xlo),xhi))
        elif truths[n_traces-1]>xhi:
            dx = truths[n_traces-1]-xhi
            hist_1d_axes[n_traces-1].set_xlim((xlo,xhi+dx+0.05*(xhi-xlo)))
        hist_1d_axes[n_traces - 1].axvline(truths[n_traces - 1],ls='--',c='k')


    #Now Make the 2D histograms
    for x_var in xrange( n_traces ):
        for y_var in xrange( n_traces):
            try:
                H, y_edges, x_edges = np.histogram2d( traces[y_var][:num_samples], traces[x_var][:num_samples],\
                                                           bins = nbins )
                confidence_2d(traces[x_var][:num_samples],traces[y_var][:num_samples],ax=hist_2d_axes[(x_var,y_var)],\
                    nbins=nbins,intervals=None,linecolor='0.5',filled=filled,cmap=cmap,linewidth=linewidth)
                if truths is not None:
                    xlo,xhi = hist_2d_axes[(x_var,y_var)].get_xlim()
                    ylo,yhi = hist_2d_axes[(x_var,y_var)].get_ylim()
                    if truths[x_var]<xlo:
                        dx = xlo-truths[x_var]
                        hist_2d_axes[(x_var,y_var)].set_xlim((xlo-dx-0.05*(xhi-xlo),xhi))
                    elif truths[x_var]>xhi:
                        dx = truths[x_var]-xhi
                        hist_2d_axes[(x_var,y_var)].set_xlim((xlo,xhi+dx+0.05*(xhi-xlo)))
                    if truths[y_var]<ylo:
                        dy = ylo - truths[y_var]
                        hist_2d_axes[(x_var,y_var)].set_ylim((ylo-dy-0.05*(yhi-ylo),yhi))
                    elif truths[y_var]<ylo:
                        dy = truths[y_var] - yhi
                        hist_2d_axes[(x_var,y_var)].set_ylim((ylo,yhi+dy+0.05*(yhi-ylo)))
                    #TODO: deal with the pesky case of a prior edge
                    hist_2d_axes[(x_var,y_var)].plot( truths[x_var], truths[y_var], '*', color = 'k', markersize = 10 )
            except KeyError:
                pass
        if x_var < n_traces - 1:
            vals, walls = np.histogram( traces[x_var][:num_samples], bins=nbins, normed = True )

            xplot = np.zeros( nbins*2 + 2 )
            yplot = np.zeros( nbins*2 + 2 )
            for i in xrange(1, nbins * 2 + 1 ):
                xplot[i] = walls[int((i-1)/2)]
                yplot[i] = vals[int((i-2)/2)]

            xplot[0] = walls[0]
            xplot[-1] = walls[-1]
            yplot[0] = yplot[1]
            yplot[-1] = yplot[-2]

            hist_1d_axes[x_var].plot(xplot, yplot, color = 'k' , lw=linewidth)
            if filled: hist_1d_axes[x_var].fill_between(xplot,yplot,color=cVal)
            hist_1d_axes[x_var].set_xlim( x_edges[0], x_edges[-1] )
            if truths is not None:
                xlo,xhi = hist_1d_axes[x_var].get_xlim()
                if truths[x_var]<xlo:
                    dx = xlo-truths[x_var]
                    hist_1d_axes[x_var].set_xlim((xlo-dx-0.05*(xhi-xlo),xhi))
                elif truths[x_var]>xhi:
                    dx = truths[x_var]-xhi
                    hist_1d_axes[x_var].set_xlim((xlo,xhi+dx+0.05*(xhi-xlo)))
                hist_1d_axes[x_var].axvline(truths[x_var],ls='--',c='k')

    #Finally Add the Axis Labels
    for x_var in xrange(n_traces - 1):
        hist_2d_axes[(x_var, n_traces-1)].set_xlabel(axis_labels[x_var],fontsize=fontsize)
        hist_2d_axes[(x_var, n_traces-1)].tick_params(labelsize=tickfontsize)
        hist_2d_axes[(x_var, n_traces-1)].xaxis.set_major_locator(MaxNLocator(nticks))
        plt.setp(hist_2d_axes[(x_var, n_traces-1)].xaxis.get_majorticklabels(), rotation=45)
    for y_var in xrange(1, n_traces ):
        hist_2d_axes[(0,y_var)].set_ylabel(axis_labels[y_var],fontsize=fontsize)
        hist_2d_axes[(0,y_var)].tick_params(labelsize=tickfontsize)
        plt.setp(hist_2d_axes[(0,y_var)].yaxis.get_majorticklabels(), rotation=45)
        hist_2d_axes[(0,y_var)].yaxis.set_major_locator(MaxNLocator(nticks))

    if fname != None:
        if len(fname.split('.')) == 1:
            fname += '.pdf'
        plt.savefig(fname, transparent=True)

    return None