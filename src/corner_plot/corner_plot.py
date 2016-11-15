from __future__ import division, print_function

import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import sys
import matplotlib.cm as cm
import matplotlib.colors as colors 

from matplotlib.ticker import MaxNLocator, FuncFormatter

__all__ = ["corner_plot"]


def confidence_2d(xsamples,ysamples,ax=None,intervals=None,nbins=20,linecolor='k',histunder=False,cmap="Blues",filled=False,linewidth=1., gradient=False, \
                    scatter=False, scatter_size=2.,scatter_color='k', scatter_alpha=0.5 ):
    """Draw confidence intervals at the levels asked from a 2d sample of points (e.g. 
        output of MCMC)"""

    if intervals is None:
        intervals  = 1.0 - np.exp(-0.5 * np.array([0., 1., 2.]) ** 2)
    H,yedges,xedges = np.histogram2d(ysamples,xsamples,bins=nbins)

    #get the contour levels
    if not scatter:
        try:
            h = np.sort(H.flatten())[::-1]
            cdf = np.cumsum(h)/np.cumsum(h)[-1]
            v = np.array([h[ cdf<=li ][-1] for li in intervals[1:]])[::-1]
            v = np.append(v,h[0])
            if not np.all(np.diff(v)>0.):
                raise RuntimeError() 
        except:
            if ax is None:
                fig,ax = plt.subplots
            cNorm = colors.Normalize(vmin=0.,vmax=1.)
            scalarMap = cm.ScalarMappable(norm=cNorm,cmap=cmap)
            cVal = scalarMap.to_rgba(0.65)
            ax.plot(xsamples,ysamples,'o',mec='none',mfc=cVal,alpha=scatter_alpha,ms=scatter_size,rasterized=True)
            ax.set_xlim((np.min(xedges),np.max(xedges)))
            ax.set_ylim((np.min(yedges),np.max(yedges)))
            return None


    if scatter is True:
        #if the contour levels are not monotonically increasing, just do a scatter plot
        if ax is None:
            fig,ax = plt.subplots
        ax.plot(xsamples,ysamples,'o',mec='none',mfc=scatter_color,alpha=scatter_alpha,ms=scatter_size,rasterized=True)
        ax.set_xlim((np.min(xedges),np.max(xedges)))
        ax.set_ylim((np.min(yedges),np.max(yedges)))
        return None

    xc = np.array([.5*(xedges[i]+xedges[i+1]) for i in np.arange(nbins)]) #bin centres
    yc = np.array([.5*(yedges[i]+yedges[i+1]) for i in np.arange(nbins)])

    xx,yy = np.meshgrid(xc,yc)

    if ax is None:
        fig,ax = plt.subplots()
    if histunder:
        ax.hist2d(xsamples,ysamples,bins=nbins,cmap=cmap)
        ax.contour(xx,yy,H,levels=v,colors=linecolor,extend='max',linewidths=linewidth)
    elif filled:
        if gradient:
            ax.imshow(H,cmap=cmap,origin='lower',extent=(np.min(xedges),np.max(xedges),np.min(yedges),np.max(yedges)),\
                    interpolation='bicubic',aspect='auto')
        else:
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

def chain_results(chain):
    """Get the results from a chain using the 16th, 50th and 84th percentiles. 
    For each parameter a tuple is returned (best_fit, +err, -err)"""
    return np.array(map(lambda v: [v[1],v[2]-v[1],v[1]-v[0]],\
                zip(*np.percentile(chain,[16,50,84],axis=0))))

