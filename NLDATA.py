"""
NLDATA API v1.0.3
Creative Commons Commercial-ShareAlike 
https://creativecommons.org/licenses/by/4.0/
contact: nlfar15562547@gmail.com / bsky @nlfar.neocities.org
last updated timestamp: 1135AM UTC -8 03/08/2026

NLDATA:
Data is serialized as such:

char[8] NAME/Header
optional uint16_t Length
char[Length] data

Any atomic datatype (floats, integers) is little endian by default. 
Strings are handled by the implementation, but assumed to be little-endian.

Matrix2D is a special case:
First byte of length = width
Second byte of length = height
Length is calculated by width*height, and values are stored as float32, and are stored sequentially, left to right, top to bottom.

|   char    |   length  |   type    |   name            |
|-----------|-----------|-----------|-------------------|
|   i       |   4       |   uint32  |   unsigned int    |
|   I       |   4       |   int32   |   signed int      |
|   l       |   2       |   uint16  |   unsigned long   |
|   L       |   2       |   int16   |   signed long     |
|   b       |   8       |   uint64  |   unsigned big    |
|   B       |   8       |   int64   |   signed big      |
|   c       |   1       |   uint8   |   char            |
|   C       |   1       |   int8    |   signed char     |
|   o       |   1       |   bool    |   boolean         |
|   0       |   0/1     |   false   |   false           |
|   1       |   0/1     |   true    |   true            |
|   s       |   varies  |   string  |   string          |
|   S       |   varies  |   bytes   |   bytestring      |
|   v       |   12      |   Vec3    |   Vector3         |
|   V       |   8       |   Vec2    |   Vector2         |
|   w       |   16      |   Vec4    |   Vector4         |
|   W       |   4       |   Color   |   RGBAColor       |
|   p       |   varies  |   data    |   PascalData      |
|   f       |   4       |   float32 |   754f32          |
|   F       |   8       |   float64 |   754f64          |
|   m       |   varies  |   2darray |   Matrix2D        |
"""

import struct
import os
from dataclasses import dataclass, field
from typing import Any, List, Tuple

def _packKey(name: str) -> bytes:
    return name.encode("utf-8")[:8].ljust(8, b"\x00")

def _unpackKey(raw: bytes) -> str:
    return raw.rstrip(b"\x00").decode("utf-8")

def _encodeValue(tc: str, value: Any) -> bytes:
    if tc == "i":  return struct.pack("<I", value)
    if tc == "I":  return struct.pack("<i", value)
    if tc == "l":  return struct.pack("<H", value)
    if tc == "L":  return struct.pack("<h", value)
    if tc == "b":  return struct.pack("<Q", value)
    if tc == "B":  return struct.pack("<q", value)
    if tc == "c":
        if isinstance(value, str):
            return value.encode("latin-1")[:1].ljust(1, b"\x00")
        return struct.pack("B", value & 0xFF)
    if tc == "C":  return struct.pack("<b", value)
    if tc == "o":  return b"\xff" if value else b"\x00"
    if tc in ("0", "1"):  return b"\x00" if tc == "0" else b"\xff"
    if tc == "s":
        raw = value.encode("utf-8")
        return struct.pack("<H", len(raw)) + raw
    if tc == "S":
        raw = value if isinstance(value, (bytes, bytearray)) else value.encode("latin-1")
        return struct.pack("<H", len(raw)) + raw
    if tc == "v":
        x, y, z = value; return struct.pack("<fff", x, y, z)
    if tc == "V":
        x, y = value; return struct.pack("<ff", x, y)
    if tc == "w":
        x, y, z, w = value; return struct.pack("<ffff", x, y, z, w)
    if tc == "W":
        r, g, b, a = value; return struct.pack("BBBB", r, g, b, a)
    if tc == "p":
        raw = value if isinstance(value, (bytes, bytearray)) else b"\x00"
        return struct.pack("<H", len(raw)) + raw
    if tc == "f":  return struct.pack("<f", value)
    if tc == "F":  return struct.pack("<d", value)
    if tc == "m":
        if isinstance(value, (list, tuple)):
            if len(value) == 3 and isinstance(value[0], int) and isinstance(value[1], int):
                width, height, raw = value
            else:
                rows = value
                height = len(rows)
                width = len(rows[0]) if height > 0 else 0
                raw = [float(x) for row in rows for x in row]
        else:
            raise ValueError("Matrix2D value must be (w,h,values) or 2D list of rows")
        if not (0 <= width <= 255 and 0 <= height <= 255):
            raise ValueError("Matrix2D width/height must fit in one byte (0-255)")
        if len(raw) != width * height:
            raise ValueError(f"Matrix2D data length {len(raw)} does not match width*height {width*height}")
        header = struct.pack("BB", width, height)
        body = b"".join(struct.pack("<f", float(v)) for v in raw)
        return header + body
    raise ValueError("Unknown type char: %r" % tc)  # no-op for safety

