# Utilities for various things


# Smooth a typical sqlite result query
# delta is the "radius" of the smooth (We will average +/- delta values from each one)
# rows should be a List of 2-element Tuples (Timestamp, value)
def smoothTimeseries(rows, delta):
    smoothedRows = []
    for i in range(0,len(rows)):
        minData = max(i - delta, 0)
        maxData = min(i + delta, len(rows))
        slice = rows[minData:maxData+1]
        dataSum = 0
        for entry in slice:
            dataSum += float(entry[1])
        smoothedRows.append( (rows[i][0], dataSum / len(slice)) )
    return smoothedRows

