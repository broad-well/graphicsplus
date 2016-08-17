# Michael's GraphicsPlus module

from graphics import *
import json, lzma, os, traceback

gplus_options = {
    "debug": False,
    "compress": False,
    "default_window_size": {
        "x": 800,
        "y": 800
    }
}

def gplus_attribute(key, value="ATTRIBUTE_NULL_VALUE"):
    """Changes GraphicsPlus options.
    When called with 1 argument, this function returns the value of the requested option.
    When called with 2 arguments, this function sets the value of the requested option and returns the set value.
    May raise KeyError if the key is not present and the function was called with 1 argument."""
    if value == "ATTRIBUTE_NULL_VALUE":
        return gplus_options[key]
    else:
        gplus_options[key] = value
        return gplus_options[key]

def gplus_get_center(obj):
    """Reserved for GraphicsPlus internal use"""
    # Returns the centroid of a given shape (Rectangle, Circle, Oval, Line, Polygon, Image).
    if isinstance(obj, Polygon):
        xs = [a.x for a in obj.getPoints()]
        ys = [a.y for a in obj.getPoints()]
        return Point((max(xs)+min(xs))/2, (max(ys)+min(ys))/2)
    elif type(obj) in [Image, Text]:
        return obj.getAnchor()
    elif type(obj) in [Rectangle, Oval, Circle, Line]:
        return obj.getCenter()
    elif type(obj) == list:
        mx = max([a.x for a in obj])
        Mx = min([a.x for a in obj])
        xs = [a.x for a in obj]

    else:
        raise RuntimeError("Argument type not supported: " + str(type(obj)))

def gplus_relation(p1, p2):
    """Reserved for GraphicsPlus internal use"""
    # p1 in gplus_relation to p2
    return (p1.x-p2.x, p1.y-p2.y)

def gplus_vector_apply(center, rel):
    """Reserved for GraphicsPlus internal use"""
    return Point(center.x+rel.x, center.y+rel.y)

def gplus_invert_point(p):
    """Reserved for GraphicsPlus internal use"""
    return Point(0-p.x, 0-p.y)

def gplus_dump_point(p):
    """Reserved for GraphicsPlus internal use"""
    assert type(p) == Point
    ob = {
        "type":"Point",
        "x":p.x,
        "y":p.y,
        "config":p.config
    }
    return ob

def gplus_parse_point(parsed):
    """Reserved for GraphicsPlus internal use"""
    assert parsed["type"] == "Point"
    p = Point(parsed["x"], parsed["y"])
    p.config = parsed["config"]
    return p

def gplus_dump_poly(obj):
    """Reserved for GraphicsPlus internal use"""
    assert type(obj) == Polygon
    attrs = {
        "type":"Polygon",
        "config":obj.config,
        "points":[],
        "center":gplus_dump_point(gplus_get_center(obj))
    }
    for p in obj.getPoints():
        attrs["points"].append(gplus_dump_point(Point(*gplus_relation(p, gplus_get_center(obj)))))
    return attrs

def gplus_parse_poly(parsed, c):
    """Reserved for GraphicsPlus internal use"""
    assert parsed["type"] == "Polygon"
    points = [gplus_parse_point(a_) for a_ in parsed["points"]]
    poly = Polygon([gplus_vector_apply(c, p) for p in points])
    poly.config = parsed["config"]
    return poly

def gplus_dump_line(line):
    """Reserved for GraphicsPlus internal use"""
    assert type(line) == Line
    return {
        "type":"Line",
        "config":line.config,
        "offset":gplus_dump_point(Point(*gplus_relation(line.p1, gplus_get_center(line))))
    }

def gplus_parse_line(parsed, c):
    """Reserved for GraphicsPlus internal use"""
    assert parsed["type"] == "Line"
    p1 = gplus_vector_apply(c, gplus_parse_point(parsed["offset"]))
    l = Line(p1, gplus_vector_apply(c, gplus_invert_point(gplus_parse_point(parsed["offset"]))))
    l.config = parsed["config"]
    return l

def gplus_dump_rect(rect):
    """Reserved for GraphicsPlus internal use"""
    assert type(rect) == Rectangle
    attrs = {
        "type":"Rectangle",
        "config":rect.config,
        "offset":gplus_dump_point(Point(*gplus_relation(rect.p1, gplus_get_center(rect))))
    }
    return attrs

def gplus_parse_rect(parsed, c):
    """Reserved for GraphicsPlus internal use"""
    assert parsed["type"] == "Rectangle"
    offset = gplus_parse_point(parsed["offset"])
    rect = Rectangle(gplus_vector_apply(c, offset), gplus_vector_apply(c, gplus_invert_point(offset)))
    rect.config = parsed["config"]
    return rect

