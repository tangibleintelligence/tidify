# `tidify`: Convert nested objects into tidy data

[![Build Status](https://cloud.drone.io/api/badges/tangibleintelligence/tidify/status.svg)](https://cloud.drone.io/tangibleintelligence/tidify)
[![PyPI version](https://badge.fury.io/py/tidify.svg)](https://badge.fury.io/py/tidify)

This package allows for simple conversion of arbitrarily nested data (of objects and arrays) into a format akin to
[Tidy Data](https://vita.had.co.nz/papers/tidy-data.pdf).

Arrays are expanded to multiple rows, with a new `.index` column created. Nested objects are expanded into multiple
columns with `.` (or customizable) separator.