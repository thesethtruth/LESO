import matplotlib.pyplot as plt

PAD = 0.3

def default_matplotlib_style(
    fig: plt.figure,
    ax: plt.axes,
    font_size=10,
    height=None,
    disable_box=True,
    subplots=None,
    decrease_legend=True
)-> plt.figure:
    """ Convience method for styling figures to meet default styling"""
    ratio=2

    plt.tight_layout(pad=PAD)

    rc = {
        'font.family':'Open Sans',
        'font.size' : font_size,
        'legend.fontsize' : font_size-2 if decrease_legend else font_size
        }

    plt.rcParams.update(rc)
    if disable_box:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    if subplots is None or subplots == 1:
        width = 6
        if height is None:
            height = width/ratio
        
        fig.set_size_inches(width, height)
    elif subplots == 2:
        width = 3
        if height is None:
            height = width/ratio

        fig.set_size_inches(width, height)

    
    
    return fig, ax

def default_matplotlib_save(fig: plt.figure, filename: str, dpi=300, pad=None, adjust_left = None):
    if pad is None:
        pad=PAD
    plt.tight_layout(pad=pad)
    
    if adjust_left is not None:
        plt.subplots_adjust(left=adjust_left)
    
    plt.savefig(filename, dpi=dpi)


olivedrab_02 = "#e1e8d3"
olivedrab_05 = '#b4c690'

steelblue_02 = '#dae6f0'
steelblue_05 = '#a2c0d9'

firebrick_02='#efd2d2'
firebrick_05='#c96767'