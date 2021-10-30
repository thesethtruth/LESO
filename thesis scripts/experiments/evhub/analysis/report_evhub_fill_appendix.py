#%%
from pathlib import Path
from copy import copy

IMAGE_FOLDER = Path(__file__).parent / "images" / "bivariate and deployment"


#%%

plot_list = list(IMAGE_FOLDER.glob("*.png"))
bivars = [plot for plot in plot_list if "_bivar" in str(plot)]

grid_policy = {
    "0.0": "1",
    "0.5": "2",
    "1.0": "3",
    "1.5": "4",
}

tech_trans = {"pv": "PV", "wind": "wind", "bat": "battery"}

WIDTH = 5

#%%
template = r"""
\begin{figure}[H]
    \centering
    \includegraphics[width=WIDTHin]{images/FILENAME.png}
    \caption{ZZZ deployment on the uncertainty plane spanned by XXX and YYY capacity cost for GGG MW grid capacity \textit{(policy PPP)}}
    \label{fig:FILENAME}
\end{figure}
"""
figures = {}
for plot in bivars:
    fn = plot.stem
    details = fn.split("-")[1].split("_")

    grid_cap = details[0]
    policy = grid_policy[grid_cap]
    x = tech_trans[details[2]]
    y = tech_trans[details[4]]
    z = details[-1] if details[-1] == "PV" else details[-1].title()
    _template = copy(template)

    template_map = {
        "WIDTH": str(WIDTH),
        "FILENAME": fn,
        "XXX": x,
        "YYY": y,
        "ZZZ": z,
        "GGG": grid_cap,
        "PPP": policy,
    }
    for word, replacement in template_map.items():
        _template = _template.replace(word, replacement)

    figures.update({
        grid_cap+z+x+y: _template
    })

d_items = figures.items()

s_items = sorted(d_items)

for key, value in s_items:
    print(value)