def corner_plot( chain, axis_labels=None,  print_values=True, fname = None, nbins=40, figsize = (7.,7.), filled=True, gradient=False, cmap="Blues", truths = None,\
                fontsize=20 , tickfontsize=15, nticks=4, linewidth=1., truthlinewidth=2., linecolor = 'k', markercolor = 'k', markersize = 10, \
                wspace=0.5, hspace=0.5, scatter=False, scatter_size=2., scatter_color='k', scatter_alpha=0.5):

    """
    Make a corner plot from MCMC output.
    Parameters
    ----------
    chain : array_like[nsamples, ndim]
        Samples from an MCMC chain. ndim should be >= 2.
    axis_labels : array_like[ndim]
        Strings corresponding to axis labels.
    print_values:
        If True, print median values from 1D posteriors and +/- uncertainties 
        from the 84th and 16th percentiles above the 1D histograms.
    fname : str 
        The name of the file to save the figure to.
    nbins : int 
        The number of bins to use in each dimension for the histograms.
    figsize : tuple
        The height and width of the plot in inches.
    filled : bool
        If True, the histograms and contours will be filled.
    gradient: bool
        If True, then instead of filled contours, bicubic interpolation is applied to the 2D histograms (appropriate 
            when your posterior is densely sampled).
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
    truthlinewidth:
        The width of the dashed lines in 1D histograms at 'true' values.
    linecolor: str
        The color of the lines surrounding the contours and histograms.
    markercolor: str
        The color of the marker at the 'true' values in the 2D subplots.
    markersize: float
        The size of the marker to put on the 2D subplots.
    wspace : float
        The amount of whitespace to place vertically between subplots.
    hspace : float
        The amount of whitespace to place horizontally between subplots.
    scatter: bool
        If true, do scatter plots instead of contour plots in the 2D projections.
    scatter_size: float
        The size of the points in the scatter plot.
    scatter_color: str 
        The color of the points in the scatter plot. 
    scatter_alpha: float 
        The alpha value for the scatter points. 
    """

    major_formatter = FuncFormatter(my_formatter)

    if print_values is True:
        res = chain_results(chain)
        
    traces = chain.T

    if axis_labels is None:
        axis_labels = ['']*len(traces)

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

    if not scatter:
        Cmap = colors.Colormap(cmap)
        cNorm = colors.Normalize(vmin=0.,vmax=1.)
        scalarMap = cm.ScalarMappable(norm=cNorm,cmap=cmap)
        cVal = scalarMap.to_rgba(0.65)
    else:
        cVal = scatter_color

    #this one's special, so do it on it's own
    if print_values is True:
        hist_1d_axes[n_traces - 1].set_title("${0:.2f}^{{ +{1:.2f} }}_{{ -{2:.2f} }}$".\
            format(res[n_traces - 1][0],res[n_traces - 1][1],res[n_traces - 1][2]),fontsize=fontsize)    
    hist_1d_axes[n_traces - 1].plot(xplot, yplot, color = linecolor, lw=linewidth)
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
        hist_1d_axes[n_traces - 1].axvline(truths[n_traces - 1],ls='--',c='k',lw=truthlinewidth)


    #Now Make the 2D histograms
    for x_var in xrange( n_traces ):
        for y_var in xrange( n_traces):
            try:
                H, y_edges, x_edges = np.histogram2d( traces[y_var][:num_samples], traces[x_var][:num_samples],\
                                                           bins = nbins )
                confidence_2d(traces[x_var][:num_samples],traces[y_var][:num_samples],ax=hist_2d_axes[(x_var,y_var)],\
                    nbins=nbins,intervals=None,linecolor=linecolor,filled=filled,cmap=cmap,linewidth=linewidth, gradient=gradient,\
                    scatter=scatter,scatter_color=scatter_color, scatter_alpha=scatter_alpha)
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
                    elif truths[y_var]>yhi:
                        dy = truths[y_var] - yhi
                        hist_2d_axes[(x_var,y_var)].set_ylim((ylo,yhi+dy+0.05*(yhi-ylo)))
                    #TODO: deal with the pesky case of a prior edge
                    hist_2d_axes[(x_var,y_var)].set_axis_bgcolor(scalarMap.to_rgba(0.)) #so that the contours blend
                    hist_2d_axes[(x_var,y_var)].plot( truths[x_var], truths[y_var], '*', color = markercolor, markersize = markersize, \
                        markeredgecolor = 'none')
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

            if print_values is True:
                hist_1d_axes[x_var].set_title("${0:.2f}^{{ +{1:.2f} }}_{{ -{2:.2f} }}$".\
                                format(res[x_var][0],res[x_var][1],res[x_var][2]),fontsize=fontsize)  
            hist_1d_axes[x_var].plot(xplot, yplot, color = linecolor , lw=linewidth)
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
                hist_1d_axes[x_var].axvline(truths[x_var],ls='--',c='k',lw=truthlinewidth)

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

    plt.gcf().subplots_adjust(bottom=0.15) #make sure nothing is getting chopped off

    if fname != None:
        if len(fname.split('.')) == 1:
            fname += '.pdf'
        plt.savefig(fname, transparent=True)

    return None
