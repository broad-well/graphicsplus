# Michael's GraphicsPlus module

from graphics import *
import json
gplus_debug = False

def gplus_get_center(obj):
    # Returns the centroid of a given shape (Rectangle, Circle, Oval, Line, Polygon, Image).
    if isinstance(obj, Polygon):
        xs = [a.x for a in obj.getPoints()]
        ys = [a.y for a in obj.getPoints()]
        return Point((max(xs)+min(xs))/2, (max(ys)+min(ys))/2)
    elif isinstance(obj, Image):
        return obj.getAnchor()
    elif type(obj) in [Line, Oval, Circle, Rectangle]:
        return obj.getCenter()
    else:
        raise RuntimeError("Argument type not supported")

def gplus_relation(p1, p2):
    # p1 in gplus_relation to p2
    return (p1.x-p2.x, p1.y-p2.y)

def gplus_vector_apply(center, rel):
    return Point(center.x+rel.x, center.y+rel.y)

def gplus_invert_point(p):
    return Point(0-p.x, 0-p.y)

def gplus_dump_point(p):
    assert type(p) == Point
    return json.dumps({
        "type":"Point",
        "x":p.x,
        "y":p.y,
        "config":p.config
    })

def gplus_parse_point(s):
    parsed = json.loads(s)
    assert parsed["type"] == "Point"
    p = Point(parsed["x"], parsed["y"])
    p.config = parsed["config"]
    return p

def gplus_dump_poly(obj):
    assert type(obj) == Polygon
    attrs = {
        "type":"Polygon",
        "config":obj.config,
        "points":[],
        "center":gplus_dump_point(gplus_get_center(obj))
    }
    for p in obj.getPoints():
        attrs["points"].append(gplus_dump_point(Point(*gplus_relation(p, gplus_get_center(obj)))))
    return json.dumps(attrs)

def gplus_parse_poly(s, c):
    parsed = json.loads(s)
    assert parsed["type"] == "Polygon"
    points = [gplus_parse_point(a_) for a_ in parsed["points"]]
    poly = Polygon([gplus_vector_apply(c, p) for p in points])
    poly.config = parsed["config"]
    return poly

def gplus_dump_line(line):
    assert type(line) == Line
    attrs = {
        "type":"Line",
        "config":line.config,
        "center":gplus_dump_point(gplus_get_center(line)),
        "offset":gplus_dump_point(Point(*gplus_relation(line.p1, gplus_get_center(line))))
    }
    return json.dumps(attrs)

def gplus_parse_line(s, c):
    parsed = json.loads(s)
    assert parsed["type"] == "Line"
    p1 = gplus_vector_apply(c, gplus_parse_point(parsed["offset"]))
    l = Line(p1, gplus_vector_apply(c, gplus_invert_point(gplus_parse_point(parsed["offset"]))))
    l.config = parsed["config"]
    return l

gplus_types = {
    "Polygon": (gplus_dump_poly, gplus_parse_poly),
    "Line": (gplus_dump_line, gplus_parse_line),
    "Point": (gplus_dump_point, gplus_parse_point),
}

def gplus_seek_types(objtype):
    for key in gplus_types.keys():
        if (type(objtype) == type and key == objtype.__name__) or (type(objtype) == str and json.loads(objtype)["type"] == key):
            return gplus_types[key]
    return None

def export_graphics(obj, filename):
    # Exports the given object (shapes: Rectangle, Circle, Oval, Line, Polygon) and GraphWin.
    parsetuple = gplus_seek_types(type(obj))
    if parsetuple == None:
        print("export_graphics failure: {} objects are unsupported".format(type(obj).__name__))
        return False
    else:
        with open(filename, "w+") as fil:
            fil.write(parsetuple[0](obj))
        return True

def import_graphics(filename, anchorpoint):
    c = None
    with open(filename) as fil:
        c = fil.read()
    parsetuple = gplus_seek_types(c)
    if parsetuple == None:
        print("import_graphics error: file not supported")
        return False
    else:
        return parsetuple[1](c, anchorpoint)

# Window800;800;462%163.25->Polygon121.14%25.25|14.24%-36|;

def gplus_dump_window(w):
    attrs = {
        "type":"GraphWin",
        "width":w.width,
        "height":w.height,
        "objects":[]
    }
    for i in w.items:
        fun = gplus_seek_types(type(i))
        if fun == None: raise RuntimeError("{} graphics object not supported".format(type(i).__name__))
        attrs["objects"].append({"center":gplus_dump_point(gplus_get_center(i)), "object":fun[0](i)})
    assert len(attrs["objects"]) == len(w.items)
    if gplus_debug:
        print("Debug: " + str(attrs))
    return json.dumps(attrs)

def gplus_parse_window(s, title="Graphics Window"):
    parsed = json.loads(s)
    assert parsed["type"] == "GraphWin"
    win = GraphWin(title, parsed["width"], parsed["height"])
    for item in parsed["objects"]:
        sts = gplus_seek_types(item["object"])
        if sts == None: raise RuntimeError("Malformed expression encountered: " + item)
        sts[1](item["object"], gplus_parse_point(item["center"])).draw(win)
    return win

gplus_types["GraphWin"] = (gplus_dump_window, gplus_parse_window)

gplus_supported_types = gplus_types.keys()
