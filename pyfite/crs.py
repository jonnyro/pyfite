import re
import numpy as np
import pymap3d as p3d
from math import floor
from pyproj import CRS, Transformer
from typing import Callable, Optional, Tuple, Union
from .util import DECIMAL_REGEX

_OPTIONAL_OFFSET = f'(?: ({DECIMAL_REGEX}) ({DECIMAL_REGEX}) ({DECIMAL_REGEX}))?'
_ECEF_PROJ = "+proj=geocent +ellps=WGS84"
_GEODETIC_PROJ = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"

_activeEllipsoid = p3d.Ellipsoid()  # Default to WGS84


def SetActiveEllipsoid(ellipsoid: p3d.Ellipsoid = None) -> None:
    """Sets the ellipsoid upon which converters are built
    """
    if type(ellipsoid) is p3d.Ellipsoid:
        # TODO(rhite): Properly support different ellipsoids
        print('Currently only WGS84 has complete support - it is not advised the active ellipsoid be cahnged')
        raise RuntimeError("No existing support for ellipsoids other than WGS84")
        # _activeEllipsoid = ellipsoid
    else:
        raise RuntimeError("Can only act on an ellipsoid compatible with pymap3d")


class CrsDefError(Exception):
    """Exception for invalid CRS definitions.

    Thrown when a coordinate reference system is unable to parse necessary
    information from a provided string representation.
    """

    def __init__(self, message: str = 'Could not parse provided string representation of coordinate reference system'):
        super().__init__(message)


class CoordinateReferenceSystem:
    """
    """

    @staticmethod
    def fromStr(srep: str) -> 'CoordinateReferenceSystem':
        """
        """
        if not srep:
            raise RuntimeError('Cannot instantiate a CoordinateReferenceSystem without an empty string representation')
        else:
            if re.match('(?:ltp|enu)', srep, re.IGNORECASE):
                return LocalTangentPlane.fromStr(srep)
            elif re.match('(?:geodetic|gdc|lla)', srep, re.IGNORECASE):
                return Geodetic.fromStr(srep)
            elif re.match('(?:utm)', srep, re.IGNORECASE):
                return Utm.fromStr(srep)
            elif re.match('(?:ecef|gcc)', srep, re.IGNORECASE):
                return Geocentric.fromStr(srep)

    @property
    def offset(self):
        try:
            return self._offset
        except AttributeError:
            raise NotImplementedError('CoordinateReferenceSystem must set _offset')

    @offset.setter
    def offset(self, offset):
        self._offset = offset

    def _getOffsetStr(self):
        if self.offset != (0.0, 0.0, 0.0):
            return ' {} {} {}'.format(*self.offset)
        else:
            return ''


class LocalTangentPlane(CoordinateReferenceSystem):

    srepRegex = re.compile(f'(?:ltp|enu) ({DECIMAL_REGEX}) ({DECIMAL_REGEX}) ({DECIMAL_REGEX}){_OPTIONAL_OFFSET}', re.IGNORECASE)

    def __init__(self, lon: float, lat: float, alt: float, offset: Optional[Tuple[float, float, float]] = (0.0, 0.0, 0.0)):
        """Construct a local tangent plane CRS.

        Construct a local tangent plane coordinate reference system at the specified longitude, latitude,
        and altitude. Optionally, an offset may be provided that represents an offset within the tangent
        plane. Typically the additional offset is unnecessary, but can be useful for cases such as providing
        sets of points around a local origin that exists within the tangent plane.

        Args:
                lon: The longitude of the tangent plane origin
                lat: The latitude of the tangent plane origin
                alt: The altitude above the WGS84 ellipsoid of the tangent plane origin
                offset: The offset by which points are adjusted
        """
        self.lon, self.lat, self.alt, self._offset = lon, lat, alt, offset

    def __str__(self):
        return f'ENU {self.lon} {self.lat} {self.alt}' + self._getOffsetStr()

    @staticmethod
    def fromStr(srep: str) -> 'LocalTangentPlane':
        """
        """
        sm = LocalTangentPlane.srepRegex.match(srep)
        if sm:
            lon, lat, alt, offset = float(sm[1]), float(sm[2]), float(sm[3]), (0.0, 0.0, 0.0)
            if sm[4]:
                # The regex is defined such that either all 3 offset parameters are available, or none are
                offset = (float(sm[4]), float(sm[5]), float(sm[6]))
            return LocalTangentPlane(lon, lat, alt, offset)
        else:
            raise CrsDefError(f'Could not parse provided string representation for {LocalTangentPlane}: {srep}')


