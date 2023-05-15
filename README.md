# UKGenderPayGap
Visualisations of the UK gender pay gap data. Publically avaliable, not often seen: https://gender-pay-gap.service.gov.uk/

## Datasets

 - The main dataset is from the [UK Government's gender pay gap service](https://gender-pay-gap.service.gov.uk/). As more years are released, they can be downloaded and appended to the database:

```
python3 parser.py ../RawData/UK\ Gender\ Pay\ Gap\ Data\ -\ 2019\ to\ 2020.csv
```

 - [ONS data](https://www.ons.gov.uk/aboutus/transparencyandgovernance/freedomofinformationfoi/ukpostcodestownsandcounties) is required to turn the address postcode to a county or unitary authority for the map. This data is rather complicated, thankfully the [Borough of Camden](https://www.data.gov.uk/dataset/7ec10db7-c8f4-4a40-8d82-8921935b4865/national-statistics-postcode-lookup-uk) has processed this data nicely for us. To append the county or local authority data, give `parser.py` a file downloaded from the above with the exact name:

```
python3 parser.py ../RawData/National_Statistics_Postcode_Lookup_UK.csv
```
