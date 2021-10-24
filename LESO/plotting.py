import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
from pathlib import Path


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


def crop_transparency_top_bottom(
    single_filepath: str = None,
    folder_to_crop: str = None,
    file_ext_to_crop: str = None,
    crop_top=False,
    crop_bottom=True,
    override_original=False,
    crop_suffix="_cropped",
    pad=1,
):
    if single_filepath and type(single_filepath) is str:
        fps = [single_filepath]
    if folder_to_crop is not None:
        if file_ext_to_crop is None:
            raise SyntaxError("Cannot use folder cropping without a file extension! Please supply one.")
        else:
            f = Path(folder_to_crop)
            list(f.glob(f"*.{file_ext_to_crop}"))
            fps = list(f.glob(f"*.{file_ext_to_crop}"))

    for fp_in in fps:

        p_in = Path(fp_in)
        im = Image.open(p_in)
        alpha_channel = np.asarray(im)[:, :, 3].T
        alpha_rows = alpha_channel.sum(axis=0)
        first_content_row, last_content_row = alpha_rows.nonzero()[0][[0, -1]]
        width, height = im.size

        upper = first_content_row - pad if crop_top else 0
        lower = last_content_row + pad if crop_bottom else height
        left = 0
        right = width

        cropped = im.crop((left, upper, right, lower))
        
        if not override_original:
            p_out = p_in.parent / (p_in.stem + crop_suffix + p_in.suffix)
        else:
            p_out = p_in
        
        cropped.save(p_out)


olivedrab_02 = "#e1e8d3"
olivedrab_05 = '#b4c690'

steelblue_02 = '#dae6f0'
steelblue_05 = '#a2c0d9'

firebrick_02='#efd2d2'
firebrick_05='#c96767'

