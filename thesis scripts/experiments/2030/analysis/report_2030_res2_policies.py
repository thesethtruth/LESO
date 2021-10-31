# %%
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from LESO.plotting import default_matplotlib_save, default_matplotlib_style
from util_2030_postprocess_tools import (
    plot_grouped_stackedbars,
    get_data_from_db,
    gcloud_read_experiment,
    pv_col,
    wind_col,
    bat2_col,
    bat6_col,
    bat10_col,
    total_bat_col,
    batcols,
    bivar_tech_dict,
    grid_col,
)

#%%
## constants
FOLDER = Path(__file__).parent
RESOURCE_FOLDER = FOLDER / "resources"
IMAGE_FOLDER = FOLDER / "images"
IMAGE_FOLDER.mkdir(exist_ok=True)
RESOURCE_FOLDER.mkdir(exist_ok=True)

COLLECTION = "gld2030"
RUN_ID = "3010_RES2"

color = {
    "PV": "#edc645",
    "wind": "steelblue",
    "battery": "darkseagreen",
    "grid": "darkgrey",
}

idx_map = {
    "2030RES_Foodvalley ": "Foodvalley",
    "2030RES_NoordVeluwe": "Noord-Veluwe",
    "2030RES_ArnhemNijmegen": "Arnhem Nijmegen",
    "2030RES_Rivierenland": "Rivierenland",
    "2030RES_Cleantech": "Cleantech",
    "2030RES_Achterhoek": "Achterhoek",
}

col_map = {pv_col: "PV", wind_col: "wind", total_bat_col: "battery", grid_col: "grid"}

#%% load in results

resdf = pd.read_pickle(RESOURCE_FOLDER / "RES_deployment.pkl")
resdf.columns = ["wind", "PV"]

db = get_data_from_db(collection=COLLECTION, run_id=RUN_ID, force_refresh=False)
db = db.query("target_RE_strategy == 'current_projection_excl_export'")
db.set_index("scenario", inplace=True)
db.rename(col_map, inplace=True, axis=1)
db.rename(idx_map, inplace=True, axis=0)
db.sort_index(inplace=True)

#%%
lesodf = db[["wind", "PV"]].copy()

#%% wind factor
lesodf["wind"] = lesodf["wind"] * 2.8
resdf["wind"] = resdf["wind"] * 2.8

leso_total = (lesodf["wind"] + lesodf["PV"]).values
res_total = (resdf["wind"] + resdf["PV"]).values


#%%
fig, axi = plt.subplots(nrows=2, ncols=6, figsize=(6, 3))

plt.tight_layout(pad=0.3)

rc = {
    "font.family": "Open Sans",
    "font.size": 10,
    "legend.fontsize": 8,
    "legend.title_fontsize": 8
}
colors = {
    "wind": "steelblue",
    "PV": "#edc645",
}
ridx = resdf.index
lidx = lesodf.index
max_radius = np.max([leso_total, res_total])
labels = [i.replace(" ", "\n").replace("-", "\n") for i in sorted(idx_map.values())]
labels.extend([""] * 6)
hline_specs = dict(color="k", alpha=0.5, zorder=0, linestyle="--", linewidth=0.2)
vline_specs = dict(color="k", alpha=0.8, zorder=0, linewidth=0.5)
light_colors = [(242, 215, 124, 255), (125, 167, 202, 255)]
light_colors = [(x/255) for y in light_colors for x in y]
light_colors = [tuple(light_colors[:4]), tuple(light_colors[4:])]
light_colors.reverse()

for i, ax in enumerate(axi.T):
    lesodf.T[lidx[i]].plot.pie(
        subplots=True,
        ax=ax[0],
        frame=False,
        startangle=90,
        radius=leso_total[i],
        labels=None,
        colors=colors.values()
    )
    pie = resdf.T[ridx[i]].plot.pie(
        subplots=True,
        ax=ax[1],
        frame=False,
        startangle=90,
        radius=res_total[i],
        labels=None,
        colors=light_colors
    )
    ax[0].axvline(x=0, **vline_specs)
    ax[1].plot([0, 0], [0, 2 * max_radius], **vline_specs)
    if i != 5 and i != 11:
        ax[0].axhline(y=0, **hline_specs)
        ax[1].axhline(y=0, **hline_specs)
    else:
        ax[0].plot([-max_radius, 0], [0, 0], **hline_specs)
        ax[1].plot([-max_radius, 0], [0, 0], **hline_specs)

for i, ax in enumerate(axi.flat):
    ax.set_xticklabels([])
    ax.set_yticklabels([])

    ax.axis("equal")
    ax.set_xlim([-max_radius, max_radius])
    ax.set_ylim([-max_radius, max_radius])
    ax.title.set_text(labels[i])
    ax.set_ylabel("")
    ax.set_xlabel("")
plt.subplots_adjust(wspace=0, hspace=0)
plt.legend(
    handles = [Patch(facecolor=c, edgecolor=c,label=l) for l, c in colors.items()],
    frameon=False,
    ncol=2,
    bbox_to_anchor=(-1.9,-0.3),
    loc="lower center",
    title="yearly energy yield (PJ)"
)
axi[0, 0].set_ylabel("optimisation")
axi[1, 0].set_ylabel("RES policy")

plt.subplots_adjust(top=0.82)

plt.rcParams.update(rc)

default_matplotlib_save(fig, filename=IMAGE_FOLDER / "report_2030_res_pie_policies_light.png")