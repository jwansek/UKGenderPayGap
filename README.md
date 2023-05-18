# UKGenderPayGap
Visualisations of the UK gender pay gap data. Publically avaliable, not often seen: https://gender-pay-gap.service.gov.uk/

## Dataset Notes

Most of the information comes from the [UK Government website](https://gender-pay-gap.service.gov.uk/). The data is provided as a single CSV for each year, so I made a script that parses these CSV files and builds a relational database. Using a relational database has a number of advantages including fast processing thanks to MySQL queries and significantly lowering the amount of repeated data. Data from this source alone would not be enough, however. The information about emloyers is limited, so I HTML scrape the *companies house* government website to fetch additional data about all of the employers. Each employer has a number of SIC codes, a code system for what business an employer is in, but there are thousands of them, too many to use in practice. Thankfully the government provides a list of SIC section headers which give a more palatable idea of what an employer is doing. Making the chloropleth map was a significant challenge. The datasets provide us with an address of the employer, but this is not enough to pinpoint its location because the county or local authority in the postal system is not the same as the `offical' one used by the local authorities system. Instead, we use ONS data to get the local authority or county name of an employer proper. The ONS data is very large and comprehend, thankfully the [London Borough of Camden](https://www.data.gov.uk/dataset/7ec10db7-c8f4-4a40-8d82-8921935b4865/national-statistics-postcode-lookup-uk) produced a processed version of it which is what we use. We scrape this data and append it to the database.

There are some issues with these datasets. For instance, the chloropleth map might not be especially useful, since it bases off of the employers' registered address, if an employer has many branches, only their head office will appear on the map. Sometimes there are only a few data points in a dataset, which can sometimes lead to distortion, even with using the median- for example female bonus pay in the waste management industry.

## Dataset Usage

 - The main dataset is from the [UK Government's gender pay gap service](https://gender-pay-gap.service.gov.uk/). As more years are released, they can be downloaded and appended to the database:

```
python3 parser.py ../RawData/UK\ Gender\ Pay\ Gap\ Data\ -\ 2019\ to\ 2020.csv
```

 - [ONS data](https://www.ons.gov.uk/aboutus/transparencyandgovernance/freedomofinformationfoi/ukpostcodestownsandcounties) is required to turn the address postcode to a county or unitary authority for the map. This data is rather complicated, thankfully the [Borough of Camden](https://www.data.gov.uk/dataset/7ec10db7-c8f4-4a40-8d82-8921935b4865/national-statistics-postcode-lookup-uk) has processed this data nicely for us. To append the county or local authority data, give `parser.py` a file downloaded from the above with the exact name:

```
python3 parser.py ../RawData/National_Statistics_Postcode_Lookup_UK.csv
```