def _decodeValue(tc: str, data: bytes, offset: int):
    if tc == "i":  return struct.unpack_from("<I", data, offset)[0], offset + 4
    if tc == "I":  return struct.unpack_from("<i", data, offset)[0], offset + 4
    if tc == "l":  return struct.unpack_from("<H", data, offset)[0], offset + 2
    if tc == "L":  return struct.unpack_from("<h", data, offset)[0], offset + 2
    if tc == "b":  return struct.unpack_from("<Q", data, offset)[0], offset + 8
    if tc == "B":  return struct.unpack_from("<q", data, offset)[0], offset + 8
    if tc == "c":  return data[offset:offset+1].decode("latin-1"), offset + 1
    if tc == "C":  return struct.unpack_from("<b", data, offset)[0], offset + 1
    if tc in ("o", "0", "1"): return (data[offset] != 0), offset + 1
    if tc == "s":
        length = struct.unpack_from("<H", data, offset)[0]; offset += 2
        return data[offset:offset+length].decode("utf-8"), offset + length
    if tc == "S":
        length = struct.unpack_from("<H", data, offset)[0]; offset += 2
        return bytes(data[offset:offset+length]), offset + length
    if tc == "v":
        x, y, z = struct.unpack_from("<fff", data, offset); return (x, y, z), offset + 12
    if tc == "V":
        x, y = struct.unpack_from("<ff", data, offset); return (x, y), offset + 8
    if tc == "w":
        x, y, z, w = struct.unpack_from("<ffff", data, offset); return (x, y, z, w), offset + 16
    if tc == "W":
        r, g, b, a = struct.unpack_from("BBBB", data, offset); return (r, g, b, a), offset + 4
    if tc == "p":
        length = struct.unpack_from("<H", data, offset)[0]; offset += 2
        return bytes(data[offset:offset+length]), offset + length
    if tc == "m":
        if offset + 2 > len(data):
            raise ValueError(f"Not enough data for Matrix2D header at offset {offset}")
        width = data[offset]; height = data[offset+1]; offset += 2
        count = width * height
        if count:
            fmt = "<" + ("f" * count)
            # ensure enough bytes
            needed = 4 * count
            if offset + needed > len(data):
                raise ValueError(f"Not enough data for Matrix2D values at offset {offset}")
            flat = list(struct.unpack_from(fmt, data, offset))
            offset += needed
        else:
            flat = []
        rows: List[List[float]] = []
        for r in range(height):
            start = r * width
            rows.append(flat[start:start+width])
        return rows, offset
    if tc == "f":  
        return struct.unpack_from("<f", data, offset)[0], offset + 4
    if tc == "F":  
        return struct.unpack_from("<d", data, offset)[0], offset + 8
    raise ValueError("Unknown type char: %r" % tc)


@dataclass # new and exciting way to store 3 values 
class BinaryField:
    key: str
    typeChar: str
    value: Any

    def serialize(self) -> bytes:
        return _packKey(self.key) + self.typeChar.encode("ascii") + _encodeValue(self.typeChar, self.value)

    @classmethod
    def deserializeFrom(cls, data: bytes, offset: int):
        if offset + 9 > len(data):
            raise ValueError(f"Not enough data at offset {offset}")
        key = _unpackKey(data[offset:offset+8]); offset += 8
        typeChar = chr(data[offset]); offset += 1
        value, offset = _decodeValue(typeChar, data, offset)
        return cls(key=key, typeChar=typeChar, value=value), offset

    def __repr__(self):
        if self.typeChar != 'p': return "BinaryField(key=%r, type=%r, value=%r)" % (self.key, self.typeChar, self.value)
        else: return "BinaryField(key=%r, type=%r, length=%r)" % (self.key, self.typeChar, len(self.value))


@dataclass
class BinaryRecord:
    fields: List[BinaryField] = field(default_factory=list)

    def add(self, key: str, typeChar: str, value: Any = None) -> "BinaryRecord":
        if typeChar == "0": value = False
        elif typeChar == "1": value = True
        for f in self.fields:
            if f.key == key:
                f.typeChar = typeChar
                f.value = value
                return self
        self.fields.append(BinaryField(key, typeChar, value))
        return self

    def get(self, key: str) -> Any:
        for f in self.fields:
            if f.key == key: return f.value
        raise KeyError(key)

    def getField(self, key: str) -> BinaryField:
        for f in self.fields:
            if f.key == key: return f
        raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        return any(f.key == key for f in self.fields)

    def serialize(self) -> bytes:
        return b"".join(f.serialize() for f in self.fields) # "python must be readable" sure ok man

    @classmethod
    def deserialize(cls, data: bytes) -> "BinaryRecord":
        record = cls()
        offset = 0
        while offset < len(data):
            bf, offset = BinaryField.deserializeFrom(data, offset)
            record.fields.append(bf)
        return record

    def save(self, path: str) -> None:
        dirpart = os.path.dirname(os.path.abspath(path))
        if dirpart: os.makedirs(dirpart, exist_ok=True)
        with open(path, "wb") as fh: fh.write(self.serialize())

    @classmethod
    def load(cls, path: str) -> "BinaryRecord":
        with open(path, "rb") as fh: return cls.deserialize(fh.read())

    def __repr__(self):
        inner = ",\n  ".join(repr(f) for f in self.fields)
        return "BinaryRecord([\n  %s\n])" % inner if self.fields else "BinaryRecord([])"
