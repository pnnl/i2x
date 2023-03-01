import i2x.api as i2x
import i2x.opendss_interface as dssint

if __name__=="__main__":
    G = i2x.load_builtin_graph('ieee9500')
    pvder, gender, batder, largeder, resloads, loadkw = i2x.parse_opendss_graph(G)