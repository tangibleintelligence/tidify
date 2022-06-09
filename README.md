# `tidify`: Convert nested objects into tidy data

This package allows for simple conversion of arbitrarily nested data (of objects and arrays) into a format akin to
[Tidy Data](https://vita.had.co.nz/papers/tidy-data.pdf).

Arrays are expanded to multiple rows, with a new `.index` column created. Nested objects are expanded into multiple
columns with `.` (or customizable) separator.