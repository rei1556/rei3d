"""
MODELLOAD.PY

load a model from a .nlm file
"""

import NLDATA
import numpy

class Model:
    def __init__(self, modelPath):
        model = NLDATA.BinaryRecord.load(modelPath)
        if model.get("MAGIC_NM") != "NLMSH":
            raise IOError("Not a NLMesh!")
        count = model.get("tri#")
        self.pos = numpy.stack([numpy.frombuffer(model.get("tp%d" % c), dtype=numpy.float32).reshape(count, 3) for c in (1, 2, 3)], axis=1)
        self.uv = numpy.stack([numpy.stack([numpy.frombuffer(model.get("uv%da" % c), dtype=numpy.float32), numpy.frombuffer(model.get("uv%db" % c), dtype=numpy.float32)], axis=-1) for c in (1, 2, 3)], axis=1)
        self.matID = numpy.frombuffer(model.get("matID"), dtype=numpy.uint16)
    
    def getMesh(self): 
        return numpy.concatenate([self.pos, self.uv], axis=2).astype('f4').reshape(-1) # okay this is a lot cleaner