def gplus_dump_text(text):
    """Reserved for GraphicsPlus internal use"""
    assert type(text) == Text
    attrs = {
        "type":"Text",
        "config":text.config
    }
    return attrs

def gplus_parse_text(parsed, a):
    """Reserved for GraphicsPlus internal use"""
    assert parsed["type"] == "Text"
    tex = Text(a, "")
    tex.config = parsed["config"]
    return tex

gplus_types = {
    "Polygon": (gplus_dump_poly, gplus_parse_poly),
    "Line": (gplus_dump_line, gplus_parse_line),
    "Point": (gplus_dump_point, gplus_parse_point),
    "Rectangle": (gplus_dump_rect, gplus_parse_rect),
    "Text": (gplus_dump_text, gplus_parse_text)
}

def gplus_parse(string, args):
    """Reserved for GraphicsPlus internal use"""
    return gplus_parse_obj(json.loads(string), args)

def gplus_parse_obj(obj, args):
    """Reserved for GraphicsPlus internal use"""
    try:
        return gplus_types[obj["type"]][1](obj, *args)
    except:
        traceback.print_exc()
        raise Exception("parser of specified type not available: {}".format(obj["type"]))
        return None

def gplus_dump(gobj):
    """Reserved for GraphicsPlus internal use"""
    return json.dumps(gplus_dump_obj(gobj))

def gplus_dump_obj(gobj):
    """Reserved for GraphicsPlus internal use"""
    try:
        return gplus_types[type(gobj).__name__][0](gobj)
    except:
        traceback.print_exc()
        raise Exception("dumper for specified Graphics object not available: {}".format(type(gobj)))
        return None

def gplus_get_filehandler(write, fname):
    """Reserved for GraphicsPlus internal use"""
    if gplus_options["compress"]:
        if write:
            if os.path.exists(fname):
                return lzma.open(fname, "w")
            else:
                return lzma.open(fname, "x")
        else:
            return lzma.open(fname, "r")
    else:
        if write:
            return open(fname, "w+b")
        else:
            return open(fname, "rb")

def export_graphics(obj, filename):
    """Exports the given graphical object to the specified filename."""
    with gplus_get_filehandler(True, filename) as fil:
        fil.write(gplus_dump(obj).encode())
    return True

def import_graphics(filename, anchorpoint):
    """Reads the file with the filename argument and returns the graphical object that the file contents represent.
    Supply anchorpoint for all objects other than GraphWin for the coordinates (location) of the returning graphical object."""
    c = None
    with gplus_get_filehandler(False, filename) as fil:
        c = fil.read().decode()
    return gplus_parse(c, (anchorpoint))

# Window800;800;462%163.25->Polygon121.14%25.25|14.24%-36|;

def gplus_dump_window(w):
    """Reserved for GraphicsPlus internal use"""
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
    if gplus_options["debug"]:
        print("Debug: " + str(attrs))
    return attrs

def gplus_parse_window(parsed, title="Graphics Window"):
    """Reserved for GraphicsPlus internal use"""
    assert parsed["type"] == "GraphWin"
    win = GraphWin(title, parsed["width"], parsed["height"])
    for item in parsed["objects"]:
        sts = gplus_seek_types(item["object"])
        if sts == None: raise RuntimeError("Malformed expression encountered: " + item)
        sts[1](item["object"], gplus_parse_point(item["center"])).draw(win)
    return win

def graphic_pack(o, center, filename):
    """Packs the specified objects and exports the pack to the specified filename."""
    pack = []
    for obj in o:
        pack.append({
            "type":"graphicobj",
            "centeroffset":gplus_dump_point(Point(*gplus_relation(gplus_get_center(obj), center))),
            "object":gplus_dump_obj(o)
        })
    with gplus_get_filehandler(True, filename) as fil:
        fil.write(json.dumps(pack).encode())

def graphic_unpack(filename, location):
    """Unpacks the pack at the file with the provided filename. The pack is placed with the provided location as the anchor point. Returns a list of graphical objects to draw."""
    with gplus_get_filehandler(False, filename) as fil:
        parsed = json.loads(fil.read().decode())
    assert type(parsed) == list
    output = []
    for obj in parsed:
        if obj["type"] == "graphicobj":
            output.append(gplus_parse_obj(obj["object"], [gplus_vector_apply(location, gplus_parse_point(obj["centeroffset"]))]))
    if gplus_options["debug"]:
        print("output: {}, parsed: {}".format(output, parsed))
    return output

def gplus_draw(objs, win):
    """Draws the provided objects to the provided window. Great for use with graphic_unpack."""
    [o.draw(win) for o in objs]

gplus_types["GraphWin"] = (gplus_dump_window, gplus_parse_window)
gplus_supported_types = list(gplus_types.keys())
