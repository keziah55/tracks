import numpy as np

summaryArgs = [('Time (hours)', sum),
                ('Distance (km)', sum),
                ('Avg. speed (km/h)', max),
                ('Calories', sum),
                ('Gear', lambda v: np.around(np.mean(v)))]