class Geocentric(CoordinateReferenceSystem):

    srepRegex = re.compile(f'(?:gcc|geocentric|ecef){_OPTIONAL_OFFSET}', re.IGNORECASE)

    def __init__(self, offset: Optional[Tuple[float, float, float]] = (0.0, 0.0, 0.0)):
        self._offset = offset

    def __str__(self):
        return 'GCC' + self._getOffsetStr()

    @staticmethod
    def fromStr(srep: str) -> 'Geocentric':
        sm = Geocentric.srepRegex.match(srep)
        if sm:
            offset = (0.0, 0.0, 0.0)
            if sm[1]:
                offset = (float(sm[1]), float(sm[2]), float(sm[3]))
            return Geocentric(offset)
        else:
            raise CrsDefError(f'Could not parse provided string representation for {Geocentric}: {srep}')

    def getProjStr(self) -> str:
        return _ECEF_PROJ


class Geodetic(CoordinateReferenceSystem):

    srepRegex = re.compile(f'(?:gdc|geodetic|lla){_OPTIONAL_OFFSET}', re.IGNORECASE)

    def __init__(self, offset: Optional[Tuple[float, float, float]] = (0.0, 0.0, 0.0)):
        self._offset = offset

    def __str__(self):
        return 'GDC' + self._getOffsetStr()

    @staticmethod
    def fromStr(srep: str) -> 'Geodetic':
        sm = Geodetic.srepRegex.match(srep)
        if sm:
            offset = (0.0, 0.0, 0.0)
            if sm[1]:
                offset = (float(sm[1]), float(sm[2]), float(sm[3]))
            return Geodetic(offset)
        else:
            raise CrsDefError(f'Could not parse provided string representation for {Geodetic}: {srep}')

    def getProjStr(self) -> str:
        return _GEODETIC_PROJ


class Utm(CoordinateReferenceSystem):

    srepRegex = re.compile(rf'(?:utm) (\d{{1,2}})(\w){_OPTIONAL_OFFSET}', re.IGNORECASE)

    def __init__(self, zone: int, south: bool, offset: Optional[Tuple[float, float, float]] = (0.0, 0.0, 0.0)):
        self.zone, self.south, self._offset = zone, south, offset

    def __str__(self):
        return 'UTM {}{}'.format(self.zone, 'S' if self.south else 'N') + self._getOffsetStr()

    @staticmethod
    def fromStr(srep: str) -> 'Utm':
        sm = Utm.srepRegex.match(srep)
        if sm:
            offset = (0.0, 0.0, 0.0)
            if sm[3]:
                offset = (float(sm[3]), float(sm[4]), float(sm[5]))
            return Utm(int(sm[1]), sm[2].upper() <= 'M', offset)
        else:
            raise CrsDefError(f'Could not parse provided string representation for {Utm}: {srep}')

    @staticmethod
    def fromPoint(lon: float, lat: float, alt: Optional[float] = 0.0) -> 'Utm':
        # TODO(rhite): handle special EU case
        return Utm(floor((lon + 180) / 360 * 60) + 1, lat < 0)

    def getProjStr(self) -> str:
        proj_str = f"+proj=utm +zone={self.zone} +ellps=WGS84"
        if self.south:
            proj_str += ' +south'

        return proj_str


class ProjCrs(CoordinateReferenceSystem):

    def __init__(self, proj_str: str):
        self.proj = proj_str

    def __str__(self):
        return self.proj

    @staticmethod
    def fromStr(srep: str) -> 'ProjCrs':
        return ProjCrs(srep)

    def getProjStr(self) -> str:
        return self.proj


