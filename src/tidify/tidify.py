from functools import cmp_to_key, partial
from typing import List, Dict, Any, Union, Optional

import pandas as pd


def tidify(data: List[Dict[str, Any]], *, exclude: Optional[List[str]] = None, sep: str = ".") -> pd.DataFrame:
    """
    Convert `data` (an arbitrarily nested list of dictionaries) into tidy data format. Each element of the data list is considered a separate
    "record" and will be expanded into one or more rows (multiple rows if a data element contains arrays).

    Nested objects result in columns separated by dot (or otherwise) notation:

    ```python
    o = {
        'a': {
            "a": 1,
            "b": 2
        }
    }

    tidify([o]).columns => ["a.a", "a.b"]
    ```

    Nested arrays expand into rows:
    ```
    o = {
        "a": 1,
        "b": [
            {"sub1": 1, "sub2": 2},
            {"sub1": 3, "sub2": 4},
        ]
    }

    tidify([o]) =>

    a | b.index | b.sub1 | b.sub2
    1 | 0 | 1 | 2
    1 | 1 | 3 | 4
    ```

    Multiple arrays expand via cartesian product.

    `exclude` can be a list of dot-wise notated "paths" to exclude. For example, "a.a" in the first example, or "b.sub1" in the second
    example.
    """

    # Since some columns might be blank, we'll save to a list of flat records (dicts) with no nesting.
    tidy_data: List[Dict[str, Any]] = list()
    if exclude is None:
        exclude = list()
    convert_to_tidy(data, {}, tidy_data, exclude, sep)

    df = pd.DataFrame.from_records(tidy_data).convert_dtypes()

    # rearrange the columns of this df to be a little more sensible.

    cols: List[str] = df.columns.to_list()
    cols.sort(key=cmp_to_key(partial(col_comparator, sep=sep)))

    return df[cols]


def col_comparator(item1: str, item2: str, *, sep: str) -> int:
    """
    Sort by number of periods, then alphabetically, but with "index" coming first.
    That way you end up with similar columns grouped together.
    """
    # row_index is always first
    if item1 == "row_index":
        return -1
    if item2 == "row_index":
        return 1

    # Situations like a.b.c and a.b.c.index are always sorted with the `.index` one first
    if item1 == f"{item2}{sep}index":
        return -1
    if item2 == f"{item1}{sep}index":
        return 1

    # Differing number of periods? If so, less periods comes first
    # Exception occurs if one of them is the other + ".index". That means an array of primitives.
    item1_periods = item1.count(sep)
    item2_periods = item2.count(sep)

    if item1_periods != item2_periods:
        return item1_periods - item2_periods

    # Alright, same number of periods. Sort alphabetically *but* with "*.index" coming before
    if (
        item1.split(sep)[:-1] == item2.split(sep)[:-1]
        or item1.split(sep) == item2.split(sep)[:-1]
        or item1.split(sep)[:-1] == item2.split(sep)
    ):
        if item1.endswith(".index"):
            return -1
        if item2.endswith(".index"):
            return 1

    if item2 < item1:
        return 1
    else:
        return -1


def convert_to_tidy(
    remaining_data: Union[Dict[str, Any], List[Dict[str, Any]]],
    fixed_data: Dict[str, Any],
    tidy_data: List[Dict[str, Any]],
    exclude: List[str],
    sep: str,
):
    """
    Convert the information in remaining_data into tidy data and append to the tidy_data dict. For each row added from obj, include the information
    from fixed_data as well.

    Warning: recursive logic ahead :)
    """
    # If an iterable was passed in, need to make record(s) for each element
    if isinstance(remaining_data, list) or isinstance(remaining_data, tuple):
        for idx, row in enumerate(remaining_data):
            convert_to_tidy(row, {"row_index": idx}, tidy_data, exclude, sep)
    elif remaining_data is not None and len(remaining_data) > 0:
        # An object was passed in.
        # We can remove any keys which match the exclusion list
        remaining_data = {k: v for k, v in remaining_data.items() if k not in exclude}

        # Any arrays or subobjects on this object? If so, we need to expand on them
        arrays = [k for k, v in remaining_data.items() if isinstance(v, list) or isinstance(v, tuple)]
        subobjects = [k for k, v in remaining_data.items() if isinstance(v, dict)]

        if len(arrays) >= 1:
            # We'll expand on one of them (creating fixed_data of a row index) and pass the contents, as well as any other fields at this
            # level as remaining data.
            array_key = arrays[0]
            for sub_idx, sub_row_or_primitive in enumerate(remaining_data[array_key]):
                # Only thing we can fix right now is the array index column (and anything that was already fixed)
                fixed = {
                    **fixed_data,
                    f"{array_key}{sep}index": sub_idx,
                }
                # The values in this array get prepended with the array key, and everything else goes in straight
                # If this was an array of primitives (strings, ints, etc.) then we can use those directly. otherwise
                # need another level of nesting.
                if hasattr(sub_row_or_primitive, "items"):
                    remaining = {
                        **{f"{array_key}{sep}{k}": v for k, v in sub_row_or_primitive.items()},
                        **{k: v for k, v in remaining_data.items() if k != array_key},
                    }
                else:
                    remaining = {
                        f"{array_key}": sub_row_or_primitive,
                        **{k: v for k, v in remaining_data.items() if k != array_key},
                    }

                convert_to_tidy(remaining, fixed, tidy_data, exclude, sep)
        elif len(subobjects) >= 1:
            # Nothing new to fix here. But we can "flatten" the nesting of object into new top-level remaining_data
            remaining = dict()
            for subobject in subobjects:
                for k, v in remaining_data[subobject].items():
                    remaining[f"{subobject}{sep}{k}"] = v
            # everything else gets passed along too
            remaining.update({k: v for k, v in remaining_data.items() if k not in subobjects})

            convert_to_tidy(remaining, fixed_data, tidy_data, exclude, sep)
        else:
            # Nothing nested remains
            # we can add to the tidy data and move on now
            tidy_data.append({**fixed_data, **remaining_data})
