"""
Do you love a certain data access server that begins with
ERD? Do you love writing out each variable in XML files?
Well have I got a script for you.
"""

import pathlib
import netCDF4 as nc4
import typing
import numpy as np
import sys

global ERRDAP_NPY_TYPE_MAP
global ERDDAP_DATAVARIABLE_STR
ERDDAP_NPY_TYPE_MAP = {
    "byte": "byte",
    "int8": "byte",
    "int16": "short",
    "uint16": "char",
    "int32": "int",
    "int64": "long",
    "float": "float",
    "float32": "float",
    "float64": "double",
    "|S1": "String",
    "string": "String",
    "str": "String",
}

# TODO string.Template
# {attributes} is left-justified as the strings substituted in
# contain the necessary spaces to indent
ERDDAP_DATAVARIABLE_STR = """
<dataVariable>
  <sourceName>{sourceName}</sourceName>
  <destinationName>{destinationName}</destinationName>
  <dataType>{dataType}</dataType>
  <addAttributes>
{attributes}
  </addAttributes>
</dataVariable>"""

ERDDAP_ATT_TAG = '    <att name={name} type="{type}">{value}</att>'

def create_att_tags(atts: typing.Dict[str, str]):
    return "\n".join(
        s for s in map(
            lambda _t: ERDDAP_ATT_TAG.format(
                **get_attr_name_type_val_for_erddap(_t[0], _t[1])
            ), atts.items()))

def get_attr_name_type_val_for_erddap(name: str, attr: typing.Any) -> typing.Dict[str, str]:
    """
    Returns dict of {name: name, type: type, value: value}
    """

    out = dict(name=name)

    if isinstance(attr, np.generic):
        out["type"] = ERDDAP_NPY_TYPE_MAP.get(attr.dtype.__str__(), "float")
        out["value"] = attr.__str__()

    elif isinstance(attr, np.ndarray):
        out["type"] = ERDDAP_NPY_TYPE_MAP.get(attr.dtype.__str__(), "float")
        out["value"] = " ".join(str(v) for v in attr)

    elif isinstance(attr, list):
        # type of first element, could go wrong as lists aren't
        # required to have single type; cross that bridge later
        out["type"] = ERDDAP_NPY_TYPE_MAP.get(str(type(attr[0])), "String")
        out["value"] = " ".join(str(v) for v in attr)

    else:
        out["type"] = ERDDAP_NPY_TYPE_MAP.get(str(type(attr)), "String")
        out["value"] = str(attr)

    return out

def load_var_attr_dict(nc_var: nc4.Variable) -> typing.Dict[str, str]:
    return {k: nc_var.getncattr(k) for k in nc_var.ncattrs()}

def assemble_erddap_variables_dict(data: nc4.Dataset) -> dict:
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
            attributes=load_var_attr_dict(var)
        )

    return out

def dump_variables_as_erddap_string(vardict: dict) -> str:
    """
    Take the fields in vardict and dump them out in string
    form like you'd see in ERDDAP datasets.xml.
    """

    return "\n".join(s for s in map(
            lambda x: ERDDAP_DATAVARIABLE_STR.format(
                attributes=create_att_tags(x.pop("attributes")),
                **x
            ),
            vardict.values()
        )
    )

def main(datapath: str, fragments_path: str, outname: str) -> None:
    """
    Assemble a full datasets.xml file for a given set of NetCDF files
    located at <datapath>. Write the document out as datasets.<outname>.xml
    to fragments_path.
    """

    frag_path = pathlib.Path(fragments_path)

    # load user-defined <dataset></datasset> block
    with open(frag_path / "datasets.fragment.xml", "r") as f:
        fragment = f.read()

    # iterate through datasets in datapath; for each, fill in the needed
    # fields in <dataset> block and create <dataVariable> blocks for each
    # variable in the dataset.
    # TODO make a generator
    datasets = []
    for ncfile in pathlib.Path(datapath).glob("*.nc"):

        _fname = ncfile.name
        nc = nc4.Dataset(ncfile)
        fields_dict = {
            "dataset_id": _fname.split(".nc")[0],
            "filename": _fname,
            "dataVariables": dump_variables_as_erddap_string(assemble_erddap_variables_dict(nc))
        }
        

        # fill the fragment, add to list
        datasets.append(fragment.format(**fields_dict))

    # load generic datasets.xml header fragment
    with open(pathlib.Path(fragments_path) / "datasets.header.xml", "r") as f:
        header = f.read()

    # concatenate header with body
    out_str = "{}\n{}\n</erddapDatasets>".format(header, "\n".join(datasets))

    with open(frag_path / f"datasets.{outname}.xml", "w") as f:
        f.write(out_str)

if __name__ == "__main__":
    main(
        sys.argv[1], # data path
        sys.argv[2], # path to fragments (datasets.header.xml, datasets.fragment.xml)
        sys.argv[3]  # string to to format output (datasets.{}.xml), written to fragments path
    )