class CoordinateConverter:
    """Converts points from one CRS to another.
    """

    def __init__(self, fromCrs: Union[CoordinateReferenceSystem, str], toCrs: Union[CoordinateReferenceSystem, str]):
        """Constructs a CoordinateConverter with a provided convert method

        A CoordinateConverter is constructed with the provided convert method.
        It is expected that the convert method provided adheres to the rules of
        the __call__ method of this class.

        Args:
                fromCrs: The CRS to convert points from
                toCrs: The CRS to convert points to
        """
        self.__fromOffset = fromCrs.offset
        self.__toOffset = toCrs.offset

        fromCrs = fromCrs if isinstance(fromCrs, CoordinateReferenceSystem) else CoordinateReferenceSystem.fromStr(fromCrs)
        toCrs = toCrs if isinstance(toCrs, CoordinateReferenceSystem) else CoordinateReferenceSystem.fromStr(toCrs)
        self.__convert = CoordinateConverter.__getConverter(fromCrs, toCrs)

    def __call__(self, points: np.ndarray) -> np.ndarray:
        """Convert a set of points to the targeted CRS.

        Args:
                points: A numpy array of 3D points with shape (N, 3)

        Returns:
                A set of points converted to the target CRS with shape (N, 3)
        """
        shape = np.asarray(points).shape
        if len(shape) is not 2 or shape[1] != 3:
            raise RuntimeError(f"Cannot convert non-3D points: shape was {shape}")
        else:
            return self.__convert(points + self.__fromOffset) - self.__toOffset

    def convert(self, points: np.ndarray) -> np.ndarray:
        """
        """
        return self.__call__(points)

    @staticmethod
    def __getConverter(fromCrs: CoordinateReferenceSystem, toCrs: CoordinateReferenceSystem) -> Callable[[np.ndarray], np.ndarray]:
        """
        """
        # note that offsets are handled in __call__ so they aren't here

        if type(fromCrs) is not LocalTangentPlane and type(toCrs) is not LocalTangentPlane:
            return CoordinateConverter.__getPyprojFunc(fromCrs.getProjStr(), toCrs.getProjStr())

        # Anything dealing with a local tangent plane isn't supported by PROJ, so use pymap3d
        if type(fromCrs) is LocalTangentPlane:

            if type(toCrs) is LocalTangentPlane:

                def c(points):
                    x, y, z = p3d.enu2ecef(points[:, 0], points[:, 1], points[:, 2], fromCrs.lat, fromCrs.lon, fromCrs.alt, ell=_activeEllipsoid)
                    x, y, z = p3d.ecef2enu(x, y, z, toCrs.lat, toCrs.lon, toCrs.alt, ell=_activeEllipsoid)
                    return np.column_stack((x, y, z))
                return c

            elif type(toCrs) is Geocentric:

                def c(points):
                    x, y, z = p3d.enu2ecef(points[:, 0], points[:, 1], points[:, 2], fromCrs.lat, fromCrs.lon, fromCrs.alt, ell=_activeEllipsoid)
                    return np.column_stack((x, y, z))
                return c

            elif type(toCrs) is Geodetic:

                def c(points):
                    lat, lon, alt = p3d.enu2geodetic(points[:, 0], points[:, 1], points[:, 2], fromCrs.lat, fromCrs.lon, fromCrs.alt, ell=_activeEllipsoid)
                    return np.column_stack((lon, lat, alt))
                return c

            elif type(toCrs) is Utm:

                def c(points):
                    lat, lon, alt = p3d.enu2geodetic(points[:, 0], points[:, 1], points[:, 2], fromCrs.lat, fromCrs.lon, fromCrs.alt, ell=_activeEllipsoid)
                    return CoordinateConverter.__getPyprojFunc(_GEODETIC_PROJ, toCrs.getProjStr())(np.column_stack((lon, lat, alt)))
                return c

        elif type(fromCrs) is Geocentric:
            def c(points):
                x, y, z = p3d.ecef2enu(points[:, 0], points[:, 1], points[:, 2], toCrs.lat, toCrs.lon, toCrs.alt, ell=_activeEllipsoid)
                return np.column_stack((x, y, z))
            return c

        elif type(fromCrs) is Geodetic:
            def c(points):
                lat, lon, alt = p3d.geodetic2enu(points[:, 1], points[:, 0], points[:, 2], toCrs.lat, toCrs.lon, toCrs.alt, ell=_activeEllipsoid)
                return np.column_stack((lon, lat, alt))
            return c

        elif type(fromCrs) is Utm:
            def c(points):
                points = CoordinateConverter.__getPyprojFunc(fromCrs.getProjStr(), _GEODETIC_PROJ)(points)
                lat, lon, alt = p3d.geodetic2enu(points[:, 1], points[:, 0], points[:, 2], toCrs.lat, toCrs.lon, toCrs.alt, ell=_activeEllipsoid)
                return np.column_stack((lon, lat, alt))
            return c

    @staticmethod
    def __getPyprojFunc(fromCrs: str, toCrs: str) -> Callable[[np.ndarray], np.ndarray]:
        def c(points):
            transformer = Transformer.from_crs(CRS.from_string(fromCrs), CRS.from_string(toCrs), always_xy=True)
            return np.column_stack(transformer.transform(points[:, 0], points[:, 1], points[:, 2]))
        return c
