import pandas as pd
import i2x.der_hca.PlotUtils as pltutl
import argparse, os


def main(h5path, savename=""):
    with pd.HDFStore(h5path, mode='r') as hdf:
        df = pd.read_hdf(hdf, key="/post_process/analysis").sort_index()
        # fig = pd.pivot_table(df.loc[100].droplevel(1).loc[:,["ts", "feqa"]], values="feqa", index="ts", columns="lv").plot(backend="plotly", markers=True)
        # fig.update_traces(connectgaps=True)
        # ln = 100

        ## TODO: get the tv as a text annotation/as hover text for plot
        lns = [50, 75, 90, 100]
        lvs = [125,150,175,200,225,250]
        markers = ["circle", "square", "diamond", "cross"]
        fig = pltutl.make_subplots(rows=len(lns), cols=1, shared_xaxes=True,
                                   vertical_spacing=0.03,
                                   subplot_titles=[f"plot {i}" for i in range(len(lns))])
        colors = pltutl.ColorList()
        subplot_titles = {}
        for i, ln in enumerate(reversed(lns)):
            colors.setidx(0)
            for lv in lvs:
                tmp = df.loc[(ln,lv), ["ts", "feqa"]]
                fig.add_trace(pltutl.go.Scatter(
                    x=tmp["ts"]/60, y=tmp["feqa"],
                    text=tmp.index,
                    name = f"$L_v = {lv}\%$",
                    mode="lines+markers",
                    line_color=colors(),
                    marker_symbol=markers[i],
                    legendgroup=f"{ln}",
                    legendgrouptitle_text=fr"$L_n = {ln}\%$",
                    hovertemplate=f"<b>Ln={ln}%</b>, <b>Lv={lv}%</b><br>" + 
                    "Feqa=%{y:.3f}<br>tv=%{text} [s]<br>tv+ts=%{x:.2f} [min]<extra></extra>" 
                ), row=i+1, col=1)
                # fig.update_layout(title=fr"$L_n = {ln}%$", row=i+1, col=1)
                subplot_titles[f"plot {i}"] = fr"$L_n = {ln}\%$"
                colors.step()
    
    fig.update_layout(template="plotly_white", font_size=20, font_family="Arial")
    fig.update_layout(legend=dict(groupclick="toggleitem", xanchor="right", x=1),
                      margin_t=30, margin_b=10)
    fig.for_each_annotation(lambda x:  x.update(text=subplot_titles.get(x.text,x.text),
                                                font_size=20))
    fig.update_xaxes(title=r"$t_v + t_s [\text{min}]$", row=len(lns), col=1)
    fig.update_yaxes(title=r"$F_{EQA}\;[\text{p.u.}]$s")
    fig.update_layout(width=800, height=800)
    
    if savename:
        ext = os.path.splitext(savename)[1]
        if ext == "html":
            fig.write_html(savename, include_plotlyjs="cdn")
        else:
            fig.write_image(savename)
    else:
        fig.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="transformer thermal modeling simulation")
    parser.add_argument("h5path", help="h5 solution")
    parser.add_argument("--savename", help="save name for figure (html, png, pdf, svg)", default="")
    args = parser.parse_args()
    
    # h5path = "../scratch/avgmin_results/res.h5"
    main(args.h5path, args.savename)
    
