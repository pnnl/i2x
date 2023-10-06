import sys
import os
if os.path.abspath("..") not in sys.path:
    sys.path.append(os.path.abspath(".."))
import hca as h

def main(title, include=None, exclude=None):
    ### load config (note: just changes to defaults)
    inputs = h.load_config("defaults.json")

    if include is not None:
        inputs["metrics"]["include"] = include
    if exclude is not None:
        inputs["metrics"]["exclude"] = exclude
    h.print_config(inputs["metrics"], title=title)

    metrics = h.HCAMetrics(**inputs["metrics"])
    metrics.print_metrics()

if __name__ == "__main__":
    
    main("All metrics")
    
    include= ["thermal", {"voltage": ["vmax", "vdiff"]}]
    main("Include Metrics Test", include=include)

    exclude= ["voltage", "thermal"]
    main("Exclude Metrics Test", exclude=exclude)

    exclude = {"voltage": "vmax"}
    main("Another Exclude Metrics Test", exclude=exclude)