"""
Do you love a certain data access server that begins with
ERD? Do you love writing out each variable in XML files?
Well have I got a script for you.
"""

import netCDF4 as nc4

global ERRDAP_NPY_TYPE_MAP
global ERDDAP_DATAVARIABLE_STR
ERDDAP_NPY_TYPE_MAP = {
    "byte": "byte",
    "int8":"byte",
    "int16":"short",
    "uint16":"char",
    "int32":"int",
    "int64":"long",
    "float32":"float",
    "float64":"double",
    "|S1": "String"
}

ERDDAP_DATAVARIABLE_STR = """
<dataVariable>
    <sourceName>{sourceName}</sourceName>
    <destinationName>{destinationName}</destinationName>
    <dataType>{dataType}</dataType>
    <addAttributes>
    </addAttributes>
</dataVariable>
"""

def assemble_basic_erddap_variables_dict(data: nc4.Dataset) -> dict:
    """
    Given a NetCDF4.Dataset object, return a dict of each
    variable and its corresponding ERDDAP type. Include basic
    fields such as sourceName, destinationName.
    """

    out = dict()

    for varname, var in data.variables.items():
        out[varname] = dict(
            dataType=ERDDAP_NPY_TYPE_MAP.get(var.dtype.__str__(), "float64"),
            sourceName=varname,
            destinationName=varname,
        )

    return out

def dump_variables_as_erddap(vardict: dict) -> str:
    """
    Take the fields in vardict and dump them out in string
    form like you'd see in ERDDAP datasets.xml.
    """

    return "\n".join(s for s in map(
            lambda x: ERDDAP_DATAVARIABLE_STR.format(**x),
            vardict.values()
        )
    )

if __name__ == "__main__":
    nc = nc4.Dataset("/home/dalton/gulfhub-data-conversion/data/enhanced/DeepLG/apex/leidos/apx4901043_ctd.nc")
    d = assemble_basic_erddap_variables_dict(nc)
    print(dump_variables_as_erddap(d))
