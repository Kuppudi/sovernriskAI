"""CSV output with blank missing values and safe spreadsheet text."""

import csv
import io

from backend.app.schemas.api import ObservationOut
from backend.app.services.observations import serialize_observation


def protect_spreadsheet_text(value):
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value
    return value


def build_observation_csv(rows) -> str:
    output = io.StringIO(newline="")
    columns = list(ObservationOut.model_fields)
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()

    for row in rows:
        observation = serialize_observation(row).model_dump(mode="json")
        safe_values = {}
        for column, value in observation.items():
            safe_values[column] = protect_spreadsheet_text(value)
        writer.writerow(safe_values)

    return output.getvalue()
