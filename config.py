regex_patterns = dict(
    MSISDN="^(?:\+30)?69\d{8}$",
    CLI="^(?:\+30)?2\d{9}$",
    Email="^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    AFM="^[0-4|7-9]\d{8}$"
)

labels = dict(
    yes= "Yes",
    probably_yes= "Probably Yes",
    probably_no= "Probably No",
    dk_na="Not enough data"
)

patterns = dict(
    system_id="^1-[A-Z0-9]+([-.\w]+)*$",
    greek_word="[\u0370-\u03FF\u1F00-\u1FFF]+"
)


categories = dict(
    system_id="System generated ID",
    greek_word="Greek word",
    min_unique_values="Less than 3 unique values",
    datetime="Datetime value"
)

min_unique_values = 3