import webbrowser
import os

style = """
<style> 
    html, body {
        height: 100%;
    }
    
    html {
        display: table;
        margin: auto;
    }
    
    body {
        display: table-cell;
        vertical-align: middle;
    }
</style>
"""
def add_centering_to_plotly_html(filename):
    with open(filename, 'r+') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if line.startswith('<head>'):   # find a pattern so that we can add next to that line
                lines[i] = lines[i]+style
        f.truncate()
        f.seek(0)                                           # rewrite into the file
        for line in lines:
            f.write(line)
    return None

def add_title_to_plotly_html(filename, title):
    title = f"<title> {title} </title>"
    with open(filename, 'r+') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if line.startswith('<head>'):   # find a pattern so that we can add next to that line
                lines[i] = lines[i]+title
        f.truncate()
        f.seek(0)                                           # rewrite into the file
        for line in lines:
            f.write(line)

def open_html(filename):
    cwd = os.getcwd()
    filepath = os.path.join('file:\\\\',cwd,filename)

    webbrowser.register('chrome',
        None,
        webbrowser.BackgroundBrowser("C://Program Files (x86)//Google//Chrome//Application//chrome.exe"))
    webbrowser.get('chrome').open(filepath)


def add_author_source(fig, author="Seth van Wieringen", source="Source will be displayed here", x=None, y=None):

    x = [0, 1] if x is None else x
    y = [-0.45, -0.4] if y is None else y
    
    fig.add_annotation(text=author,
                    xref="paper", yref="paper",
                    yanchor='bottom', xanchor='left',
                    x=x[0], y=y[0], showarrow=False)

    fig.add_annotation(text="Source:",
                    xref="paper", yref="paper",
                    yanchor='bottom', xanchor='right',
                    x=x[1], y=y[1], showarrow=False)
    fig.add_annotation(text=source,
                    xref="paper", yref="paper",
                    yanchor='bottom', xanchor='right',
                    font_size=10,
                    x=x[1], y=y[0], showarrow=False)
    
    return fig

def thesis_default_styling(fig):
    
    fig.update_layout(
        # template
        template="simple_white",
        # move legend
        legend_yanchor='middle', 
        legend_y=0.5,
        # set size
        width=600,
        height=350,
        # remove margins
        margin = dict(
            l=0,
            r=0,
            t=0,
            b=0
        ),
        # remove title if present
        title=None,
        ) 
    return fig   

def lighten_color(color, amount=0.5, return_as_hex=True):
    """
    Taken from:
    https://stackoverflow.com/questions/37765197/darken-or-lighten-a-color-in-matplotlib
    Lightens the given color by multiplying (1-luminosity) by the given amount.
    Input can be matplotlib color string, hex string, or RGB tuple.

    Examples:
    >> lighten_color('g', 0.3)
    >> lighten_color('#F034A3', 0.6)
    >> lighten_color((.3,.55,.1), 0.5)
    """
    import matplotlib.colors as mc
    import colorsys
    try:
        c = mc.cnames[color]
    except:
        c = color
    c = colorsys.rgb_to_hls(*mc.to_rgb(c))
    hls = c[0], 1 - amount * (1 - c[1]), c[2]
    lc = colorsys.hls_to_rgb(*hls)
    if return_as_hex:
        lc = '#%02x%02x%02x' % tuple([round(x * 255) for x in lc])
    return lc

