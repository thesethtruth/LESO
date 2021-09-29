def add_single_line(ax, df, column, color, label=None, dash=False, marker='o', alpha=1):

    ax.plot(
        column,
        data=df,
        marker=marker,
        linestyle= '-' if not dash else '--',
        mfc=color,
        color=color,
        label=label if label != None else "_d",
        alpha=alpha,
    )
    ax.legend(loc="lower left", frameon=False)

def add_range(ax, df, lower_col, upper_col, color, label):

    ax.fill_between(
        df.index,
        upper_col,
        lower_col,
        data=df,
        color=color,
        label=label,
        alpha=0.2,
    )    
    add_single_line(ax, df, lower_col, color, alpha=0.5, marker=None)
    add_single_line(ax, df, upper_col, color, alpha=0.5, marker=None)
    
    ax.set_xlim([df.index[0]-1, df.index[-1]+1])
    ax.set_ylim([0, df.max().max()*1.05])
    
    
    ax.legend(loc="lower left", frameon=False)