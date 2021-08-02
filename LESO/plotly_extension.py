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


